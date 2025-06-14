#!/bin/bash
echo "🔧 Instalación rápida para AMD A4-9125"

# Dependencias básicas
sudo apt update
sudo apt install -y build-essential cmake git
sudo apt install -y mesa-opencl-icd clinfo

# Clonar y compilar
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make -j2

echo "✅ Compilado! Ejecuta: ./main --help"