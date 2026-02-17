# Enterprise AI Security Red Teaming Platform

A comprehensive security testing platform for validating enterprise AI vendor data isolation promises.

## Features

- **Attack Scenario Library**: Pre-defined security test scenarios targeting enterprise AI isolation
- **Variant Generation**: Stylistic prompt variations (poetry, narrative, metaphor, euphemism, role-shift)
- **Multi-Model Support**: OpenAI, Anthropic, Google Gemini, and local Ollama models
- **Data Leakage Detection**: Heuristic and LLM-based detection of information leakage
- **Risk Scoring**: Automated risk assessment with compliance mapping
- **Real-time Dashboard**: Live monitoring of test execution and results
- **Compliance Frameworks**: SOC2, ISO27001, CPCSC, NIST AI RMF mappings

## Architecture

### Backend
- **FastAPI** (Python 3.9+) - RESTful API
- **PostgreSQL** 16 - Primary database
- **Redis + RQ** - Async job queue for model execution
- **SQLAlchemy** - ORM

### Frontend
- **React 18** - UI framework
- **Material-UI** - Component library
- **Chart.js** - Data visualization
- **React Query** - Data fetching

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 16
- Redis 6+
- (Optional) Ollama for local models

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app.core.db import init_db; init_db()"

# Seed scenarios
python -c "from app.seed_data import seed_scenarios; from app.core.db import SessionLocal; db = SessionLocal(); seed_scenarios(db); db.close()"

# Run the API server
python main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Environment Variables

Create `.env` files for both backend and frontend:

**Backend (backend/.env):**
```
DATABASE_URL=postgresql://user:password@localhost:5432/ai_security
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
API_KEYS=test-api-key-1,test-api-key-2
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Model API Keys (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Model Configuration
OPENAI_MODEL=gpt-4
ANTHROPIC_MODEL=claude-3-opus-20240229
GOOGLE_MODEL=gemini-1.5-pro
OLLAMA_BASE_URL=http://localhost:11434
```

**Frontend (frontend/.env):**
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_KEY=test-api-key-1
```

### Running RQ Workers

For production deployments, run RQ workers to process model execution jobs:

```bash
cd backend
rq worker --url redis://localhost:6379/0
```

## API Endpoints

### Health & Configuration
- `GET /health` - Health check
- `GET /api/v1/health/production` - Production health with dependency checks
- `GET /api/v1/scenarios` - List attack scenarios

### Security Tests
- `POST /api/v1/security-tests/run` - Create and run a new test
- `GET /api/v1/security-tests/{test_id}/status` - Get test progress
- `GET /api/v1/security-tests/{test_id}` - Get full test results

### Variants
- `POST /api/v1/variants/generate` - Generate style variants
- `GET /api/v1/variants/by-prompt/{id}` - Get variants for a baseline prompt

### Analytics
- `GET /api/v1/analytics/test/{test_id}/summary` - Test analytics
- `GET /api/v1/analytics/vendor-comparison` - Cross-vendor comparison
- `GET /api/v1/analytics/compliance-dashboard` - Compliance violations

## Attack Scenarios

The platform includes 5 pre-defined attack scenarios:

1. **S-001**: Enterprise Data Isolation Testing
2. **S-002**: Cross-User Information Leakage
3. **S-003**: Training Data Extraction
4. **S-004**: Context Boundary Violation
5. **S-005**: System Prompt Leakage

## Deployment

### Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Railway/Render (Cloud)

See `docs/DEPLOYMENT.md` for detailed cloud deployment instructions.

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Quality

```bash
# Backend
black app/
flake8 app/

# Frontend
cd frontend
npm run lint
```

## Security Considerations

- All API endpoints require API key authentication
- Rate limiting enforced per IP address
- CORS restricted to configured origins
- No secrets committed to version control
- 30-second timeout on all model API calls
- Exponential backoff on rate limit errors

## License

MIT License - See LICENSE file for details.

## Contributing

See `docs/CONTRIBUTING.md` for contribution guidelines.

## Support

For issues and feature requests, please use the GitHub issue tracker.