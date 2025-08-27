#!/bin/bash

# Automated health monitoring script for WTfffmpeg service
# This script can be run by administrators to continuously monitor
# service configuration and health status

# Don't use set -e since we want to handle errors gracefully

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_URL="${SERVICE_URL:-}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"  # seconds
LOG_FILE="${LOG_FILE:-/tmp/wtfffmpeg-monitor.log}"
ALERT_THRESHOLD="${ALERT_THRESHOLD:-3}"  # consecutive failures before alert

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CONSECUTIVE_FAILURES=0
TOTAL_CHECKS=0
TOTAL_FAILURES=0

log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

check_local_configuration() {
    log_message "INFO" "🔍 Checking local configuration..."
    
    # Check if running locally
    if [[ -f "$SCRIPT_DIR/app.py" ]]; then
        log_message "INFO" "Found local app.py, running local tests..."
        
        # Run basic configuration test
        cd "$SCRIPT_DIR"
        local python_result
        python_result=$(python3 -c "
import app
import sys
with app.app.test_client() as client:
    health_response = client.get('/_health')
    config_response = client.get('/_config')
    
    print(f'Health: {health_response.status_code}')
    print(f'Config: {config_response.status_code}')
    
    if health_response.status_code != 200:
        sys.exit(1)
    
    config_data = config_response.get_json()
    print(f'Ready for video creation: {config_data[\"ready_for_video_creation\"]}')
    
    if len(config_data[\"issues\"]) > 0:
        print('Configuration issues found:')
        for issue in config_data[\"issues\"]:
            print(f'  - {issue}')
        if config_data['ready_for_video_creation']:
            sys.exit(2)  # Warnings but functional
        else:
            sys.exit(3)  # Critical issues
    sys.exit(0)  # All good
        " 2>&1)
        local exit_code=$?
        
        echo "$python_result"
        
        if [[ $exit_code -eq 0 ]]; then
            log_message "INFO" "✅ Local configuration check passed"
            return 0
        elif [[ $exit_code -eq 2 ]]; then
            log_message "WARN" "⚠️  Local configuration has issues but service is functional"
            return 2
        elif [[ $exit_code -eq 3 ]]; then
            log_message "ERROR" "❌ Local configuration has critical issues"
            return 1
        else
            log_message "ERROR" "❌ Local configuration check failed"
            return 1
        fi
    else
        log_message "WARN" "Local app.py not found, skipping local tests"
        return 0
    fi
}

check_remote_service() {
    if [[ -z "$SERVICE_URL" ]]; then
        log_message "WARN" "SERVICE_URL not set, skipping remote checks"
        return 0
    fi
    
    log_message "INFO" "🌐 Checking remote service at $SERVICE_URL"
    
    # Check health endpoint
    local health_status
    if health_status=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$SERVICE_URL/_health" 2>/dev/null); then
        if [[ "$health_status" == "200" ]]; then
            log_message "INFO" "✅ Health endpoint: OK (200)"
        else
            log_message "ERROR" "❌ Health endpoint: Failed ($health_status)"
            return 1
        fi
    else
        log_message "ERROR" "❌ Health endpoint: Connection failed"
        return 1
    fi
    
    # Check config endpoint
    local config_status
    if config_status=$(curl -s -w "%{http_code}" -o /tmp/config_response.json "$SERVICE_URL/_config" 2>/dev/null); then
        if [[ "$config_status" == "200" ]]; then
            log_message "INFO" "✅ Config endpoint: OK (200) - Service ready"
            
            # Parse and log configuration details
            if command -v jq &> /dev/null; then
                local bucket_configured=$(jq -r '.configuration.cloud_storage_bucket_configured' /tmp/config_response.json 2>/dev/null)
                local bucket_value=$(jq -r '.configuration.cloud_storage_bucket_value' /tmp/config_response.json 2>/dev/null)
                local secret_configured=$(jq -r '.configuration.secret_key_configured' /tmp/config_response.json 2>/dev/null)
                
                log_message "INFO" "  Bucket configured: $bucket_configured ($bucket_value)"
                log_message "INFO" "  Secret configured: $secret_configured"
            fi
        elif [[ "$config_status" == "503" ]]; then
            log_message "ERROR" "❌ Config endpoint: Service Unavailable (503) - Configuration issues"
            
            # Log configuration issues if available
            if command -v jq &> /dev/null && [[ -f /tmp/config_response.json ]]; then
                local issues=$(jq -r '.issues[]' /tmp/config_response.json 2>/dev/null)
                if [[ -n "$issues" ]]; then
                    log_message "ERROR" "Configuration issues:"
                    while IFS= read -r issue; do
                        log_message "ERROR" "  - $issue"
                    done <<< "$issues"
                fi
            fi
            return 1
        else
            log_message "ERROR" "❌ Config endpoint: Unexpected status ($config_status)"
            return 1
        fi
    else
        log_message "ERROR" "❌ Config endpoint: Connection failed"
        return 1
    fi
    
    return 0
}

perform_health_check() {
    ((TOTAL_CHECKS++))
    local check_failed=false
    
    # Check local configuration
    local local_result=0
    check_local_configuration || local_result=$?
    
    # Check remote service if URL provided
    local remote_result=0
    if [[ -n "$SERVICE_URL" ]]; then
        check_remote_service || remote_result=$?
    fi
    
    # Determine overall result
    if [[ $local_result -ne 0 && $local_result -ne 2 ]] || [[ $remote_result -ne 0 ]]; then
        check_failed=true
        ((CONSECUTIVE_FAILURES++))
        ((TOTAL_FAILURES++))
    else
        CONSECUTIVE_FAILURES=0
        if [[ $local_result -eq 2 ]]; then
            log_message "WARN" "⚠️  Service is functional but has configuration warnings"
        else
            log_message "INFO" "✅ Overall health check: PASSED"
        fi
    fi
    
    # Alert if threshold reached
    if [[ $CONSECUTIVE_FAILURES -ge $ALERT_THRESHOLD ]]; then
        log_message "ALERT" "🚨 ALERT: $CONSECUTIVE_FAILURES consecutive failures detected!"
        log_message "ALERT" "🚨 Service may require administrator attention"
        
        # Could add email/webhook notification here
        # send_alert_notification "$CONSECUTIVE_FAILURES consecutive failures"
    fi
    
    # Log statistics
    local success_rate=$((100 * (TOTAL_CHECKS - TOTAL_FAILURES) / TOTAL_CHECKS))
    log_message "INFO" "📊 Stats: $TOTAL_CHECKS checks, $TOTAL_FAILURES failures ($success_rate% success rate)"
}

run_single_check() {
    log_message "INFO" "🏥 Starting WTfffmpeg health check..."
    perform_health_check
    log_message "INFO" "🏁 Health check completed"
}

run_continuous_monitoring() {
    log_message "INFO" "🔄 Starting continuous monitoring (interval: ${CHECK_INTERVAL}s)"
    log_message "INFO" "📝 Logging to: $LOG_FILE"
    if [[ -n "$SERVICE_URL" ]]; then
        log_message "INFO" "🌐 Monitoring remote service: $SERVICE_URL"
    fi
    
    while true; do
        perform_health_check
        
        echo -e "\n${BLUE}Waiting ${CHECK_INTERVAL} seconds until next check...${NC}"
        sleep "$CHECK_INTERVAL"
    done
}

show_help() {
    cat << EOF
WTfffmpeg Health Monitor

Usage: $0 [OPTIONS] [COMMAND]

Commands:
  check       Run a single health check (default)
  monitor     Run continuous monitoring
  help        Show this help message

Options:
  --service-url URL    URL of the deployed service to monitor
  --interval SECONDS   Check interval for continuous monitoring (default: 60)
  --log-file PATH      Log file path (default: /tmp/wtfffmpeg-monitor.log)
  --alert-threshold N  Consecutive failures before alert (default: 3)

Environment Variables:
  SERVICE_URL          URL of the deployed service
  CHECK_INTERVAL       Check interval in seconds
  LOG_FILE            Log file path
  ALERT_THRESHOLD     Alert threshold

Examples:
  # Single check (local only)
  $0 check
  
  # Monitor local and remote service
  $0 --service-url https://my-service.run.app monitor
  
  # Quick remote check
  SERVICE_URL=https://my-service.run.app $0 check

EOF
}

main() {
    local command="check"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --service-url)
                SERVICE_URL="$2"
                shift 2
                ;;
            --interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            --log-file)
                LOG_FILE="$2"
                shift 2
                ;;
            --alert-threshold)
                ALERT_THRESHOLD="$2"
                shift 2
                ;;
            check|monitor|help)
                command="$1"
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    case $command in
        check)
            run_single_check
            ;;
        monitor)
            run_continuous_monitoring
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