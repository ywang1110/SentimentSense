#!/bin/bash

# SentimentSense Kubernetes Quick Start Deployment Script

set -e

echo "🚀 Starting SentimentSense Kubernetes Quick Start Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_APP="sentiment-sense"
NAMESPACE_MONITORING="monitoring"
IMAGE_NAME="sentiment-sense:latest"

# Functions
print_step() {
    echo -e "${BLUE}📋 Step $1: $2${NC}"
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

# Check prerequisites
check_prerequisites() {
    print_step 1 "Checking prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Deploy namespaces
deploy_namespaces() {
    print_step 2 "Creating namespaces"
    kubectl apply -f ../app/namespace.yaml
    print_success "Namespaces created"
}

# Deploy application
deploy_application() {
    print_step 3 "Deploying SentimentSense application"
    
    # Apply configurations
    kubectl apply -f ../app/configmap.yaml
    kubectl apply -f ../app/secret.yaml
    
    # Check if image exists (for local development)
    print_warning "Make sure your Docker image '$IMAGE_NAME' is available"
    print_warning "For local clusters (minikube/kind): docker build -t $IMAGE_NAME ."
    print_warning "For cloud clusters: push image to registry and update deployment.yaml"
    
    # Deploy application
    kubectl apply -f ../app/deployment.yaml
    kubectl apply -f ../app/service.yaml
    kubectl apply -f ../app/hpa.yaml

    print_success "Application and autoscaling deployed"
}

# Deploy monitoring
deploy_monitoring() {
    print_step 4 "Deploying monitoring stack"
    
    kubectl apply -f ../monitoring/prometheus.yaml
    kubectl apply -f ../monitoring/grafana.yaml
    
    print_success "Monitoring stack deployed"
}

# Wait for deployments
wait_for_deployments() {
    print_step 5 "Waiting for deployments to be ready"
    
    echo "Waiting for SentimentSense..."
    kubectl wait --for=condition=available --timeout=300s deployment/sentiment-sense -n $NAMESPACE_APP
    
    echo "Waiting for Prometheus..."
    kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n $NAMESPACE_MONITORING
    
    echo "Waiting for Grafana..."
    kubectl wait --for=condition=available --timeout=300s deployment/grafana -n $NAMESPACE_MONITORING
    
    print_success "All deployments are ready"
}

# Show access information
show_access_info() {
    print_step 6 "Getting access information"
    
    echo ""
    echo "🌐 Access Information:"
    echo "===================="
    
    # Get external IPs
    echo ""
    echo "📱 SentimentSense API:"
    kubectl get svc sentiment-sense-external -n $NAMESPACE_APP -o wide 2>/dev/null || echo "   Internal access only (ClusterIP)"
    
    echo ""
    echo "📊 Prometheus:"
    kubectl get svc prometheus-service -n $NAMESPACE_MONITORING -o wide
    
    echo ""
    echo "📈 Grafana:"
    kubectl get svc grafana-service -n $NAMESPACE_MONITORING -o wide
    echo "   Default login: admin / admin123"
    
    echo ""
    echo "🔍 To check pod status:"
    echo "   kubectl get pods -n $NAMESPACE_APP"
    echo "   kubectl get pods -n $NAMESPACE_MONITORING"
    
    echo ""
    echo "📝 To view logs:"
    echo "   kubectl logs -f deployment/sentiment-sense -n $NAMESPACE_APP"
    echo "   kubectl logs -f deployment/prometheus -n $NAMESPACE_MONITORING"
    echo "   kubectl logs -f deployment/grafana -n $NAMESPACE_MONITORING"
}

# Main execution
main() {
    check_prerequisites
    deploy_namespaces
    deploy_application
    deploy_monitoring
    wait_for_deployments
    show_access_info
    
    echo ""
    print_success "🎉 SentimentSense Quick Start deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Test the API endpoints"
    echo "2. Access Grafana dashboards"
    echo "3. Check Prometheus metrics"
    echo "4. Monitor application logs"
}

# Run main function
main "$@"
