# 🐳 Docker Installation von GitHub (Einfachste Methode)

## Schnelle Installation mit Docker

### 1. Server vorbereiten
```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose installieren
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Neuanmeldung für Docker-Gruppenmitgliedschaft
newgrp docker
```

### 2. Code vom GitHub klonen
```bash
# Projekt-Verzeichnis erstellen
mkdir -p ~/car-dealership
cd ~/car-dealership

# Repository klonen
git clone https://github.com/IHR-USERNAME/car-dealership-inventory.git .
```

### 3. Docker-Dateien erstellen

#### docker-compose.yml erstellen:
```bash
nano docker-compose.yml
```

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: car_dealership

  backend:
    build: ./backend
    restart: always
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=car_dealership
      - JWT_SECRET_KEY=ihr_sehr_sicherer_secret_key_123456789
      - CORS_ORIGINS=http://localhost:3000,http://ihre-domain.com
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    restart: always
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_BACKEND_URL=http://ihre-domain.com:8001
    volumes:
      - ./frontend:/app

volumes:
  mongodb_data:
```

#### Backend Dockerfile erstellen:
```bash
nano backend/Dockerfile
```

```dockerfile
FROM python:3.9-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App Code kopieren
COPY . .

# Port öffnen
EXPOSE 8001

# App starten
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

#### Frontend Dockerfile erstellen:
```bash
nano frontend/Dockerfile
```

```dockerfile
FROM node:18-alpine

# Arbeitsverzeichnis setzen
WORKDIR /app

# Package files kopieren
COPY package*.json ./

# Dependencies installieren
RUN npm install

# App Code kopieren
COPY . .

# Port öffnen
EXPOSE 3000

# App starten
CMD ["npm", "start"]
```

### 4. System starten
```bash
# Alle Services mit einem Befehl starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

### 5. System testen
- **Frontend**: http://ihre-domain.com:3000
- **Backend API**: http://ihre-domain.com:8001/api/docs
- **Login**: admin / admin123

### 6. Production Setup mit Nginx
```bash
nano docker-compose.prod.yml
```

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    restart: always
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: car_dealership

  backend:
    build: ./backend
    restart: always
    depends_on:
      - mongodb
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=car_dealership
      - JWT_SECRET_KEY=ihr_sehr_sicherer_secret_key_123456789
      - CORS_ORIGINS=https://ihre-domain.com

  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: always
    depends_on:
      - backend
    environment:
      - REACT_APP_BACKEND_URL=https://ihre-domain.com

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  mongodb_data:
```

### 7. Updates einspielen
```bash
# Code vom GitHub aktualisieren
git pull origin main

# Services neu starten
docker-compose down
docker-compose up -d --build

# Nur bestimmte Services neu starten
docker-compose restart backend frontend
```

### 8. Wartung
```bash
# Logs anzeigen
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb

# Container Status
docker-compose ps

# Services stoppen
docker-compose down

# Mit Volume löschen (ACHTUNG: Löscht alle Daten!)
docker-compose down -v
```

## ✅ Vorteile der Docker-Installation:

- ✅ **Ein-Befehl-Installation**: `docker-compose up -d`
- ✅ **Automatische Dependencies**: Alles wird automatisch installiert
- ✅ **Einfache Updates**: `git pull && docker-compose up -d --build`
- ✅ **Portable**: Läuft auf jedem Server mit Docker
- ✅ **Isoliert**: Keine Konflikte mit anderen Anwendungen
- ✅ **Backup-freundlich**: Volume-basierte Datenspeicherung

## 🎯 Empfehlung:
Die Docker-Installation ist die **einfachste und sicherste Methode** für die meisten Server-Setups!