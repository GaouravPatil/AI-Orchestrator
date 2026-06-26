# ==========================
# AI DevOps Orchestrator
# ==========================

.PHONY: help db-up db-down db-logs db-shell run-auth install-auth freeze-auth run-k8s install-k8s freeze-k8s

help:
	@echo "Available Commands:"
	@echo " make run-auth      - Run Auth Service"
	@echo " make run-k8s       - Run Kubernetes Service"
	@echo " make db-up         - Start PostgreSQL"
	@echo " make db-down       - Stop PostgreSQL"
	@echo " make db-logs       - View PostgreSQL logs"
	@echo " make db-shell      - Open PostgreSQL shell"
	@echo " make install-auth  - Install Auth dependencies"
	@echo " make freeze-auth   - Update requirements.txt for Auth"
	@echo " make install-k8s   - Install Kubernetes Service dependencies"
	@echo " make freeze-k8s    - Update requirements.txt for Kubernetes"


db-up:
	sudo docker compose -f infra/docker-compose.yaml up -d

db-down:
	sudo docker compose -f infra/docker-compose.yaml down

db-logs:
	sudo docker compose -f infra/docker-compose.yaml logs -f postgres

db-shell:
	sudo docker exec -it postgres psql -U postgres -d orchestrator

run-auth:
	cd backend/auth_service && \
		source venv/bin/activate && \
		PYTHONPATH=.. uvicorn main:app --reload

install-auth:
	cd backend/auth_service && \
		source venv/bin/activate && \
		pip install -r requirements.txt

freeze-auth:
	cd backend/auth_service && \
		source venv/bin/activate && \
		pip freeze > requirements.txt

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