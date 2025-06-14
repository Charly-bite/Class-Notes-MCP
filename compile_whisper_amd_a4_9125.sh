#!/bin/bash
echo "🔨 Compilando whisper.cpp para AMD A4-9125"
echo "=========================================="

# Crear directorio de trabajo
WORK_DIR="$HOME/whisper_amd_build"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Clonar whisper.cpp si no existe
if [ ! -d "whisper.cpp" ]; then
    echo "📥 Clonando whisper.cpp..."
    git clone https://github.com/ggerganov/whisper.cpp.git
    cd whisper.cpp
else
    echo "📂 Usando whisper.cpp existente..."
    cd whisper.cpp
    git pull origin master
fi

# Crear directorio de build
mkdir -p build
cd build

echo "⚙️ Configurando CMake para AMD A4-9125..."

# Configuración CMake específica para A4-9125 (arquitectura Excavator/btver2)
cmake -DCMAKE_BUILD_TYPE=Release \
      -DWHISPER_OPENBLAS=ON \
      -DWHISPER_OPENCL=ON \
      -DWHISPER_OPENMP=ON \
      -DCMAKE_C_FLAGS="-O2 -march=btver2 -mtune=btver2 -mfma -mavx -msse4.2" \
      -DCMAKE_CXX_FLAGS="-O2 -march=btver2 -mtune=btver2 -mfma -mavx -msse4.2" \
      -DCMAKE_INSTALL_PREFIX="/usr/local" \
      ..

if [ $? -ne 0 ]; then
    echo "❌ Error en configuración CMake"
    exit 1
fi

echo "🔨 Compilando con 2 threads (óptimo para A4-9125)..."
make -j2

if [ $? -ne 0 ]; then
    echo "❌ Error en compilación"
    exit 1
fi

echo "✅ Compilación exitosa!"

# Instalar binarios con nombres específicos para AMD
echo "📦 Instalando whisper-amd..."
sudo cp bin/whisper /usr/local/bin/whisper-amd
sudo cp bin/main /usr/local/bin/whisper-main-amd
sudo cp bin/bench /usr/local/bin/whisper-bench-amd 2>/dev/null || true

# Crear enlaces simbólicos para compatibilidad
sudo ln -sf /usr/local/bin/whisper-amd /usr/local/bin/whisper 2>/dev/null || true

# Verificar instalación
echo "🧪 Verificando instalación..."
if /usr/local/bin/whisper-amd --help >/dev/null 2>&1; then
    echo "✅ whisper-amd instalado correctamente"
    echo "📍 Ubicación: /usr/local/bin/whisper-amd"
    
    # Mostrar versión y características
    echo "📊 Información del binario:"
    /usr/local/bin/whisper-amd --help | head -5
else
    echo "❌ Error: whisper-amd no funciona correctamente"
    exit 1
fi

echo "🎉 Instalación de whisper-amd completada!"
echo "🔥 Optimizado específicamente para AMD A4-9125 + Radeon R3"
echo "⚡ Compilado con soporte OpenCL y OpenBLAS"