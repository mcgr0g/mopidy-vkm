#!/bin/bash

echo "Setting up audio for DevContainer..."

# PulseAudio exists check
if command -v pulseaudio &> /dev/null; then
    echo "PulseAudio detected"
    # Загрузка TCP модуля для удаленного доступа
    pactl load-module module-native-protocol-tcp \
        auth-ip-acl=127.0.0.1;172.17.0.0/16;192.168.0.0/16 \
        port=4713 \
        auth-anonymous=1 2>/dev/null || echo "Module already loaded"
fi

# PipeWire exists check
if command -v pipewire &> /dev/null; then
    echo "PipeWire detected"
    systemctl --user enable --now pipewire.socket 2>/dev/null || true
    systemctl --user enable --now pipewire-pulse.socket 2>/dev/null || true
fi

echo "Audio setup completed"
exit 0
