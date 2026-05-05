#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. 파이썬 의존성 설치
pip install flask google-generativeai python-dotenv

# 2. Bun 설치
curl -fsSL https://bun.sh/install | bash
export PATH="/opt/render/.bun/bin:$PATH"

# 3. MCP 폴더 의존성 설치
cd mcp-google-sheets
bun install
cd ..