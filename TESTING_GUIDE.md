# WTfffmpeg Testing and Configuration Guide

This document provides comprehensive guidance for testing the WTfffmpeg service and troubleshooting configuration errors.

## Quick Start for Administrators

### 1. Validate Configuration
```bash
# Run full configuration validation
./config-validator.sh

# Check specific components
./config-validator.sh env          # Environment variables only
./config-validator.sh gcloud       # Google Cloud setup only
./config-validator.sh bucket       # Bucket access only
./config-validator.sh app          # Application test only
```

### 2. Monitor Service Health
```bash
# Single health check
./monitor.sh check

# Continuous monitoring
./monitor.sh --service-url https://your-service.run.app monitor

# Monitor with custom interval
./monitor.sh --interval 30 monitor
```

### 3. Run Tests
```bash
# Basic configuration tests
python3 test_config.py

# Comprehensive integration tests
python3 test_integration.py

# Verify deployment readiness
./verify.sh
```

## Configuration Error Troubleshooting

### Common Error: "Service configuration error. Please contact administrator"

**Cause:** The `CLOUD_STORAGE_BUCKET` environment variable is not set in the deployment.

**Quick Diagnosis:**
1. Check the configuration endpoint: `curl https://your-service.run.app/_config`
2. Look for `"ready_for_video_creation": false` in the response
3. Check the `issues` array for specific problems

**Solution:**
```bash
# For Cloud Run deployment
gcloud run services update your-service-name \
    --region=your-region \
    --set-env-vars="CLOUD_STORAGE_BUCKET=your-bucket-name"

# For local Docker testing
docker run -e CLOUD_STORAGE_BUCKET=your-bucket-name your-image
```

**Verification:**
```bash
# Should return HTTP 200 with ready_for_video_creation: true
curl https://your-service.run.app/_config
```

## Testing Infrastructure

### 1. Basic Configuration Tests (`test_config.py`)
- Tests service behavior with and without environment variables
- Validates health and configuration endpoints
- Tests video creation error handling

### 2. Integration Tests (`test_integration.py`)
- Comprehensive edge case testing
- Deployment scenario validation
- Concurrent request handling
- Error logging verification

### 3. GitHub Actions CI/CD (`.github/workflows/test-config.yml`)
- Automated testing on push/PR
- Python environment setup
- Docker build validation
- Multi-scenario testing

### 4. Health Monitoring (`monitor.sh`)
- Local and remote service monitoring
- Automated alerting on failures
- Detailed logging and statistics
- Continuous monitoring support

### 5. Configuration Validation (`config-validator.sh`)
- Environment variable validation
- Google Cloud setup verification
- Bucket access testing
- Application startup testing

## Deployment Testing Workflow

### Pre-Deployment
```bash
# 1. Validate local configuration
./config-validator.sh validate

# 2. Run comprehensive tests
python3 test_integration.py

# 3. Verify deployment readiness
./verify.sh

# 4. Test with proper environment
CLOUD_STORAGE_BUCKET=your-bucket ./monitor.sh check
```

### Post-Deployment
```bash
# 1. Check service health
curl https://your-service.run.app/_health

# 2. Validate configuration
curl https://your-service.run.app/_config

# 3. Start monitoring
./monitor.sh --service-url https://your-service.run.app monitor

# 4. Test video creation (optional)
# Upload test files through the web interface
```

## Diagnostic Endpoints

### Health Check: `/_health`
```json
{
  "status": "healthy",
  "service": "wtfffmpeg"
}
```
- Always returns HTTP 200 if service is running
- Use for basic connectivity testing

### Configuration Check: `/_config`
```json
{
  "service": "wtfffmpeg",
  "configuration": {
    "cloud_storage_bucket_configured": true,
    "cloud_storage_bucket_value": "your-bucket-name",
    "secret_key_configured": true,
    "secret_key_source": "environment",
    "port": "8080"
  },
  "issues": [],
  "ready_for_video_creation": true
}
```
- Returns HTTP 200 when ready, HTTP 503 when misconfigured
- Provides detailed configuration status
- Lists specific issues preventing video creation

## Automated Monitoring Setup

### Basic Monitoring
```bash
# Start monitoring in background
nohup ./monitor.sh --service-url https://your-service.run.app monitor > monitor.log 2>&1 &

# Check logs
tail -f monitor.log
```

