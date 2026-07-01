#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  AI-Orchestrator — Start All Services
#  Launches auth, k8s, ai, and monitoring services in a tmux session
#  with one pane per service (2x2 grid).
#
#  Usage:
#    ./start-all.sh            → starts in tmux session 'orchestrator'
#    ./start-all.sh --no-tmux  → starts in background, tails logs
# ════════════════════════════════════════════════════════════════
set -euo pipefail

SESSION="orchestrator"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$REPO_ROOT/backend"
LOG_DIR="$REPO_ROOT/.logs"

# ── Colours ───────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

echo -e "${BOLD}${CYAN}"
echo "  ╔════════════════════════════════════════╗"
echo "  ║       AI DevOps Orchestrator           ║"
echo "  ║       Starting all services...         ║"
echo "  ╚════════════════════════════════════════╝"
echo -e "${NC}"

# ── Kill anything already on our ports ───────────────────────────
kill_port() {
  local port=$1
  local pid
  pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo -e "  ${YELLOW}⚠ Port $port in use — stopping PID $pid${NC}"
    kill "$pid" 2>/dev/null || true
    sleep 0.5
  fi
}

echo -e "${BOLD}Clearing ports...${NC}"
kill_port 8080
kill_port 8001
kill_port 8002
kill_port 8003
kill_port 8004

# ── Venv binary (shared across all services) ─────────────────────
VENV="$BACKEND/auth_service/venv/bin/python3"

# ── Service commands (use direct binary — `source activate` is unreliable in subshells) ──
AUTH_CMD="cd '$BACKEND/auth_service'         && PYTHONPATH='$BACKEND' '$VENV' -m uvicorn main:app --reload --host 0.0.0.0 --port 8080"
K8S_CMD="cd '$BACKEND/k8s_service'           && PYTHONPATH='$BACKEND' '$VENV' -m uvicorn main:app --reload --host 0.0.0.0 --port 8001"
AI_CMD="cd '$BACKEND/ai_service'             && PYTHONPATH='$BACKEND' '$VENV' -m uvicorn main:app --reload --host 0.0.0.0 --port 8002"
MON_CMD="cd '$BACKEND/monitoring_service'    && PYTHONPATH='$BACKEND' '$VENV' -m uvicorn main:app --reload --host 0.0.0.0 --port 8003"
NOTIFY_CMD="cd '$BACKEND/notification_service' && PYTHONPATH='$BACKEND' '$VENV' -m uvicorn main:app --reload --host 0.0.0.0 --port 8004"

# ══════════════════════════════════════════════════════════════════
#  MODE 1: tmux (default)
# ══════════════════════════════════════════════════════════════════
if [[ "${1:-}" != "--no-tmux" ]] && command -v tmux &>/dev/null; then

  # Kill existing session if present
  tmux kill-session -t "$SESSION" 2>/dev/null || true

  echo -e "${BOLD}Launching tmux session '${SESSION}'...${NC}"

  # Create session with first pane (auth)
  tmux new-session  -d -s "$SESSION" -x "220" -y "50" \
    -n "services" \
    "bash -c \"$AUTH_CMD; echo '--- auth_service exited ---'; read\""

  # Split vertically → k8s (right of auth)
  tmux split-window -h -t "$SESSION:0" \
    "bash -c \"$K8S_CMD; echo '--- k8s_service exited ---'; read\""

  # Split the left pane horizontally → monitoring (below auth)
  tmux split-window -v -t "$SESSION:0.0" \
    "bash -c \"$MON_CMD; echo '--- monitoring_service exited ---'; read\""

  # Split the right pane horizontally → ai (below k8s)
  tmux split-window -v -t "$SESSION:0.1" \
      "bash -c \"$AI_CMD; echo '--- ai_service exited ---'; read\"" 

  # Open a new window for notification_service
  tmux new-window -t "$SESSION" -n "notify" \
    "bash -c \"$NOTIFY_CMD; echo '--- notification_service exited ---'; read\""

  # Equalise pane sizes
  tmux select-layout -t "$SESSION:0" tiled

  # Add a status bar with port info
  tmux set-option -t "$SESSION" status on
  tmux set-option -t "$SESSION" status-left  " ${BOLD}AI-Orchestrator${NC} "
  tmux set-option -t "$SESSION" status-right " auth:8080 | k8s:8001 | ai:8002 | monitor:8003 | notify:8004 "

  # Attach
  echo ""
  echo -e "  ${GREEN}✅ auth_service     → http://localhost:8080/docs${NC}"
  echo -e "  ${GREEN}✅ k8s_service      → http://localhost:8001/docs${NC}"
  echo -e "  ${GREEN}✅ ai_service       → http://localhost:8002/docs${NC}"
  echo -e "  ${GREEN}✅ monitoring_svc   → http://localhost:8003/docs${NC}"
  echo -e "  ${GREEN}✅ notify_svc       → http://localhost:8004/docs${NC}"
  echo ""
  echo -e "  ${CYAN}Attaching to tmux session '${SESSION}'...${NC}"
  echo -e "  ${YELLOW}Tip: Ctrl+B then D to detach, ./stop-all.sh to stop all${NC}"
  echo ""
  sleep 1
  tmux attach-session -t "$SESSION"

