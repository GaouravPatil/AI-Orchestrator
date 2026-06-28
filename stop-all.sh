#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  AI-Orchestrator — Stop All Services
#  Kills any process on ports 8080, 8001, 8002, 8003, 8004
#  and kills the tmux 'orchestrator' session if running.
# ════════════════════════════════════════════════════════════════

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_ROOT/.logs"

echo -e "${BOLD}${CYAN}Stopping AI-Orchestrator services...${NC}"
echo ""

# ── Kill tmux session ─────────────────────────────────────────────
if tmux has-session -t orchestrator 2>/dev/null; then
  tmux kill-session -t orchestrator
  echo -e "  ${GREEN}✅ tmux session 'orchestrator' killed${NC}"
fi

# ── Kill by port (catches --no-tmux processes too) ────────────────
kill_port() {
  local port=$1
  local name=$2
  local pid
  pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    kill "$pid" 2>/dev/null || true
    echo -e "  ${GREEN}✅ $name (port $port) stopped — PID $pid${NC}"
  else
    echo -e "  ${YELLOW}–  $name (port $port) was not running${NC}"
  fi
}

kill_port 8080 "auth_service"
kill_port 8001 "k8s_service"
kill_port 8002 "ai_service"
kill_port 8003 "monitoring_service"
kill_port 8004 "notification_service"

# ── Clean up PID file ─────────────────────────────────────────────
[ -f "$LOG_DIR/pids" ] && rm -f "$LOG_DIR/pids"

echo ""
echo -e "${BOLD}All services stopped.${NC}"
