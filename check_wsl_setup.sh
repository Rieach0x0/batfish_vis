#!/bin/bash
# WSL2環境のセットアップ状態をチェックするスクリプト

echo "=========================================="
echo "WSL2 Backend Setup Checker"
echo "=========================================="
echo ""

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# チェック関数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $2 is installed"
        if [ ! -z "$3" ]; then
            echo "  Version: $($3)"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} $2 is NOT installed"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $2 does NOT exist"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $2 does NOT exist"
        return 1
    fi
}

# 1. システム環境チェック
echo "1. System Environment"
echo "-------------------"
check_command "docker" "Docker" "docker --version"
check_command "python3.11" "Python 3.11" "python3.11 --version"
echo ""

# 2. プロジェクトディレクトリチェック
echo "2. Project Directory"
echo "-------------------"
check_dir "/mnt/d/batfish_vis" "Windows project directory mounted"
check_dir "/mnt/d/batfish_vis/backend" "Backend directory"
check_dir "/mnt/d/batfish_vis/frontend" "Frontend directory"
echo ""

# 3. バックエンドセットアップチェック
echo "3. Backend Setup"
echo "-------------------"
if [ -d "/mnt/d/batfish_vis/backend" ]; then
    cd /mnt/d/batfish_vis/backend

    check_dir ".venv" "Python virtual environment"
    check_file "requirements.txt" "Requirements file"

    if [ -d ".venv" ]; then
        source .venv/bin/activate
        check_command "uvicorn" "Uvicorn (in venv)" "uvicorn --version"
        check_command "pip" "Pip (in venv)" "pip --version"

        echo ""
        echo "  Installed packages:"
        pip list | grep -E "(fastapi|uvicorn|pybatfish|pydantic)" | sed 's/^/  /'
        deactivate
    fi

    check_file ".env" ".env configuration file"
else
    echo -e "${RED}✗${NC} Cannot access backend directory"
fi
echo ""

# 4. Dockerコンテナチェック
echo "4. Docker Containers"
echo "-------------------"
if docker ps &> /dev/null; then
    BATFISH_RUNNING=$(docker ps --filter "name=batfish" --format "{{.Names}}")
    if [ ! -z "$BATFISH_RUNNING" ]; then
        echo -e "${GREEN}✓${NC} Batfish container is running"
        docker ps --filter "name=batfish" --format "  ID: {{.ID}}\n  Image: {{.Image}}\n  Status: {{.Status}}\n  Ports: {{.Ports}}"
    else
        echo -e "${YELLOW}⚠${NC} Batfish container is NOT running"
        echo "  To start: docker run -d --name batfish -p 9996:9996 batfish/allinone:v2025.07.07"
    fi
else
    echo -e "${RED}✗${NC} Cannot connect to Docker"
    echo "  Make sure Docker Desktop is running with WSL2 integration enabled"
fi
echo ""

# 5. ネットワークチェック
echo "5. Network Connectivity"
echo "-------------------"
if nc -z localhost 9996 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Batfish port 9996 is accessible"
else
    echo -e "${YELLOW}⚠${NC} Batfish port 9996 is NOT accessible"
    echo "  Make sure Batfish container is running"
fi

if nc -z localhost 8000 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Backend port 8000 is already in use"
    echo "  Another process might be using this port"
else
    echo -e "${GREEN}✓${NC} Backend port 8000 is available"
fi
echo ""

# 6. 推奨アクション
echo "=========================================="
echo "Recommendations"
echo "=========================================="

ERRORS=0

if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ACTION REQUIRED]${NC} Install Docker and enable WSL2 integration"
    ERRORS=$((ERRORS+1))
fi

if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}[ACTION REQUIRED]${NC} Install Python 3.11:"
    echo "  sudo add-apt-repository -y ppa:deadsnakes/ppa"
    echo "  sudo apt update"
    echo "  sudo apt install -y python3.11 python3.11-venv python3.11-dev"
    ERRORS=$((ERRORS+1))
fi

if [ ! -d "/mnt/d/batfish_vis/backend/.venv" ]; then
    echo -e "${YELLOW}[RECOMMENDED]${NC} Create Python virtual environment:"
    echo "  cd /mnt/d/batfish_vis/backend"
    echo "  python3.11 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
fi

if [ ! -f "/mnt/d/batfish_vis/backend/.env" ]; then
    echo -e "${YELLOW}[RECOMMENDED]${NC} Create .env file:"
    echo "  cd /mnt/d/batfish_vis/backend"
    echo "  cat > .env << 'EOF'"
    echo "BATFISH_HOST=localhost"
    echo "BATFISH_PORT=9996"
    echo "LOG_LEVEL=INFO"
    echo "EOF"
fi

if [ -z "$BATFISH_RUNNING" ]; then
    echo -e "${YELLOW}[RECOMMENDED]${NC} Start Batfish container:"
    echo "  docker run -d --name batfish -p 9996:9996 batfish/allinone:v2025.07.07"
fi

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Setup looks good! You're ready to start the backend.${NC}"
    echo ""
    echo "To start the backend:"
    echo "  cd /mnt/d/batfish_vis/backend"
    echo "  source .venv/bin/activate"
    echo "  PYTHONPATH=\$PWD uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
fi

echo ""
