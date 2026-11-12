#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo '== SHIVANK AI Android setup =='
pkg update -y
pkg install -y python openssl libffi
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-mobile.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo 'Created .env. Edit it with: nano .env'
fi
mkdir -p data workspace
cat <<'MSG'

Setup complete.
1) Edit .env and add freshly rotated API keys locally.
2) Start with: bash termux/start.sh
3) Open http://127.0.0.1:8000 in Chrome on this phone.
MSG
