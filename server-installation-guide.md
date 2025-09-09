# 🖥️ Server Installation von GitHub

## Schritt 1: Server vorbereiten

### System-Requirements (Ubuntu/Debian)
```bash
# System updaten
sudo apt update && sudo apt upgrade -y

# Git installieren
sudo apt install -y git

# Node.js 18+ installieren
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.8+ installieren
sudo apt install -y python3 python3-pip python3-venv

# MongoDB installieren
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# MongoDB starten und aktivieren
sudo systemctl start mongod
sudo systemctl enable mongod

# Nginx für Reverse Proxy (optional)
sudo apt install -y nginx
```

## Schritt 2: Code vom GitHub klonen

```bash
# In Ihr Projekt-Verzeichnis wechseln
cd /opt
sudo mkdir car-dealership
sudo chown $USER:$USER /opt/car-dealership
cd /opt/car-dealership

# Repository klonen
git clone https://github.com/IHR-USERNAME/car-dealership-inventory.git .

# Oder falls privates Repository:
git clone https://IHR-USERNAME:IHR-TOKEN@github.com/IHR-USERNAME/car-dealership-inventory.git .
```

## Schritt 3: Backend Setup

```bash
cd /opt/car-dealership/backend

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Environment Variables konfigurieren
cp .env.example .env 2>/dev/null || touch .env
nano .env
```

### Backend .env Datei konfigurieren:
```env
# MongoDB Konfiguration
MONGO_URL=mongodb://localhost:27017
DB_NAME=car_dealership

# JWT Secret (WICHTIG: Ändern Sie diesen Wert!)
JWT_SECRET_KEY=ihr_sehr_sicherer_secret_key_hier_123456789

# CORS Einstellungen
CORS_ORIGINS=http://localhost:3000,http://ihre-domain.com
```

## Schritt 4: Frontend Setup

```bash
cd /opt/car-dealership/frontend

# Dependencies installieren
npm install

# Environment Variables konfigurieren
cp .env.example .env 2>/dev/null || touch .env
nano .env
```

### Frontend .env Datei konfigurieren:
```env
# Backend URL (Anpassen an Ihre Domain/IP)
REACT_APP_BACKEND_URL=http://ihre-domain.com:8001

# Oder für lokale Installation:
# REACT_APP_BACKEND_URL=http://localhost:8001
```

## Schritt 5: System testen

### Backend starten:
```bash
cd /opt/car-dealership/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend starten (neues Terminal):
```bash
cd /opt/car-dealership/frontend
npm start
```

### System testen:
- Backend API: http://ihre-domain.com:8001/api/docs
- Frontend: http://ihre-domain.com:3000
- Login: admin / admin123

## Schritt 6: Production Setup mit Systemd

### Backend Service erstellen:
```bash
sudo nano /etc/systemd/system/car-dealership-backend.service
```

```ini
[Unit]
Description=Car Dealership Backend API
After=network.target mongodb.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/car-dealership/backend
Environment=PATH=/opt/car-dealership/backend/venv/bin
ExecStart=/opt/car-dealership/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Frontend Service erstellen:
```bash
sudo nano /etc/systemd/system/car-dealership-frontend.service
```

```ini
[Unit]
Description=Car Dealership Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/car-dealership/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=3
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

### Services aktivieren und starten:
```bash
# Systemd neu laden
sudo systemctl daemon-reload

# Services aktivieren
sudo systemctl enable car-dealership-backend
sudo systemctl enable car-dealership-frontend

# Services starten
sudo systemctl start car-dealership-backend
sudo systemctl start car-dealership-frontend

# Status prüfen
sudo systemctl status car-dealership-backend
sudo systemctl status car-dealership-frontend
```

## Schritt 7: Nginx Reverse Proxy (Empfohlen)

```bash
sudo nano /etc/nginx/sites-available/car-dealership
```

```nginx
server {
    listen 80;
    server_name ihre-domain.com;

    # Frontend (React)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Nginx Site aktivieren
sudo ln -s /etc/nginx/sites-available/car-dealership /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Schritt 8: SSL mit Let's Encrypt (Optional)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# SSL Zertifikat erstellen
sudo certbot --nginx -d ihre-domain.com

# Auto-Renewal testen
sudo certbot renew --dry-run
```

## 🎉 Fertig!

Ihr System ist nun verfügbar unter:
- **Frontend**: http://ihre-domain.com (oder https:// mit SSL)
- **Login**: admin / admin123
- **Backend API**: http://ihre-domain.com/api/docs

## 📋 Wartung und Updates

### Code Updates vom GitHub:
```bash
cd /opt/car-dealership
git pull origin main

# Backend Updates
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart car-dealership-backend

# Frontend Updates
cd ../frontend
npm install
sudo systemctl restart car-dealership-frontend
```

### Logs anzeigen:
```bash
# Backend Logs
sudo journalctl -u car-dealership-backend -f

# Frontend Logs
sudo journalctl -u car-dealership-frontend -f

# Nginx Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```