#!/bin/bash

##############################################################################
# lineage-skill -- Claude Code / Codex / OpenClaw Skill installer
#
# Copies this repository into the target agent skill directory and installs
# Python dependencies needed by the local course-processing scripts.
#
# Usage: bash install_as_skill.sh [--target auto|claude|codex|openclaw]
##############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}(i)  $1${NC}"; }
print_success() { echo -e "${GREEN}[OK] $1${NC}"; }
print_warning() { echo -e "${YELLOW}(!)  $1${NC}"; }
print_error() { echo -e "${RED}[X] $1${NC}"; }
print_header() { echo ""; echo "========================================"; echo "$1"; echo "========================================"; echo ""; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

TARGET="auto"

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)
                TARGET="${2:-}"
                shift 2
                ;;
            --target=*)
                TARGET="${1#*=}"
                shift
                ;;
            *)
                print_error "Unknown argument: $1"
                echo "Usage: bash install_as_skill.sh [--target auto|claude|codex|openclaw]"
                exit 1
                ;;
        esac
    done
}

resolve_install_target() {
    case "$TARGET" in
        auto)
            if [ -n "${CODEX_HOME:-}" ]; then
                echo "codex"
            elif [ -d "$HOME/.claude" ]; then
                echo "claude"
            elif [ -d "$HOME/.codex" ]; then
                echo "codex"
            else
                echo "claude"
            fi
            ;;
        claude|codex|openclaw)
            echo "$TARGET"
            ;;
        *)
            print_error "Unsupported target: $TARGET"
            echo "Options: auto | claude | codex | openclaw"
            exit 1
            ;;
    esac
}

resolve_skill_dir() {
    case "$1" in
        claude)
            echo "$HOME/.claude/skills/lineage-skill"
            ;;
        codex)
            echo "${CODEX_HOME:-$HOME/.codex}/skills/lineage-skill"
            ;;
        openclaw)
            echo "$HOME/skills/lineage-skill"
            ;;
    esac
}

resolve_agent_label() {
    case "$1" in
        claude)
            echo "Claude Code"
            ;;
        codex)
            echo "Codex"
            ;;
        openclaw)
            echo "OpenClaw"
            ;;
    esac
}

main() {
    parse_args "$@"

    print_header "lineage-skill -- install"

    INSTALL_TARGET="$(resolve_install_target)"
    SKILL_DIR="$(resolve_skill_dir "$INSTALL_TARGET")"
    AGENT_LABEL="$(resolve_agent_label "$INSTALL_TARGET")"

    print_info "Target agent: $AGENT_LABEL"
    print_info "Target directory: $SKILL_DIR"

    if [ -d "$SKILL_DIR" ]; then
        print_warning "Skill directory already exists: $SKILL_DIR"
        read -p "Overwrite it? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cancelled"
            exit 0
        fi
        if [ -f "$SKILL_DIR/.env" ]; then
            cp "$SKILL_DIR/.env" "/tmp/lineage-skill.env.bak"
            print_info "Backed up existing .env to /tmp/lineage-skill.env.bak"
        fi
        rm -rf "$SKILL_DIR"
    fi

    print_info "Creating skill directory..."
    mkdir -p "$SKILL_DIR"
    print_success "Directory created"

    print_info "Copying skill files..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    rsync -a \
        --exclude='.git' \
        --exclude='.env' \
        --include='.env.example' \
        --exclude='.env.*' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='env' \
        --exclude='__pycache__' \
        --exclude='dist' \
        --exclude='output' \
        --exclude='outputs' \
        --exclude='tmp' \
        --exclude='logs' \
        --exclude='*/transcripts' \
        --exclude='*/analysis' \
        --exclude='*/documents' \
        --exclude='*/course_package.json' \
        --exclude='*/course_distillation_*.md' \
        --exclude='*/course_distillation_*.json' \
        --exclude='*/lesson_summaries.json' \
        --exclude='*/full_transcript.md' \
        "$SCRIPT_DIR/" "$SKILL_DIR/"

    print_success "Files copied"

    if [ -f "/tmp/lineage-skill.env.bak" ]; then
        mv "/tmp/lineage-skill.env.bak" "$SKILL_DIR/.env"
        print_success "Restored existing .env"
    fi

    print_info "Checking Python..."
    if ! command_exists python3; then
        print_error "python3 is required. Install Python 3.11+ first."
        exit 1
    fi
    print_success "Python: $(python3 --version)"

    print_info "Installing Python dependencies..."
    if command_exists pip3; then
        pip3 install -q -r "$SKILL_DIR/requirements.txt"
    else
        pip install -q -r "$SKILL_DIR/requirements.txt"
    fi
    print_success "Dependencies installed"

    print_header "Environment setup"
    print_info "No .env was created automatically."
    print_info "Prefer agent config or system env vars for API keys."
    print_info "For standalone script fallback, copy .env.example to a private .env in the skill directory."

    print_header "Done"
    print_success "Installed to $SKILL_DIR"
    echo ""
    print_info "Restart $AGENT_LABEL so it can load the skill."
    print_info "Then say: 'Use lineage-skill to turn my course videos and PDFs into a course expert skill.'"
    echo ""
}

trap 'print_error "Install failed"; exit 1' ERR

main "$@"
