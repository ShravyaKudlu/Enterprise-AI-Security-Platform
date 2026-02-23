# Security Guide

## Overview

This document outlines security considerations for the Enterprise AI Security Platform.

## Data Classification

### Data Handled by the Platform

| Data Type | Classification | Storage | Notes |
|-----------|---------------|---------|-------|
| API Keys | HIGHLY CONFIDENTIAL | Environment variables | Never logged or exposed |
| Test Configurations | CONFIDENTIAL | Database | May contain sensitive prompts |
| Model Responses | CONFIDENTIAL | Database | May contain leaked data |
| Analysis Results | CONFIDENTIAL | Database | Risk scores and findings |
| User Data | INTERNAL | Database | Minimal PII collected |

## Authentication & Authorization

### API Key Authentication

All API endpoints require authentication via `X-API-Key` header:

```http
X-API-Key: test-api-key-1
```

**Best Practices:**
- Use strong, randomly generated API keys in production
- Rotate keys regularly (every 90 days)
- Use different keys for different environments
- Never commit keys to version control

### API Key Storage

```python
# backend/.env
API_KEYS=production-key-1,production-key-2
```

## Rate Limiting

### Current Limits

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| POST /security-tests/run | 10/hour | Prevent abuse |
| POST /variants/generate | 50/hour | Prevent abuse |
| GET endpoints | 1000/hour | Normal usage |

### Implementation

Uses `slowapi` with Redis backend for distributed rate limiting.

## Input Validation

### Request Validation

All endpoints use Pydantic schemas for validation:

```python
class RunSecurityTestRequest(BaseModel):
    test_name: str = Field(min_length=3, max_length=100)
    baseline_prompts: List[str] = Field(min_items=1, max_items=50)
    # ... validation rules
```

### SQL Injection Prevention

- Uses SQLAlchemy ORM (parameterized queries)
- Never concatenates user input into SQL
- Input sanitization on all text fields

### XSS Prevention

- Frontend uses React (automatic escaping)
- API returns JSON (not HTML)
- Content-Type headers properly set

## CORS Configuration

### Development
```python
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production
```python
ALLOWED_ORIGINS=https://yourdomain.com
```

## Secure Deployment Checklist

### Environment
- [ ] Use HTTPS only
- [ ] Disable DEBUG mode
- [ ] Set strong SECRET_KEY
- [ ] Configure proper CORS origins
- [ ] Enable security headers

### Database
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable SSL connections
- [ ] Use strong passwords
- [ ] Enable connection encryption
- [ ] Regular backups

### API Keys
- [ ] Use environment variables
- [ ] Rotate regularly
- [ ] Use different keys per environment
- [ ] Monitor for unauthorized usage

### Model API Keys
- [ ] Store in environment variables
- [ ] Never log or expose
- [ ] Use read-only keys where possible
- [ ] Monitor usage and costs

## Security Headers

### Recommended Headers

```python
# FastAPI middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Logging & Monitoring

### Security Events to Log

- Authentication failures
- Rate limit exceeded
- Invalid API key usage
- Database connection failures
- Model API errors

### Sensitive Data in Logs

**NEVER log:**
- API keys
- Model API responses (may contain sensitive data)
- Full prompts (may contain PII)

**DO log:**
- Test IDs
- Model names
- Status codes
- Error messages (sanitized)

## Model API Security

### Timeout Protection

All model API calls have 30-second timeouts:

```python
response = client.chat.completions.create(
    ...,
    timeout=30
)
```

### Retry Logic

Exponential backoff on failures:
- Max 3 retries
- 2^retry_count seconds between attempts
- Prevents thundering herd

### Error Handling

Errors are caught and logged without exposing internal details:

```python
try:
    result = adapter.generate(prompt)
except Exception as e:
    logger.error(f"Model API error: {e}")
    return {"error": "Model request failed"}  # Generic message
```

## Data Leakage Testing Ethics

### Responsible Testing

1. **Only test systems you own or have permission to test**
2. **Never use findings to harm others**
3. **Report vulnerabilities through proper channels**
4. **Follow responsible disclosure practices**

### Legal Considerations

- Testing without authorization may violate laws
- CFAA (US), Computer Misuse Act (UK), etc.
- Always get written authorization
- Document scope and limitations

## Compliance

### GDPR

- Minimal data collection
- Right to deletion
- Data portability
- Consent management

### SOC 2

- Access controls
- Audit logging
- Change management
- Incident response

## Incident Response

### Security Incident Types

1. **Unauthorized API access**
2. **Data breach**
3. **System compromise**
4. **Model API key exposure**

### Response Steps

1. **Identify** - Detect and assess
2. **Contain** - Limit damage
3. **Eradicate** - Remove threat
4. **Recover** - Restore services
5. **Learn** - Post-incident review

## Penetration Testing

### Self-Testing

The platform itself should be security tested:

1. API security testing
2. Authentication bypass attempts
3. Injection attacks
4. CSRF testing
5. SSL/TLS configuration

### Tools

- OWASP ZAP
- Burp Suite
- Nmap
- SSL Labs

## Vulnerability Disclosure

### Reporting Vulnerabilities

If you find a security vulnerability:

1. **DO NOT** create a public issue
2. Email security@yourcompany.com
3. Provide detailed reproduction steps
4. Allow reasonable time for fix before disclosure

### Bug Bounty

Consider offering bug bounties for critical findings.

## Security Updates

### Dependency Management

```bash
# Check for vulnerabilities
pip audit
npm audit

# Update dependencies
pip install --upgrade -r requirements.txt
npm update
```

### Automated Scanning

- Dependabot for GitHub
- Snyk for continuous monitoring
- OWASP Dependency Check

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [React Security](https://reactjs.org/docs/security.html)