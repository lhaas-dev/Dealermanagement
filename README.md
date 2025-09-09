# 🚗 Car Dealership Inventory System

Ein vollständiges Fahrzeug-Inventarsystem mit Login-Authentifizierung und Foto-Verifizierung für Autohäuser.

## ✨ Features

- 🔐 **Benutzer-Authentifizierung** - JWT-basiertes Login-System
- 👥 **Rollen-Management** - Admin und normale Benutzer
- 📸 **Foto-Verifizierung** - Fahrzeug und VIN-Fotos für Anwesenheitsbestätigung
- 📊 **CSV Import** - Bulk-Import von Fahrzeugen mit BOM-Unterstützung
- 🔍 **Such- und Filterfunktionen** - Nach Marke, Modell, VIN oder Status
- 📱 **Responsive Design** - Funktioniert auf Desktop und Mobile
- 🇩🇪 **Deutsche Oberfläche** - Vollständig lokalisiert

## 🏗️ Technologie-Stack

- **Frontend**: React 19, Tailwind CSS, Shadcn/UI Components
- **Backend**: FastAPI (Python), JWT Authentication, Motor (MongoDB)
- **Datenbank**: MongoDB
- **Deployment**: Docker, Systemd Services, Nginx

## 🚀 Schnellstart mit Docker (Empfohlen)

### 1. Repository klonen
```bash
git clone https://github.com/IHR-USERNAME/car-dealership-inventory.git
cd car-dealership-inventory
```

### 2. Docker starten
```bash
docker-compose up -d
```

### 3. System öffnen
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api/docs
- **Login**: `admin` / `admin123`

## 👥 Standard-Anmeldedaten

- **Username**: `admin`
- **Passwort**: `admin123`

⚠️ **Wichtig**: Ändern Sie das Passwort nach dem ersten Login!

## 📋 Vollständige Installations-Anleitungen

Detaillierte Schritt-für-Schritt-Anleitungen finden Sie in den Dokumentations-Dateien:

- `github-upload-guide.md` - Code auf GitHub hochladen
- `server-installation-guide.md` - Manuelle Server-Installation  
- `docker-github-installation.md` - Docker-Installation (Empfohlen)

## 🔧 Konfiguration

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=car_dealership
JWT_SECRET_KEY=ihr_sehr_sicherer_secret_key
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 📸 Funktionen im Detail

### CSV Import
- Unterstützte Spalten: `make,model,year,price,vin,image_url`
- BOM-Unterstützung für Excel-generierte CSV-Dateien
- Duplicate-VIN-Erkennung
- Alle importierten Fahrzeuge sind standardmäßig "abwesend"

### Foto-Verifizierung
- Fahrzeug-Foto erforderlich
- VIN-Plaketten-Foto erforderlich
- Base64-Speicherung in MongoDB
- Anzeige der Verifizierungsfotos statt Stock-Bilder

### Benutzer-Management (nur Admin)
- Neue Benutzer erstellen
- Rollen zuweisen (Admin/Benutzer)
- Benutzer löschen
- Kein Selbst-Registrierung möglich
