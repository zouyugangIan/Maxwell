#!/bin/bash
# Antigravity IDE 启动包装脚本
# 自动清理 Service Worker 缓存以避免 webview 问题

# 清理有问题的缓存目录
rm -rf ~/.config/Antigravity/Service\ Worker \
       ~/.config/Antigravity/GPUCache \
       ~/.config/Antigravity/Cache \
       ~/.config/Antigravity/Code\ Cache \
       2>/dev/null

# 启动 Antigravity
exec /usr/bin/antigravity "$@"