# ══════════════════════════════════════════════════════════════════
#  MODE 2: --no-tmux (background + interleaved log tail)
# ══════════════════════════════════════════════════════════════════
else
  mkdir -p "$LOG_DIR"

  echo -e "${BOLD}Starting services in background (logs → .logs/)...${NC}"

  # Start each service, capturing PID
  (eval "$AUTH_CMD" > "$LOG_DIR/auth.log" 2>&1)      & AUTH_PID=$!
  (eval "$K8S_CMD"  > "$LOG_DIR/k8s.log"  2>&1)      & K8S_PID=$!
  (eval "$AI_CMD"   > "$LOG_DIR/ai.log"   2>&1)      & AI_PID=$!
  (eval "$MON_CMD"  > "$LOG_DIR/monitor.log" 2>&1)   & MON_PID=$!
  (eval "$NOTIFY_CMD" > "$LOG_DIR/notify.log" 2>&1)  & NOTIFY_PID=$!

  echo "$AUTH_PID $K8S_PID $AI_PID $MON_PID $NOTIFY_PID" > "$LOG_DIR/pids"

  echo ""
  echo -e "  ${GREEN}✅ auth_service     PID=$AUTH_PID    → http://localhost:8080/docs${NC}"
  echo -e "  ${GREEN}✅ k8s_service      PID=$K8S_PID     → http://localhost:8001/docs${NC}"
  echo -e "  ${GREEN}✅ ai_service       PID=$AI_PID      → http://localhost:8002/docs${NC}"
  echo -e "  ${GREEN}✅ monitoring_svc   PID=$MON_PID     → http://localhost:8003/docs${NC}"
  echo -e "  ${GREEN}✅ notify_svc       PID=$NOTIFY_PID  → http://localhost:8004/docs${NC}"
  echo ""
  echo -e "  ${YELLOW}Tailing logs (Ctrl+C to detach — services keep running)${NC}"
  echo -e "  ${YELLOW}Run ./stop-all.sh to stop everything${NC}"
  echo ""

  # Tail all logs with prefixes
  trap 'echo -e "\n${CYAN}Detached from logs. Services are still running.${NC}"' INT
  tail -f \
    <(tail -F "$LOG_DIR/auth.log"    2>/dev/null | sed "s/^/[${GREEN}auth   ${NC}] /") \
    <(tail -F "$LOG_DIR/k8s.log"     2>/dev/null | sed "s/^/[${CYAN}k8s    ${NC}] /") \
    <(tail -F "$LOG_DIR/ai.log"      2>/dev/null | sed "s/^/[${YELLOW}ai     ${NC}] /") \
    <(tail -F "$LOG_DIR/monitor.log" 2>/dev/null | sed "s/^/[${RED}monitor${NC}] /") \
    <(tail -F "$LOG_DIR/notify.log"  2>/dev/null | sed "s/^/[notify ] /")
fi
