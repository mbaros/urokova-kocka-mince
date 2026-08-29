#!/usr/bin/env bash
# Download the priming video once and keep it next to the app data, so the
# check-in never depends on YouTube's embed rules (error 153 etc.).
#
#   deploy/fetch-video.sh https://youtu.be/faTGTgid8Uc
#
# Needs yt-dlp (installs a standalone binary into ~/.local/bin if missing) and ffmpeg.
# Output: data/video/priming.mp4 (served by the app at media/priming.mp4).
set -euo pipefail
cd "$(dirname "$0")/.."
URL="${1:?usage: deploy/fetch-video.sh <youtube-url>}"
mkdir -p data/video ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"
if ! command -v yt-dlp >/dev/null; then
  echo "→ installing yt-dlp into ~/.local/bin"
  curl -sSL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o ~/.local/bin/yt-dlp
  chmod +x ~/.local/bin/yt-dlp
fi
yt-dlp -U >/dev/null 2>&1 || true
yt-dlp --no-playlist -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b" \
  --merge-output-format mp4 -o data/video/priming.tmp.mp4 "$URL"
mv -f data/video/priming.tmp.mp4 data/video/priming.mp4
ls -la data/video/priming.mp4
echo "✓ video ready — the app serves it as media/priming.mp4 (no restart needed)"
