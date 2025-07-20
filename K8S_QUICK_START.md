# SentimentSense Kubernetes Quick Start

This guide helps you quickly deploy SentimentSense to Kubernetes.

## 🚀 Quick Deployment (15 minutes)

### **Prerequisites Checklist**
```bash
✅ Kubernetes cluster running (local or cloud)
✅ kubectl configured and working
✅ Docker image built and pushed to registry
✅ Basic understanding of Kubernetes concepts
```

### **Step 1: Verify Cluster Access**
```bash
# Check cluster connection
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check available storage classes
kubectl get storageclass
```

### **Step 2: Choose Deployment Method**

#### **Option A: Minimal Deployment (Development)**
- Single replica
- No persistent storage
- Basic monitoring
- Local/minikube friendly

#### **Option B: Production Deployment**
- Multiple replicas
- Persistent storage
- Full monitoring stack
- Auto-scaling enabled

#### **Option C: Monitoring-First Deployment**
- Application + complete monitoring
- Grafana dashboards pre-configured
- Alerting enabled
- Production-ready

## 📦 What We'll Create

### **Minimal Deployment**
```
Namespaces:
├── sentiment-sense          # Application namespace
└── monitoring              # Basic monitoring

Resources:
├── Deployment (1 replica)
├── Service (ClusterIP)
├── ConfigMap (app config)
└── Basic Prometheus
```

### **Production Deployment**
```
Namespaces:
├── sentiment-sense          # Application namespace
├── monitoring              # Full monitoring stack
└── ingress-system          # Ingress controller

Resources:
├── Deployment (2-5 replicas with HPA)
├── Service + Ingress
├── ConfigMap + Secrets
├── PersistentVolumes
├── Prometheus + Grafana + Loki
└── SSL certificates
```

## 🛠️ Required Information

### **Before Starting, Gather:**

#### **1. Container Image**
```bash
# Where is your image?
REGISTRY=gcr.io/your-project        # or docker.io/username
IMAGE_NAME=sentiment-sense
IMAGE_TAG=latest

# Full image path
IMAGE_PATH=${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
```

#### **2. Domain Names (Production)**
```bash
# What domains will you use?
APP_DOMAIN=sentiment-sense.yourdomain.com
GRAFANA_DOMAIN=grafana.yourdomain.com
PROMETHEUS_DOMAIN=prometheus.yourdomain.com  # optional
```

#### **3. Resource Requirements**
```bash
# How much resources do you need?
MIN_REPLICAS=2
MAX_REPLICAS=5
CPU_REQUEST=500m
MEMORY_REQUEST=1Gi
CPU_LIMIT=2000m
MEMORY_LIMIT=2Gi
```

#### **4. Storage Requirements**
```bash
# Do you need persistent storage?
MODEL_CACHE_SIZE=10Gi          # For HuggingFace models
PROMETHEUS_STORAGE=50Gi        # For metrics data
GRAFANA_STORAGE=10Gi          # For dashboards
LOKI_STORAGE=100Gi            # For logs
```

#### **5. Monitoring Configuration**
```bash
# Alerting setup
ALERT_EMAIL=admin@yourdomain.com
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Grafana admin
GRAFANA_ADMIN_PASSWORD=your-secure-password
```

## 📋 Deployment Checklist

### **Pre-deployment**
- [ ] Kubernetes cluster is running and accessible
- [ ] kubectl is configured correctly
- [ ] Container image is built and pushed
- [ ] Domain names are configured (if using ingress)
- [ ] SSL certificates are ready (if using HTTPS)

### **Application Deployment**
- [ ] Create namespace
- [ ] Deploy ConfigMap with application settings
- [ ] Deploy Secret with sensitive data
- [ ] Deploy application Deployment
- [ ] Create Service for internal access
- [ ] Configure Ingress for external access (optional)
- [ ] Set up HPA for auto-scaling (optional)

### **Monitoring Deployment**
- [ ] Create monitoring namespace
- [ ] Deploy Prometheus for metrics
- [ ] Deploy Grafana for visualization
- [ ] Deploy Loki for logs (optional)
- [ ] Configure service discovery
- [ ] Import Grafana dashboards
- [ ] Set up alerting rules

### **Post-deployment**
- [ ] Test application endpoints
- [ ] Verify monitoring is collecting data
- [ ] Test auto-scaling (if enabled)
- [ ] Configure backup strategies
- [ ] Set up CI/CD integration

## 🎯 Deployment Strategies

### **Strategy 1: Start Simple**
```bash
1. Deploy minimal application first
2. Verify it works
3. Add monitoring gradually
4. Scale up as needed
```

### **Strategy 2: All-in-One**
```bash
1. Deploy everything at once
2. Use provided manifests
3. Configure after deployment
4. Good for experienced users
```

### **Strategy 3: Monitoring First**
```bash
1. Set up monitoring stack
2. Deploy application with monitoring
3. Immediate visibility
4. Best for production
```

## 🔧 Configuration Templates

### **Environment Variables Template**
```bash
# Copy and customize these values
export NAMESPACE=sentiment-sense
export IMAGE_REGISTRY=gcr.io/your-project
export IMAGE_TAG=latest
export APP_DOMAIN=sentiment-sense.example.com
export GRAFANA_DOMAIN=grafana.example.com
export ALERT_EMAIL=admin@example.com
export GRAFANA_PASSWORD=change-me-please
```

### **Resource Limits Template**
```yaml
# Customize based on your needs
resources:
  requests:
    cpu: 500m      # Minimum CPU
    memory: 1Gi    # Minimum memory
  limits:
    cpu: 2000m     # Maximum CPU
    memory: 2Gi    # Maximum memory
```

## 📊 Monitoring Setup

### **What You'll Get**
```bash
Prometheus Metrics:
├── HTTP request rates and latencies
├── Model inference metrics
├── System resource usage
├── Error rates and counts
└── Custom business metrics

Grafana Dashboards:
├── API Performance Overview
├── Model Performance Metrics
├── System Resource Usage
├── Error Analysis
└── Business Intelligence

Loki Logs:
├── Structured JSON logs
├── Request tracing
├── Error investigation
└── Performance analysis
```

### **Default Dashboards**
- **API Performance**: Request rates, response times, error rates
- **Model Metrics**: Inference times, sentiment distribution
- **System Health**: CPU, memory, disk usage
- **Alerts Overview**: Active alerts and history

## 🚨 Common Issues & Solutions

### **Image Pull Issues**
```bash
# Problem: ImagePullBackOff
# Solution: Check image path and registry access
kubectl describe pod <pod-name>
```

### **Resource Issues**
```bash
# Problem: Pods pending due to insufficient resources
# Solution: Check node capacity
kubectl describe nodes
kubectl top nodes
```

### **Networking Issues**
```bash
# Problem: Service not accessible
# Solution: Check service and endpoints
kubectl get svc
kubectl get endpoints
```

### **Storage Issues**
```bash
# Problem: PVC pending
# Solution: Check storage class and availability
kubectl get pvc
kubectl get storageclass
```

## 📝 Next Steps

### **Choose Your Path:**

1. **🏃‍♂️ Quick Start**: "I want to deploy now"
   → Go to minimal deployment manifests

2. **🏗️ Production Ready**: "I need a robust setup"
   → Go to production deployment manifests

3. **📊 Monitoring Focus**: "I want full observability"
   → Go to monitoring-first deployment

4. **🎓 Learning Mode**: "I want to understand each step"
   → Go to step-by-step tutorial

**Ready to proceed?** Let me know which path you'd like to take, and I'll create the specific Kubernetes manifests for your chosen deployment strategy!
