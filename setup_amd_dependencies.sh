#!/bin/bash
echo "🔧 Preparando sistema para AMD A4-9125 + whisper.cpp"

# Detectar distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$NAME
    echo "🐧 Distribución: $DISTRO"
fi

# Instalar dependencias
if [[ "$DISTRO" == *"Ubuntu"* ]] || [[ "$DISTRO" == *"Debian"* ]] || [[ "$DISTRO" == *"Parrot"* ]]; then
    sudo apt update
    sudo apt install -y build-essential cmake git pkg-config libopenblas-dev libomp-dev mesa-opencl-icd opencl-headers clinfo espeak-ng
    echo "✅ Dependencias instaladas"
fi

# Verificar OpenCL
echo "🔍 Verificando OpenCL..."
clinfo -l 2>/dev/null || echo "⚠️ OpenCL básico detectado"

echo "✅ Sistema preparado para compilación"