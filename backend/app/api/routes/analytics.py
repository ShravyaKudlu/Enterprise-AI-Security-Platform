from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.core.db import get_db
from app.models import (
    SecurityTest,
    ModelRun,
    EvaluationScore,
    Scenario,
    TestStatus,
    RunStatus,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/test/{test_id}/summary")
def get_test_analytics(test_id: int, db: Session = Depends(get_db)):
    """Get comprehensive analytics for a single test."""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get all runs with evaluations
    runs_with_evals = (
        db.query(ModelRun, EvaluationScore)
        .outerjoin(EvaluationScore, EvaluationScore.model_run_id == ModelRun.id)
        .filter(ModelRun.security_test_id == test_id)
        .all()
    )

    # Calculate ASR
    total_runs = len(runs_with_evals)
    leakage_runs = sum(1 for _, e in runs_with_evals if e and e.leakage_detected)
    asr = (leakage_runs / total_runs * 100) if total_runs > 0 else 0

    # Risk distribution
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for _, eval_score in runs_with_evals:
        if eval_score and eval_score.risk_level:
            risk_distribution[eval_score.risk_level] = (
                risk_distribution.get(eval_score.risk_level, 0) + 1
            )

    # Technique effectiveness
    technique_stats = {}
    for model_run, eval_score in runs_with_evals:
        from app.models import StyleVariant

        variant = (
            db.query(StyleVariant)
            .filter(StyleVariant.id == model_run.style_variant_id)
            .first()
        )

        if variant:
            tech = variant.technique
            if tech not in technique_stats:
                technique_stats[tech] = {"total": 0, "leakage": 0}
            technique_stats[tech]["total"] += 1
            if eval_score and eval_score.leakage_detected:
                technique_stats[tech]["leakage"] += 1

    technique_effectiveness = {
        tech: {
            "total_runs": stats["total"],
            "leakage_count": stats["leakage"],
            "asr": round(stats["leakage"] / stats["total"] * 100, 1)
            if stats["total"] > 0
            else 0,
        }
        for tech, stats in technique_stats.items()
    }

    # Vendor comparison
    vendor_stats = {}
    for model_run, eval_score in runs_with_evals:
        vendor = model_run.model_vendor
        if vendor not in vendor_stats:
            vendor_stats[vendor] = {
                "total_runs": 0,
                "leakage_count": 0,
                "total_risk_score": 0,
                "max_risk_score": 0,
            }

        vendor_stats[vendor]["total_runs"] += 1
        if eval_score:
            if eval_score.leakage_detected:
                vendor_stats[vendor]["leakage_count"] += 1
            if eval_score.risk_score:
                vendor_stats[vendor]["total_risk_score"] += eval_score.risk_score
                vendor_stats[vendor]["max_risk_score"] = max(
                    vendor_stats[vendor]["max_risk_score"], eval_score.risk_score
                )

    vendor_comparison = {
        vendor: {
            "total_runs": stats["total_runs"],
            "leakage_count": stats["leakage_count"],
            "leakage_rate": round(
                stats["leakage_count"] / stats["total_runs"] * 100, 1
            ),
            "avg_risk_score": round(stats["total_risk_score"] / stats["total_runs"], 2),
            "max_risk_score": stats["max_risk_score"],
        }
        for vendor, stats in vendor_stats.items()
    }

    return {
        "test_id": test_id,
        "test_name": test.test_name,
        "attack_success_rate": round(asr, 2),
        "total_runs": total_runs,
        "leakage_detected_count": leakage_runs,
        "risk_distribution": risk_distribution,
        "technique_effectiveness": technique_effectiveness,
        "vendor_comparison": vendor_comparison,
    }


@router.get("/vendor-comparison")
def get_vendor_comparison(db: Session = Depends(get_db)):
    """Get vendor comparison across all tests."""
    # Aggregate stats across all completed tests
    runs = (
        db.query(ModelRun, EvaluationScore)
        .outerjoin(EvaluationScore, EvaluationScore.model_run_id == ModelRun.id)
        .join(SecurityTest, SecurityTest.id == ModelRun.security_test_id)
        .filter(SecurityTest.status == TestStatus.COMPLETED)
        .all()
    )

    vendor_stats = {}
    for model_run, eval_score in runs:
        vendor = model_run.model_vendor
        if vendor not in vendor_stats:
            vendor_stats[vendor] = {
                "total_runs": 0,
                "leakage_incidents": 0,
                "total_risk_score": 0,
                "max_risk_score": 0,
                "promise_compliance_violations": 0,
                "enterprise_runs": 0,
            }

        vendor_stats[vendor]["total_runs"] += 1

        if eval_score:
            if eval_score.leakage_detected:
                vendor_stats[vendor]["leakage_incidents"] += 1
            if eval_score.risk_score:
                vendor_stats[vendor]["total_risk_score"] += eval_score.risk_score
                vendor_stats[vendor]["max_risk_score"] = max(
                    vendor_stats[vendor]["max_risk_score"], eval_score.risk_score
                )

        if model_run.model_type == "enterprise":
            vendor_stats[vendor]["enterprise_runs"] += 1
            if eval_score and eval_score.vendor_promise_held == False:
                vendor_stats[vendor]["promise_compliance_violations"] += 1

    result = []
    for vendor, stats in vendor_stats.items():
        leakage_rate = (
            (stats["leakage_incidents"] / stats["total_runs"] * 100)
            if stats["total_runs"] > 0
            else 0
        )
        promise_compliance_rate = (
            (
                (stats["enterprise_runs"] - stats["promise_compliance_violations"])
                / stats["enterprise_runs"]
                * 100
            )
            if stats["enterprise_runs"] > 0
            else None
        )

        result.append(
            {
                "vendor": vendor,
                "total_runs": stats["total_runs"],
                "leakage_incidents": stats["leakage_incidents"],
                "leakage_rate": round(leakage_rate, 1),
                "avg_risk_score": round(
                    stats["total_risk_score"] / stats["total_runs"], 2
                )
                if stats["total_runs"] > 0
                else 0,
                "max_risk_score": stats["max_risk_score"],
                "promise_compliance_rate": round(promise_compliance_rate, 1)
                if promise_compliance_rate is not None
                else None,
            }
        )

    return {"vendors": result}


@router.get("/compliance-dashboard")
def get_compliance_dashboard(db: Session = Depends(get_db)):
    """Get compliance violation summary across all frameworks."""
    evaluations = (
        db.query(EvaluationScore).filter(EvaluationScore.leakage_detected == True).all()
    )

    framework_violations = {
        "SOC2": {"violations": 0, "controls": set()},
        "ISO27001": {"violations": 0, "controls": set()},
        "CPCSC": {"violations": 0, "controls": set()},
        "NIST_AI_RMF": {"violations": 0, "controls": set()},
    }

    for eval_score in evaluations:
        if eval_score.compliance_violations:
            for framework, data in eval_score.compliance_violations.items():
                if framework in framework_violations:
                    framework_violations[framework]["violations"] += 1
                    if isinstance(data, dict) and "controls" in data:
                        for control in data["controls"]:
                            if isinstance(control, dict):
                                framework_violations[framework]["controls"].add(
                                    control.get("control_id", "")
                                )
                            else:
                                framework_violations[framework]["controls"].add(control)

    return {
        framework: {
            "violation_count": data["violations"],
            "affected_controls": list(data["controls"]),
            "overall_risk_level": "HIGH"
            if data["violations"] > 10
            else "MEDIUM"
            if data["violations"] > 0
            else "LOW",
        }
        for framework, data in framework_violations.items()
    }
