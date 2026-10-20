#!/usr/bin/env bash
# 一次性环境准备：ffmpeg / Python 依赖 / Chromium(HyperFrames 渲染用)
set -e
command -v ffmpeg >/dev/null || { echo "安装 ffmpeg..."; (apt-get update -qq && apt-get install -y -qq ffmpeg fonts-noto-cjk fonts-noto-color-emoji) || brew install ffmpeg; }
VENV="${STUDIO_VENV:-$HOME/.venvs/studio}"
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -U pip numpy faster-whisper
echo "Python 环境: $VENV  (使用 $VENV/bin/python 运行脚本)"
command -v node >/dev/null && echo "node OK: $(node -v)" || echo "缺少 node"
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvpx-vp9 && echo "libvpx-vp9 OK(透明叠层需要)" || echo "警告: ffmpeg 缺少 libvpx-vp9"
echo "HyperFrames 渲染环境检查: npx hyperframes doctor"
