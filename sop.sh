#!/usr/bin/env bash
# sop.sh — SLG Sentinel 服务操作脚本
# 用法: ./sop.sh [start|stop|restart|reload|status]

set -euo pipefail

# ── 配置 ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.streamlit.pid"
LOG_FILE="$SCRIPT_DIR/.streamlit.log"
PORT=8501
APP="$SCRIPT_DIR/app.py"
VENV="$SCRIPT_DIR/venv"

# ── 颜色 ─────────────────────────────────────────────────────────────────────
GOLD='\033[0;33m'; GREEN='\033[0;32m'; RED='\033[0;31m'; DIM='\033[2m'; NC='\033[0m'
info() { echo -e "${GOLD}[SOP]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK ]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC} $*" >&2; }
dim()  { echo -e "${DIM}      $*${NC}"; }

# ── 工具函数 ─────────────────────────────────────────────────────────────────
pid_alive() {
    [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

port_in_use() {
    lsof -ti "tcp:$PORT" &>/dev/null
}

kill_port() {
    local pids
    pids=$(lsof -ti "tcp:$PORT" 2>/dev/null || true)
    if [[ -z "$pids" ]]; then
        return 0
    fi
    echo "$pids" | xargs kill 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti "tcp:$PORT" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
    return 0
}

wait_up() {
    local i=0
    while (( i < 24 )); do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT" 2>/dev/null | grep -q "200"; then
            return 0
        fi
        sleep 0.5
        ((++i))
    done
    return 1
}

do_start() {
    if pid_alive; then
        ok "已在运行 (PID $(cat "$PID_FILE"))  →  http://localhost:$PORT"
        return 0
    fi

    # 清理残留 PID 文件
    rm -f "$PID_FILE"

    # 检查端口占用
    if port_in_use; then
        err "端口 $PORT 已被占用，正在清理残留进程 ..."
        kill_port
        sleep 0.5
    fi

    if [[ ! -d "$VENV" ]]; then
        err "未找到虚拟环境 $VENV，请先执行: python -m venv venv && pip install -r requirements.txt"
        exit 1
    fi

    info "启动 GUI 控制台 ..."
    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    # 用子 shell 启动，写好 PID 后再 disown
    ( streamlit run "$APP" \
          --server.port "$PORT" \
          --server.headless true \
          >> "$LOG_FILE" 2>&1 ) &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    disown "$pid"

    if wait_up; then
        ok "启动成功 (PID $pid)  →  http://localhost:$PORT"
        dim "日志: tail -f $LOG_FILE"
    else
        # 进程可能已挂，检查一次
        if pid_alive; then
            ok "进程运行中 (PID $pid)，服务仍在初始化  →  http://localhost:$PORT"
        else
            err "启动失败，请查看日志: $LOG_FILE"
            rm -f "$PID_FILE"
            exit 1
        fi
    fi
}

do_stop() {
    local stopped=false

    if pid_alive; then
        local pid
        pid=$(cat "$PID_FILE")
        info "停止进程 (PID $pid) ..."
        kill "$pid" 2>/dev/null || true
        local i=0
        while (( i < 20 )) && kill -0 "$pid" 2>/dev/null; do
            sleep 0.3; ((++i))
        done
        kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
        stopped=true
    fi
    rm -f "$PID_FILE"

    # 兜底：清理端口上的残留进程
    if port_in_use; then
        info "清理端口 $PORT 上的残留进程 ..."
        kill_port
        stopped=true
    fi

    if $stopped; then ok "已停止"; else info "服务未在运行"; fi
}

do_restart() {
    info "重启服务 ..."
    do_stop
    sleep 0.4
    do_start
}

do_reload() {
    # Streamlit 内置 file watcher：检测到文件变更后自动重新执行 app.py
    # touch app.py 触发 watcher，无需重启进程（session 状态会重置）
    if ! pid_alive && ! port_in_use; then
        info "服务未运行，改为启动 ..."
        do_start
        return 0
    fi
    info "触发热重载 (touch app.py) ..."
    touch "$APP"
    ok "已触发，浏览器页面将在 1-2 秒内自动刷新"
    dim "注：Streamlit session 状态会重置，效果等同于浏览器刷新"
}

do_status() {
    if pid_alive; then
        local pid
        pid=$(cat "$PID_FILE")
        ok "运行中  PID=$pid  →  http://localhost:$PORT"
        dim "$(ps -p "$pid" -o pid=,vsz=,rss=,etime= 2>/dev/null \
            | awk '{printf "VSZ=%sMB  RSS=%sMB  已运行=%s", int($2/1024), int($3/1024), $4}' \
            || echo '进程信息读取失败')"
        dim "日志: tail -f $LOG_FILE"
    elif port_in_use; then
        err "端口 $PORT 被占用但 PID 文件不存在（残留进程），可运行: ./sop.sh stop"
    else
        info "未运行"
    fi
}

# ── 入口 ─────────────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

case "${1:-help}" in
    start)   do_start   ;;
    stop)    do_stop    ;;
    restart) do_restart ;;
    reload)  do_reload  ;;
    status)  do_status  ;;
    *)
        echo -e "${GOLD}SLG Sentinel — 服务操作脚本${NC}"
        echo ""
        echo "  用法:  ./sop.sh <命令>"
        echo ""
        echo "  命令:"
        echo -e "    ${GREEN}start${NC}    启动 GUI 控制台  (http://localhost:$PORT)"
        echo -e "    ${GREEN}stop${NC}     停止服务（含端口残留清理）"
        echo -e "    ${GREEN}restart${NC}  重启服务"
        echo -e "    ${GREEN}reload${NC}   热重载（touch app.py → file watcher 重新执行，不重启进程）"
        echo -e "    ${GREEN}status${NC}   查看运行状态与资源占用"
        echo ""
        ;;
esac
