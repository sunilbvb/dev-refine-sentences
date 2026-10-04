#!/usr/bin/env bash
# ==============================================================================
# Setup Local Offline AI (Ollama) for Sentence Refiner
# Supports Linux and macOS
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Setting up Local Offline AI (Ollama) for dev-refine-sentences ===${NC}"

# 1. Check if Ollama is installed
if ! command -v ollama >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] Ollama is not installed.${NC}"
    echo -e "Installing Ollama official binary via https://ollama.com/install.sh..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}[ERROR] curl not found. Please install curl or install Ollama manually from https://ollama.com${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[OK] Ollama binary is installed: $(which ollama)${NC}"
fi

# 2. Check if Ollama daemon is running
echo -e "\nChecking if Ollama daemon is active..."
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] Ollama daemon is not running on 127.0.0.1:11434.${NC}"
    echo "Starting Ollama service..."
    if command -v systemctl >/dev/null 2>&1; then
        systemctl start ollama 2>/dev/null || systemctl --user start ollama 2>/dev/null || true
    fi
    # If still not reachable, start in background
    if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        echo "Launching ollama serve in background..."
        nohup ollama serve >/dev/null 2>&1 &
        sleep 3
    fi
fi

if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}[OK] Ollama daemon is online at http://127.0.0.1:11434${NC}"
else
    echo -e "${RED}[!] Could not start Ollama daemon automatically. Run 'ollama serve' in a separate terminal.${NC}"
    exit 1
fi

# 3. Pull recommended lightweight model (qwen2.5:0.5b - 390MB, sub-second responses)
MODEL="qwen2.5:0.5b"
echo -e "\nEnsuring model '${MODEL}' is available..."
ollama pull "${MODEL}"

# 4. Verify refiner integration
echo -e "\nVerifying refiner with Ollama..."
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_OUT=$(python3 "${REPO_DIR}/main.py" --mode cli --engine ollama --text "he go to store and buyed apples" 2>/dev/null || true)

if [ -n "$TEST_OUT" ]; then
    echo -e "${GREEN}[SUCCESS] Test refinement result:${NC} ${TEST_OUT}"
    echo -e "\n${GREEN}✔ Local offline AI is ready! Sentence Refiner will automatically use Ollama.${NC}"
else
    echo -e "${YELLOW}[!] Model pulled, but CLI test timed out or returned empty. Check 'ollama list'.${NC}"
fi
