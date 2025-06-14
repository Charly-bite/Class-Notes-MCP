#!/bin/bash
echo "🔧 SOLUCIONANDO DEPENDENCIAS DE BIBLIOTECAS"
echo "==========================================="

# Ir al directorio de build
cd ~/whisper_amd_build/whisper.cpp/build

echo "📁 Verificando bibliotecas compiladas..."
find . -name "*.so*" -type f

echo -e "\n📦 Instalando bibliotecas necesarias..."

# Instalar libwhisper
if [ -f "./src/libwhisper.so.1.7.5" ]; then
    echo "📚 Instalando libwhisper..."
    sudo cp ./src/libwhisper.so.* /usr/local/lib/
    sudo ln -sf /usr/local/lib/libwhisper.so.1.7.5 /usr/local/lib/libwhisper.so.1
    sudo ln -sf /usr/local/lib/libwhisper.so.1.7.5 /usr/local/lib/libwhisper.so
    echo "✅ libwhisper instalada"
fi

# Instalar libggml
if [ -f "./ggml/src/libggml.so" ]; then
    echo "📚 Instalando libggml..."
    sudo cp ./ggml/src/libggml*.so* /usr/local/lib/
    echo "✅ libggml instalada"
fi

# Actualizar cache de bibliotecas
echo "🔄 Actualizando cache de bibliotecas del sistema..."
sudo ldconfig

echo -e "\n🧪 Verificando instalación corregida..."

# Verificar dependencias ahora
echo "📋 Dependencias actuales de whisper-amd:"
ldd /usr/local/bin/whisper-amd

echo -e "\n🧪 Probando funcionalidad..."
if /usr/local/bin/whisper-amd --help >/dev/null 2>&1; then
    echo "✅ ¡whisper-amd ahora funciona correctamente!"
    
    echo -e "\n📊 Información del binario:"
    /usr/local/bin/whisper-amd --help 2>&1 | head -10
    
    echo -e "\n🎯 CONFIGURACIÓN ESPECÍFICA AMD A4-9125:"
    echo "Threads recomendados: 1-2"
    echo "Modelos recomendados: tiny, base"
    echo "Soporte OpenCL: Habilitado"
    
    echo -e "\n🎉 ¡INSTALACIÓN COMPLETADA!"
    
else
    echo "❌ whisper-amd aún no funciona"
    echo "🔍 Diagnóstico adicional..."
    
    # Verificar si las bibliotecas están en el lugar correcto
    echo "📁 Bibliotecas en /usr/local/lib:"
    ls -la /usr/local/lib/libwhisper* 2>/dev/null || echo "No encontradas"
    ls -la /usr/local/lib/libggml* 2>/dev/null || echo "No encontradas"
    
    # Probar ejecutar directamente con información de error
    echo "🧪 Intentando ejecutar con información de error:"
    /usr/local/bin/whisper-amd --help 2>&1 | head -5
    
    echo -e "\n💡 SOLUCIÓN ALTERNATIVA:"
    echo "Usar el binario directamente desde el directorio build:"
    echo "  cd ~/whisper_amd_build/whisper.cpp/build"
    echo "  export LD_LIBRARY_PATH=./src:./ggml/src:\$LD_LIBRARY_PATH"
    echo "  ./bin/main --help"
fi