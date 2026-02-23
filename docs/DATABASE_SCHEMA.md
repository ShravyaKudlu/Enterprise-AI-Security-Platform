# Database Schema

## Overview

The platform uses SQLAlchemy ORM with PostgreSQL (production) or SQLite (development). Below is the complete database schema.

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│  scenarios   │◄──────┤ baseline_prompts │◄──────┤ style_variants│
└──────────────┘       └──────────────────┘       └──────┬───────┘
                                                          │
                              ┌───────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   model_runs     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ evaluation_scores│
                    └──────────────────┘
```

## Tables

### scenarios

Stores attack scenario definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| scenario_id | VARCHAR | UNIQUE | External identifier (e.g., S-001) |
| scenario_name | VARCHAR | NOT NULL | Human-readable name |
| description | TEXT | NOT NULL | Detailed description |
| target_model_type | VARCHAR | NOT NULL | enterprise\|public\|local |
| data_classification | VARCHAR | NOT NULL | public\|internal\|confidential\|restricted |
| compliance_frameworks | JSON | | Array of frameworks |
| severity_threshold | VARCHAR | NOT NULL | low\|medium\|high\|critical |
| attack_techniques | JSON | | Array of technique identifiers |
| vendor_promise_tested | TEXT | | Description of promise being tested |
| created_at | TIMESTAMP | | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (scenario_id)

---

### baseline_prompts

Stores original security test prompts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| prompt_text | TEXT | NOT NULL | The baseline prompt text |
| scenario_id | INTEGER | FK | References scenarios.id |
| created_at | TIMESTAMP | | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (scenario_id) REFERENCES scenarios(id)

---

### style_variants

Stores stylistically rewritten prompts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| baseline_prompt_id | INTEGER | FK | References baseline_prompts.id |
| scenario_id | INTEGER | FK | References scenarios.id |
| technique | VARCHAR | NOT NULL | poetry\|narrative\|metaphor\|euphemism\|role_shift |
| variant_text | TEXT | | The generated variant text |
| created_at | TIMESTAMP | | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (baseline_prompt_id) REFERENCES baseline_prompts(id)
- FOREIGN KEY (scenario_id) REFERENCES scenarios(id)

---

### security_tests

Stores test configurations and results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| test_name | VARCHAR(100) | NOT NULL | 3-100 character name |
| description | TEXT | | Optional description |
| status | VARCHAR | | queued\|running\|completed\|failed\|draft |
| attack_scenario_id | INTEGER | FK | References scenarios.id |
| target_models | JSON | | Array of model configurations |
| baseline_prompts | JSON | | Array of prompt IDs and texts |
| techniques | JSON | | Array of selected techniques |
| variants_per_technique | INTEGER | DEFAULT 2 | Number of variants per technique |
| created_at | TIMESTAMP | | Creation timestamp |
| completed_at | TIMESTAMP | NULLABLE | Completion timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (attack_scenario_id) REFERENCES scenarios(id)

---

### model_runs

Stores individual model execution results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| security_test_id | INTEGER | FK | References security_tests.id |
| style_variant_id | INTEGER | FK | References style_variants.id |
| model_name | VARCHAR | | Name of model used |
| model_type | VARCHAR | | enterprise\|public\|local |
| model_vendor | VARCHAR | | openai\|anthropic\|google\|ollama |
| response_text | TEXT | | Model's response |
| response_metadata | JSON | | Tokens, timing, version |
| status | VARCHAR | DEFAULT 'queued' | queued\|running\|completed\|failed |
| created_at | TIMESTAMP | | Creation timestamp |
| completed_at | TIMESTAMP | NULLABLE | Completion timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (security_test_id) REFERENCES security_tests(id)
- FOREIGN KEY (style_variant_id) REFERENCES style_variants(id)
- INDEX (security_test_id, status)

---

### evaluation_scores

Stores leakage detection and risk scoring results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| model_run_id | INTEGER | FK | References model_runs.id |
| leakage_detected | BOOLEAN | | Whether leakage was found |
| leakage_categories | JSON | | Array of category strings |
| confidence_scores | JSON | | Per-category confidence 0.0-1.0 |
| evidence_snippets | JSON | | Extracted text evidence |
| risk_score | FLOAT | | Calculated score 0.0-10.0 |
| risk_level | VARCHAR | | LOW\|MEDIUM\|HIGH\|CRITICAL |
| data_classification | VARCHAR | | PII\|CONVERSATION_HISTORY\|BUSINESS_CONFIDENTIAL\|SYSTEM_CONFIGURATION\|UNCLASSIFIED |
| compliance_violations | JSON | | Per-framework violations |
| vendor_promise_held | BOOLEAN | NULLABLE | For enterprise models only |
| scoring_rationale | TEXT | | Human-readable explanation |
| remediation | TEXT | | Recommended actions |
| created_at | TIMESTAMP | | Creation timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (model_run_id) REFERENCES model_runs.id
- UNIQUE (model_run_id)
- INDEX (leakage_detected)
- INDEX (risk_level)

---

### analytics_cache

Caches pre-computed analytics for fast retrieval.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Auto-increment primary key |
| cache_key | VARCHAR | UNIQUE | Identifier for cached data |
| data | JSON | | Cached metric object |
| computed_at | TIMESTAMP | | When cache was generated |
| security_test_id | INTEGER | FK, NULLABLE | Optional test reference |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (cache_key)
- FOREIGN KEY (security_test_id) REFERENCES security_tests(id)

## Sample Queries

### Get test with all runs
```sql
SELECT 
    st.id, st.test_name, st.status,
    COUNT(mr.id) as total_runs,
    SUM(CASE WHEN mr.status = 'completed' THEN 1 ELSE 0 END) as completed_runs,
    SUM(CASE WHEN es.leakage_detected THEN 1 ELSE 0 END) as leakage_count
