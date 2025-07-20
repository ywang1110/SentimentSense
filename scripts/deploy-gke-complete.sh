#!/bin/bash

# SentimentSense Complete GKE Deployment Script
# This script creates GKE cluster, builds image, and deploys the application

set -e

echo "🚀 Starting SentimentSense Complete GKE Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - MODIFY THESE VALUES
PROJECT_ID="${PROJECT_ID:-sentiment-sense-demo}"
CLUSTER_NAME="${CLUSTER_NAME:-sentiment-sense-cluster}"
ZONE="${ZONE:-us-central1-a}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-2}"
NUM_NODES="${NUM_NODES:-1}"
IMAGE_NAME="gcr.io/$PROJECT_ID/sentiment-sense:latest"

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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step 1 "Checking prerequisites"
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed"
        echo "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        echo "Install with: gcloud components install kubectl"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup GCP project
setup_gcp_project() {
    print_step 2 "Setting up GCP project"
    
    # Set project
    gcloud config set project $PROJECT_ID
    print_info "Project set to: $PROJECT_ID"
    
    # Enable required APIs
    print_info "Enabling required APIs..."
    gcloud services enable container.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable compute.googleapis.com
    
    print_success "GCP project setup completed"
}

# Create GKE cluster
create_gke_cluster() {
    print_step 3 "Creating GKE cluster"
    
    # Check if cluster already exists
    if gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE &> /dev/null; then
        print_warning "Cluster $CLUSTER_NAME already exists, skipping creation"
        return 0
    fi
    
    print_info "Creating cluster: $CLUSTER_NAME"
    print_info "Zone: $ZONE"
    print_info "Machine type: $MACHINE_TYPE (preemptible)"
    print_info "Number of nodes: $NUM_NODES"
    print_warning "Using preemptible nodes for cost savings (~80% cheaper)"
    
    gcloud container clusters create $CLUSTER_NAME \
        --zone=$ZONE \
        --num-nodes=$NUM_NODES \
        --machine-type=$MACHINE_TYPE \
        --preemptible \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=2 \
        --enable-autorepair \
        --enable-autoupgrade \
        --disk-size=50GB \
        --scopes=https://www.googleapis.com/auth/cloud-platform
    
    print_success "GKE cluster created successfully"
}

# Get cluster credentials
get_cluster_credentials() {
    print_step 4 "Getting cluster credentials"
    
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE
    
    # Verify connection
    kubectl cluster-info
    
    print_success "Cluster credentials configured"
}

# Build and push Docker image
build_and_push_image() {
    print_step 5 "Building and pushing Docker image"
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in current directory"
        exit 1
    fi
    
    print_info "Building image: $IMAGE_NAME"
    docker build -t $IMAGE_NAME .
    
    print_info "Pushing image to Google Container Registry"
    docker push $IMAGE_NAME
    
    print_success "Docker image built and pushed"
}

# Update deployment with correct image
update_deployment_image() {
    print_step 6 "Updating deployment configuration"
    
    # Update deployment.yaml with correct image
    if [ -f "k8s/app/deployment.yaml" ]; then
        sed -i.bak "s|image: .*sentiment-sense:latest|image: $IMAGE_NAME|g" k8s/app/deployment.yaml
        print_info "Updated deployment.yaml with image: $IMAGE_NAME"
    else
        print_error "k8s/app/deployment.yaml not found"
        exit 1
    fi
    
    print_success "Deployment configuration updated"
}

# Deploy application
deploy_application() {
    print_step 7 "Deploying SentimentSense application"
    
    # Create namespaces
    kubectl apply -f k8s/app/namespace.yaml
    
    # Deploy configurations
    kubectl apply -f k8s/app/configmap.yaml
    kubectl apply -f k8s/app/secret.yaml
    
    # Deploy application
    kubectl apply -f k8s/app/deployment.yaml
    kubectl apply -f k8s/app/service.yaml

    # Deploy autoscaling
    kubectl apply -f k8s/app/hpa.yaml

    print_success "Application and autoscaling deployed"
}

# Deploy monitoring
deploy_monitoring() {
    print_step 8 "Deploying monitoring stack"
    
    kubectl apply -f k8s/monitoring/prometheus.yaml
    kubectl apply -f k8s/monitoring/grafana.yaml
    
    print_success "Monitoring stack deployed"
}

# Wait for deployments
wait_for_deployments() {
    print_step 9 "Waiting for deployments to be ready"
    
    print_info "This may take several minutes for first-time model download..."
    
    echo "Waiting for SentimentSense (up to 10 minutes)..."
    kubectl wait --for=condition=available --timeout=600s deployment/sentiment-sense -n sentiment-sense

    # Skip monitoring wait for cost savings
    # echo "Waiting for Prometheus..."
    # kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring

    # echo "Waiting for Grafana..."
    # kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring
    
    print_success "All deployments are ready"
}