### Advanced Monitoring with Alerting
```bash
# Custom alert threshold and interval
./monitor.sh \
  --service-url https://your-service.run.app \
  --interval 30 \
  --alert-threshold 5 \
  --log-file /var/log/wtfffmpeg-monitor.log \
  monitor
```

### Integration with External Monitoring
The monitoring script logs in structured format that can be integrated with:
- Cloud Logging
- Prometheus/Grafana
- Datadog
- New Relic
- Custom alerting systems

## Error Analysis

### Log Analysis for Configuration Issues
```bash
# Check application startup logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=your-service" --limit=50

# Filter for configuration errors
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message:\"CLOUD_STORAGE_BUCKET\""

# Monitor real-time logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=your-service"
```

### Common Log Patterns
- `❌ CLOUD_STORAGE_BUCKET environment variable not set` - Missing bucket configuration
- `⚠️ Using default SECRET_KEY` - Production security warning
- `✅ Configuration validation completed successfully` - All good
- `🚀 Service ready for video creation: true` - Ready for use

## Troubleshooting Checklist

### ✅ Environment Variables
- [ ] `CLOUD_STORAGE_BUCKET` is set and valid
- [ ] `SECRET_KEY` is set (optional but recommended)
- [ ] `PORT` is valid if customized

### ✅ Google Cloud Setup
- [ ] Google Cloud CLI installed and authenticated
- [ ] Correct project selected
- [ ] Required APIs enabled (Cloud Run, Cloud Storage)

### ✅ Storage Bucket
- [ ] Bucket exists in the correct project
- [ ] Service account has Storage Object Admin role
- [ ] Bucket is accessible from the service

### ✅ Application
- [ ] Python dependencies installed
- [ ] Application starts without errors
- [ ] Health endpoint returns 200
- [ ] Config endpoint returns 200

### ✅ Network/Deployment
- [ ] Service is publicly accessible
- [ ] No firewall blocking access
- [ ] DNS resolution working
- [ ] SSL/TLS certificate valid

## Advanced Testing Scenarios

### Load Testing
```bash
# Use Apache Bench for basic load testing
ab -n 100 -c 10 https://your-service.run.app/_health

# Use curl for configuration endpoint testing
for i in {1..10}; do
  curl -s https://your-service.run.app/_config | jq '.ready_for_video_creation'
done
```

### Error Injection Testing
```bash
# Test with invalid bucket name
CLOUD_STORAGE_BUCKET=invalid-bucket-name python3 test_config.py

# Test without authentication
unset GOOGLE_APPLICATION_CREDENTIALS
python3 test_integration.py
```

### Performance Monitoring
```bash
# Monitor response times
./monitor.sh --service-url https://your-service.run.app check | grep "response time"

# Check resource usage
gcloud run services describe your-service --region=your-region --format="value(status.traffic[0].percent)"
```

## Security Considerations

### Environment Variables
- Never log the actual `SECRET_KEY` value
- Use strong, randomly generated secret keys in production
- Rotate secret keys periodically

### Bucket Access
- Use principle of least privilege for service accounts
- Consider bucket-level IAM instead of project-level
- Enable audit logging for bucket access

### Monitoring
- Protect monitoring endpoints if they contain sensitive information
- Use secure channels for alert notifications
- Implement rate limiting for diagnostic endpoints

## Getting Help

### Self-Service Troubleshooting
1. Run `./config-validator.sh troubleshoot` for guided troubleshooting
2. Check the configuration endpoint: `/_config`
3. Review the troubleshooting demo: `./troubleshooting_demo.sh`
4. Monitor with: `./monitor.sh check`

### Advanced Support
- Enable debug logging by setting `LOG_LEVEL=DEBUG`
- Collect logs from Cloud Logging
- Use the integration test suite to isolate issues
- Check GitHub Actions results for CI/CD issues

### Useful Commands Summary
```bash
# Quick health check
curl https://your-service.run.app/_health

# Configuration diagnosis  
curl https://your-service.run.app/_config | jq

# Local validation
./config-validator.sh validate

# Continuous monitoring
./monitor.sh --service-url https://your-service.run.app monitor

# Run all tests
python3 test_integration.py && python3 test_config.py

# Deployment verification
./verify.sh
```