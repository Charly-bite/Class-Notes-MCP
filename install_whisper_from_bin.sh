#!/bin/bash
echo "🎯 INSTALANDO WHISPER DESDE DIRECTORIO BIN"
echo "=========================================="

# Ir al directorio de build
cd ~/whisper_amd_build/whisper.cpp/build

echo "📁 Verificando binarios en ./bin/:"
ls -la bin/

echo -e "\n🔧 Instalando binarios principales..."

# Instalar el binario principal (main)
if [ -x "./bin/main" ]; then
    echo "📦 Instalando ./bin/main como whisper-amd..."
    sudo cp ./bin/main /usr/local/bin/whisper-amd
    sudo chmod +x /usr/local/bin/whisper-amd
    echo "✅ whisper-amd instalado"
else
    echo "❌ ./bin/main no encontrado"
    exit 1
fi

# Instalar binarios adicionales útiles
if [ -x "./bin/whisper-cli" ]; then
    echo "📦 Instalando whisper-cli..."
    sudo cp ./bin/whisper-cli /usr/local/bin/whisper-cli-amd
    sudo chmod +x /usr/local/bin/whisper-cli-amd
    echo "✅ whisper-cli-amd instalado"
fi

if [ -x "./bin/whisper-bench" ]; then
    echo "📦 Instalando whisper-bench..."
    sudo cp ./bin/whisper-bench /usr/local/bin/whisper-bench-amd
    sudo chmod +x /usr/local/bin/whisper-bench-amd
    echo "✅ whisper-bench-amd instalado"
fi

# Crear enlaces simbólicos para compatibilidad
sudo ln -sf /usr/local/bin/whisper-amd /usr/local/bin/whisper 2>/dev/null || true

echo -e "\n🧪 Verificando instalación..."

# Verificar whisper-amd
if /usr/local/bin/whisper-amd --help >/dev/null 2>&1; then
    echo "✅ whisper-amd funciona correctamente"
    echo "📍 Ubicación: /usr/local/bin/whisper-amd"
    
    echo -e "\n📊 Información del binario whisper-amd:"
    /usr/local/bin/whisper-amd --help 2>&1 | head -8
    
    echo -e "\n🎯 OPCIONES PRINCIPALES DISPONIBLES:"
    /usr/local/bin/whisper-amd --help 2>&1 | grep -E "(model|language|threads|output)" | head -5
    
else
    echo "❌ Error: whisper-amd no funciona"
    echo "🔧 Verificando dependencias..."
    ldd /usr/local/bin/whisper-amd | head -5
    exit 1
fi

# Verificar whisper-cli si está disponible
if [ -x "/usr/local/bin/whisper-cli-amd" ]; then
    echo -e "\n📋 whisper-cli-amd también disponible para uso alternativo"
fi

echo -e "\n🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo "🔥 whisper-amd listo para AMD A4-9125"
echo "⚡ Compilado con OpenCL y OpenBLAS"
echo "🧵 Optimizado para 2 threads (tu CPU)"

echo -e "\n🚀 PRÓXIMOS PASOS:"
echo "1. Descargar modelos optimizados"
echo "2. Hacer benchmark de rendimiento" 
echo "3. Integrar con ProcessingAgent"

echo -e "\n📋 BINARIOS INSTALADOS:"
echo "  /usr/local/bin/whisper-amd (principal)"
[ -x "/usr/local/bin/whisper-cli-amd" ] && echo "  /usr/local/bin/whisper-cli-amd (alternativo)"
[ -x "/usr/local/bin/whisper-bench-amd" ] && echo "  /usr/local/bin/whisper-bench-amd (benchmark)"