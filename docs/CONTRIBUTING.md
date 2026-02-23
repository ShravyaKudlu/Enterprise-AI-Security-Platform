# Contributing Guide

Thank you for your interest in contributing to the Enterprise AI Security Platform!

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+ (or SQLite for dev)
- Redis 6+
- Git

### Development Setup

1. **Fork and Clone**
```bash
git clone https://github.com/yourusername/enterprise-ai-security-platform.git
cd enterprise-ai-security-platform
```

2. **Set up Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

3. **Set up Frontend**
```bash
cd frontend
npm install
cp .env.example .env
```

4. **Run Tests**
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical fixes

### Creating a Feature

1. **Create branch**
```bash
git checkout -b feature/my-new-feature
```

2. **Make changes**
3. **Run tests**
4. **Commit**
```bash
git add .
git commit -m "feat: add new feature"
```

5. **Push and create PR**
```bash
git push origin feature/my-new-feature
```

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting)
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

Examples:
```
feat(api): add webhook support
fix(detector): correct regex pattern
docs: update API reference
test(leakage): add unit tests
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100
- Use Black for formatting

```bash
# Format code
black app/

# Check style
flake8 app/

# Type checking
mypy app/
```

### JavaScript/React

- Use ESLint configuration
- Functional components preferred
- Destructuring props
- Meaningful variable names

```bash
# Lint
npm run lint

# Fix auto-fixable issues
npm run lint:fix
```

## Testing

### Backend Tests

```bash
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_leakage_detection.py::test_cross_user_detection
```

### Frontend Tests

```bash
cd frontend
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Writing Tests

**Backend Example:**
```python
def test_leakage_detector():
    detector = LeakageDetector()
    result = detector.detect("User Alice asked about passwords")
    assert result.leakage_detected == True
    assert "cross_user" in result.categories
```

**Frontend Example:**
```javascript
test('renders dashboard', () => {
  render(<Dashboard />);
  expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
});
```

## Adding New Features

### New Attack Scenario

1. Add to `app/seed_data.py`:
```python
{
    "scenario_id": "S-006",
    "scenario_name": "New Attack Vector",
    "description": "...",
    "target_model_type": "enterprise",
    # ...
}
```

2. Add baseline prompts
3. Update documentation
4. Add tests

### New Model Adapter

1. Create file: `app/models/adapters/new_adapter.py`
2. Extend `ModelAdapter` base class
3. Implement `generate()` and `get_model_info()`
4. Add to adapter map
5. Add tests

Example:
```python
class NewAdapter(ModelAdapter):
    def generate(self, prompt: str, params: Optional[Dict] = None) -> Dict:
        # Implementation
        return {
            "response_text": "...",
            "model_name": "...",
            "model_type": "...",
            "vendor": "...",
            "metadata": {...}
        }
```

### New Attack Technique

1. Add template to `app/services/variant_generator.py`:
```python
Technique.NEW_TECHNIQUE: [
    "Template 1: {prompt}",
    "Template 2: {prompt}",
]
```

2. Update Technique enum
3. Add frontend option
4. Document in guide

## Documentation

### Code Documentation

- All public functions/classes must have docstrings
- Use Google-style docstrings
- Include type hints

```python
def calculate_risk_score(
    detection_result: LeakageDetectionResult,
    data_classification: str
) -> Dict:
    """
    Calculate risk score based on detection results.
    
    Args:
        detection_result: Result from leakage detection
        data_classification: Classification of data (public/internal/confidential/restricted)
        
    Returns:
        Dict with risk_score, risk_level, and scoring_rationale
        
    Example:
        >>> result = calculate_risk_score(detection, "confidential")
        >>> print(result["risk_score"])
        7.5
    """
```

### API Documentation

- Document all endpoints in `docs/API.md`
- Include request/response examples
- Document error responses

## Code Review Process

1. **Create PR** from feature branch to `develop`
2. **Fill out PR template**:
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

3. **Automated checks**:
   - Tests must pass
   - Linting must pass
   - Coverage threshold (80%)

4. **Review requirements**:
   - 2 approving reviews
   - No outstanding comments
   - Up-to-date with base branch

5. **Merge** using "Squash and merge"

## Reporting Issues

### Bug Reports

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs/error messages

Template:
```markdown
**Description**
Brief description of the bug

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

**Logs**
```
Paste relevant logs
```
```

### Feature Requests

Include:
- Use case
- Proposed solution
- Alternatives considered
- Additional context

## Security Issues

**DO NOT** create public issues for security vulnerabilities.

Email security@yourcompany.com with:
- Description
- Impact assessment
- Reproduction steps
- Suggested fix (if known)

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the issue, not the person
- Respect different viewpoints

### Communication Channels

- GitHub Issues - Bug reports, feature requests
- GitHub Discussions - General questions
- Discord - Real-time chat (link)
- Email - Security issues

## Release Process

1. **Version Bump**
   - Update `version` in `backend/app/core/config.py`
   - Update `version` in `frontend/package.json`

2. **Changelog**
   - Update `CHANGELOG.md`
   - Categorize changes

3. **Create Release**
   - Tag: `git tag -a v1.1.0 -m "Release 1.1.0"`
   - Push: `git push origin v1.1.0`
   - Create GitHub release with notes

4. **Deploy**
   - Deploy to staging
   - Run smoke tests
   - Deploy to production

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to team events

## Questions?

- Check existing documentation
- Search GitHub issues
- Ask in Discussions
- Email maintainers

Thank you for contributing! 🎉