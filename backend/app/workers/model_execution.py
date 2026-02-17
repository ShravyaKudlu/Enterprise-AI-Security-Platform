import logging
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models import ModelRun, RunStatus
from app.models.adapters.openai_adapter import OpenAIAdapter
from app.models.adapters.anthropic_adapter import AnthropicAdapter
from app.models.adapters.google_adapter import GoogleAdapter
from app.models.adapters.ollama_adapter import OllamaAdapter
from app.services.test_orchestrator import TestOrchestrator
from datetime import datetime

logger = logging.getLogger(__name__)

# Adapter factory
ADAPTER_MAP = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "google": GoogleAdapter,
    "ollama": OllamaAdapter,
}


def execute_model_run(job_data: dict):
    """
    Execute a single model run job.

    This function is called by RQ workers.
    """
    db = SessionLocal()

    try:
        model_run_id = job_data.get("model_run_id")
        adapter_name = job_data.get("adapter")
        model_name = job_data.get("model")
        prompt = job_data.get("prompt")

        logger.info(
            f"Executing model run {model_run_id} with {adapter_name}/{model_name}"
        )

        # Update status to running
        model_run = db.query(ModelRun).filter(ModelRun.id == model_run_id).first()
        if model_run:
            model_run.status = RunStatus.RUNNING
            db.commit()

        # Get adapter
        adapter_class = ADAPTER_MAP.get(adapter_name)
        if not adapter_class:
            raise ValueError(f"Unknown adapter: {adapter_name}")

        adapter = adapter_class(model=model_name)

        # Generate response
        result = adapter.generate(prompt)
        response_text = result["response_text"]

        # Update model run with response
        if model_run:
            model_run.response_text = response_text
            model_run.response_metadata = result.get("metadata", {})
            model_run.status = RunStatus.COMPLETED
            model_run.completed_at = datetime.utcnow()
            db.commit()

        # Evaluate the response
        orchestrator = TestOrchestrator(db)
        orchestrator.evaluate_run(model_run_id, response_text)

        # Check if test is complete
        test_id = job_data.get("test_id") or (
            model_run.security_test_id if model_run else None
        )
        if test_id:
            orchestrator.check_test_completion(test_id)

        logger.info(f"Completed model run {model_run_id}")

        return {"status": "success", "model_run_id": model_run_id}

    except Exception as e:
        logger.error(
            f"Error executing model run {job_data.get('model_run_id')}: {str(e)}"
        )

        # Update status to failed
        model_run_id = job_data.get("model_run_id")
        if model_run_id:
            model_run = db.query(ModelRun).filter(ModelRun.id == model_run_id).first()
            if model_run:
                model_run.status = RunStatus.FAILED
                model_run.response_text = f"Error: {str(e)}"
                model_run.completed_at = datetime.utcnow()
                db.commit()

        # Don't re-raise - we want to mark as failed, not crash the worker
        return {"status": "failed", "error": str(e), "model_run_id": model_run_id}

    finally:
        db.close()
