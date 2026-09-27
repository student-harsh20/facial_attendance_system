# 🚀 Deployment Guide - Smart Facial Attendance System

This guide provides complete, step-by-step instructions for deploying the **Smart Facial Attendance System** to cloud platforms, Docker containers, virtual private servers (VPS), or local campus networks.

---

## 📋 Table of Contents
1. [Important: Webcam & HTTPS Security Requirement](#-important-webcam--https-security-requirement)
2. [Deployment Option 1: Free Cloud Deployment on Render.com (Recommended)](#-option-1-free-cloud-deployment-on-rendercom-recommended)
3. [Deployment Option 2: 1-Command Docker Deployment (Universal)](#-option-2-1-command-docker-deployment-universal)
4. [Deployment Option 3: Railway / Fly.io Cloud Platforms](#-option-3-railway--flyio-cloud-platforms)
5. [Deployment Option 4: Linux VPS (Ubuntu / Debian on AWS EC2, DigitalOcean) with Nginx + SSL](#-option-4-linux-vps-ubuntu--debian-on-aws-ec2-digitalocean-with-nginx--ssl)
6. [Deployment Option 5: Campus Gate / Local Intranet Deployment](#-option-5-campus-gate--local-intranet-deployment)
7. [Post-Deployment Security & Administration Checklist](#-post-deployment-security--administration-checklist)

---

## 🔒 Important: Webcam & HTTPS Security Requirement

Modern web browsers (Google Chrome, Mozilla Firefox, Safari, Microsoft Edge) enforce strict security policies regarding camera hardware access:

> **Webcam access (`navigator.mediaDevices.getUserMedia`) is ONLY permitted on:**
> 1. `localhost` / `127.0.0.1` (during local development and testing)
> 2. **HTTPS** origins (e.g., `https://your-app.onrender.com` or `https://attendance.yourcollege.edu`)

**Key Rule:** If you deploy to a remote server without SSL over plain HTTP (e.g., `http://54.120.30.40:8000`), the browser will block the webcam gate camera. **Always use HTTPS for remote deployments** (provided automatically on Render, Railway, Cloud Run, or via Let's Encrypt Certbot on VPS).

---

## 🌐 Option 1: Free Cloud Deployment on Render.com (Recommended)

Render provides free hosting with **automatic free HTTPS certificates**, making it the easiest way to deploy this project in under 5 minutes.

### Step-by-Step Instructions:

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit for facial attendance system"
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Log into Render:**
   - Go to [render.com](https://render.com) and sign in with your GitHub account.

3. **Create a New Web Service:**
   - Click the **"New +"** button in the dashboard &rarr; Select **"Web Service"**.
   - Connect your GitHub repository.

4. **Configure Settings:**
   - **Name:** `facial-attendance-system` (or any custom name)
   - **Region:** Choose the region nearest to you (e.g., Singapore, Frankfurt, Oregon)
   - **Environment:** `Docker` (Render will automatically detect the provided [Dockerfile](file:///d:/facial_attendance_system/Dockerfile))
   - **Instance Type:** `Free`

5. **(Optional) Add a Persistent Disk:**
   - If you want student uploaded photos and database changes to persist across server restarts on Render:
     - Under **Disks**, click **"Add Disk"**
     - **Name:** `attendance_data`
     - **Mount Path:** `/app/data`
     - **Size:** `1 GB`

6. **Click "Create Web Service":**
   - Render will build the Docker image, download the dependencies, and deploy the application.
   - Once the build succeeds, you will receive a secure live URL:
     ```
     https://facial-attendance-system.onrender.com
     ```
   - Open the URL in your browser &rarr; you are ready to log in as Administrator or Teacher!

---

## 🐳 Option 2: 1-Command Docker Deployment (Universal)

This repository includes a pre-configured [Dockerfile](file:///d:/facial_attendance_system/Dockerfile) and [docker-compose.yml](file:///d:/facial_attendance_system/docker-compose.yml) with automatic volume mounts for persistent data storage.

### Prerequisites:
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose installed on your host system.

### Deployment Commands:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/facial_attendance_system.git
   cd facial_attendance_system
   ```

2. **Start the application container:**
   ```bash
   docker compose up --build -d
   ```

3. **Verify the container is healthy and running:**
   ```bash
   docker compose ps
   docker compose logs -f
   ```

4. **Access the application:**
   - Open your browser at: `http://localhost:8000` (or `http://<your-server-ip>:8000`)
   - Swagger API Documentation: `http://localhost:8000/docs`

5. **Stop or Restart:**
   ```bash
   # Stop container
   docker compose down

   # Restart container
   docker compose restart
   ```

> **Data Persistence:** SQLite database (`data/attendance.db`), face encodings (`data/encodings_cache.pkl`), and uploaded student photos (`uploads/`) are mounted on the host machine and will not be lost when the container is recreated or stopped.

---

## 🚂 Option 3: Railway / Fly.io Cloud Platforms

### Deploying to Railway:
1. Go to [railway.app](https://railway.app) and sign in.
2. Click **"New Project"** &rarr; **"Deploy from GitHub repo"**.
3. Select your repository.
4. Railway will automatically detect the [Dockerfile](file:///d:/facial_attendance_system/Dockerfile) or [Procfile](file:///d:/facial_attendance_system/Procfile).
5. In project settings, generate a domain (e.g., `https://facial-attendance-production.up.railway.app`).
6. Done! Free automatic HTTPS is enabled immediately.

---

## 🖥️ Option 4: Linux VPS (Ubuntu / Debian on AWS EC2, DigitalOcean) with Nginx + SSL

For permanent campus or institutional production environments, running on an Ubuntu VPS with Nginx and Let's Encrypt SSL provides dedicated speed and reliability.

### Step 1: Update System & Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx certbot python3-certbot-nginx libgl1 libglib2.0-0 curl
```

### Step 2: Clone Repository & Create Virtual Environment
```bash
cd /var/www
sudo git clone https://github.com/<your-username>/facial_attendance_system.git
cd facial_attendance_system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
pip install --upgrade pip
pip install -r requirements.txt

# (Optional) Seed sample data
python seed_data.py
```

### Step 3: Create Systemd Background Service
Create a systemd unit file to ensure the service runs continuously and restarts automatically on reboot:

```bash
sudo nano /etc/systemd/system/facial-attendance.service
```

Paste the following configuration:
```ini
[Unit]
Description=Facial Attendance System FastAPI Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/facial_attendance_system
Environment="PATH=/var/www/facial_attendance_system/venv/bin"
ExecStart=/var/www/facial_attendance_system/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 2

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Set permissions, enable, and start the service:
```bash
sudo chown -R www-data:www-data /var/www/facial_attendance_system
sudo systemctl daemon-reload
sudo systemctl enable facial-attendance
sudo systemctl start facial-attendance
sudo systemctl status facial-attendance
```

### Step 4: Configure Nginx as Reverse Proxy
```bash
sudo nano /etc/nginx/sites-available/attendance
```

Paste the following Nginx block (replace `attendance.yourcollege.edu` with your domain):
```nginx
server {
    listen 80;
    server_name attendance.yourcollege.edu;

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: Install Free Let's Encrypt SSL Certificate (HTTPS)
```bash
sudo certbot --nginx -d attendance.yourcollege.edu
```
Certbot will automatically configure HTTPS with auto-renewal. Your system is now live with full secure camera permissions!

---

## 🏫 Option 5: Campus Gate / Local Intranet Deployment

If you want to run the system directly on a computer at the college gate or department lab:

1. **Launch the server:**
   ```bash
   python run.py
   ```
2. **Access locally:**
   - The browser opens automatically at: `http://localhost:8000`
3. **Access from other devices on the same Wi-Fi/LAN:**
   - Find the host PC's local IP address (e.g. `ipconfig` on Windows &rarr; `192.168.1.45`).
   - Other devices on the same network can access `http://192.168.1.45:8000`.
   - *Note on remote camera:* If another computer accesses the gate camera page via `http://192.168.1.45:8000`, Chrome will require you to add `http://192.168.1.45:8000` under `chrome://flags/#unsafely-treat-insecure-origin-as-secure` OR use a free HTTPS tunnel like [ngrok](https://ngrok.com) (`ngrok http 8000`).

---

## 🛡️ Post-Deployment Security & Administration Checklist

| Step | Action | Why |
|---|---|---|
| 1 | **Change Default Admin Password** | Log into Admin portal (`admin@college.edu`) and update credentials via your backend config or database. |
| 2 | **Register Real Faculty Members** | In Admin Portal &rarr; *Manage Teachers*, add official teachers with their Department, Section, and Subject. |
| 3 | **Register Students** | Have teachers log in with their Branch/Section credentials and register students with webcam snapshot or passport photo. |
| 4 | **Verify Daily Gate Operation** | Open the *Gate Camera* tab and verify automatic facial detection, subject logging, and cooldown gate banner functionality. |
| 5 | **Backup Database** | Regularly backup `data/attendance.db` and the `uploads/` directory to preserve student attendance archives. |
