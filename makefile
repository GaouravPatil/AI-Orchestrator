# ==========================
# AI DevOps Orchestrator
# ==========================

.PHONY: help db-up db-down db-logs db-shell \
        run-auth run-k8s run-ai \
        install-auth install-k8s install-ai \
        freeze-auth freeze-k8s freeze-ai

help:
	@echo ""
	@echo "  AI DevOps Orchestrator — Make Commands"
	@echo "  ─────────────────────────────────────"
	@echo "  Services:"
	@echo "    make run-auth      Run Auth Service     (port 8080)"
	@echo "    make run-k8s       Run K8s Service      (port 8001)"
	@echo "    make run-ai        Run AI Service       (port 8002)"
	@echo ""
	@echo "  Database:"
	@echo "    make db-up         Start PostgreSQL"
	@echo "    make db-down       Stop PostgreSQL"
	@echo "    make db-logs       View PostgreSQL logs"
	@echo "    make db-shell      Open PostgreSQL shell"
	@echo ""
	@echo "  Dependencies:"
	@echo "    make install-auth  Install auth_service deps"
	@echo "    make install-k8s   Install k8s_service deps"
	@echo "    make install-ai    Install ai_service deps"
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
	cd backend/ai-service && \
		source ../auth_service/venv/bin/activate && \
		PYTHONPATH=.. uvicorn main:app --reload --port 8002

install-ai:
	cd backend/ai-service && \
		source ../auth_service/venv/bin/activate && \
		pip install -r requirements.txt

freeze-ai:
	cd backend/ai-service && \
		source ../auth_service/venv/bin/activate && \
		pip freeze > requirements.txt