# SentimentSense Kubernetes Quick Start
# SentimentSense Kubernetes 快速开始

This directory contains Kubernetes manifests for deploying SentimentSense with basic monitoring.

本目录包含用于部署 SentimentSense 及基础监控的 Kubernetes 配置文件。

## 🚀 Quick Deployment (5 minutes) | 快速部署（5分钟）

### Prerequisites | 前置条件
- Kubernetes cluster running (minikube, kind, GKE, EKS, etc.) | Kubernetes 集群运行中（minikube、kind、GKE、EKS 等）
- kubectl configured and connected | kubectl 已配置并连接
- Docker image built (see instructions below) | Docker 镜像已构建（见下方说明）

### Step 1: Prepare Docker Image | 步骤1：准备 Docker 镜像

#### For Local Clusters (minikube/kind) | 本地集群（minikube/kind）:
```bash
# Build image locally | 本地构建镜像
docker build -t sentiment-sense:latest .

# For minikube, load image | minikube 加载镜像
minikube image load sentiment-sense:latest

# For kind, load image | kind 加载镜像
kind load docker-image sentiment-sense:latest
```

#### For Cloud Clusters | 云集群:
```bash
# Tag and push to your registry | 标记并推送到您的注册表
docker tag sentiment-sense:latest gcr.io/your-project/sentiment-sense:latest
docker push gcr.io/your-project/sentiment-sense:latest

# Update image in k8s/app/deployment.yaml | 更新 k8s/app/deployment.yaml 中的镜像
# Change | 修改: image: sentiment-sense:latest
# To | 改为: image: gcr.io/your-project/sentiment-sense:latest
```

### Step 2: Deploy Everything | 步骤2：部署所有组件
```bash
cd k8s/scripts
chmod +x deploy-quick-start.sh
./deploy-quick-start.sh
```

### Step 3: Access Services | 步骤3：访问服务

#### Get External IPs | 获取外部 IP:
```bash
# Check services | 检查服务
kubectl get svc -n sentiment-sense
kubectl get svc -n monitoring

# For LoadBalancer services, wait for EXTERNAL-IP | LoadBalancer 服务等待外部 IP
kubectl get svc -w
```

#### Access URLs | 访问地址:
- **SentimentSense API | API 服务**: `http://<EXTERNAL-IP>:80`
- **Prometheus | 指标监控**: `http://<PROMETHEUS-IP>:9090`
- **Grafana | 可视化面板**: `http://<GRAFANA-IP>:3000` (admin/admin123)

## 📁 File Structure | 文件结构

```
k8s/
├── app/                        # 应用配置
│   ├── namespace.yaml          # Application namespace | 应用命名空间
│   ├── configmap.yaml         # App configuration | 应用配置
│   ├── secret.yaml            # Sensitive data | 敏感数据
│   ├── deployment.yaml        # Main application | 主应用部署
│   └── service.yaml           # Service exposure | 服务暴露
├── monitoring/                 # 监控配置
│   ├── prometheus.yaml        # Metrics collection | 指标收集
│   └── grafana.yaml          # Visualization | 可视化
└── scripts/                   # 脚本
    ├── deploy-quick-start.sh  # Deployment script | 部署脚本
    └── cleanup.sh             # Cleanup script | 清理脚本
```

## 🔧 Configuration | 配置

### Customize Application Settings | 自定义应用设置
Edit `k8s/app/configmap.yaml` | 编辑 `k8s/app/configmap.yaml`:
```yaml
data:
  LOG_LEVEL: "DEBUG"           # Change log level | 修改日志级别
  MODEL_NAME: "your-model"     # Use different model | 使用不同模型
  BATCH_SIZE_LIMIT: "20"       # Increase batch size | 增加批处理大小
```

### Customize Resources | 自定义资源
Edit `k8s/app/deployment.yaml` | 编辑 `k8s/app/deployment.yaml`:
```yaml
resources:
  requests:
    cpu: 500m                  # Increase CPU request | 增加 CPU 请求
    memory: 1Gi               # Increase memory request | 增加内存请求
  limits:
    cpu: 2000m                # Increase CPU limit | 增加 CPU 限制
    memory: 2Gi               # Increase memory limit | 增加内存限制
```

### Update Secrets | 更新密钥
Edit `k8s/app/secret.yaml` | 编辑 `k8s/app/secret.yaml`:
```bash
# Encode your values | 编码您的值
echo -n "your-email@domain.com" | base64
echo -n "your-grafana-password" | base64

# Update the base64 values in secret.yaml | 更新 secret.yaml 中的 base64 值
```

## 🔍 Monitoring & Debugging | 监控和调试

