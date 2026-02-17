from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.db import get_db
from app.services.variant_generator import VariantGenerator
from app.models import StyleVariant, BaselinePrompt

router = APIRouter(prefix="/variants", tags=["variants"])


class GenerateVariantsRequest(BaseModel):
    baseline_prompt_id: int
    attack_scenario_id: int
    techniques: List[str]
    count_per_technique: Optional[int] = 2


class VariantResponse(BaseModel):
    variant_id: int
    technique: str
    variant_text: str
    created_at: str


class GenerateVariantsResponse(BaseModel):
    baseline_prompt_id: int
    variants_generated: int
    variants: List[VariantResponse]


@router.post("/generate", response_model=GenerateVariantsResponse)
def generate_variants(request: GenerateVariantsRequest, db: Session = Depends(get_db)):
    """Generate style variants for a baseline prompt."""
    try:
        generator = VariantGenerator(db)

        variants = generator.generate_variants(
            baseline_prompt_id=request.baseline_prompt_id,
            scenario_id=request.attack_scenario_id,
            techniques=request.techniques,
            count_per_technique=request.count_per_technique,
        )

        return GenerateVariantsResponse(
            baseline_prompt_id=request.baseline_prompt_id,
            variants_generated=len(variants),
            variants=[
                VariantResponse(
                    variant_id=v.id,
                    technique=v.technique,
                    variant_text=v.variant_text,
                    created_at=v.created_at.isoformat() if v.created_at else None,
                )
                for v in variants
            ],
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-prompt/{baseline_prompt_id}")
def get_variants_by_prompt(
    baseline_prompt_id: int,
    technique: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all variants for a baseline prompt."""
    baseline = (
        db.query(BaselinePrompt).filter(BaselinePrompt.id == baseline_prompt_id).first()
    )

    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline prompt not found")

    query = db.query(StyleVariant).filter(
        StyleVariant.baseline_prompt_id == baseline_prompt_id
    )

    if technique:
        query = query.filter(StyleVariant.technique == technique)

    variants = query.all()

    from app.models import ModelRun

    return {
        "baseline_prompt_id": baseline_prompt_id,
        "baseline_text": baseline.prompt_text,
        "attack_scenario": baseline.scenario.scenario_name
        if baseline.scenario
        else None,
        "variants": [
            {
                "variant_id": v.id,
                "technique": v.technique,
                "variant_text": v.variant_text,
                "model_runs_count": db.query(ModelRun)
                .filter(ModelRun.style_variant_id == v.id)
                .count(),
            }
            for v in variants
        ],
    }
