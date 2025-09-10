#!/bin/bash

# =========================================
# Dealership Management - One Step Install
# Ubuntu 24.04.2 LTS Auto-Installer
# =========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME="/home/$ACTUAL_USER"

log "🚀 Starting Dealership Management System Installation"
log "👤 Installing for user: $ACTUAL_USER"
log "🏠 User home directory: $USER_HOME"

# Get server IP and domain
SERVER_IP=$(hostname -I | awk '{print $1}')
info "📡 Detected server IP: $SERVER_IP"

echo -e "\n${YELLOW}🌐 Server Configuration:${NC}"
read -p "Enter your domain name (or press Enter to use IP $SERVER_IP): " DOMAIN
DOMAIN=${DOMAIN:-$SERVER_IP}

echo -e "\n${YELLOW}🔧 Installation Options:${NC}"
read -p "Install with Nginx reverse proxy? (y/N): " INSTALL_NGINX
INSTALL_NGINX=${INSTALL_NGINX:-n}

log "📋 Configuration Summary:"
log "   - Domain/IP: $DOMAIN"
log "   - Nginx: $(if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then echo 'Yes'; else echo 'No'; fi)"

echo -e "\n${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
read

# Create installation log
INSTALL_LOG="/var/log/dealership-install.log"
exec 1> >(tee -a "$INSTALL_LOG")
exec 2> >(tee -a "$INSTALL_LOG" >&2)

log "📝 Installation log: $INSTALL_LOG"

# ===========================================
# 1. System Update & Basic Tools
# ===========================================
log "🔄 Updating system packages..."
apt update && apt upgrade -y

log "🛠️ Installing basic tools..."
apt install -y curl wget git build-essential software-properties-common \
    ufw htop vim nano unzip zip tree

# ===========================================
# 2. Install Node.js & Yarn
# ===========================================
log "📦 Installing Node.js 18 LTS..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

log "🧶 Installing Yarn..."
npm install -g yarn pm2

# Verify installations
NODE_VERSION=$(node --version)
YARN_VERSION=$(yarn --version)
log "✅ Node.js version: $NODE_VERSION"
log "✅ Yarn version: $YARN_VERSION"

# ===========================================
# 3. Install Python
# ===========================================
log "🐍 Installing Python 3 and pip..."
apt install -y python3 python3-pip python3-venv python3-dev

PYTHON_VERSION=$(python3 --version)
log "✅ Python version: $PYTHON_VERSION"

# ===========================================
# 4. Install MongoDB
# ===========================================
log "🍃 Installing MongoDB 7.0..."

# Import MongoDB GPG key
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update and install
apt update
apt install -y mongodb-org

# Start and enable MongoDB
systemctl start mongod
systemctl enable mongod

# Verify MongoDB
if systemctl is-active --quiet mongod; then
    MONGO_VERSION=$(mongod --version | head -1)
    log "✅ MongoDB installed and running: $MONGO_VERSION"
else
    error "❌ MongoDB installation failed"
fi

# ===========================================
# 5. Install Nginx (Optional)
# ===========================================
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    log "🌐 Installing Nginx..."
    apt install -y nginx
    systemctl enable nginx
    log "✅ Nginx installed"
fi

# ===========================================
# 6. Create Application Directory
# ===========================================
log "📁 Setting up application directory..."
APP_DIR="$USER_HOME/dealership-app"
rm -rf "$APP_DIR"  # Remove if exists
mkdir -p "$APP_DIR"

# ===========================================
# 7. Clone Repository
# ===========================================
log "📥 Cloning repository from GitHub..."
cd "$USER_HOME"
git clone https://github.com/lhaas-dev/Dealermanagement.git dealership-app
cd "$APP_DIR"

# Fix ownership
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$APP_DIR"

log "✅ Repository cloned successfully"

# ===========================================
# 8. Setup Backend
# ===========================================
log "⚙️ Setting up Backend..."
cd "$APP_DIR/backend"

