# SentimentSense Kubernetes Quick Start

This directory contains Kubernetes manifests for deploying SentimentSense with basic monitoring.

## 🚀 Quick Deployment (5 minutes)

### Prerequisites
- Kubernetes cluster running (minikube, kind, GKE, EKS, etc.)
- kubectl configured and connected
- Docker image built (see instructions below)

### Step 1: Prepare Docker Image

#### For Local Clusters (minikube/kind):
```bash
# Build image locally
docker build -t sentiment-sense:latest .

# For minikube, load image
minikube image load sentiment-sense:latest

# For kind, load image
kind load docker-image sentiment-sense:latest
```

#### For Cloud Clusters:
```bash
# Tag and push to your registry
docker tag sentiment-sense:latest gcr.io/your-project/sentiment-sense:latest
docker push gcr.io/your-project/sentiment-sense:latest

# Update image in k8s/app/deployment.yaml
# Change: image: sentiment-sense:latest
# To: image: gcr.io/your-project/sentiment-sense:latest
```

### Step 2: Deploy Everything
```bash
cd k8s/scripts
chmod +x deploy-quick-start.sh
./deploy-quick-start.sh
```

### Step 3: Access Services

#### Get External IPs:
```bash
# Check services
kubectl get svc -n sentiment-sense
kubectl get svc -n monitoring

# For LoadBalancer services, wait for EXTERNAL-IP
kubectl get svc -w
```

#### Access URLs:
- **SentimentSense API**: `http://<EXTERNAL-IP>:80`
- **Prometheus**: `http://<PROMETHEUS-IP>:9090`
- **Grafana**: `http://<GRAFANA-IP>:3000` (admin/admin123)

## 📁 File Structure

```
k8s/
├── app/
│   ├── namespace.yaml          # Application namespace
│   ├── configmap.yaml         # App configuration
│   ├── secret.yaml            # Sensitive data
│   ├── deployment.yaml        # Main application
│   └── service.yaml           # Service exposure
├── monitoring/
│   ├── prometheus.yaml        # Metrics collection
│   └── grafana.yaml          # Visualization
└── scripts/
    ├── deploy-quick-start.sh  # Deployment script
    └── cleanup.sh             # Cleanup script
```

## 🔧 Configuration

### Customize Application Settings
Edit `k8s/app/configmap.yaml`:
```yaml
data:
  LOG_LEVEL: "DEBUG"           # Change log level
  MODEL_NAME: "your-model"     # Use different model
  BATCH_SIZE_LIMIT: "20"       # Increase batch size
```

### Customize Resources
Edit `k8s/app/deployment.yaml`:
```yaml
resources:
  requests:
    cpu: 500m                  # Increase CPU request
    memory: 1Gi               # Increase memory request
  limits:
    cpu: 2000m                # Increase CPU limit
    memory: 2Gi               # Increase memory limit
```

### Update Secrets
Edit `k8s/app/secret.yaml`:
```bash
# Encode your values
echo -n "your-email@domain.com" | base64
echo -n "your-grafana-password" | base64

# Update the base64 values in secret.yaml
```

## 🔍 Monitoring & Debugging

### Check Pod Status
```bash
# Application pods
kubectl get pods -n sentiment-sense

# Monitoring pods
kubectl get pods -n monitoring

# Detailed pod info
kubectl describe pod <pod-name> -n sentiment-sense
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/sentiment-sense -n sentiment-sense

# Prometheus logs
kubectl logs -f deployment/prometheus -n monitoring

# Grafana logs
kubectl logs -f deployment/grafana -n monitoring
```

### Test API
```bash
# Get service IP
SENTIMENT_IP=$(kubectl get svc sentiment-sense-external -n sentiment-sense -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl http://$SENTIMENT_IP/health

# Test sentiment analysis
curl -X POST http://$SENTIMENT_IP/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!"}'
```

## 📊 Monitoring Access

### Prometheus
- URL: `http://<prometheus-ip>:9090`
- Query examples:
  ```promql
  # Request rate
  rate(http_requests_total[5m])
  
  # Memory usage
  memory_usage_bytes / (1024*1024*1024)
  ```

### Grafana
- URL: `http://<grafana-ip>:3000`
- Login: admin / admin123
- Data source: Prometheus (pre-configured)

## 🧹 Cleanup

### Remove Everything
```bash
cd k8s/scripts
./cleanup.sh
```

### Manual Cleanup
```bash
# Delete namespaces (removes everything)
kubectl delete namespace sentiment-sense
kubectl delete namespace monitoring
```

## 🚨 Troubleshooting

### Common Issues

#### 1. ImagePullBackOff
```bash
# Check image name and availability
kubectl describe pod <pod-name> -n sentiment-sense

# For local clusters, ensure image is loaded
minikube image ls | grep sentiment-sense
```

#### 2. Pods Pending
```bash
# Check node resources
kubectl describe nodes
kubectl top nodes

# Check events
kubectl get events -n sentiment-sense --sort-by='.lastTimestamp'
```

#### 3. Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n sentiment-sense

# Check if LoadBalancer is supported
kubectl get svc sentiment-sense-external -n sentiment-sense
```

#### 4. Model Loading Slow
```bash
# Increase startup probe timeout in deployment.yaml
startupProbe:
  failureThreshold: 20  # Allow more time
  
# Check logs for model download progress
kubectl logs -f deployment/sentiment-sense -n sentiment-sense
```

## 🔄 Updates

### Update Application
```bash
# Build new image
docker build -t sentiment-sense:v2 .

# Update deployment
kubectl set image deployment/sentiment-sense sentiment-sense=sentiment-sense:v2 -n sentiment-sense

# Check rollout status
kubectl rollout status deployment/sentiment-sense -n sentiment-sense
```

### Scale Application
```bash
# Scale to 3 replicas
kubectl scale deployment sentiment-sense --replicas=3 -n sentiment-sense

# Check scaling
kubectl get pods -n sentiment-sense
```

## 📚 Next Steps

1. **Add Ingress**: Set up ingress controller for domain-based routing
2. **Add HPA**: Implement horizontal pod autoscaling
3. **Add Persistence**: Use PVCs for model cache persistence
4. **Add Security**: Implement RBAC and network policies
5. **Add CI/CD**: Set up automated deployments

For production deployment, see the full deployment guide in the parent directory.
