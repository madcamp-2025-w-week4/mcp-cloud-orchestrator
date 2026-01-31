#!/bin/bash
# =============================================================================
# MCP Cloud Orchestrator - Production Deployment Script
# =============================================================================
# 설명: Nginx + Tailscale Funnel을 통한 프로덕션 배포
# 실행: chmod +x deploy.sh && sudo ./deploy.sh
# =============================================================================

set -e

echo "=============================================="
echo "🚀 KWS (KAIST Web Service) Deployment"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (sudo ./deploy.sh)"
    exit 1
fi

# Install Nginx if not present
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    apt-get update
    apt-get install -y nginx
fi

# Deploy Nginx configuration
echo "📝 Deploying Nginx configuration..."
cp nginx.conf /etc/nginx/sites-available/mcp-orchestrator
ln -sf /etc/nginx/sites-available/mcp-orchestrator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
echo "🔍 Testing Nginx configuration..."
nginx -t

echo "🔄 Reloading Nginx..."
systemctl reload nginx
systemctl enable nginx

# Start Tailscale Funnel
echo "🌐 Starting Tailscale Funnel on port 80..."
echo "   Public URL: https://kws.p-e.kr/"

# Note: Funnel needs to be run separately as it's interactive
echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "📌 Next Steps:"
echo "   1. Start Backend:  cd backend && source venv/bin/activate && python main.py"
echo "   2. Start Frontend: cd frontend && npm run dev"
echo "   3. Start Funnel:   sudo tailscale funnel 80"
echo ""
echo "🌐 Access URL: https://kws.p-e.kr/"
echo "📚 API Docs:   https://kws.p-e.kr/api/docs"
echo ""
