# SentimentSense GKE Deployment Guide

## Overview

This document provides a comprehensive guide for deploying SentimentSense (a sentiment analysis ML service) to Google Kubernetes Engine (GKE), including troubleshooting steps and common interview questions.

## Prerequisites

### Required Tools
- Google Cloud SDK (`gcloud`)
- Docker
- kubectl
- GCP Project with billing enabled

### Required Services
- Google Kubernetes Engine API
- Container Registry API
- Compute Engine API

## Step-by-Step Deployment

### 1. Environment Setup

```bash
# Set project ID
export PROJECT_ID="sentiment-sense-demo"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create sentiment-sense-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --machine-type=e2-standard-4 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5

# Get credentials
gcloud container clusters get-credentials sentiment-sense-cluster \
    --zone=us-central1-a
```

### 3. Build and Push Docker Image

```bash
# Build image
docker build -t gcr.io/$PROJECT_ID/sentiment-sense:latest .

# Push to GCR
docker push gcr.io/$PROJECT_ID/sentiment-sense:latest
```

### 4. Deploy Application

#### 4.1 Create Namespace
```bash
kubectl apply -f k8s/app/namespace.yaml
```

#### 4.2 Deploy Configuration
```bash
kubectl apply -f k8s/app/configmap.yaml
kubectl apply -f k8s/app/secret.yaml
```

#### 4.3 Deploy Application
```bash
kubectl apply -f k8s/app/deployment.yaml
kubectl apply -f k8s/app/service.yaml
```

#### 4.4 Deploy Monitoring
```bash
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n sentiment-sense
kubectl get pods -n monitoring

# Check services
kubectl get svc -n sentiment-sense
kubectl get svc -n monitoring

# Test API
curl http://<EXTERNAL-IP>/health/simple
```

## Troubleshooting

### Common Issues

#### 1. OOMKilled (Out of Memory)
**Problem**: Pod crashes with OOMKilled status
**Solution**: Increase memory limits in deployment.yaml

```yaml
resources:
  requests:
    memory: 2Gi
  limits:
    memory: 4Gi
```

#### 2. CrashLoopBackOff
**Problem**: Pod keeps restarting
**Solution**: Check logs and increase startup probe timeout

```yaml
startupProbe:
  initialDelaySeconds: 30
  periodSeconds: 15
  timeoutSeconds: 10
  failureThreshold: 20  # 5 minutes total
```

#### 3. CreateContainerConfigError
**Problem**: Container cannot start due to config issues
**Solution**: Verify ConfigMap and Secret references

```bash
kubectl describe pod <pod-name> -n <namespace>
```

### Debugging Commands

```bash
# View pod logs
kubectl logs <pod-name> -n <namespace>
kubectl logs -f deployment/<deployment-name> -n <namespace>

# Describe resources
kubectl describe pod <pod-name> -n <namespace>
kubectl describe deployment <deployment-name> -n <namespace>

# Get events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Execute into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LoadBalancer  │    │   Prometheus    │    │    Grafana      │
│   (External)    │    │   (Monitoring)  │    │  (Dashboard)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ SentimentSense  │    │   ConfigMap     │    │     Secret      │
│   Deployment    │    │ (Configuration) │    │  (Credentials)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Performance Optimization

### Resource Management
- **CPU**: Start with 500m request, 2000m limit
- **Memory**: 2Gi request, 4Gi limit for HuggingFace models
- **Storage**: Use persistent volumes for model caching

### Scaling Strategies
```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sentiment-sense-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sentiment-sense
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Security Best Practices

### 1. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sentiment-sense-netpol
spec:
  podSelector:
    matchLabels:
      app: sentiment-sense
  policyTypes:
  - Ingress
  - Egress
```

### 2. RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: sentiment-sense-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

### 3. Pod Security Standards
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  capabilities:
    drop:
    - ALL

## Common Interview Questions

### Kubernetes Fundamentals

**Q1: What is the difference between Deployment and StatefulSet?**

**A**:
- **Deployment**: For stateless applications, pods are interchangeable
- **StatefulSet**: For stateful applications, maintains pod identity and order

**Q2: Explain the purpose of Services in Kubernetes**

**A**: Services provide stable network endpoints for pods:
- **ClusterIP**: Internal cluster communication
- **NodePort**: External access via node ports
- **LoadBalancer**: Cloud provider load balancer

**Q3: What are ConfigMaps and Secrets?**

**A**:
- **ConfigMap**: Store non-sensitive configuration data
- **Secret**: Store sensitive data (passwords, tokens)
- Both can be mounted as volumes or environment variables

### GKE Specific

**Q4: What are the advantages of using GKE over self-managed Kubernetes?**

**A**:
- **Managed control plane**
- **Automatic updates and patches**
- **Integration with GCP services**
- **Built-in monitoring and logging**
- **Auto-scaling capabilities**

**Q5: How does GKE handle node upgrades?**

**A**:
- **Rolling updates**: Nodes updated one by one
- **Surge upgrades**: Multiple nodes updated simultaneously
- **Blue-green**: Create new node pool, migrate workloads

### Troubleshooting

**Q6: How would you debug a pod that's in CrashLoopBackOff state?**

**A**:
1. Check pod logs: `kubectl logs <pod-name>`
2. Describe pod: `kubectl describe pod <pod-name>`
3. Check resource limits and requests
4. Verify configuration (ConfigMap, Secret)
5. Check startup/liveness/readiness probes

**Q7: What causes OOMKilled errors and how to fix them?**

**A**:
- **Cause**: Pod exceeds memory limits
- **Solutions**:
  - Increase memory limits
  - Optimize application memory usage
  - Use memory profiling tools

### ML/AI Deployment

**Q8: What are the challenges of deploying ML models in Kubernetes?**

**A**:
- **Large model sizes**: Slow startup times
- **Memory requirements**: High resource consumption
- **Model loading**: Network dependencies for downloads
- **GPU scheduling**: Resource allocation complexity

**Q9: How to handle model updates in production?**

**A**:
- **Blue-green deployment**: Switch traffic between versions
- **Canary deployment**: Gradual rollout
- **A/B testing**: Compare model performance
- **Model versioning**: Track and manage versions

### Monitoring and Observability

**Q10: What metrics should you monitor for ML services?**

**A**:
- **Infrastructure**: CPU, memory, disk usage
- **Application**: Request latency, throughput, error rate
- **ML-specific**: Model accuracy, prediction confidence
- **Business**: User satisfaction, conversion rates

## Cost Optimization

### Resource Management
- Use **Spot instances** for non-critical workloads
- Implement **cluster autoscaling**
- Set appropriate **resource requests and limits**
- Use **node pools** for different workload types

### Monitoring Costs
```bash
# Check resource usage
kubectl top nodes
kubectl top pods --all-namespaces

# GCP cost monitoring
gcloud billing budgets list
```

## Conclusion

This guide provides a comprehensive overview of deploying ML services on GKE, covering deployment steps, troubleshooting, and common interview questions. The key to successful deployment is understanding both Kubernetes fundamentals and ML-specific requirements.

## Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [ML on Kubernetes Best Practices](https://cloud.google.com/architecture/best-practices-for-ml-on-gke)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
```
