#!/bin/sh
# Restore the Ad Astra daily film kit: fonts and the local transcriber.
set -e
KIT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$KIT/fonts"
G=https://raw.githubusercontent.com/google/fonts/main/ofl
[ -s "$KIT/fonts/InterTight.ttf" ] || curl -sSfL -o "$KIT/fonts/InterTight.ttf" "$G/intertight/InterTight%5Bwght%5D.ttf"
[ -s "$KIT/fonts/Inter.ttf" ] || curl -sSfL -o "$KIT/fonts/Inter.ttf" "$G/inter/Inter%5Bopsz,wght%5D.ttf"
[ -s "$KIT/fonts/IBMPlexMono-Bold.ttf" ] || curl -sSfL -o "$KIT/fonts/IBMPlexMono-Bold.ttf" "$G/ibmplexmono/IBMPlexMono-Bold.ttf"
python3 -c "import faster_whisper" 2>/dev/null || pip install --break-system-packages -q faster-whisper
python3 -c "import cv2, numpy, PIL, scipy" 2>/dev/null || pip install --break-system-packages -q opencv-python-headless numpy pillow scipy
echo "kit ready in $KIT"
