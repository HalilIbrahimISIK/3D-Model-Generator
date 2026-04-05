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

# ── TripoSR → TRELLIS ────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] TRELLIS kuruluyor...${NC}"
if [ -d "$SCRIPT_DIR/trellis_lib" ]; then
    echo -e "    Mevcut trellis_lib mevcut ✓"
else
    echo -e "    GitHub'dan klonlanıyor (microsoft/TRELLIS)..."
    git clone --quiet https://github.com/microsoft/TRELLIS.git "$SCRIPT_DIR/trellis_lib"
    rm -rf "$SCRIPT_DIR/trellis_lib/.git"
fi

echo -e "    TRELLIS bağımlılıkları kuruluyor..."
$PIP install easydict imageio imageio-ffmpeg plyfile jaxtyping einops ninja --quiet
echo -e "${GREEN}✓ TRELLIS kuruldu${NC}"
echo ""
echo -e "${YELLOW}⚠️  TRELLIS CUDA GPU gerektirir. CUDA kurulumu için:${NC}"
echo -e "    ${BLUE}pip install spconv-cu118   # CUDA 11.8${NC}"
echo -e "    ${BLUE}pip install spconv-cu121   # CUDA 12.1${NC}"
echo -e "    (CUDA sürümünüze uygun olanı seçin)"

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
