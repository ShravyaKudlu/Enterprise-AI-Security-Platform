from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.db import get_db
from app.services.test_orchestrator import TestOrchestrator
from app.models import SecurityTest, TestStatus

router = APIRouter(prefix="/security-tests", tags=["security-tests"])


class TargetModelConfig(BaseModel):
    adapter: str
    model: str
    model_type: Optional[str] = "public"


class RunSecurityTestRequest(BaseModel):
    test_name: str
    attack_scenario_id: int
    baseline_prompts: List[str]
    techniques: List[str]
    target_models: List[TargetModelConfig]
    description: Optional[str] = ""
    variants_per_technique: Optional[int] = 2


class RunSecurityTestResponse(BaseModel):
    test_id: int
    status: str
    variants_to_generate: int
    model_runs_to_execute: int
    estimated_time_minutes: int
    job_ids: List[str]


@router.post("/run", response_model=RunSecurityTestResponse)
def run_security_test(request: RunSecurityTestRequest, db: Session = Depends(get_db)):
    """Create and queue a new security test."""
    try:
        orchestrator = TestOrchestrator(db)

        # Validate request
        if len(request.test_name) < 3 or len(request.test_name) > 100:
            raise HTTPException(
                status_code=400, detail="Test name must be between 3 and 100 characters"
            )

        if len(request.baseline_prompts) == 0 or len(request.baseline_prompts) > 50:
            raise HTTPException(
                status_code=400, detail="Must provide between 1 and 50 baseline prompts"
            )

        if len(request.techniques) == 0:
            raise HTTPException(
                status_code=400, detail="Must specify at least one technique"
            )

        if len(request.target_models) == 0:
            raise HTTPException(
                status_code=400, detail="Must specify at least one target model"
            )

        # Create test
        test = orchestrator.create_test(
            test_name=request.test_name,
            attack_scenario_id=request.attack_scenario_id,
            baseline_prompts=request.baseline_prompts,
            techniques=request.techniques,
            target_models=[m.dict() for m in request.target_models],
            variants_per_technique=request.variants_per_technique,
            description=request.description,
        )

        # Prepare jobs
        jobs = orchestrator.prepare_test_execution(test.id)

        # Execute jobs synchronously with progress tracking
        import logging
        import time

        logger = logging.getLogger(__name__)
        logger.info(f"Executing {len(jobs)} jobs synchronously")

        from app.workers.model_execution import execute_model_run
        from app.models import SecurityTest as ST, TestStatus

        # Update test status to running
        test.status = TestStatus.RUNNING
        db.commit()

        job_ids = []
        start_time = time.time()

        for i, job in enumerate(jobs):
            job_data = {**job, "test_id": test.id}

            # Log progress
            elapsed = time.time() - start_time
            avg_time_per_job = elapsed / (i + 1) if i > 0 else 30
            remaining_jobs = len(jobs) - i - 1
            estimated_remaining = remaining_jobs * avg_time_per_job

            logger.info(
                f"Progress: {i + 1}/{len(jobs)} jobs completed. Est. remaining: {estimated_remaining:.0f}s"
            )

            # Run synchronously
            try:
                result = execute_model_run(job_data)
                job_ids.append(f"sync-job-{i}")
                logger.info(f"Job {i + 1} completed successfully")
            except Exception as e:
                logger.error(f"Job {i + 1} failed: {e}")
                job_ids.append(f"sync-job-{i}-failed")

        # Estimate time: ~30 seconds per model run
        estimated_minutes = max(1, len(jobs) * 30 // 60)

        return RunSecurityTestResponse(
            test_id=test.id,
            status=TestStatus.QUEUED,
            variants_to_generate=len(request.baseline_prompts)
            * len(request.techniques)
            * request.variants_per_technique,
            model_runs_to_execute=len(jobs),
            estimated_time_minutes=estimated_minutes,
            job_ids=job_ids,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}/status")
def get_test_status(test_id: int, db: Session = Depends(get_db)):
    """Get real-time status and progress of a security test."""
    try:
        orchestrator = TestOrchestrator(db)
        progress = orchestrator.get_test_progress(test_id)
        return progress
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}")
def get_test_results(test_id: int, db: Session = Depends(get_db)):
    """Get full test results including all model runs and evaluations."""
    from app.models import ModelRun, EvaluationScore, StyleVariant

    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get all model runs with evaluations
    runs = (
        db.query(ModelRun, EvaluationScore)
        .outerjoin(EvaluationScore, EvaluationScore.model_run_id == ModelRun.id)
        .filter(ModelRun.security_test_id == test_id)
        .all()
    )

    results = []
    for model_run, evaluation in runs:
        variant = (
            db.query(StyleVariant)
            .filter(StyleVariant.id == model_run.style_variant_id)
            .first()
        )

        results.append(
            {
                "run_id": model_run.id,
                "model_name": model_run.model_name,
                "model_vendor": model_run.model_vendor,
                "model_type": model_run.model_type,
                "status": model_run.status,
                "technique": variant.technique if variant else None,
                "response_text": model_run.response_text
                if model_run.response_text
                else None,
                "response_preview": model_run.response_text[:200]
                if model_run.response_text
                else None,
                "evaluation": {
                    "leakage_detected": evaluation.leakage_detected
                    if evaluation
                    else None,
                    "risk_score": evaluation.risk_score if evaluation else None,
                    "risk_level": evaluation.risk_level if evaluation else None,
                    "categories": evaluation.leakage_categories if evaluation else [],
                }
                if evaluation
                else None,
            }
        )

    return {
        "test_id": test.id,
        "test_name": test.test_name,
        "status": test.status,
        "created_at": test.created_at,
        "completed_at": test.completed_at,
        "target_models": test.target_models,
        "techniques": test.techniques,
        "total_runs": len(results),
        "runs": results,
    }
