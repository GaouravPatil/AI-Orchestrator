# 🤖 AI DevOps Orchestrator

<div align="center">

![AI Orchestrator Banner](https://img.shields.io/badge/AI-DevOps%20Orchestrator-blueviolet?style=for-the-badge&logo=kubernetes&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Managed-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-Dashboards-F46800?style=for-the-badge&logo=grafana&logoColor=white)

**A full-stack, AI-powered platform for managing and monitoring Kubernetes clusters through natural language.**

</div>

---

## 🚀 The Problem It Solves

Managing Kubernetes clusters traditionally requires deep expertise in `kubectl` commands, YAML configuration files, and complex CLI tooling. Operations teams face three persistent pain points:

| Pain Point | Impact |
|---|---|
| **High learning curve** | Engineers must memorize hundreds of `kubectl` commands and cluster concepts |
| **Reactive monitoring** | Cluster degradation is discovered after users are already affected |
| **Fragmented tooling** | Auth, resource inspection, alerting, and visualization are in separate, disconnected tools |

**AI-Orchestrator solves this** by combining a conversational AI assistant with real-time cluster health monitoring and multi-channel alerting into a single, unified Jarvis-style dashboard. Any operator — regardless of Kubernetes expertise level — can inspect nodes, scale deployments, or investigate pod failures simply by asking in plain English.

---

## ✨ Key Features

- 🗣️ **Natural Language Kubernetes Control** — Chat with an AI assistant to query pods, nodes, deployments, and services without writing a single `kubectl` command
- 🩺 **Real-Time Cluster Health Monitoring** — Background polling continuously tracks cluster state and surfaces health aggregations
- 🔔 **Multi-Channel Alerting** — Dispatches alerts to Slack, Discord, webhooks, email, and console with built-in deduplication
- 📊 **Prometheus + Grafana Observability** — Metrics exposed from both monitoring and notification services; auto-provisioned Grafana dashboards
- 🔐 **JWT Authentication** — Secure login with role-based access; all service-to-service calls are authenticated
- 🖥️ **Jarvis-Themed Dashboard** — Animated React UI with a live AI chat sidebar, cluster overview cards, and real-time metric graphs
- 🐘 **PostgreSQL Persistence** — User accounts and session data persisted via SQLAlchemy with Alembic migrations

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend (Vite)               │
│          Jarvis Dashboard  ·  AI Chat  ·  Login      │
│                    Port: 5173                        │
└───────────────────────┬─────────────────────────────┘
                        │  REST / JWT
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Auth Service│ │  K8s Service │ │    AI Service    │
│  Port: 8080  │ │  Port: 8001  │ │   Port: 8002     │
│  JWT + Users │ │  Pods/Nodes/ │ │  NL → K8s Query  │
│  PostgreSQL  │ │  Deployments │ │  LLM Integration │
└──────────────┘ └──────────────┘ └──────────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │                               │
        ▼                               ▼
┌───────────────────┐       ┌──────────────────────┐
│ Monitoring Service│       │ Notification Service  │
│    Port: 8003     │       │     Port: 8004        │
│ Cluster Poller    │──────▶│ Slack/Discord/Email   │
│ Health Aggregation│       │ Alert Deduplication   │
│ Prometheus /metrics│      │ Prometheus /metrics   │
└───────────────────┘       └──────────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        ▼
        ┌──────────────────────────────┐
        │  Infra (Docker Compose)      │
        │  PostgreSQL  :5432           │
        │  Prometheus  :9090           │
        │  Grafana     :3001           │
        └──────────────────────────────┘
```

---

## 📁 Directory Structure

```
AI-Orchestrator/
│
├── 📄 start-all.sh           # One-command launcher (tmux or background mode)
├── 📄 stop-all.sh            # Gracefully stops all services
├── 📄 makefile               # Make targets for individual services & infra
│
├── 🗂️ backend/
│   │
│   ├── 🔐 auth_service/       # Authentication & user management (port 8080)
│   │   ├── app/
│   │   │   ├── api/auth.py    # Register, login, refresh endpoints
│   │   │   ├── models/        # SQLAlchemy User model
│   │   │   └── services/      # Business logic (password hashing, JWT)
│   │   ├── alembic/           # Database migrations
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── requirements.txt
│   │   └── .env               # DB URL, JWT secret
│   │
│   ├── ☸️ k8s_service/        # Kubernetes cluster management (port 8001)
│   │   ├── app/
│   │   │   ├── api/kubernetes.py  # REST endpoints for K8s resources
│   │   │   └── managers/          # Pods, Nodes, Deployments managers
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env               # KUBECONFIG path, JWT config
│   │
│   ├── 🤖 ai_service/         # Natural language AI assistant (port 8002)
│   │   ├── app/
│   │   │   └── api/chat.py    # Chat endpoint; routes NL → K8s queries
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env               # LLM API keys, AI model config
│   │
│   ├── 📡 monitoring_service/ # Real-time cluster health monitoring (port 8003)
│   │   ├── app/
│   │   │   ├── api/monitor.py # Health, alerts, and /metrics endpoints
│   │   │   ├── core/          # Config, logger
│   │   │   └── tasks/         # Background polling loop
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env               # Poll interval, K8s service URL, thresholds
│   │
│   ├── 🔔 notification_service/ # Multi-channel alert dispatcher (port 8004)
│   │   ├── app/
│   │   │   ├── api/notify.py  # Notification dispatch endpoints
│   │   │   ├── core/          # Config, logger
│   │   │   └── tasks/poller.py # Background alert poller with deduplication
│   │   ├── main.py
│   │   └── .env               # Slack/Discord/Email/webhook URLs
│   │
│   └── 🔗 shared/             # Shared code across all services
│       ├── database/          # SQLAlchemy Base, engine, session factory
│       ├── security/          # JWT creation/verification, password hashing
│       ├── middleware/        # Auth middleware (JWT guard)
│       ├── exceptions/        # Common HTTP exception handlers
│       ├── logger/            # Structured logging setup
│       └── utils/             # Misc helpers
│
├── 🖥️ frontend/               # React + Vite Jarvis-themed dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIChat.jsx         # Floating AI chat assistant panel
│   │   │   ├── Sidebar.jsx        # Navigation sidebar
│   │   │   └── JarvisBackground.jsx # Animated background effect
│   │   ├── pages/
│   │   │   ├── Login.jsx          # Auth login page
│   │   │   └── Dashboard.jsx      # Main cluster overview dashboard
│   │   ├── services/              # Axios API client wrappers
│   │   ├── styles/                # Per-component CSS files
│   │   ├── App.jsx                # Router + auth guard
│   │   └── index.css              # Global design tokens & theme
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── 🏗️ infra/                  # Infrastructure as code
    ├── docker-compose.yaml    # PostgreSQL, Prometheus, Grafana
    ├── prometheus/
    │   └── prometheus.yml     # Scrape configs for monitoring & notify services
    ├── grafana/
    │   ├── provisioning/      # Auto-provision Prometheus datasource
    │   └── dashboards/        # Pre-built Grafana dashboards
    └── kubernetes/            # K8s manifests (ConfigMaps, Deployments, etc.)
```

---

## ⚙️ Prerequisites

Ensure the following are installed before proceeding:

| Tool | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Backend services |
| **Node.js** | 18+ | React frontend |
| **Docker** | 24+ | PostgreSQL, Prometheus, Grafana |
| **Docker Compose** | v2+ | Infrastructure orchestration |
| **tmux** | any | Multi-pane service launcher (optional) |
| **kubectl** | any | Kubernetes cluster access |
| **lsof** | any | Port conflict resolution in `start-all.sh` |

A running Kubernetes cluster (local or remote) with a valid `~/.kube/config` is required for the K8s service.

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-Orchestrator.git
cd AI-Orchestrator
```

### 2. Set Up the Python Virtual Environment

All backend services share a single virtual environment managed under `auth_service/venv`:

```bash
cd backend/auth_service
python3 -m venv venv
source venv/bin/activate

# Install dependencies for ALL services
pip install -r requirements.txt
cd ../k8s_service    && pip install -r requirements.txt
cd ../ai_service     && pip install -r requirements.txt
cd ../monitoring_service  && pip install -r requirements.txt

# Return to project root
cd ../../..
```

Or use the Make shortcuts:

```bash
make install-auth
make install-k8s
make install-ai
make install-monitor
```

### 3. Configure Environment Variables

Each service has its own `.env` file. Copy and fill in values:

**`backend/auth_service/.env`**
```env
DATABASE_URL=postgresql://postgres:redhat@localhost:5432/orchestrator
SECRET_KEY=your-super-secret-jwt-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**`backend/k8s_service/.env`**
```env
KUBECONFIG=/home/your-user/.kube/config
SECRET_KEY=your-super-secret-jwt-key
AUTH_SERVICE_URL=http://localhost:8080
```

**`backend/ai_service/.env`**
```env
GEMINI_API_KEY=your-google-gemini-api-key   # or equivalent LLM key
K8S_SERVICE_URL=http://localhost:8001
AUTH_SERVICE_URL=http://localhost:8080
```

**`backend/monitoring_service/.env`**
```env
K8S_SERVICE_URL=http://localhost:8001
NOTIFICATION_SERVICE_URL=http://localhost:8004
POLL_INTERVAL_SECONDS=30
```

**`backend/notification_service/.env`**
```env
MONITORING_SERVICE_URL=http://localhost:8003
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...   # optional
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/... # optional
POLL_INTERVAL_SECONDS=60
```

### 4. Start the Infrastructure (Database + Observability)

```bash
make db-up
# or directly:
sudo docker compose -f infra/docker-compose.yaml up -d
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Prometheus** on `localhost:9090`
- **Grafana** on `localhost:3001` (default login: `admin` / `admin`)

### 5. Run Database Migrations

```bash
cd backend/auth_service
source venv/bin/activate
PYTHONPATH=.. alembic upgrade head
cd ../..
```

### 6. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Running the Application

### Option A — All Services at Once (Recommended)

**With tmux** (displays all services in a 2×2 grid):

```bash
./start-all.sh
# or:
make run-all
```

Press `Ctrl+B` then `D` to detach from the tmux session without stopping services.

**Without tmux** (background processes with log tailing):

```bash
./start-all.sh --no-tmux
# or:
make run-all-bg
```

### Option B — Individual Services

```bash
make run-auth      # Auth Service     → http://localhost:8080
make run-k8s       # K8s Service      → http://localhost:8001
make run-ai        # AI Service       → http://localhost:8002
make run-monitor   # Monitor Service  → http://localhost:8003
```

### Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: **http://localhost:5173**

---

## 🌐 Service Endpoints

| Service | Port | Swagger Docs | Description |
|---|---|---|---|
| Auth Service | `8080` | http://localhost:8080/docs | Login, register, JWT |
| K8s Service | `8001` | http://localhost:8001/docs | Pods, nodes, deployments |
| AI Service | `8002` | http://localhost:8002/docs | NL chat → K8s |
| Monitoring Service | `8003` | http://localhost:8003/docs | Health, alerts, metrics |
| Notification Service | `8004` | http://localhost:8004/docs | Alert dispatch |
| Frontend | `5173` | — | React dashboard |
| Prometheus | `9090` | http://localhost:9090 | Metrics explorer |
| Grafana | `3001` | http://localhost:3001 | Dashboards |

---

## 🛑 Stopping All Services

```bash
./stop-all.sh
# or:
make stop-all

# Stop infrastructure
make db-down
```

---

## 🧑‍💻 Development Workflow

```bash
# Check all available make targets
make help

# View PostgreSQL logs
make db-logs

# Open a PostgreSQL shell
make db-shell

# Freeze current pip packages for a service
make freeze-auth
make freeze-k8s
```

---

## 📐 How It Works — End-to-End Flow

```
User types: "Show me all failing pods"
        │
        ▼
   React Frontend (Dashboard / AI Chat)
        │ POST /ai/chat  { "message": "Show me all failing pods" }
        ▼
   AI Service (port 8002)
        │ Parses intent → calls K8s Service
        ▼
   K8s Service (port 8001)
        │ Queries live cluster via kubernetes-python client
        ▼
   Returns pod list → AI formats response → displayed in chat

Simultaneously:
   Monitoring Service polls K8s Service every N seconds
        │ Detects anomalies (CrashLoopBackOff, OOMKilled, etc.)
        ▼
   Notification Service polls Monitoring Service
        │ Deduplicates alerts → sends to Slack / Discord / webhook
        ▼
   Prometheus scrapes /metrics from both services
        ▼
   Grafana visualises trends on pre-built dashboards
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push and open a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

<div align="center">
Built with ❤️ using FastAPI · React · Kubernetes · Prometheus · Grafana
</div>
