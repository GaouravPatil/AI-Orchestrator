# ==========================
# AI DevOps Orchestrator
# ==========================

.PHONY: help run-all stop-all \
        db-up db-down db-logs db-shell \
        run-auth run-k8s run-ai run-monitor \
        install-auth install-k8s install-ai install-monitor \
        freeze-auth freeze-k8s freeze-ai freeze-monitor

help:
	@echo ""
	@echo "  AI DevOps Orchestrator — Make Commands"
	@echo "  ─────────────────────────────────────"
	@echo "  All-in-one:"
	@echo "    make run-all       Start ALL services in tmux (2x2 grid)"
	@echo "    make stop-all      Stop ALL services"
	@echo ""
	@echo "  Services:"
	@echo "    make run-auth      Run Auth Service        (port 8080)"
	@echo "    make run-k8s       Run K8s Service         (port 8001)"
	@echo "    make run-ai        Run AI Service          (port 8002)"
	@echo "    make run-monitor   Run Monitoring Service  (port 8003)"
	@echo ""
	@echo "  Database:"
	@echo "    make db-up         Start PostgreSQL"
	@echo "    make db-down       Stop PostgreSQL"
	@echo "    make db-logs       View PostgreSQL logs"
	@echo "    make db-shell      Open PostgreSQL shell"
	@echo ""
	@echo "  Dependencies:"
	@echo "    make install-auth     Install auth_service deps"
	@echo "    make install-k8s      Install k8s_service deps"
	@echo "    make install-ai       Install ai_service deps"
	@echo "    make install-monitor  Install monitoring_service deps"
	@echo ""


# ─── Infrastructure ──────────────────────────────────────────────────────────

db-up:
	sudo docker compose -f infra/docker-compose.yaml up -d

db-down:
	sudo docker compose -f infra/docker-compose.yaml down -v

db-logs:
	sudo docker compose -f infra/docker-compose.yaml logs -f postgres

db-shell:
	sudo docker exec -it infra-postgres-1 psql -U postgres -d orchestrator


# ─── Auth Service (port 8080) ─────────────────────────────────────────────────

run-auth:
	cd backend/auth_service && \
		source venv/bin/activate && \
		PYTHONPATH=.. uvicorn main:app --reload --port 8080

install-auth:
	cd backend/auth_service && \
		source venv/bin/activate && \
		pip install -r requirements.txt

freeze-auth:
	cd backend/auth_service && \
		source venv/bin/activate && \
		pip freeze > requirements.txt


# ─── K8s Service (port 8001) ─────────────────────────────────────────────────

run-k8s:
	cd backend/k8s_service && \
		source ../auth_service/venv/bin/activate && \
		PYTHONPATH=.. uvicorn main:app --reload --port 8001

install-k8s:
	cd backend/k8s_service && \
		source ../auth_service/venv/bin/activate && \
		pip install -r requirements.txt

freeze-k8s:
	cd backend/k8s_service && \
		source ../auth_service/venv/bin/activate && \
		pip freeze > requirements.txt


# ─── AI Service (port 8002) ──────────────────────────────────────────────────

run-ai:
	cd backend/ai_service && \
		source ../auth_service/venv/bin/activate && \
		PYTHONPATH=.. uvicorn main:app --reload --port 8002

install-ai:
	cd backend/ai_service && \
		source ../auth_service/venv/bin/activate && \
		pip install -r requirements.txt

freeze-ai:
	cd backend/ai_service && \
		source ../auth_service/venv/bin/activate && \
		pip freeze > requirements.txt


# ─── Monitoring Service (port 8003) ──────────────────────────────────────────

run-monitor:
	cd backend/monitoring_service && \
		source ../auth_service/venv/bin/activate && \
		PYTHONPATH=.. uvicorn main:app --reload --port 8003

install-monitor:
	cd backend/monitoring_service && \
		source ../auth_service/venv/bin/activate && \
		pip install -r requirements.txt

freeze-monitor:
	cd backend/monitoring_service && \
		source ../auth_service/venv/bin/activate && \
		pip freeze > requirements.txt


# ─── All services ─────────────────────────────────────────────────────────────

run-all:
	@echo "Starting all services in tmux session 'orchestrator'..."
	@./start-all.sh

stop-all:
	@./stop-all.sh

run-all-bg:
	@echo "Starting all services in background (no tmux)..."
	@./start-all.sh --no-tmux