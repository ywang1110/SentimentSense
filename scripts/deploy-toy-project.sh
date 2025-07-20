#!/bin/bash

# SentimentSense Ultra-Cheap Toy Project Deployment
# Optimized for minimum cost - perfect for learning and experimentation

set -e

echo "🎯 Starting Ultra-Cheap SentimentSense Toy Project Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ultra-cheap configuration
PROJECT_ID="${PROJECT_ID:-sentiment-sense-demo}"
CLUSTER_NAME="${CLUSTER_NAME:-sentiment-toy}"
ZONE="${ZONE:-us-central1-a}"
MACHINE_TYPE="e2-small"  # Smallest possible
NUM_NODES="1"            # Absolute minimum
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

# Show cost breakdown
show_cost_breakdown() {
    echo ""
    echo "💰 Ultra-Cheap Configuration Cost Breakdown:"
    echo "============================================="
    echo "GKE Management Fee:    ~\$72/month"
    echo "1x e2-small (preempt): ~\$5/month"
    echo "LoadBalancer:          ~\$18/month"
    echo "Storage/Network:       ~\$5/month"
    echo "----------------------------------------"
    echo "TOTAL:                 ~\$100/month"
    echo ""
    echo "🎉 That's 85% cheaper than production setup!"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    print_step 1 "Checking prerequisites"
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup GCP project
setup_gcp_project() {
    print_step 2 "Setting up GCP project"
    
    gcloud config set project $PROJECT_ID
    print_info "Project set to: $PROJECT_ID"
    
    # Enable required APIs
    print_info "Enabling required APIs..."
    gcloud services enable container.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    print_success "GCP project setup completed"
}

# Create ultra-cheap GKE cluster
create_toy_cluster() {
    print_step 3 "Creating ultra-cheap toy cluster"
    
    if gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE &> /dev/null; then
        print_warning "Cluster $CLUSTER_NAME already exists, skipping creation"
        return 0
    fi
    
    print_info "Creating ULTRA-CHEAP cluster: $CLUSTER_NAME"
    print_info "Machine type: $MACHINE_TYPE (smallest available)"
    print_info "Nodes: $NUM_NODES (absolute minimum)"
    print_warning "This is optimized for cost, not performance!"
    
    gcloud container clusters create $CLUSTER_NAME \
        --zone=$ZONE \
        --num-nodes=$NUM_NODES \
        --machine-type=$MACHINE_TYPE \
        --preemptible \
        --disk-size=20GB \
        --no-enable-autoupgrade \
        --no-enable-autorepair \
        --scopes=https://www.googleapis.com/auth/cloud-platform
    
    print_success "Ultra-cheap cluster created!"
}

# Get cluster credentials
get_cluster_credentials() {
    print_step 4 "Getting cluster credentials"
    
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE
    kubectl cluster-info
    
    print_success "Cluster credentials configured"
}

# Build and push image
build_and_push_image() {
    print_step 5 "Building and pushing Docker image"
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in current directory"
        exit 1
    fi
    
    print_info "Building image: $IMAGE_NAME"
    docker build -t $IMAGE_NAME .
    
    print_info "Pushing to Google Container Registry"
    docker push $IMAGE_NAME
    
    print_success "Docker image ready"
}

# Update deployment for toy project
update_deployment_for_toy() {
    print_step 6 "Optimizing deployment for toy project"
    
    # Create a minimal deployment config
    cat > k8s/app/deployment-toy.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-sense
  namespace: sentiment-sense
  labels:
    app: sentiment-sense
spec:
  replicas: 1  # Single replica for cost savings
  selector:
    matchLabels:
      app: sentiment-sense
  template:
    metadata:
      labels:
        app: sentiment-sense
    spec:
      containers:
      - name: sentiment-sense
        image: $IMAGE_NAME
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        
        # Minimal resources for toy project
        resources:
          requests:
            cpu: 100m      # Very low CPU
            memory: 1Gi    # Minimal memory
          limits:
            cpu: 500m      # Low CPU limit
            memory: 2Gi    # Low memory limit
        
        # Simple health checks
        livenessProbe:
          httpGet:
            path: /health/simple
            port: 8000
          initialDelaySeconds: 120
          periodSeconds: 60
        
        readinessProbe:
          httpGet:
            path: /health/simple
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        
        # Startup probe with long timeout for model loading
        startupProbe:
          httpGet:
            path: /health/simple
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 20  # 10+ minutes for model download
        
        # Environment variables
        envFrom:
        - configMapRef:
            name: sentiment-sense-config
        
        env:
        - name: ALERT_EMAIL
          valueFrom:
            secretKeyRef:
              name: sentiment-sense-secret
              key: ALERT_EMAIL
      
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
EOF
    
    print_success "Toy deployment configuration created"
}

# Deploy minimal application
deploy_toy_application() {
    print_step 7 "Deploying minimal toy application"
    
    # Create namespace
    kubectl apply -f k8s/app/namespace.yaml
    
    # Deploy configurations
    kubectl apply -f k8s/app/configmap.yaml
    kubectl apply -f k8s/app/secret.yaml
    
    # Deploy minimal application
    kubectl apply -f k8s/app/deployment-toy.yaml
    kubectl apply -f k8s/app/service.yaml
    
    print_success "Minimal application deployed"
}

# Wait for deployment
wait_for_toy_deployment() {
    print_step 8 "Waiting for toy deployment"
    
    print_info "This may take 10+ minutes for first-time model download..."
    print_warning "Be patient - we're using minimal resources!"
    
    kubectl wait --for=condition=available --timeout=900s deployment/sentiment-sense -n sentiment-sense
    
    print_success "Toy deployment is ready!"
}

# Show access info
show_toy_access_info() {
    print_step 9 "Getting access information"
    
    echo ""
    echo "🎯 Toy Project Access Information:"
    echo "=================================="
    
    # Wait for external IP
    print_info "Waiting for external IP..."
    sleep 30
    
    EXTERNAL_IP=$(kubectl get svc sentiment-sense-external -n sentiment-sense -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$EXTERNAL_IP" ]; then
        echo "   🌍 API URL: http://$EXTERNAL_IP"
        echo "   📖 Docs: http://$EXTERNAL_IP/docs"
        echo "   ❤️  Health: http://$EXTERNAL_IP/health/simple"
        echo ""
        echo "🧪 Test your API:"
        echo "   curl http://$EXTERNAL_IP/health/simple"
        echo "   curl -X POST http://$EXTERNAL_IP/analyze -H 'Content-Type: application/json' -d '{\"text\":\"I love this!\"}'"
    else
        echo "   ⏳ External IP still being assigned..."
        kubectl get svc sentiment-sense-external -n sentiment-sense
    fi
    
    show_cost_breakdown
}

# Main execution
main() {
    echo "🎯 Ultra-Cheap Toy Project Configuration:"
    echo "  Project ID: $PROJECT_ID"
    echo "  Cluster: $CLUSTER_NAME"
    echo "  Machine: $MACHINE_TYPE (smallest)"
    echo "  Nodes: $NUM_NODES (minimum)"
    echo "  Cost: ~\$100/month"
    echo ""
    
    print_warning "This is optimized for COST, not performance!"
    print_warning "Perfect for learning, testing, and experimentation"
    echo ""
    
    read -p "Deploy ultra-cheap toy project? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    check_prerequisites
    setup_gcp_project
    create_toy_cluster
    get_cluster_credentials
    build_and_push_image
    update_deployment_for_toy
    deploy_toy_application
    wait_for_toy_deployment
    show_toy_access_info
    
    echo ""
    print_success "🎉 Ultra-Cheap Toy Project Deployed!"
    echo ""
    echo "💡 Remember:"
    echo "1. This costs ~\$100/month (very cheap!)"
    echo "2. Performance is limited but functional"
    echo "3. Perfect for learning and experimentation"
    echo "4. Run './scripts/cleanup-gke.sh' when done"
    echo ""
    print_warning "Don't forget to clean up when you're done experimenting!"
}

# Run main function
main "$@"
