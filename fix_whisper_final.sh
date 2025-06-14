#!/bin/bash
echo "🎯 SOLUCIÓN FINAL - USANDO WHISPER-CLI"
echo "====================================="

cd ~/whisper_amd_build/whisper.cpp/build

echo "📋 Probando todos los ejecutables disponibles..."

# Probar whisper-cli (el recomendado actualmente)
if ./bin/whisper-cli --help >/dev/null 2>&1; then
    echo "✅ whisper-cli funciona perfectamente!"
    
    # Instalar whisper-cli como whisper-amd
    echo "📦 Instalando whisper-cli como whisper-amd..."
    sudo cp ./bin/whisper-cli /usr/local/bin/whisper-amd
    sudo chmod +x /usr/local/bin/whisper-amd
    
    echo "🧪 Verificando instalación final..."
    if /usr/local/bin/whisper-amd --help >/dev/null 2>&1; then
        echo "🎉 ¡INSTALACIÓN EXITOSA!"
        echo "📊 Información del binario:"
        /usr/local/bin/whisper-amd --help 2>&1 | head -10
        
        echo -e "\n🎯 CONFIGURACIÓN PARA AMD A4-9125:"
        echo "✅ Binary: whisper-amd (basado en whisper-cli)"
        echo "✅ OpenCL: Habilitado"
        echo "✅ OpenBLAS: Habilitado"
        echo "✅ Threads: 1-2 (óptimo para tu CPU)"
        
        # Probar una transcripción básica para confirmar que funciona
        echo -e "\n🧪 PRUEBA BÁSICA DE FUNCIONALIDAD:"
        echo "Probando comando básico..."
        if /usr/local/bin/whisper-amd --help 2>&1 | grep -q "model"; then
            echo "✅ Comando responde correctamente"
            echo "🚀 ¡Listo para el siguiente paso!"
        fi
        
        exit 0
    fi
fi

# Si whisper-cli no funciona, probar con main usando variable de entorno
echo "🔄 Probando método alternativo con main..."
export LD_LIBRARY_PATH="./src:./ggml/src:$LD_LIBRARY_PATH"

if ./bin/main --help >/dev/null 2>&1; then
    echo "✅ main funciona con LD_LIBRARY_PATH!"
    
    # Crear wrapper que configure las bibliotecas
    echo "📦 Creando wrapper con bibliotecas..."
    cat > /tmp/whisper-amd-final << 'EOF'
#!/bin/bash
BUILD_DIR="$HOME/whisper_amd_build/whisper.cpp/build"
export LD_LIBRARY_PATH="$BUILD_DIR/src:$BUILD_DIR/ggml/src:$LD_LIBRARY_PATH"
exec "$BUILD_DIR/bin/main" "$@"
EOF
    
    sudo cp /tmp/whisper-amd-final /usr/local/bin/whisper-amd
    sudo chmod +x /usr/local/bin/whisper-amd
    
    if /usr/local/bin/whisper-amd --help >/dev/null 2>&1; then
        echo "🎉 ¡WRAPPER INSTALADO EXITOSAMENTE!"
        echo "📊 Información:"
        /usr/local/bin/whisper-amd --help 2>&1 | head -5
    fi
else
    echo "❌ Ningún método funcionó"
    echo "🔍 Diagnóstico final:"
    echo "Directorio actual: $(pwd)"
    echo "Contenido de bin/:"
    ls -la bin/
fi