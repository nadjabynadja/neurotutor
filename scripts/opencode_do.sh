#!/bin/bash
# OpenCode wrapper for NeuroTutor
# Usage: ./opencode_do "natural language command"

PROJECT_DIR="/root/.openclaw/workspace/NeuroTutor"
OPENCODE_BIN="/root/.opencode/bin/opencode"

cd "$PROJECT_DIR"

# Run OpenCode with the command
$OPENCODE_BIN -m minimax "$PROJECT_DIR" "$1"
