#!/bin/bash

# Configuration validation and setup helper for WTfffmpeg
# This script helps administrators validate and configure the service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${BLUE}${BOLD}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..50})${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_environment_variables() {
    print_section "Environment Variables Check"
    
    local issues=0
    
    # Check CLOUD_STORAGE_BUCKET
    if [[ -n "$CLOUD_STORAGE_BUCKET" ]]; then
        print_success "CLOUD_STORAGE_BUCKET is set: $CLOUD_STORAGE_BUCKET"
        
        # Validate bucket name format
        if [[ "$CLOUD_STORAGE_BUCKET" =~ ^[a-z0-9][a-z0-9._-]*[a-z0-9]$ ]] && [[ ${#CLOUD_STORAGE_BUCKET} -le 63 ]]; then
            print_success "Bucket name format is valid"
        else
            print_error "Bucket name format is invalid (must be lowercase, 3-63 chars, alphanumeric/._-)"
            ((issues++))
        fi
    else
        print_error "CLOUD_STORAGE_BUCKET is not set"
        print_info "Set with: export CLOUD_STORAGE_BUCKET=your-bucket-name"
        ((issues++))
    fi
    
    # Check SECRET_KEY
    if [[ -n "$SECRET_KEY" ]]; then
        if [[ "$SECRET_KEY" == "a_very_strong_secret_key" ]]; then
            print_warning "Using default SECRET_KEY (not recommended for production)"
            print_info "Set with: export SECRET_KEY=your-custom-secret-key"
        else
            print_success "Custom SECRET_KEY is configured"
            if [[ ${#SECRET_KEY} -ge 32 ]]; then
                print_success "SECRET_KEY length is adequate (${#SECRET_KEY} chars)"
            else
                print_warning "SECRET_KEY is short (${#SECRET_KEY} chars, recommend 32+)"
            fi
        fi
    else
        print_warning "SECRET_KEY not set (will use default)"
        print_info "Set with: export SECRET_KEY=your-custom-secret-key"
    fi
    
    # Check PORT
    if [[ -n "$PORT" ]]; then
        if [[ "$PORT" =~ ^[0-9]+$ ]] && [[ $PORT -ge 1024 ]] && [[ $PORT -le 65535 ]]; then
            print_success "PORT is set to valid value: $PORT"
        else
            print_error "PORT value is invalid (must be 1024-65535)"
            ((issues++))
        fi
    else
        print_info "PORT not set (will default to 8080)"
    fi
    
    return $issues
}

check_google_cloud_configuration() {
    print_section "Google Cloud Configuration"
    
    local issues=0
    
    # Check if gcloud is installed
    if command -v gcloud &> /dev/null; then
        print_success "Google Cloud CLI is installed"
        
        # Check authentication
        if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
            local active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
            if [[ -n "$active_account" ]]; then
                print_success "Authenticated as: $active_account"
            else
                print_error "No active Google Cloud authentication"
                print_info "Run: gcloud auth login"
                ((issues++))
            fi
        else
            print_error "Failed to check Google Cloud authentication"
            ((issues++))
        fi
        
        # Check project
        local current_project=$(gcloud config get-value project 2>/dev/null)
        if [[ -n "$current_project" ]]; then
            print_success "Current project: $current_project"
        else
            print_error "No Google Cloud project set"
            print_info "Run: gcloud config set project YOUR_PROJECT_ID"
            ((issues++))
        fi
        
    else
        print_error "Google Cloud CLI not installed"
        print_info "Install from: https://cloud.google.com/sdk/docs/install"
        ((issues++))
    fi
    
    return $issues
}

check_bucket_access() {
    print_section "Cloud Storage Bucket Access"
    
    if [[ -z "$CLOUD_STORAGE_BUCKET" ]]; then
        print_error "Cannot check bucket access - CLOUD_STORAGE_BUCKET not set"
        return 1
    fi
    
    local issues=0
    
    if command -v gsutil &> /dev/null; then
        print_success "gsutil is available"
        
        # Check if bucket exists and is accessible
        if gsutil ls "gs://$CLOUD_STORAGE_BUCKET/" &> /dev/null; then
            print_success "Bucket gs://$CLOUD_STORAGE_BUCKET/ is accessible"
            
            # Test write permission
            local test_file="/tmp/wtfffmpeg-test-$(date +%s).txt"
            echo "Test file for WTfffmpeg configuration validation" > "$test_file"
            
            if gsutil cp "$test_file" "gs://$CLOUD_STORAGE_BUCKET/test-access.txt" &> /dev/null; then
                print_success "Write access to bucket confirmed"
                
                # Clean up test file
                gsutil rm "gs://$CLOUD_STORAGE_BUCKET/test-access.txt" &> /dev/null || true
            else
                print_error "Cannot write to bucket - check permissions"
                print_info "Required role: Storage Object Admin"
                ((issues++))
            fi
            
            rm -f "$test_file"
            
        else
            print_error "Cannot access bucket gs://$CLOUD_STORAGE_BUCKET/"
            print_info "Check if bucket exists and you have permissions"
            ((issues++))
        fi
    else
        print_error "gsutil not available"
        print_info "Install Google Cloud SDK"
        ((issues++))
    fi
    
    return $issues
}

test_application_locally() {
    print_section "Local Application Test"
    
    if [[ ! -f "$SCRIPT_DIR/app.py" ]]; then
        print_error "app.py not found in current directory"
        return 1
    fi
    
    local issues=0
    
    # Test Python imports
    if python3 -c "import flask, google.cloud.storage" &> /dev/null; then
        print_success "Required Python packages are available"
    else
        print_error "Missing required Python packages"
        print_info "Run: pip install -r requirements.txt"
        ((issues++))
    fi
    
    # Test application startup
    if python3 -c "import app; print('App imports successfully')" &> /dev/null; then
        print_success "Application imports successfully"
        
        # Test endpoints
        local test_output
        test_output=$(python3 -c "
import app
with app.app.test_client() as client:
    health_response = client.get('/_health')
    config_response = client.get('/_config')
    
    print(f'Health endpoint: {health_response.status_code}')
    print(f'Config endpoint: {config_response.status_code}')
    
    config_data = config_response.get_json()
    print(f'Ready for video creation: {config_data[\"ready_for_video_creation\"]}')
    
    if len(config_data[\"issues\"]) > 0:
        print('Issues detected:')
        for issue in config_data[\"issues\"]:
            print(f'  - {issue}')
        " 2>/dev/null)
        
        echo "$test_output"
        
        if echo "$test_output" | grep -q "Health endpoint: 200"; then
            print_success "Health endpoint working"
        else
            print_error "Health endpoint failed"
            ((issues++))
        fi
        
        if echo "$test_output" | grep -q "Ready for video creation: True"; then
            print_success "Service ready for video creation"
        else
            print_warning "Service not ready for video creation (check configuration)"
        fi
        
    else
        print_error "Application failed to start"
        ((issues++))
    fi
    
    return $issues
}

generate_deployment_config() {
    print_section "Deployment Configuration"
    
    print_info "Current configuration for deployment:"
    echo
    echo "Environment Variables:"
    echo "  CLOUD_STORAGE_BUCKET=${CLOUD_STORAGE_BUCKET:-NOT_SET}"
    echo "  SECRET_KEY=${SECRET_KEY:+***SET***}"
    echo "  PORT=${PORT:-8080}"
    echo
    
    if [[ -n "$CLOUD_STORAGE_BUCKET" ]]; then
        echo "Cloud Run deployment command:"
        echo "  gcloud run deploy YOUR_SERVICE_NAME \\"
        echo "    --image gcr.io/YOUR_PROJECT/wtfffmpeg \\"
        echo "    --platform managed \\"
        echo "    --region YOUR_REGION \\"
        echo "    --allow-unauthenticated \\"
        echo "    --set-env-vars=\"CLOUD_STORAGE_BUCKET=$CLOUD_STORAGE_BUCKET\""
        if [[ -n "$SECRET_KEY" && "$SECRET_KEY" != "a_very_strong_secret_key" ]]; then
            echo "    --set-env-vars=\"SECRET_KEY=$SECRET_KEY\""
        fi
        echo
    fi
    
    echo "Docker run command for local testing:"
    echo "  docker run -p 8080:8080 \\"
    if [[ -n "$CLOUD_STORAGE_BUCKET" ]]; then
        echo "    -e CLOUD_STORAGE_BUCKET=$CLOUD_STORAGE_BUCKET \\"
    fi
    if [[ -n "$SECRET_KEY" ]]; then
        echo "    -e SECRET_KEY=$SECRET_KEY \\"
    fi
    echo "    wtfffmpeg:latest"
}

show_troubleshooting_guide() {
    print_section "Troubleshooting Guide"
    
    echo "Common issues and solutions:"
    echo
    echo "1. 'Service configuration error. Please contact administrator'"
    echo "   → CLOUD_STORAGE_BUCKET environment variable not set"
    echo "   → Solution: Set the environment variable in your deployment"
    echo
    echo "2. 'Video creation will fail'"
    echo "   → Cloud Storage bucket not accessible"
    echo "   → Solution: Check bucket exists and service account has permissions"
    echo
    echo "3. Service returns HTTP 503 on /_config"
    echo "   → Configuration issues prevent video creation"
    echo "   → Solution: Check /_config response for specific issues"
    echo
    echo "4. Permission denied accessing bucket"
    echo "   → Service account lacks Storage Object Admin role"
    echo "   → Solution: Grant appropriate IAM permissions"
    echo
    echo "Useful commands:"
    echo "  Check service health: curl https://YOUR_SERVICE_URL/_health"
    echo "  Check configuration: curl https://YOUR_SERVICE_URL/_config"
    echo "  View logs: gcloud logging tail \"resource.type=cloud_run_revision\""
    echo "  Monitor service: ./monitor.sh --service-url YOUR_URL monitor"
}

run_full_validation() {
    print_section "WTfffmpeg Configuration Validation"
    echo -e "${BOLD}This script will validate your WTfffmpeg configuration${NC}"
    echo
    
    local total_issues=0
    
    check_environment_variables
    ((total_issues += $?))
    
    check_google_cloud_configuration
    ((total_issues += $?))
    
    check_bucket_access
    ((total_issues += $?))
    
    test_application_locally
    ((total_issues += $?))
    
    generate_deployment_config
    
    print_section "Validation Summary"
    
    if [[ $total_issues -eq 0 ]]; then
        print_success "Configuration validation completed successfully!"
        print_success "Your WTfffmpeg setup is ready for deployment"
    else
        print_error "Configuration validation found $total_issues issue(s)"
        print_info "Please address the issues above before deployment"
    fi
    
    echo
    echo "For additional help, run: $0 troubleshoot"
    
    return $total_issues
}

show_help() {
    cat << EOF
WTfffmpeg Configuration Validator

Usage: $0 [COMMAND]

Commands:
  validate      Run full configuration validation (default)
  env           Check environment variables only
  gcloud        Check Google Cloud configuration only  
  bucket        Check bucket access only
  app           Test application locally only
  config        Show deployment configuration
  troubleshoot  Show troubleshooting guide
  help          Show this help message

Environment Variables:
  CLOUD_STORAGE_BUCKET    Required: Cloud Storage bucket name
  SECRET_KEY              Optional: Custom secret key for Flask
  PORT                    Optional: Port number (default: 8080)

Examples:
  # Full validation
  $0 validate
  
  # Quick environment check
  CLOUD_STORAGE_BUCKET=my-bucket $0 env
  
  # Check only Google Cloud setup
  $0 gcloud

EOF
}

main() {
    local command="${1:-validate}"
    
    case $command in
        validate)
            run_full_validation
            ;;
        env)
            check_environment_variables
            ;;
        gcloud)
            check_google_cloud_configuration
            ;;
        bucket)
            check_bucket_access
            ;;
        app)
            test_application_locally
            ;;
        config)
            generate_deployment_config
            ;;
        troubleshoot)
            show_troubleshooting_guide
            ;;
        help)
            show_help
            ;;
        *)
            echo "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"