#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────
#  3D Model Generator AI Agent — Setup Script
#  Bu script gerekli tüm bağımlılıkları kurar.
# ───────────────────────────────────────────────────────────

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   3D Model Generator AI Agent Setup    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# ── Python check ──────────────────────────────────────────
echo -e "${YELLOW}[1/6] Python sürümü kontrol ediliyor...${NC}"
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Python bulunamadı. Python 3.9+ kurun.${NC}"
    exit 1
fi
VERSION=$($PYTHON --version 2>&1)
echo -e "${GREEN}✓ $VERSION${NC}"

# ── Virtual environment ───────────────────────────────────
echo ""
echo -e "${YELLOW}[2/6] Sanal ortam hazırlanıyor...${NC}"
cd "$SCRIPT_DIR"
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    echo -e "${GREEN}✓ .venv oluşturuldu${NC}"
else
    echo -e "${GREEN}✓ .venv mevcut${NC}"
fi

# Activate
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
fi

PIP="python -m pip"

# ── Core dependencies ─────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/6] Temel bağımlılıklar kuruluyor...${NC}"
$PIP install --upgrade pip --quiet
$PIP install -r requirements.txt --quiet
echo -e "${GREEN}✓ Temel paketler kuruldu${NC}"

# ── PyTorch ───────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/6] PyTorch kuruluyor...${NC}"
$PIP install torch torchvision --quiet
echo -e "${GREEN}✓ PyTorch kuruldu${NC}"

# ── TripoSR (git clone) ───────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] TripoSR kuruluyor...${NC}"
if [ -d "$SCRIPT_DIR/triposr_lib" ]; then
    echo -e "    Mevcut triposr_lib güncelleniyor..."
    cd "$SCRIPT_DIR/triposr_lib" && git pull --quiet && cd "$SCRIPT_DIR"
else
    echo -e "    GitHub'dan klonlanıyor..."
    git clone --quiet https://github.com/VAST-AI-Research/TripoSR.git "$SCRIPT_DIR/triposr_lib"
fi

echo -e "    TripoSR bağımlılıkları kuruluyor..."
$PIP install git+https://github.com/tatsy/torchmcubes.git --quiet
$PIP install transformers xatlas moderngl --quiet
echo -e "${GREEN}✓ TripoSR kuruldu${NC}"

# ── Directories ───────────────────────────────────────────
echo ""
echo -e "${YELLOW}[6/6] Dizinler oluşturuluyor...${NC}"
mkdir -p "$SCRIPT_DIR/output" "$SCRIPT_DIR/uploads"
echo -e "${GREEN}✓ output/ ve uploads/ dizinleri hazır${NC}"

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Kurulum Tamamlandı! ✓          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Uygulamayı başlatmak için:"
echo -e "  ${BLUE}source .venv/bin/activate${NC}"
echo -e "  ${BLUE}python main.py${NC}"
echo ""
echo -e "Groq API anahtarı almak için (ücretsiz):"
echo -e "  ${BLUE}https://console.groq.com/${NC}"
echo ""
echo -e "${YELLOW}Not: TripoSR modeli (~1.5 GB) ilk dönüştürme işleminde${NC}"
echo -e "${YELLOW}otomatik olarak HuggingFace'den indirilecektir.${NC}"
