# SentimentSense GKE Deployment Scripts

## 🚀 One-Click Deployment Scripts

This directory contains scripts for complete GKE deployment and cleanup of the SentimentSense application.

## 📋 Prerequisites

Before running the scripts, ensure you have:

1. **Google Cloud SDK** installed and configured
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Docker** installed
   ```bash
   # Install Docker
   # Visit: https://docs.docker.com/get-docker/
   ```

3. **GCP Project** with billing enabled
   ```bash
   # Create project (optional)
   gcloud projects create sentiment-sense-demo
   gcloud config set project sentiment-sense-demo
   ```

## 🎯 Quick Start

### 1. Complete Deployment (Creates everything)

```bash
# Make script executable
chmod +x scripts/deploy-gke-complete.sh

# Run deployment (will prompt for confirmation)
./scripts/deploy-gke-complete.sh
```

**What this script does:**
- ✅ Creates GKE cluster
- ✅ Builds and pushes Docker image
- ✅ Deploys SentimentSense application
- ✅ Deploys monitoring (Prometheus + Grafana)
- ✅ Configures external access
- ✅ Shows access URLs

**Estimated time:** 15-20 minutes
**Estimated cost:** ~$80-120/month (using preemptible nodes)

### 2. Complete Cleanup (Deletes everything)

```bash
# Make script executable
chmod +x scripts/cleanup-gke.sh

# Run cleanup (will prompt for confirmation)
./scripts/cleanup-gke.sh
```

**What this script does:**
- 🗑️ Deletes all Kubernetes resources
- 🗑️ Deletes GKE cluster
- 🗑️ Deletes container images
- 🗑️ Cleans up persistent disks
- 💰 Stops all billing

## ⚙️ Configuration

You can customize the deployment by setting environment variables:

```bash
# Set custom configuration
export PROJECT_ID="my-project-id"
export CLUSTER_NAME="my-cluster"
export ZONE="us-west1-a"
export MACHINE_TYPE="e2-standard-2"  # Smaller/cheaper
export NUM_NODES="1"                  # Fewer nodes

# Run deployment with custom config
./scripts/deploy-gke-complete.sh
```

## 📊 Cost Optimization Options

### Cost Comparison Table

| Configuration | Cluster Fee | Node Cost | LoadBalancer | Total/Month | Savings |
|---------------|-------------|-----------|--------------|-------------|---------|
| Regular (3x e2-standard-4) | $72 | $291 | $18 | ~$381 | 0% |
| **Preemptible (3x e2-standard-4)** | $72 | $58 | $18 | ~$148 | **61%** |
| Preemptible (1x e2-standard-2) | $72 | $10 | $18 | ~$100 | **74%** |
| Autopilot (pay-per-pod) | $0 | Variable | $18 | ~$50-150 | **60-87%** |

**✅ Current script uses: Preemptible nodes for maximum savings!**

### Option 1: Smaller Cluster
```bash
export MACHINE_TYPE="e2-standard-2"
export NUM_NODES="1"
./scripts/deploy-gke-complete.sh
```
**Savings:** ~50% reduction (~$200/month)

### Option 2: Preemptible Nodes (Already Enabled!)
The default script now uses preemptible nodes:
```bash
# Already configured in deploy-gke-complete.sh
--preemptible \
```
**Savings:** ~80% reduction (~$80-120/month)
**Note:** Nodes can be terminated by Google (usually recreated automatically)

### Option 3: Autopilot (Pay-per-pod)
```bash
# Create autopilot cluster instead
gcloud container clusters create-auto sentiment-sense-autopilot \
    --region=us-central1
```

## 🔍 Monitoring Deployment

### Check Status
```bash
# Check all pods
kubectl get pods --all-namespaces

# Check services
kubectl get svc --all-namespaces

# Check cluster info
kubectl cluster-info
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/sentiment-sense -n sentiment-sense

# Monitoring logs
kubectl logs -f deployment/grafana -n monitoring
```

### Access Services
```bash
# Get external IPs
kubectl get svc sentiment-sense-external -n sentiment-sense
kubectl get svc grafana-service -n monitoring

# Port forward for local access (alternative)
kubectl port-forward svc/sentiment-sense-service 8000:8000 -n sentiment-sense
```

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Enable required APIs
   gcloud services enable container.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

2. **Insufficient Quota**
   ```bash
   # Check quotas in GCP Console
   # Request quota increase if needed
   ```

3. **Image Build Fails**
   ```bash
   # Ensure you're in the project root directory
   # Check Dockerfile exists
   ls -la Dockerfile
   ```

4. **Pod CrashLoopBackOff**
   ```bash
   # Check pod logs
   kubectl describe pod <pod-name> -n sentiment-sense
   kubectl logs <pod-name> -n sentiment-sense
   ```

### Manual Cleanup
If scripts fail, manual cleanup:
```bash
# Delete cluster
gcloud container clusters delete sentiment-sense-cluster --zone=us-central1-a

# Delete images
gcloud container images list
gcloud container images delete <image-url>

# Check remaining resources
gcloud compute instances list
gcloud compute disks list
```

## 📁 Script Details

### `deploy-gke-complete.sh`
- **Purpose:** Complete deployment from scratch
- **Duration:** 15-20 minutes
- **Requirements:** Docker, gcloud, kubectl
- **Output:** Running GKE cluster with SentimentSense

### `cleanup-gke.sh`
- **Purpose:** Complete resource cleanup
- **Duration:** 5-10 minutes
- **Safety:** Multiple confirmation prompts
- **Output:** All resources deleted, billing stopped

### `../k8s/scripts/deploy-quick-start.sh`
- **Purpose:** Deploy to existing cluster only
- **Duration:** 5-10 minutes
- **Requirements:** Existing GKE cluster
- **Output:** Application deployed to cluster

## ⚠️ Preemptible Nodes Important Notes

**What are Preemptible Nodes?**
- Google can terminate them at any time (usually after 24 hours max)
- ~80% cheaper than regular instances
- Automatically recreated by GKE when terminated
- Perfect for development, testing, and fault-tolerant workloads

**Limitations:**
- Can be terminated with 30 seconds notice
- Not suitable for critical production workloads
- May cause temporary service interruptions
- No SLA guarantees

**Best Practices:**
- Use for development and testing environments
- Implement proper health checks and readiness probes
- Consider multiple replicas for availability
- Monitor for node terminations

## 🔐 Security Notes

- Scripts use default passwords (change in production)
- No HTTPS configured (add TLS for production)
- Basic RBAC (enhance for production)
- Public LoadBalancer (restrict access for production)

## 💡 Next Steps

After successful deployment:

1. **Test the API**
   ```bash
   curl http://<EXTERNAL-IP>/health/simple
   curl -X POST http://<EXTERNAL-IP>/analyze \
        -H "Content-Type: application/json" \
        -d '{"text": "I love this!"}'
   ```

2. **Access Grafana**
   - URL: `http://<GRAFANA-IP>:3000`
   - Login: `admin` / `admin123`

3. **Monitor Costs**
   - Check GCP Console > Billing
   - Set up budget alerts

4. **Production Hardening**
   - Add HTTPS/TLS
   - Configure proper authentication
   - Set up backup strategies
   - Implement CI/CD pipelines

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GCP Console for error messages
3. Check pod logs and events
4. Verify billing and quotas

Remember: **These scripts will incur GCP charges!** Always run cleanup when done testing.
