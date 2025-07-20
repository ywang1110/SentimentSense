# SentimentSense Monitoring System

This document describes the complete monitoring and logging system for SentimentSense.

## 🏗️ Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │    Monitoring   │    │   Alerting      │
│                 │    │                 │    │                 │
│ • Structured    │───▶│ • Prometheus    │───▶│ • Email/Slack   │
│   Logging       │    │ • Grafana       │    │ • Webhooks      │
│ • Metrics       │    │ • Loki          │    │ • Custom Rules  │
│ • Health Checks │    │ • Promtail      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Component Roles and Responsibilities

### **Data Flow Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  SentimentSense │    │   Data Layer    │    │ Visualization   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Metrics   │─┼────┼▶│ Prometheus  │ │    │ │             │ │
│ │ /metrics    │ │    │ │(Time Series)│─┼────┼▶│   Grafana   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │(Dashboards) │ │
│                 │    │                 │    │ │             │ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │             │ │
│ │    Logs     │─┼────┼▶│    Loki     │ │    │ │             │ │
│ │JSON Format  │ │    │ │(Log Aggr.)  │─┼────┼▶│             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Prometheus - Metrics Collection & Storage

### **Role in SentimentSense**
Prometheus collects and stores time-series metrics from our application:

```python
# Application generates these metrics:
http_requests_total              # Total HTTP requests
http_request_duration_seconds    # Request response time
model_inference_total           # Model inference count
model_inference_duration_seconds # Inference duration
memory_usage_bytes              # Memory usage
cpu_usage_percent              # CPU utilization
errors_total                   # Error count
```

### **Monitoring Scope**
```bash
# API Performance Metrics
- Queries Per Second (QPS)
- Average response time
- P95/P99 response times
- HTTP status code distribution
- Error rates

# Business Metrics
- Sentiment analysis request volume
- POSITIVE vs NEGATIVE ratio
- Model inference time distribution
- Batch processing performance

# System Metrics
- CPU utilization
- Memory consumption
- Disk I/O
- Network traffic
```

### **Data Storage Format**
```
Time-series database:
timestamp=1642678800, http_requests_total{method="POST",endpoint="/analyze"}=1250
timestamp=1642678815, http_requests_total{method="POST",endpoint="/analyze"}=1267
timestamp=1642678830, model_inference_duration_seconds=0.045
```

## 📝 Loki - Log Aggregation & Querying

### **Role in SentimentSense**
Loki collects and stores structured logs from our application:

```json
{
  "timestamp": "2025-07-19T16:13:19Z",
  "level": "INFO",
  "service": "SentimentSense",
  "message": "Sentiment analysis completed",
  "request_id": "abc12345",
  "endpoint": "/analyze",
  "method": "POST",
  "sentiment": "POSITIVE",
  "confidence": 0.9848,
  "processing_time": 0.035,
  "text_length": 20
}
```

### **Log Query Capabilities**
```bash
# Troubleshooting
{service="sentiment-sense"} |= "ERROR"

# Performance Analysis
{service="sentiment-sense"} | json | processing_time > 1.0

# Request Tracing
{service="sentiment-sense"} | json | request_id="abc12345"

# Business Analysis
{service="sentiment-sense"} | json | sentiment="POSITIVE"
```

### **Structured vs Traditional Logs**
```
Traditional Logs:
2025-07-19 16:13:19 INFO - Sentiment analysis completed

Structured Logs (Loki):
✅ Queryable by fields
✅ Filterable and aggregatable
✅ Complex query syntax support
✅ Automated analysis friendly
```

## 📈 Grafana - Visualization & Alerting

### **Role in SentimentSense**

#### **1. Data Visualization**
Transforms Prometheus metrics and Loki logs into intuitive charts:

```
📊 API Performance Dashboard:
├── Real-time QPS curves
├── Response time heatmaps
├── Error rate trends
└── Status code distribution

🤖 Model Monitoring Dashboard:
├── Inference count bar charts
├── Sentiment analysis ratios
├── Inference time histograms
└── Model health indicators

💻 System Resources Dashboard:
├── CPU/Memory usage curves
├── Disk space utilization
├── Network I/O statistics
└── Container status monitoring
```

#### **2. Alert Management**
```yaml
Alert Rules Examples:
- Send Slack notification when API error rate > 5%
- Send email when P95 response time > 2s
- Send urgent alert when memory usage > 90%
- Notify dev team when model inference failure rate > 1%
```

## 🔄 Component Collaboration

### **Data Flow**
```
SentimentSense Application
    ↓ (generates metrics)
Prometheus ← (scrapes /metrics periodically)
    ↓ (stores time-series data)
Grafana ← (queries and visualizes)

SentimentSense Application
    ↓ (outputs JSON logs)
Promtail ← (collects log files)
    ↓ (pushes to)
Loki ← (stores and indexes logs)
    ↓ (queries)
Grafana ← (log queries and display)
```

### **Real-world Use Cases**

#### **Scenario 1: Daily Monitoring**
```
Operations team daily routine:
1. Open Grafana dashboards
2. Check overnight API call volume (Prometheus data)
3. Review error logs if any (Loki data)
4. Confirm system resource usage is normal
```

#### **Scenario 2: Incident Response**
```
Alert received:
1. Grafana shows response time spike (Prometheus alert)
2. Switch to Loki to query error logs for that timeframe
3. Trace specific failed requests using request_id
4. Identify root cause and fix the issue
```

#### **Scenario 3: Performance Optimization**
```
Product manager wants to understand user behavior:
1. Prometheus shows sentiment analysis call trends
2. Loki analyzes user input text length distribution
3. Combine data to optimize model performance
4. Verify optimization results through Grafana
```

## 🎯 Value Proposition in SentimentSense

