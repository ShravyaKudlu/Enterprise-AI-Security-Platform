from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
    JSON,
    Enum,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class ModelType(str, enum.Enum):
    ENTERPRISE = "enterprise"
    PUBLIC = "public"
    LOCAL = "local"


class ModelVendor(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class DataClassification(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TestStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DRAFT = "draft"


class RunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Technique(str, enum.Enum):
    POETRY = "poetry"
    NARRATIVE = "narrative"
    METAPHOR = "metaphor"
    EUPHEMISM = "euphemism"
    ROLE_SHIFT = "role_shift"


class EvaluationDataClassification(str, enum.Enum):
    PII = "PII"
    CONVERSATION_HISTORY = "CONVERSATION_HISTORY"
    BUSINESS_CONFIDENTIAL = "BUSINESS_CONFIDENTIAL"
    SYSTEM_CONFIGURATION = "SYSTEM_CONFIGURATION"
    UNCLASSIFIED = "UNCLASSIFIED"


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, unique=True, index=True)
    scenario_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    target_model_type = Column(String, nullable=False)
    data_classification = Column(String, nullable=False)
    compliance_frameworks = Column(JSON, default=list)
    severity_threshold = Column(String, nullable=False)
    attack_techniques = Column(JSON, default=list)
    vendor_promise_tested = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    baseline_prompts = relationship("BaselinePrompt", back_populates="scenario")
    style_variants = relationship("StyleVariant", back_populates="scenario")


class BaselinePrompt(Base):
    __tablename__ = "baseline_prompts"

    id = Column(Integer, primary_key=True, index=True)
    prompt_text = Column(Text, nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    scenario = relationship("Scenario", back_populates="baseline_prompts")
    style_variants = relationship("StyleVariant", back_populates="baseline_prompt")


class StyleVariant(Base):
    __tablename__ = "style_variants"

    id = Column(Integer, primary_key=True, index=True)
    baseline_prompt_id = Column(Integer, ForeignKey("baseline_prompts.id"))
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    technique = Column(String, nullable=False)
    variant_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    baseline_prompt = relationship("BaselinePrompt", back_populates="style_variants")
    scenario = relationship("Scenario", back_populates="style_variants")
    model_runs = relationship("ModelRun", back_populates="style_variant")


class SecurityTest(Base):
    __tablename__ = "security_tests"

    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String, default=TestStatus.DRAFT)
    attack_scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    target_models = Column(JSON, default=list)
    baseline_prompts = Column(JSON, default=list)
    techniques = Column(JSON, default=list)
    variants_per_technique = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    model_runs = relationship("ModelRun", back_populates="security_test")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    security_test_id = Column(Integer, ForeignKey("security_tests.id"))
    style_variant_id = Column(Integer, ForeignKey("style_variants.id"))
    model_name = Column(String)
    model_type = Column(String)
    model_vendor = Column(String)
    response_text = Column(Text)
    response_metadata = Column(JSON, default=dict)
    status = Column(String, default=RunStatus.QUEUED)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    security_test = relationship("SecurityTest", back_populates="model_runs")
    style_variant = relationship("StyleVariant", back_populates="model_runs")
    evaluation_score = relationship(
        "EvaluationScore", back_populates="model_run", uselist=False
    )


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    id = Column(Integer, primary_key=True, index=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.id"))
    leakage_detected = Column(Boolean, default=False)
    leakage_categories = Column(JSON, default=list)
    confidence_scores = Column(JSON, default=dict)
    evidence_snippets = Column(JSON, default=list)
    risk_score = Column(Float)
    risk_level = Column(String)
    data_classification = Column(String)
    compliance_violations = Column(JSON, default=dict)
    vendor_promise_held = Column(Boolean, nullable=True)
    scoring_rationale = Column(Text)
    remediation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    model_run = relationship("ModelRun", back_populates="evaluation_score")


class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True)
    data = Column(JSON)
    computed_at = Column(DateTime, default=datetime.utcnow)
    security_test_id = Column(Integer, ForeignKey("security_tests.id"), nullable=True)