FROM security_tests st
LEFT JOIN model_runs mr ON st.id = mr.security_test_id
LEFT JOIN evaluation_scores es ON mr.id = es.model_run_id
WHERE st.id = 1
GROUP BY st.id, st.test_name, st.status;
```

### Get vendor comparison stats
```sql
SELECT 
    mr.model_vendor,
    COUNT(*) as total_runs,
    SUM(CASE WHEN es.leakage_detected THEN 1 ELSE 0 END) as leakage_count,
    AVG(es.risk_score) as avg_risk_score,
    MAX(es.risk_score) as max_risk_score
FROM model_runs mr
LEFT JOIN evaluation_scores es ON mr.id = es.model_run_id
WHERE mr.status = 'completed'
GROUP BY mr.model_vendor;
```

### Get compliance violations
```sql
SELECT 
    es.leakage_categories,
    es.compliance_violations,
    COUNT(*) as violation_count
FROM evaluation_scores es
WHERE es.leakage_detected = true
GROUP BY es.leakage_categories, es.compliance_violations;
```

## Migrations

Using Alembic for database migrations:

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Performance Optimization

### Indexes for Common Queries
```sql
-- Speed up test status lookups
CREATE INDEX idx_model_runs_test_status ON model_runs(security_test_id, status);

-- Speed up leakage detection queries
CREATE INDEX idx_eval_scores_leakage ON evaluation_scores(leakage_detected);

-- Speed up risk level filtering
CREATE INDEX idx_eval_scores_risk ON evaluation_scores(risk_level);

-- Speed up vendor comparison
CREATE INDEX idx_model_runs_vendor ON model_runs(model_vendor);
```

### Connection Pooling (PostgreSQL)
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

## Data Retention

### Archiving Old Tests
```sql
-- Archive tests older than 90 days
INSERT INTO security_tests_archive
SELECT * FROM security_tests
WHERE created_at < NOW() - INTERVAL '90 days'
AND status = 'completed';

-- Delete archived tests
DELETE FROM security_tests
WHERE created_at < NOW() - INTERVAL '90 days'
AND status = 'completed';
```

## Backup Strategy

### Automated Backups
```bash
#!/bin/bash
# Daily backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://my-backups/
```