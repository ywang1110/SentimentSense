#!/bin/bash

# SentimentSense Kubernetes Cleanup Script

set -e

echo "🧹 Starting SentimentSense Kubernetes cleanup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_APP="sentiment-sense"
NAMESPACE_MONITORING="monitoring"

# Functions
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Confirm deletion
confirm_deletion() {
    echo ""
    print_warning "This will delete ALL SentimentSense resources from Kubernetes!"
    echo ""
    echo "Resources to be deleted:"
    echo "- Namespace: $NAMESPACE_APP (and all resources inside)"
    echo "- Namespace: $NAMESPACE_MONITORING (and all resources inside)"
    echo "- All deployments, services, configmaps, secrets"
    echo ""
    
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Cleanup cancelled."
        exit 0
    fi
}

# Delete application resources
delete_application() {
    print_step "Deleting application resources"
    
    # Delete individual resources first (graceful)
    kubectl delete -f ../app/service.yaml --ignore-not-found=true
    kubectl delete -f ../app/deployment.yaml --ignore-not-found=true
    kubectl delete -f ../app/secret.yaml --ignore-not-found=true
    kubectl delete -f ../app/configmap.yaml --ignore-not-found=true
    
    print_success "Application resources deleted"
}

# Delete monitoring resources
delete_monitoring() {
    print_step "Deleting monitoring resources"
    
    kubectl delete -f ../monitoring/grafana.yaml --ignore-not-found=true
    kubectl delete -f ../monitoring/prometheus.yaml --ignore-not-found=true
    
    print_success "Monitoring resources deleted"
}

# Delete namespaces
delete_namespaces() {
    print_step "Deleting namespaces"
    
    # Delete namespaces (this will delete any remaining resources)
    kubectl delete namespace $NAMESPACE_APP --ignore-not-found=true
    kubectl delete namespace $NAMESPACE_MONITORING --ignore-not-found=true
    
    print_success "Namespaces deleted"
}

# Wait for cleanup completion
wait_for_cleanup() {
    print_step "Waiting for cleanup to complete"
    
    # Wait for namespaces to be fully deleted
    echo "Waiting for namespaces to be terminated..."
    
    while kubectl get namespace $NAMESPACE_APP &> /dev/null; do
        echo "  Waiting for $NAMESPACE_APP namespace to terminate..."
        sleep 5
    done
    
    while kubectl get namespace $NAMESPACE_MONITORING &> /dev/null; do
        echo "  Waiting for $NAMESPACE_MONITORING namespace to terminate..."
        sleep 5
    done
    
    print_success "Cleanup completed"
}

# Show remaining resources
show_remaining() {
    print_step "Checking for any remaining resources"
    
    echo ""
    echo "Remaining SentimentSense resources (should be empty):"
    echo "=================================================="
    
    echo ""
    echo "Namespaces:"
    kubectl get namespaces | grep -E "(sentiment-sense|monitoring)" || echo "  None found"
    
    echo ""
    echo "All namespaces:"
    kubectl get namespaces
}

# Main execution
main() {
    confirm_deletion
    delete_application
    delete_monitoring
    delete_namespaces
    wait_for_cleanup
    show_remaining
    
    echo ""
    print_success "🎉 SentimentSense cleanup completed!"
    echo ""
    echo "All SentimentSense resources have been removed from the cluster."
}

# Run main function
main "$@"
