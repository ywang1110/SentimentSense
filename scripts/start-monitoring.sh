#!/bin/bash

# SentimentSense monitoring system startup script

set -e

echo "🚀 Starting SentimentSense with full monitoring stack..."

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Set permissions
chmod +x scripts/*.sh

# Build application image
echo "🔨 Building application image..."
docker compose -f docker-compose.monitoring.yml build

# Start monitoring stack
echo "🎯 Starting monitoring stack..."
docker compose -f docker-compose.monitoring.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "🔍 Checking service status..."
docker compose -f docker-compose.monitoring.yml ps

# Show access information
echo ""
echo "✅ Monitoring stack started successfully!"
echo ""
echo "📊 Access URLs:"
echo "  • SentimentSense API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Metrics: http://localhost:8000/metrics"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana: http://localhost:3000 (admin/admin123)"
echo "  • Loki: http://localhost:3100"
echo ""
echo "📝 Logs are stored in: ./logs/"
echo "📈 Metrics are collected every 15 seconds"
echo "🔔 Configure alerts by setting environment variables:"
echo "  • ALERT_EMAIL=your-email@example.com"
echo "  • ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/..."
echo ""
echo "🛑 To stop all services: docker compose -f docker-compose.monitoring.yml down"
