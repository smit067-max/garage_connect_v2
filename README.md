# 🚗 GarageConnect v2 — Car Repair Marketplace

> **GoMechanic-style** car repair marketplace with AI-powered diagnostics, inventory management, and analytics dashboard. Built with Flask + MongoDB.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-brightgreen?logo=mongodb)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

### 🔍 For Customers
- **Browse & Book** — Find garages by city, rating, services offered
- **AI-Powered Diagnosis** — Type your car problem → get instant service recommendation with confidence % and urgency level
- **Real-Time Tracking** — Track booking status (Pending → Accepted → In Progress → Completed)
- **Rate & Review** — Star ratings and written reviews for completed services
- **Vehicle Management** — Book with your vehicle details (make, model, year, registration)

### 🔧 For Garage Owners
- **Job Management** — Accept, start, and complete repair jobs
- **📊 Analytics Dashboard** — Revenue trends, profit analysis, service breakdowns, customer stats with Chart.js visualizations
- **📦 Inventory Management** — Track spare parts, auto-deduct stock on job completion, low-stock alerts
- **Revenue Tracking** — Labour + parts pricing, commission calculations

### 👑 For Admins
- **Garage Approvals** — Review and approve/reject new garage registrations
- **Commission Reports** — Track total and monthly platform commission
- **Low Stock Alerts** — Aggregated alerts from all garages
- **Platform Overview** — Recent bookings, active garages, revenue metrics

### 🤖 AI Diagnosis Engine
- **Self-hosted** — Runs on your server, zero API cost (no OpenAI/Claude needed)
- **scikit-learn** — TF-IDF vectorizer + Multinomial Naive Bayes classifier
- **60+ training examples** across 12 service categories
- **Live suggestions** — Debounced AJAX call as you type, response in ~100ms
- **Urgency detection** — Keyword-based High/Medium/Low urgency classification

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+ installed
- MongoDB running locally on port 27017 (or use Docker)

### Option 1: Run Directly

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/garage_connect_v2.git
cd garage_connect_v2

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the app
python app.py
```

Open **http://localhost:5000** 🎉

### Option 2: Docker Compose (Recommended)

```bash
docker compose up -d
```

This starts Flask + MongoDB together. Open **http://localhost:5000**

---

## 👤 Demo Accounts

The app auto-seeds demo data on first run:

| Username | Password | Role | Description |
|---|---|---|---|
| `admin` | `admin123` | Admin | Approves garages, sees commission + alerts |
| `garage1` | `garage123` | Garage Owner | Ramesh Auto Works (with inventory) |
| `garage2` | `garage123` | Garage Owner | Speedy Motors (with inventory) |
| `customer1` | `cust123` | Customer | Can browse, book, review |
| `customer2` | `cust123` | Customer | Can browse, book, review |

---

## 🧪 Try It Yourself

### AI Diagnosis
1. Login as `customer1` → Browse Garages → Book a Repair
2. Type: *"car not starting, battery seems dead"*
3. Watch the AI suggestion appear: **Battery Replacement, High urgency, 89% confidence**
4. Click "Use This Suggestion" to auto-fill the service dropdown

### Inventory Flow
1. Login as `garage1` → Dashboard → find an "In Progress" job → Complete Job
2. Check parts used (e.g. "Brake Pads"), set quantity
3. Enter labour price → Submit
4. Stock auto-deducts, total = labour + parts, commission auto-calculated

### Analytics Dashboard
1. Login as `garage1` → Analytics tab
2. Toggle between time periods (30 days / 3 months / 1 year / 5 years)
3. View revenue trends, profit charts, service breakdowns, customer stats

---

## 🗂️ Project Structure

```
garage_connect_v2/
├── app.py                  ← Flask app (routes + business logic)
├── models.py               ← MongoDB CRUD helpers
├── ai_diagnosis.py          ← ML classifier (TF-IDF + Naive Bayes)
├── analytics.py             ← Dashboard analytics engine
├── seed.py                  ← Demo data seeder
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── AWS_DEPLOYMENT_GUIDE.md
│
├── static/
│   ├── css/style.css        ← Design system (glassmorphism, dark theme)
│   └── js/
│       ├── main.js          ← UI logic (AI panel, forms, nav)
│       └── analytics.js     ← Chart.js dashboard rendering
│
└── templates/               ← 15 Jinja2 templates
    ├── base.html            ← Shared layout
    ├── index.html           ← Landing page
    ├── login.html / register.html
    ├── garages.html / garage_detail.html
    ├── book_form.html       ← Booking + AI diagnosis
    ├── my_bookings.html     ← Customer history + ratings
    ├── garage_dashboard.html / garage_analytics.html
    ├── complete_job.html / garage_form.html
    ├── inventory.html / part_form.html
    └── admin_dashboard.html
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask 3.1, Python 3.12 |
| **Database** | MongoDB 7.0 (PyMongo) |
| **AI/ML** | scikit-learn (TF-IDF + Naive Bayes) |
| **Frontend** | Jinja2, Vanilla CSS, Vanilla JS |
| **Charts** | Chart.js 4.4 |
| **Auth** | Flask-Login + bcrypt |
| **Security** | Flask-WTF CSRF protection |
| **Deployment** | Docker, Gunicorn, Nginx |
| **Cloud** | AWS EC2 + MongoDB Atlas (Free Tier) |

---

## ☁️ Deploy to AWS

Follow **[AWS_DEPLOYMENT_GUIDE.md](./AWS_DEPLOYMENT_GUIDE.md)** for step-by-step instructions:
1. MongoDB Atlas setup (free tier M0)
2. EC2 instance (t2.micro, free tier)
3. Gunicorn + Nginx reverse proxy
4. systemd auto-restart service
5. Optional SSL with Let's Encrypt

**Total cost: ₹0/month** on AWS Free Tier.

---

## 💬 Talking Points

1. **"We use MongoDB — the same database technology powering Uber, eBay, and Adobe at scale."**
2. **"Our AI diagnosis runs on our own servers — zero per-request API cost, unlike GPT/Claude."**
3. **"Inventory isn't just tracking — parts cost automatically factors into commission calculations."**
4. **"The analytics dashboard gives garage owners real business insights — revenue trends, profit margins, customer patterns."**
5. **"This is deployment-ready. We have exact AWS commands to go live today on Free Tier."**

---

## 📄 License

MIT License. See [LICENSE](./LICENSE) for details.