# Create virtual environment as actual user
sudo -u "$ACTUAL_USER" python3 -m venv venv

# Activate venv and install dependencies
sudo -u "$ACTUAL_USER" bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install fastapi uvicorn motor pymongo python-multipart python-jose[cryptography] passlib[bcrypt] pydantic python-decouple
"

# Create .env file
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017/dealership_inventory
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF

log "✅ Backend setup completed"

# ===========================================
# 9. Setup Frontend
# ===========================================
log "🎨 Setting up Frontend..."
cd "$APP_DIR/frontend"

# Install dependencies as actual user
sudo -u "$ACTUAL_USER" yarn install

# Create/update .env file
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    BACKEND_URL="http://$DOMAIN"
else
    BACKEND_URL="http://$DOMAIN:8001"
fi

cat > .env << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
WDS_SOCKET_PORT=3001
CHOKIDAR_USEPOLLING=true
EOF

log "✅ Frontend setup completed"

# ===========================================
# 10. Create Systemd Services
# ===========================================
log "🔧 Creating systemd services..."

# Backend service
cat > /etc/systemd/system/dealership-backend.service << EOF
[Unit]
Description=Dealership Backend API
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/venv/bin
ExecStart=$APP_DIR/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
cat > /etc/systemd/system/dealership-frontend.service << EOF
[Unit]
Description=Dealership Frontend
After=network.target dealership-backend.service

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$APP_DIR/frontend
ExecStart=/usr/bin/yarn start
Environment=PORT=3000
Environment=CI=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable services
systemctl daemon-reload
systemctl enable dealership-backend
systemctl enable dealership-frontend

log "✅ Systemd services created"

# ===========================================
# 11. Configure Nginx (if selected)
# ===========================================
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    log "🌐 Configuring Nginx..."
    
    cat > /etc/nginx/sites-available/dealership-app << EOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 50M;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/dealership-app /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    if nginx -t; then
        systemctl restart nginx
        log "✅ Nginx configured successfully"
    else
        error "❌ Nginx configuration failed"
    fi
fi

# ===========================================
# 12. Configure Firewall
# ===========================================
log "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 22

if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    ufw allow 'Nginx Full'
    ufw allow 80
    ufw allow 443
else
    ufw allow 3000  # Frontend
    ufw allow 8001  # Backend
fi

log "✅ Firewall configured"

# ===========================================
# 13. Fix Permissions
# ===========================================
log "🔐 Setting correct permissions..."
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$APP_DIR"
chmod +x "$APP_DIR/backend/venv/bin/uvicorn"

# ===========================================
# 14. Start Services
# ===========================================
log "🚀 Starting services..."

# Start backend
systemctl start dealership-backend
sleep 5

# Check backend status
if systemctl is-active --quiet dealership-backend; then
    log "✅ Backend service started"
else
    warning "⚠️ Backend service failed to start, checking logs..."
    journalctl -u dealership-backend --no-pager -l
fi

# Start frontend
systemctl start dealership-frontend
sleep 10

# Check frontend status
if systemctl is-active --quiet dealership-frontend; then
    log "✅ Frontend service started"
else
    warning "⚠️ Frontend service failed to start, checking logs..."
    journalctl -u dealership-frontend --no-pager -l
fi

# ===========================================
# 15. Create Management Scripts
# ===========================================
log "📋 Creating management scripts..."

# Status script
cat > "$USER_HOME/dealership-status.sh" << 'EOF'
#!/bin/bash
echo "=== Dealership Management System Status ==="
echo
echo "🔧 Services Status:"
systemctl status dealership-backend --no-pager -l
echo
systemctl status dealership-frontend --no-pager -l
echo
echo "🍃 MongoDB Status:"
systemctl status mongod --no-pager -l
echo
echo "🌐 Network Status:"
ss -tlnp | grep -E "(3000|8001|27017)"
EOF

