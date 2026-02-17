from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.db import init_db, engine
from app.core.logging import setup_logging
from app.seed_data import seed_scenarios
from app.middleware.auth import APIKeyMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.routes import variants, security_tests, analytics

# Import all models to ensure they are registered with SQLAlchemy
from app.models import (
    Base,
    Scenario,
    BaselinePrompt,
    StyleVariant,
    SecurityTest,
    ModelRun,
    EvaluationScore,
    AnalyticsCache,
)

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting up Enterprise AI Security Platform")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Import here to avoid circular imports
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        seed_scenarios(db)
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise AI Security Red Teaming Platform API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# API Key auth (optional - can be disabled for development)
# app.add_middleware(APIKeyMiddleware)

# Include routers
app.include_router(variants.router, prefix="/api/v1")
app.include_router(security_tests.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": "production" if not settings.DEBUG else "development",
    }


@app.get("/api/v1/health/production")
def production_health_check():
    """Production health check with dependency status."""
    import redis
    from app.core.db import engine

    health = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": "production" if not settings.DEBUG else "development",
    }

    # Check database
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health["redis"] = "connected"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check model availability
    models_available = []
    if settings.OPENAI_API_KEY:
        models_available.append("openai")
    if settings.ANTHROPIC_API_KEY:
        models_available.append("anthropic")
    if settings.GOOGLE_API_KEY:
        models_available.append("google")
    models_available.append("ollama")

    health["models_available"] = models_available

    return health


@app.get("/api/v1/scenarios")
def get_scenarios():
    """Get all attack scenarios."""
    from app.core.db import SessionLocal
    from app.models import Scenario

    db = SessionLocal()
    try:
        scenarios = db.query(Scenario).all()
        return {
            "scenarios": [
                {
                    "id": s.id,
                    "scenario_id": s.scenario_id,
                    "scenario_name": s.scenario_name,
                    "description": s.description,
                    "target_model_type": s.target_model_type,
                    "data_classification": s.data_classification,
                    "compliance_frameworks": s.compliance_frameworks,
                    "severity_threshold": s.severity_threshold,
                    "attack_techniques": s.attack_techniques,
                }
                for s in scenarios
            ]
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