### Check Pod Status | 检查 Pod 状态
```bash
# Application pods | 应用 Pod
kubectl get pods -n sentiment-sense

# Monitoring pods | 监控 Pod
kubectl get pods -n monitoring

# Detailed pod info | 详细 Pod 信息
kubectl describe pod <pod-name> -n sentiment-sense
```

### View Logs | 查看日志
```bash
# Application logs | 应用日志
kubectl logs -f deployment/sentiment-sense -n sentiment-sense

# Prometheus logs | Prometheus 日志
kubectl logs -f deployment/prometheus -n monitoring

# Grafana logs | Grafana 日志
kubectl logs -f deployment/grafana -n monitoring
```

### Test API | 测试 API
```bash
# Get service IP | 获取服务 IP
SENTIMENT_IP=$(kubectl get svc sentiment-sense-external -n sentiment-sense -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint | 测试健康检查端点
curl http://$SENTIMENT_IP/health

# Test sentiment analysis | 测试情感分析
curl -X POST http://$SENTIMENT_IP/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!"}'
```

## 📊 Monitoring Access | 监控访问

### Prometheus | 指标监控
- URL: `http://<prometheus-ip>:9090`
- Query examples | 查询示例:
  ```promql
  # Request rate | 请求速率
  rate(http_requests_total[5m])

  # Memory usage | 内存使用
  memory_usage_bytes / (1024*1024*1024)
  ```

### Grafana | 可视化面板
- URL: `http://<grafana-ip>:3000`
- Login | 登录: admin / admin123
- Data source | 数据源: Prometheus (pre-configured | 预配置)

## 🧹 Cleanup | 清理

### Remove Everything | 删除所有资源
```bash
cd k8s/scripts
./cleanup.sh
```

### Manual Cleanup | 手动清理
```bash
# Delete namespaces (removes everything) | 删除命名空间（删除所有内容）
kubectl delete namespace sentiment-sense
kubectl delete namespace monitoring
```

## 🚨 Troubleshooting | 故障排查

### Common Issues | 常见问题

#### 1. ImagePullBackOff | 镜像拉取失败
```bash
# Check image name and availability | 检查镜像名称和可用性
kubectl describe pod <pod-name> -n sentiment-sense

# For local clusters, ensure image is loaded | 本地集群确保镜像已加载
minikube image ls | grep sentiment-sense
```

#### 2. Pods Pending | Pod 挂起
```bash
# Check node resources | 检查节点资源
kubectl describe nodes
kubectl top nodes

# Check events | 检查事件
kubectl get events -n sentiment-sense --sort-by='.lastTimestamp'
```

#### 3. Service Not Accessible | 服务无法访问
```bash
# Check service endpoints | 检查服务端点
kubectl get endpoints -n sentiment-sense

# Check if LoadBalancer is supported | 检查是否支持 LoadBalancer
kubectl get svc sentiment-sense-external -n sentiment-sense
```

#### 4. Model Loading Slow | 模型加载缓慢
```bash
# Increase startup probe timeout in deployment.yaml | 增加启动探针超时时间
startupProbe:
  failureThreshold: 20  # Allow more time | 允许更多时间

# Check logs for model download progress | 检查模型下载进度日志
kubectl logs -f deployment/sentiment-sense -n sentiment-sense
```

## 🔄 Updates | 更新

### Update Application | 更新应用
```bash
# Build new image | 构建新镜像
docker build -t sentiment-sense:v2 .

# Update deployment | 更新部署
kubectl set image deployment/sentiment-sense sentiment-sense=sentiment-sense:v2 -n sentiment-sense

# Check rollout status | 检查滚动更新状态
kubectl rollout status deployment/sentiment-sense -n sentiment-sense
```

### Scale Application | 扩缩应用
```bash
# Scale to 3 replicas | 扩展到 3 个副本
kubectl scale deployment sentiment-sense --replicas=3 -n sentiment-sense

# Check scaling | 检查扩缩状态
kubectl get pods -n sentiment-sense
```

## 📚 Next Steps | 下一步

1. **Add Ingress | 添加 Ingress**: Set up ingress controller for domain-based routing | 设置 Ingress 控制器进行基于域名的路由
2. **Add HPA | 添加 HPA**: Implement horizontal pod autoscaling | 实现水平 Pod 自动扩缩
3. **Add Persistence | 添加持久化**: Use PVCs for model cache persistence | 使用 PVC 进行模型缓存持久化
4. **Add Security | 添加安全**: Implement RBAC and network policies | 实现 RBAC 和网络策略
5. **Add CI/CD | 添加 CI/CD**: Set up automated deployments | 设置自动化部署

For production deployment, see the full deployment guide in the parent directory.
生产部署请参考父目录中的完整部署指南。
