#!/usr/bin/env bash
# Download the priming video once and keep it next to the app data, so the
# check-in never depends on YouTube's embed rules (error 153 etc.).
#
#   deploy/fetch-video.sh https://youtu.be/faTGTgid8Uc
#
# Needs yt-dlp (installs a standalone binary into ~/.local/bin if missing) and ffmpeg.
# NOTE: YouTube blocks datacenter IPs ("sign in to confirm you're not a bot") — if that
# happens on the server, run this on a laptop and scp data/video/priming.mp4 over.
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
# H.264 only — iPhones cannot play AV1/VP9 in <video>. (YouTube's 720p mp4 is often AV1.)
yt-dlp --no-playlist -f "bv*[vcodec^=avc1][height<=720]+ba[ext=m4a]/b[vcodec^=avc1][height<=720]/bv*[height<=720]+ba/b" \
  --merge-output-format mp4 -o data/video/priming.tmp.mp4 "$URL"
codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 data/video/priming.tmp.mp4 2>/dev/null || echo unknown)
if [ "$codec" != "h264" ]; then
  echo "→ video is $codec, transcoding to H.264 for iPhone"
  ffmpeg -y -v error -i data/video/priming.tmp.mp4 -c:v libx264 -preset veryfast -crf 24 -profile:v main -pix_fmt yuv420p -vf scale=-2:720 \
    -c:a aac -b:a 96k -movflags +faststart data/video/priming.h264.mp4
  mv -f data/video/priming.h264.mp4 data/video/priming.tmp.mp4
fi
mv -f data/video/priming.tmp.mp4 data/video/priming.mp4
ls -la data/video/priming.mp4
echo "✓ video ready — the app serves it as media/priming.mp4 (no restart needed)"
