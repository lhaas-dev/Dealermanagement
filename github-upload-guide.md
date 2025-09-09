# 📁 Code auf GitHub hochladen

## 1. GitHub Repository erstellen
1. Gehen Sie zu https://github.com
2. Klicken Sie auf "New repository"
3. Repository Name: `car-dealership-inventory`
4. Beschreibung: `Fahrzeug-Inventarsystem mit Login und Foto-Verifizierung`
5. Wählen Sie "Private" (empfohlen) oder "Public"
6. Klicken Sie "Create repository"

## 2. Code auf GitHub hochladen

### Option A: Über GitHub Web Interface (Einfach)
1. Downloaden Sie das komplette Code-Paket
2. Entpacken Sie `car-dealership-system.tar.gz`
3. Gehen Sie zu Ihrem leeren GitHub Repository
4. Klicken Sie "uploading an existing file"
5. Ziehen Sie alle Ordner hinein (backend/, frontend/, README.md, etc.)
6. Commit message: "Initial upload - Car Dealership System"
7. Klicken Sie "Commit changes"

### Option B: Über Git Command Line (Erweitert)
```bash
# Code entpacken
tar -xzf car-dealership-system.tar.gz
cd car-dealership

# Git initialisieren
git init
git add .
git commit -m "Initial commit - Car Dealership Inventory System"

# Mit GitHub verbinden
git remote add origin https://github.com/IHR-USERNAME/car-dealership-inventory.git
git branch -M main
git push -u origin main
```

## 3. Repository-Struktur prüfen
Nach dem Upload sollten Sie diese Struktur sehen:
```
car-dealership-inventory/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env
├── README.md
└── deployment-docs/
```