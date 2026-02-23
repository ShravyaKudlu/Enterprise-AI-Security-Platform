import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models import (
    SecurityTest,
    ModelRun,
    StyleVariant,
    EvaluationScore,
    TestStatus,
    RunStatus,
    Scenario,
)
from app.services.variant_generator import VariantGenerator
from app.services.leakage_detector import LeakageDetector
from app.services.risk_scorer import RiskScorer
from app.services.compliance_mapper import ComplianceMapper

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """Orchestrate the execution of security tests."""

    def __init__(self, db: Session):
        self.db = db
        self.variant_generator = VariantGenerator(db)
        self.leakage_detector = LeakageDetector()
        self.risk_scorer = RiskScorer()
        self.compliance_mapper = ComplianceMapper()

    def create_test(
        self,
        test_name: str,
        attack_scenario_id: int,
        baseline_prompts: List[str],
        techniques: List[str],
        target_models: List[Dict],
        variants_per_technique: int = 2,
        description: str = "",
    ) -> SecurityTest:
        """Create a new security test configuration."""
        # Verify scenario exists
        scenario = (
            self.db.query(Scenario).filter(Scenario.id == attack_scenario_id).first()
        )

        if not scenario:
            raise ValueError(f"Scenario {attack_scenario_id} not found")

        # Create baseline prompts
        baseline_records = []
        for prompt_text in baseline_prompts:
            from app.models import BaselinePrompt

            bp = BaselinePrompt(prompt_text=prompt_text, scenario_id=attack_scenario_id)
            self.db.add(bp)
            baseline_records.append(bp)

        self.db.flush()  # Get IDs for baseline prompts

        # Create security test
        test = SecurityTest(
            test_name=test_name,
            description=description,
            status=TestStatus.QUEUED,
            attack_scenario_id=attack_scenario_id,
            target_models=target_models,
            baseline_prompts=[
                {"id": bp.id, "text": bp.prompt_text} for bp in baseline_records
            ],
            techniques=techniques,
            variants_per_technique=variants_per_technique,
        )

        self.db.add(test)
        self.db.commit()

        logger.info(f"Created security test {test.id}: {test_name}")

        return test

    def prepare_test_execution(self, test_id: int) -> List[Dict]:
        """
        Generate variants and create model run jobs.

        Returns:
            List of job configurations for RQ workers
        """
        test = self.db.query(SecurityTest).filter(SecurityTest.id == test_id).first()

        if not test:
            raise ValueError(f"Test {test_id} not found")

        # Update status
        test.status = TestStatus.RUNNING
        self.db.commit()

        # Get baseline prompts
        baseline_ids = [bp["id"] for bp in test.baseline_prompts]

        jobs = []

        # Generate variants for each baseline prompt
        for baseline_id in baseline_ids:
            variants = self.variant_generator.generate_variants(
                baseline_prompt_id=baseline_id,
                scenario_id=test.attack_scenario_id,
                techniques=test.techniques,
                count_per_technique=test.variants_per_technique,
            )

            # Create model run records for each variant and target model
            for variant in variants:
                for model_config in test.target_models:
                    model_run = ModelRun(
                        security_test_id=test_id,
                        style_variant_id=variant.id,
                        model_name=model_config.get("model", "unknown"),
                        model_vendor=model_config.get("adapter", "unknown"),
                        model_type=model_config.get("model_type", "public"),
                        status=RunStatus.QUEUED,
                    )

                    self.db.add(model_run)
                    self.db.flush()

                    jobs.append(
                        {
                            "job_id": model_run.id,
                            "model_run_id": model_run.id,
                            "adapter": model_config.get("adapter"),
                            "model": model_config.get("model"),
                            "prompt": variant.variant_text,
                        }
                    )

        self.db.commit()

        logger.info(f"Prepared {len(jobs)} model runs for test {test_id}")

        return jobs

    def evaluate_run(self, model_run_id: int, response_text: str) -> EvaluationScore:
        """
        Evaluate a model run for data leakage.

        Args:
            model_run_id: ID of the model run
            response_text: The model's response

        Returns:
            EvaluationScore record
        """
        model_run = self.db.query(ModelRun).filter(ModelRun.id == model_run_id).first()

        if not model_run:
            raise ValueError(f"Model run {model_run_id} not found")

        # Detect leakage
        detection_result = self.leakage_detector.detect(response_text)

        # Calculate risk score
        scenario = (
            self.db.query(Scenario)
            .join(StyleVariant, StyleVariant.scenario_id == Scenario.id)
            .filter(StyleVariant.id == model_run.style_variant_id)
            .first()
        )

        data_classification = (
            scenario.data_classification if scenario else "confidential"
        )

        risk_result = self.risk_scorer.calculate_risk_score(
            detection_result=detection_result,
            data_classification=data_classification,
            model_type=model_run.model_type or "public",
        )

        # Map to compliance
        compliance_violations = self.compliance_mapper.map_to_compliance(
            detection_result.categories
        )

        # Generate remediation
        remediation = ""
        if detection_result.categories:
            primary_category = detection_result.categories[0]
            remediation = self.compliance_mapper.generate_remediation(
                primary_category, risk_result["risk_level"]
            )

        # Determine if vendor promise held (enterprise models only)
        vendor_promise_held = None
        if model_run.model_type == "enterprise":
            vendor_promise_held = not detection_result.leakage_detected

        # Create evaluation score
        score = EvaluationScore(
            model_run_id=model_run_id,
            leakage_detected=detection_result.leakage_detected,
            leakage_categories=detection_result.categories,
            confidence_scores=detection_result.confidence_scores,
            evidence_snippets=detection_result.evidence_snippets,
            risk_score=risk_result["risk_score"],
            risk_level=risk_result["risk_level"],
            data_classification=primary_category
            if detection_result.categories
            else "UNCLASSIFIED",
            compliance_violations=compliance_violations,
            vendor_promise_held=vendor_promise_held,
            scoring_rationale=risk_result["scoring_rationale"],
            remediation=remediation,
        )

        self.db.add(score)

        # Update model run status
        model_run.status = RunStatus.COMPLETED
        model_run.response_text = response_text

        self.db.commit()

        logger.info(
            f"Evaluated model run {model_run_id}: risk={risk_result['risk_level']}"
        )

        return score

    def check_test_completion(self, test_id: int) -> bool:
        """Check if all model runs for a test are completed."""
        test = self.db.query(SecurityTest).filter(SecurityTest.id == test_id).first()

        if not test:
            return False

        total_runs = (
            self.db.query(ModelRun).filter(ModelRun.security_test_id == test_id).count()
        )

        completed_runs = (
            self.db.query(ModelRun)
            .filter(
                ModelRun.security_test_id == test_id,
                ModelRun.status.in_([RunStatus.COMPLETED, RunStatus.FAILED]),
            )
            .count()
        )

        if total_runs > 0 and completed_runs == total_runs:
            test.status = TestStatus.COMPLETED
            from datetime import datetime

            test.completed_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Test {test_id} completed")
            return True

        return False

    def get_test_progress(self, test_id: int) -> Dict:
        """Get progress information for a test."""
        from datetime import datetime

        test = self.db.query(SecurityTest).filter(SecurityTest.id == test_id).first()

        if not test:
            raise ValueError(f"Test {test_id} not found")

        total_runs = (
            self.db.query(ModelRun).filter(ModelRun.security_test_id == test_id).count()
        )

        completed_runs = (
            self.db.query(ModelRun)
            .filter(
                ModelRun.security_test_id == test_id,
                ModelRun.status == RunStatus.COMPLETED,
            )
            .count()
        )

        failed_runs = (
            self.db.query(ModelRun)
            .filter(
                ModelRun.security_test_id == test_id,
                ModelRun.status == RunStatus.FAILED,
            )
            .count()
        )

        leakage_count = (
            self.db.query(EvaluationScore)
            .join(ModelRun, ModelRun.id == EvaluationScore.model_run_id)
            .filter(
                ModelRun.security_test_id == test_id,
                EvaluationScore.leakage_detected == True,
            )
            .count()
        )

        percent_complete = (completed_runs / total_runs * 100) if total_runs > 0 else 0

        # Calculate time estimates
        elapsed_seconds = 0
        avg_time_per_run = 10  # Default 10 seconds per run
        estimated_remaining_seconds = 0

        if test.created_at:
            elapsed_seconds = (datetime.utcnow() - test.created_at).total_seconds()
            if completed_runs > 0:
                avg_time_per_run = elapsed_seconds / completed_runs
                remaining_runs = total_runs - completed_runs
                estimated_remaining_seconds = remaining_runs * avg_time_per_run

        return {
            "test_id": test_id,
            "status": test.status,
            "progress": {
                "total_runs": total_runs,
                "completed_runs": completed_runs,
                "failed_runs": failed_runs,
                "percent_complete": round(percent_complete, 1),
                "elapsed_seconds": round(elapsed_seconds, 1),
                "estimated_remaining_seconds": round(estimated_remaining_seconds, 1),
                "avg_time_per_run": round(avg_time_per_run, 1),
            },
            "results_summary": {
                "runs_completed": completed_runs,
                "data_leakage_detected": leakage_count,
                "models_tested": len(test.target_models) if test.target_models else 0,
            },
        }
