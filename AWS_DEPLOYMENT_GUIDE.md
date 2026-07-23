# ☁️ AWS Deployment Guide — GarageConnect v2

Deploy GarageConnect v2 on AWS Free Tier using **EC2** (server) + **MongoDB Atlas** (database).

---

## Prerequisites

- AWS account (Free Tier eligible)
- MongoDB Atlas account (free at [mongodb.com/atlas](https://www.mongodb.com/atlas))
- A domain name (optional, for SSL)
- Git installed on your local machine

---

## Step 1: Set Up MongoDB Atlas (Free Tier)

### 1.1 Create a Cluster
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas) → **Sign Up / Sign In**
2. Click **"Build a Database"**
3. Select **M0 Free Tier**
4. Choose region: **Mumbai (ap-south-1)** for lowest latency in India
5. Cluster name: `garage-connect-cluster`
6. Click **"Create Cluster"** (takes ~3 minutes)

### 1.2 Create Database User
1. Go to **Database Access** → **Add New Database User**
2. Authentication: Password
3. Username: `gcadmin`
4. Password: Generate a strong password → **save it**
5. Role: **Atlas Admin**
6. Click **"Add User"**

### 1.3 Configure Network Access
1. Go to **Network Access** → **Add IP Address**
2. For now: Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ In production, restrict to your EC2 instance's IP
3. Click **"Confirm"**

### 1.4 Get Connection String
1. Go to **Database** → Click **"Connect"** on your cluster
2. Select **"Connect your application"**
3. Driver: Python, Version: 3.12+
4. Copy the connection string. It looks like:
```
mongodb+srv://gcadmin:<password>@garage-connect-cluster.xxxxx.mongodb.net/garage_connect?retryWrites=true&w=majority
```
5. Replace `<password>` with your actual password
6. **Save this string** — you'll need it for EC2 setup

---

## Step 2: Launch EC2 Instance (Free Tier)

### 2.1 Launch Instance
1. Go to **AWS Console** → **EC2** → **Launch Instance**
2. Settings:
   - **Name**: `garage-connect-server`
   - **AMI**: Amazon Linux 2023 (Free Tier eligible)
   - **Instance type**: `t2.micro` (Free Tier)
   - **Key pair**: Create new → `garage-connect-key` → Download `.pem` file
   - **Security Group**: Create new with these rules:
     - SSH (port 22) — Your IP only
     - HTTP (port 80) — Anywhere (0.0.0.0/0)
     - HTTPS (port 443) — Anywhere (0.0.0.0/0)
     - Custom TCP (port 5000) — Anywhere (for testing, remove later)
3. Click **"Launch Instance"**

### 2.2 Connect to EC2
```bash
# Make key file secure (Git Bash / Linux / Mac)
chmod 400 garage-connect-key.pem

# SSH into the instance
ssh -i garage-connect-key.pem ec2-user@<YOUR-EC2-PUBLIC-IP>
```

---

## Step 3: Install Dependencies on EC2

```bash
# Update system
sudo dnf update -y

# Install Python 3.12 and pip
sudo dnf install python3.12 python3.12-pip git nginx -y

# Verify
python3.12 --version
pip3.12 --version
```

---

## Step 4: Deploy Your Code

```bash
# Clone your repo
cd /home/ec2-user
git clone https://github.com/YOUR_USERNAME/garage_connect_v2.git
cd garage_connect_v2

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Configure Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
MONGODB_URI=mongodb+srv://gcadmin:YOUR_PASSWORD@garage-connect-cluster.xxxxx.mongodb.net/garage_connect?retryWrites=true&w=majority
SECRET_KEY=GENERATE_A_RANDOM_32_CHAR_STRING_HERE
FLASK_ENV=production
FLASK_DEBUG=0
EOF
```

Generate a secure secret key:
```bash
python3.12 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 6: Test the App

```bash
# Quick test (dev server)
python3.12 app.py

# Visit http://<YOUR-EC2-PUBLIC-IP>:5000
# If it works, stop with Ctrl+C

# Test with Gunicorn (production server)
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# If it works, stop with Ctrl+C
```

---

## Step 7: Configure Nginx (Reverse Proxy)

```bash
# Create Nginx config
sudo tee /etc/nginx/conf.d/garageconnect.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;  # Replace _ with your domain name if you have one

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
    }

    location /static/ {
        alias /home/ec2-user/garage_connect_v2/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Test config and start Nginx
sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## Step 8: Create systemd Service (Auto-Restart)

```bash
sudo tee /etc/systemd/system/garageconnect.service > /dev/null << 'EOF'
[Unit]
Description=GarageConnect v2 Flask Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/garage_connect_v2
Environment="PATH=/home/ec2-user/garage_connect_v2/venv/bin"
EnvironmentFile=/home/ec2-user/garage_connect_v2/.env
ExecStart=/home/ec2-user/garage_connect_v2/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --threads 2 --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl start garageconnect
sudo systemctl enable garageconnect

# Check status
sudo systemctl status garageconnect
```

---

## Step 9: Verify Deployment

```bash
# Check the service is running
sudo systemctl status garageconnect

# Check Nginx is proxying correctly
curl http://localhost

# View logs if something goes wrong
sudo journalctl -u garageconnect -f
```

Visit **http://YOUR-EC2-PUBLIC-IP** — the app should be live!

---

## Step 10 (Optional): SSL with Let's Encrypt

```bash
# Install certbot
sudo dnf install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renew
sudo systemctl enable certbot-renew.timer
```

---

## 🔄 Updating the App

When you push new code to GitHub:

```bash
ssh -i garage-connect-key.pem ec2-user@<YOUR-EC2-PUBLIC-IP>
cd garage_connect_v2
git pull
source venv/bin/activate
pip install -r requirements.txt  # if dependencies changed
sudo systemctl restart garageconnect
```

---

## 💰 Cost Summary (Free Tier)

| Service | Cost |
|---|---|
| EC2 t2.micro | **Free** (750 hrs/month for 12 months) |
| MongoDB Atlas M0 | **Free** forever (512 MB storage) |
| Nginx | **Free** (installed on EC2) |
| **Total** | **₹0/month** |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `502 Bad Gateway` | Check if Gunicorn is running: `sudo systemctl status garageconnect` |
| `Connection refused` on port 5000 | Check EC2 Security Group allows port 80 |
| MongoDB connection error | Verify Atlas Network Access includes EC2 IP |
| Static files not loading | Check Nginx `location /static/` path is correct |
| App crashes on startup | Check logs: `sudo journalctl -u garageconnect -f` |