### **Business Value**
```
📈 Performance Monitoring: Ensure API response time < 100ms
🎯 User Experience: Monitor sentiment analysis accuracy and speed
💰 Cost Control: Monitor resource usage, optimize deployment costs
🔍 Issue Resolution: Quickly locate and resolve production issues
```

### **Technical Value**
```
🚀 Observability: Complete visibility into system operations
🔧 Automated Operations: Automatic alerting and notifications
📊 Data-Driven Decisions: Make technical decisions based on real data
🛡️ Reliability: Proactive monitoring and alerting
```

### **Team Collaboration Value**
```
👨‍💻 Development Team: Debug issues quickly through logs
👨‍🔧 Operations Team: Monitor system health through metrics
👨‍💼 Product Team: Understand user usage patterns through data
👨‍💼 Management: Understand service quality through dashboards
```

These three components together form a complete observability platform, transforming SentimentSense from a "black box" service into a fully transparent, monitorable, and debuggable modern application! 🎯

## 🚀 Quick Start

### Start Complete Monitoring Stack
```bash
./scripts/start-monitoring.sh
```

### Manual Start
```bash
docker compose -f docker-compose.monitoring.yml up -d
```

## 📊 Monitoring Components

### 1. **Application Metrics** (Prometheus)
- **HTTP Request Metrics**: Request count, response time, status code distribution
- **Model Inference Metrics**: Inference time, inference count, sentiment distribution
- **System Metrics**: CPU, memory, disk utilization
- **Error Metrics**: Error count, error type distribution

### 2. **Structured Logging** (Loki + Promtail)
- **JSON Format Logs**: Easy to query and analyze
- **Request Tracing**: Each request has a unique ID
- **Performance Logs**: Record execution time of key operations
- **Error Logs**: Detailed error information and stack traces

### 3. **Health Checks** (Enhanced)
- **Model Status**: Check if model is properly loaded and working
- **System Resources**: Monitor memory and disk usage
- **Dependency Check**: Verify critical dependencies are available
- **Response Time**: Record response time of each component

### 4. **Alerting System**
- **Multi-channel Notifications**: Support email, Slack, etc.
- **Alert Levels**: INFO, WARNING, ERROR, CRITICAL
- **Alert Suppression**: Prevent alert storms
- **Auto Recovery Notifications**: Automatic notification when issues are resolved

## 🔧 Configuration

### Environment Variables
```bash
# Logging Configuration
LOG_LEVEL=INFO          # Log level
LOG_FORMAT=json         # Log format (json/text)
LOG_FILE=/app/logs/app.log  # Log file path

# Monitoring Configuration
ENABLE_METRICS=true     # Enable metrics collection
METRICS_PORT=9090       # Metrics port

# Alerting Configuration
ALERT_EMAIL=admin@example.com
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

### Alert Thresholds
- **Memory Usage**: >80% warning, >90% critical
- **Disk Usage**: >80% warning, >90% critical
- **Consecutive Health Check Failures**: >3 times critical alert
- **Response Time**: >5 seconds warning

## 📈 Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| SentimentSense API | http://localhost:8000 | Main service |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | Detailed health status |
| Metrics Endpoint | http://localhost:8000/metrics | Prometheus metrics |
| Prometheus | http://localhost:9090 | Metrics query and alerting |
| Grafana | http://localhost:3000 | Visualization dashboards |
| Loki | http://localhost:3100 | Log querying |

## 📝 Log Format

### Structured Log Example
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "app.main",
  "service": "SentimentSense",
  "version": "1.0.0",
  "message": "Sentiment analysis completed",
  "request_id": "abc12345",
  "endpoint": "/analyze",
  "method": "POST",
  "sentiment": "POSITIVE",
  "confidence": 0.9876,
  "processing_time": 0.045
}
```

## 🔍 Common Queries

### Prometheus Queries
```promql
# HTTP request rate
rate(http_requests_total[5m])

# Average response time
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Error rate
rate(errors_total[5m]) / rate(http_requests_total[5m])

# Memory usage in GB
memory_usage_bytes / (1024*1024*1024)
```

### Loki Queries
```logql
# View error logs
{service="sentiment-sense"} |= "ERROR"

# View logs for specific endpoint
{service="sentiment-sense"} | json | endpoint="/analyze"

# View requests with response time > 1 second
{service="sentiment-sense"} | json | response_time > 1.0
```

## 🛠️ Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   docker compose -f docker-compose.monitoring.yml logs sentiment-sense
   ```

2. **Metrics Not Showing**
   - Check `ENABLE_METRICS=true`
   - Verify Prometheus configuration
   - Check `/metrics` endpoint

3. **Logs Not Collected**
   - Check Promtail configuration
   - Verify log file paths
   - Confirm Loki connection

4. **Alerts Not Sending**
   - Verify alert configuration
   - Check network connectivity
   - Review alert history

### Performance Tuning

1. **Reduce Metrics Collection Frequency**
   ```yaml
   scrape_interval: 30s  # default 15s
   ```

2. **Adjust Log Level**
   ```bash
   LOG_LEVEL=WARNING  # reduce log volume
   ```

3. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G  # increase memory limit
   ```

## 🔒 Security Considerations

1. **Access Control**: Restrict monitoring endpoint access in production
2. **Sensitive Information**: Avoid logging sensitive data
3. **Network Isolation**: Use dedicated networks to isolate monitoring components
4. **Authentication**: Configure strong passwords for Grafana and other components

## 📚 Further Reading

- [Prometheus Official Documentation](https://prometheus.io/docs/)
- [Grafana Official Documentation](https://grafana.com/docs/)
- [Loki Official Documentation](https://grafana.com/docs/loki/)
- [FastAPI Monitoring Best Practices](https://fastapi.tiangolo.com/advanced/monitoring/)
