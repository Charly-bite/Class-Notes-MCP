#!/bin/bash
echo "🔍 Diagnosticando ubicación de binarios whisper.cpp"

cd ~/whisper_amd_build/whisper.cpp/build

echo "📁 Contenido del directorio build:"
ls -la

echo -e "\n🔍 Buscando ejecutables..."
find . -type f -executable

# Buscar el ejecutable principal
for candidate in "./main" "./whisper" "./examples/main" "./src/main"; do
    if [ -x "$candidate" ]; then
        echo "✅ Encontrado: $candidate"
        sudo cp "$candidate" /usr/local/bin/whisper-amd
        sudo chmod +x /usr/local/bin/whisper-amd
        
        if /usr/local/bin/whisper-amd --help >/dev/null 2>&1; then
            echo "🎉 whisper-amd instalado exitosamente!"
            /usr/local/bin/whisper-amd --help | head -3
            exit 0
        fi
    fi
done

echo "❌ No se encontró ejecutable válido"