# Show access information
show_access_info() {
    print_step 10 "Getting access information"
    
    echo ""
    echo "🌐 Access Information:"
    echo "===================="
    
    # Wait for external IP with retry logic
    print_info "Waiting for LoadBalancer external IP assignment..."

    EXTERNAL_IP=""
    RETRY_COUNT=0
    MAX_RETRIES=12  # 6 minutes total

    while [ -z "$EXTERNAL_IP" ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        sleep 30
        EXTERNAL_IP=$(kubectl get svc sentiment-sense-external -n sentiment-sense -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ -z "$EXTERNAL_IP" ]; then
            print_info "Still waiting for external IP... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        fi
    done

    # Display results
    echo ""
    echo "🌐 =========================================="
    echo "🌐 LOADBALANCER EXTERNAL IP INFORMATION"
    echo "🌐 =========================================="

    if [ -n "$EXTERNAL_IP" ]; then
        echo ""
        echo "✅ SUCCESS! Your LoadBalancer External IP is ready:"
        echo ""
        echo "🔗 EXTERNAL IP: $EXTERNAL_IP"
        echo ""
        echo "📱 SentimentSense API Access:"
        echo "   🌍 Base URL:     http://$EXTERNAL_IP"
        echo "   📖 API Docs:     http://$EXTERNAL_IP/docs"
        echo "   ❤️  Health Check: http://$EXTERNAL_IP/health/simple"
        echo "   🧪 Test Analyze: http://$EXTERNAL_IP/analyze"
        echo ""
        echo "🧪 Quick Test Commands:"
        echo "   curl http://$EXTERNAL_IP/health/simple"
        echo "   curl -X POST http://$EXTERNAL_IP/analyze \\"
        echo "        -H 'Content-Type: application/json' \\"
        echo "        -d '{\"text\": \"I love this product!\"}'"
        echo ""
    else
        echo ""
        echo "⚠️  External IP not yet assigned after 6 minutes"
        echo "   This can happen - please check manually:"
        echo ""
        kubectl get svc sentiment-sense-external -n sentiment-sense
        echo ""
        echo "   Run this command to check IP status:"
        echo "   kubectl get svc sentiment-sense-external -n sentiment-sense -o wide"
        echo ""
    fi
    
    echo ""
    echo "📊 Monitoring Services:"
    kubectl get svc -n monitoring
    echo "   🔐 Grafana login: admin / admin123"
    
    echo ""
    echo "🔍 Useful Commands:"
    echo "   Check pods: kubectl get pods --all-namespaces"
    echo "   View logs: kubectl logs -f deployment/sentiment-sense -n sentiment-sense"
    echo "   Get services: kubectl get svc --all-namespaces"
    
    echo ""
    echo "💰 Ultra-Cheap Toy Project Cost:"
    echo "   Estimated monthly cost: ~\$90-110 (minimal config)"
    echo "   💡 Savings: ~85% compared to production setup"
    echo "   🎯 Perfect for learning and experimentation"
    echo "   ⚠️  Note: Preemptible nodes can be terminated by Google"
    echo "   To stop billing: Run './scripts/cleanup-gke.sh'"
}

# Main execution
main() {
    echo "Configuration:"
    echo "  Project ID: $PROJECT_ID"
    echo "  Cluster Name: $CLUSTER_NAME"
    echo "  Zone: $ZONE"
    echo "  Machine Type: $MACHINE_TYPE"
    echo "  Number of Nodes: $NUM_NODES"
    echo ""
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    check_prerequisites
    setup_gcp_project
    create_gke_cluster
    get_cluster_credentials
    build_and_push_image
    update_deployment_image
    deploy_application
    # Skip monitoring for cost savings
    # deploy_monitoring
    wait_for_deployments
    show_access_info
    
    echo ""
    echo "🎉 =========================================="
    print_success "🎉 SentimentSense GKE Deployment Complete!"
    echo "🎉 =========================================="
    echo ""

    # Show final IP summary
    FINAL_IP=$(kubectl get svc sentiment-sense-external -n sentiment-sense -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$FINAL_IP" ]; then
        echo "🔗 YOUR API IS LIVE AT: http://$FINAL_IP"
        echo ""
        echo "📋 Quick Reference:"
        echo "   • API Base:    http://$FINAL_IP"
        echo "   • Docs:        http://$FINAL_IP/docs"
        echo "   • Health:      http://$FINAL_IP/health/simple"
        echo ""
    fi

    echo "📝 Next Steps:"
    echo "1. 🧪 Test your API with the commands shown above"
    echo "2. 📖 Explore the interactive docs at /docs"
    echo "3. 💰 Monitor costs in GCP Console (~\$110/month)"
    echo "4. 🧹 Run './scripts/cleanup-gke.sh' when done"
    echo ""
    print_warning "💰 Remember: This deployment costs ~\$110/month"
    print_warning "🧹 Don't forget to clean up when you're done experimenting!"
}

# Run main function
main "$@"
