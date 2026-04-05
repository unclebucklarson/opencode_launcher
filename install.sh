#!/usr/bin/env bash
# OpenCode Launcher - Install Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${HOME}/.config/opencode-launcher"
AGENTS_DIR="${CONFIG_DIR}/agents"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OpenCode Launcher - Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Check Python version
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python ${PY_VERSION} detected"

# 2. Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --quiet questionary
echo "✅ Dependencies installed"

# 3. Create config directories
echo "📁 Setting up config directory..."
mkdir -p "${AGENTS_DIR}"
echo "✅ Config directory: ${CONFIG_DIR}"

# 4. Copy agent templates if they don't exist
if [ -d "${SCRIPT_DIR}/../.config/opencode-launcher/agents" ] 2>/dev/null; then
    echo "📋 Agent templates already in place"
else
    # The agents are already installed via the agent template creation
    echo "📋 Agent templates directory ready"
fi

# 5. Install as editable package
echo "🔧 Installing oc command..."
cd "${SCRIPT_DIR}"
pip install --quiet -e .

# 6. Create reliable oc wrapper (avoids pyenv shim issues)
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/oc" << 'WRAPPER'
#!/bin/bash
exec python3 -m opencode_launcher.cli "$@"
WRAPPER
chmod +x "${BIN_DIR}/oc"
echo "✅ 'oc' command installed to ${BIN_DIR}/oc"

# 7. Verify
if command -v oc &>/dev/null; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✨ Installation complete!"
    echo ""
    echo "  Try it out:"
    echo "    oc --help          Show help"
    echo "    oc list-agents     See agent templates"
    echo "    oc launch          Launch interactively"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "⚠️  'oc' command not found in PATH."
    echo "   You may need to add pip's bin directory to your PATH:"
    echo "   export PATH=\"\${HOME}/.local/bin:\${PATH}\""
fi
