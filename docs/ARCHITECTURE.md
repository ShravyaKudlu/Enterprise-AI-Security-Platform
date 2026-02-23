# Enterprise AI Security Platform - Architecture

## System Overview

The Enterprise AI Security Red Teaming Platform is a full-stack application designed to validate enterprise AI vendor data isolation promises through adversarial testing.

## High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API    │────▶│   Database      │
│   (React 18)    │     │   (FastAPI)      │     │   (SQLite/      │
│                 │◄────│                  │◄────│   PostgreSQL)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   Model Adapters │
                        │   - OpenAI       │
                        │   - Anthropic    │
                        │   - Google       │
                        │   - Ollama       │
                        └──────────────────┘
```

## Technology Stack

### Frontend
- **React 18** - UI framework
- **Material-UI (MUI)** - Component library
- **React Query** - Data fetching and caching
- **React Router** - Navigation
- **Chart.js** - Data visualization

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation
- **RQ (Redis Queue)** - Background job processing
- **Redis** - Job queue storage

### Database
- **SQLite** - Development/testing
- **PostgreSQL** - Production

### AI Model Adapters
- **OpenAI SDK** - GPT-4, GPT-3.5
- **Anthropic SDK** - Claude 3
- **Google Generative AI** - Gemini
- **Ollama HTTP API** - Local models (Llama, Mistral)

## Data Flow

1. **Test Creation**
   - User configures test in frontend
   - Frontend sends POST to `/api/v1/security-tests/run`
   - Backend creates test record
   - Variants generated from baseline prompts
   - Model run jobs created

2. **Test Execution**
   - Jobs executed synchronously (development) or via RQ workers (production)
   - Each job:
     - Calls model adapter
     - Stores response
     - Runs leakage detection
     - Calculates risk score
     - Maps compliance violations

3. **Results Retrieval**
   - Frontend polls `/api/v1/security-tests/{id}/status`
   - Displays real-time progress
   - Shows final results with analysis

## Security Components

### Attack Scenario Library
5 pre-defined scenarios targeting common data isolation vulnerabilities:
- Enterprise Data Isolation Testing
- Cross-User Information Leakage
- Training Data Extraction
- Context Boundary Violation
- System Prompt Leakage

### Variant Generation Engine
5 stylistic techniques to bypass filters:
- Poetry
- Narrative
- Metaphor
- Euphemism
- Role Shift

### Leakage Detection
Heuristic pattern matching for:
- Cross-user data references
- Training data extraction
- Context boundary violations
- System prompt disclosure

### Risk Scoring
Formula: `(Data Sensitivity × Leakage Severity × Confidence) / 10`

Risk Levels:
- 0.0-2.0: LOW
- 2.1-5.0: MEDIUM
- 5.1-7.5: HIGH
- 7.6-10.0: CRITICAL

## Scalability Considerations

### Horizontal Scaling
- RQ workers can be scaled horizontally
- Each worker processes jobs independently
- No shared state between workers

### Database
- PostgreSQL supports connection pooling
- Read replicas for analytics queries
- Index on frequently queried columns

### Caching
- Analytics results cached in `analytics_cache` table
- Redis can cache model responses
- Frontend caching via React Query

## Deployment Architecture

### Development
```
Single machine:
- Frontend: npm run dev (port 3001)
- Backend: python main.py (port 8000)
- Database: SQLite file
- Redis: Local instance
- Ollama: Local instance
```

### Production
```
Separate services:
- Frontend: Vercel/Netlify
- Backend: Railway/Render
- Database: Managed PostgreSQL
- Redis: Redis Cloud/Railway
- Workers: Multiple RQ worker instances
```

## Monitoring & Logging

- **Structured logging** with rotating file handler
- **Health check endpoint** at `/api/v1/health/production`
- **Test progress tracking** via database polling
- **Error tracking** with full stack traces

## Future Enhancements

- LLM-based leakage detection (secondary verifier)
- Additional model providers (Azure, AWS Bedrock)
- Webhook notifications for test completion
- SIEM integration (Splunk, Datadog)
- PDF report generation
- Multi-tenant support