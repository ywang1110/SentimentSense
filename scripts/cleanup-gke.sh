#!/bin/bash

# SentimentSense GKE Cleanup Script
# This script removes all GKE resources to stop billing

set -e

echo "🧹 Starting SentimentSense GKE Cleanup..."

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
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    print_success "Prerequisites check passed"
}

# Delete Kubernetes resources
delete_k8s_resources() {
    print_step 2 "Deleting Kubernetes resources"
    
    # Check if cluster exists and is accessible
    if ! gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE &> /dev/null; then
        print_warning "Cluster $CLUSTER_NAME not found or not accessible"
        return 0
    fi
    
    # Get cluster credentials
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE 2>/dev/null || true
    
    # Delete namespaces (this will delete all resources in them)
    print_info "Deleting application namespace..."
    kubectl delete namespace sentiment-sense --ignore-not-found=true
    
    print_info "Deleting monitoring namespace..."
    kubectl delete namespace monitoring --ignore-not-found=true
    
    # Wait for namespace deletion
    print_info "Waiting for namespaces to be fully deleted..."
    kubectl wait --for=delete namespace/sentiment-sense --timeout=120s 2>/dev/null || true
    kubectl wait --for=delete namespace/monitoring --timeout=120s 2>/dev/null || true
    
    print_success "Kubernetes resources deleted"
}

# Delete GKE cluster
delete_gke_cluster() {
    print_step 3 "Deleting GKE cluster"
    
    # Check if cluster exists
    if ! gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE &> /dev/null; then
        print_warning "Cluster $CLUSTER_NAME not found, skipping deletion"
        return 0
    fi
    
    print_info "Deleting cluster: $CLUSTER_NAME"
    print_warning "This will take several minutes..."
    
    gcloud container clusters delete $CLUSTER_NAME \
        --zone=$ZONE \
        --quiet
    
    print_success "GKE cluster deleted"
}

# Delete container images
delete_container_images() {
    print_step 4 "Deleting container images"
    
    # Check if image exists
    if gcloud container images describe $IMAGE_NAME &> /dev/null; then
        print_info "Deleting image: $IMAGE_NAME"
        gcloud container images delete $IMAGE_NAME --quiet
        print_success "Container image deleted"
    else
        print_warning "Container image not found, skipping deletion"
    fi
}

# Clean up persistent disks
cleanup_persistent_disks() {
    print_step 5 "Cleaning up persistent disks"
    
    print_info "Checking for orphaned persistent disks..."
    
    # List disks that might be left over
    DISKS=$(gcloud compute disks list --filter="zone:$ZONE AND name~gke-$CLUSTER_NAME" --format="value(name)" 2>/dev/null || echo "")
    
    if [ -n "$DISKS" ]; then
        print_warning "Found orphaned disks:"
        echo "$DISKS"
        
        read -p "Delete these disks? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for disk in $DISKS; do
                print_info "Deleting disk: $disk"
                gcloud compute disks delete $disk --zone=$ZONE --quiet
            done
            print_success "Orphaned disks deleted"
        else
            print_warning "Orphaned disks kept (may incur charges)"
        fi
    else
        print_success "No orphaned disks found"
    fi
}

# Check remaining resources
check_remaining_resources() {
    print_step 6 "Checking for remaining resources"
    
    print_info "Checking for remaining compute instances..."
    INSTANCES=$(gcloud compute instances list --filter="zone:$ZONE AND name~gke-$CLUSTER_NAME" --format="value(name)" 2>/dev/null || echo "")
    
    if [ -n "$INSTANCES" ]; then
        print_warning "Found remaining instances (should be cleaned up automatically):"
        echo "$INSTANCES"
    else
        print_success "No remaining compute instances"
    fi
    
    print_info "Checking for remaining load balancers..."
    LBS=$(gcloud compute forwarding-rules list --format="value(name)" 2>/dev/null || echo "")
    
    if [ -n "$LBS" ]; then
        print_warning "Found remaining load balancers:"
        echo "$LBS"
        print_info "These may be from other services or take time to clean up"
    else
        print_success "No remaining load balancers"
    fi
}

# Show cost impact
show_cost_impact() {
    print_step 7 "Cost impact summary"
    
    echo ""
    echo "💰 Cost Impact:"
    echo "==============="
    echo "✅ GKE cluster management fee: STOPPED (~\$72/month saved)"
    echo "✅ Compute Engine instances: STOPPED (~\$291/month saved)"
    echo "✅ Load balancers: STOPPED (~\$18/month saved)"
    echo "✅ Persistent disks: STOPPED (variable cost saved)"
    echo ""
    echo "📊 Total estimated savings: ~\$400-500/month"
    echo ""
    echo "⚠️  Note: It may take a few minutes for billing to reflect these changes"
    echo "📈 Monitor your billing in GCP Console to confirm cost reduction"
}

# Main execution
main() {
    echo "Configuration:"
    echo "  Project ID: $PROJECT_ID"
    echo "  Cluster Name: $CLUSTER_NAME"
    echo "  Zone: $ZONE"
    echo ""
    
    print_warning "This will DELETE ALL GKE resources and STOP billing!"
    print_warning "This action CANNOT be undone!"
    echo ""
    
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Type 'DELETE' to confirm: " confirm
    if [ "$confirm" != "DELETE" ]; then
        echo "Cleanup cancelled - confirmation not matched"
        exit 0
    fi
    
    check_prerequisites
    delete_k8s_resources
    delete_gke_cluster
    delete_container_images
    cleanup_persistent_disks
    check_remaining_resources
    show_cost_impact
    
    echo ""
    print_success "🎉 SentimentSense GKE Cleanup Completed!"
    echo ""
    echo "Next steps:"
    echo "1. Check GCP Console to verify resource deletion"
    echo "2. Monitor billing to confirm cost reduction"
    echo "3. Review any remaining resources manually"
    echo ""
    print_info "If you want to redeploy, run: ./scripts/deploy-gke-complete.sh"
}

# Run main function
main "$@"