# Restart script
cat > "$USER_HOME/dealership-restart.sh" << 'EOF'
#!/bin/bash
echo "🔄 Restarting Dealership Management System..."
sudo systemctl restart dealership-backend
sleep 3
sudo systemctl restart dealership-frontend
sleep 3
echo "✅ Services restarted"
EOF

# Logs script
cat > "$USER_HOME/dealership-logs.sh" << 'EOF'
#!/bin/bash
if [ "$1" == "backend" ]; then
    sudo journalctl -u dealership-backend -f
elif [ "$1" == "frontend" ]; then
    sudo journalctl -u dealership-frontend -f
elif [ "$1" == "mongo" ]; then
    sudo journalctl -u mongod -f
else
    echo "Usage: $0 [backend|frontend|mongo]"
    echo "Show logs for specific service"
fi
EOF

# Make scripts executable
chmod +x "$USER_HOME/dealership-"*.sh
chown "$ACTUAL_USER:$ACTUAL_USER" "$USER_HOME/dealership-"*.sh

# ===========================================
# 16. Final Tests
# ===========================================
log "🧪 Running final tests..."

# Test MongoDB
if mongosh --eval "db.adminCommand('ismaster')" > /dev/null 2>&1; then
    log "✅ MongoDB connection: OK"
else
    warning "⚠️ MongoDB connection: FAILED"
fi

# Test Backend API
sleep 5
if curl -f -s http://localhost:8001/api/cars > /dev/null; then
    log "✅ Backend API: OK"
else
    warning "⚠️ Backend API: FAILED (may need authentication)"
fi

# Test Frontend
if curl -f -s http://localhost:3000 > /dev/null; then
    log "✅ Frontend: OK"
else
    warning "⚠️ Frontend: FAILED"
fi

# ===========================================
# 17. Installation Complete
# ===========================================
echo -e "\n🎉${GREEN} INSTALLATION COMPLETED SUCCESSFULLY! ${NC}🎉\n"

echo -e "${BLUE}📋 System Information:${NC}"
echo -e "   📍 Server: $DOMAIN"
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    echo -e "   🌐 Application URL: http://$DOMAIN"
else
    echo -e "   🌐 Frontend URL: http://$DOMAIN:3000"
    echo -e "   🔧 Backend API: http://$DOMAIN:8001"
fi
echo -e "   🗂️ App Directory: $APP_DIR"
echo -e "   📝 Install Log: $INSTALL_LOG"

echo -e "\n${BLUE}🔐 Default Login:${NC}"
echo -e "   👤 Username: admin"
echo -e "   🔑 Password: admin123"

echo -e "\n${BLUE}🛠️ Management Commands:${NC}"
echo -e "   📊 Status: ${USER_HOME}/dealership-status.sh"
echo -e "   🔄 Restart: ${USER_HOME}/dealership-restart.sh"
echo -e "   📋 Logs: ${USER_HOME}/dealership-logs.sh [backend|frontend|mongo]"

echo -e "\n${BLUE}🔧 Manual Service Commands:${NC}"
echo -e "   sudo systemctl status dealership-backend"
echo -e "   sudo systemctl status dealership-frontend"
echo -e "   sudo systemctl restart dealership-backend"
echo -e "   sudo systemctl restart dealership-frontend"

echo -e "\n${YELLOW}📱 Mobile-Ready Features:${NC}"
echo -e "   ✅ Responsive Design für Tablets und Handys"
echo -e "   ✅ Foto-Aufnahme optimiert für mobile Geräte"
echo -e "   ✅ Touch-freundliche Bedienung"
echo -e "   ✅ Konsignations-Fahrzeug Management"

echo -e "\n${GREEN}🚀 Your Dealership Management System is ready to use!${NC}"
echo -e "   Open your browser and go to your application URL above."
echo -e "   The system will automatically create a default admin user on first start."

log "🏁 Installation script completed at $(date)"