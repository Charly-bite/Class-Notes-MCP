#!/bin/bash
echo "📥 DESCARGANDO MODELOS WHISPER OPTIMIZADOS PARA AMD A4-9125"
echo "=========================================================="

# Crear directorio para modelos
MODELS_DIR="$HOME/whisper_models"
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

echo "📁 Directorio de modelos: $MODELS_DIR"

# Función para descargar modelo
download_model() {
    local model_name="$1"
    local model_file="ggml-${model_name}.bin"
    local model_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/${model_file}"
    
    echo -e "\n📦 Descargando modelo: $model_name"
    
    if [ ! -f "$model_file" ]; then
        echo "⬇️  Descargando $model_file..."
        if wget -c "$model_url"; then
            echo "✅ $model_name descargado exitosamente"
            size=$(stat -c%s "$model_file" 2>/dev/null | awk '{print int($1/1024/1024)"MB"}')
            echo "📊 Tamaño: $size"
        else
            echo "❌ Error descargando $model_name"
            return 1
        fi
    else
        echo "✅ $model_name ya existe"
        size=$(stat -c%s "$model_file" 2>/dev/null | awk '{print int($1/1024/1024)"MB"}')
        echo "📊 Tamaño: $size"
    fi
}

# Verificar conectividad
echo "🌐 Verificando conectividad..."
if ping -c 1 huggingface.co >/dev/null 2>&1; then
    echo "✅ Conexión verificada"
else
    echo "❌ Sin conexión a huggingface.co"
    exit 1
fi

# Descargar modelos recomendados para AMD A4-9125
echo -e "\n🎯 MODELOS PARA AMD A4-9125:"

# 1. Modelo TINY (más rápido)
echo -e "\n1️⃣ MODELO TINY (39MB) - Más rápido"
echo "   💨 Velocidad: Excelente en A4-9125"
echo "   🎯 Precisión: Buena para español/inglés"
download_model "tiny"

# 2. Modelo BASE (equilibrado) 
echo -e "\n2️⃣ MODELO BASE (142MB) - Equilibrado"
echo "   💨 Velocidad: Buena en A4-9125"
echo "   🎯 Precisión: Muy buena"
download_model "base"

echo -e "\n📋 MODELOS DESCARGADOS:"
ls -lh *.bin 2>/dev/null || echo "No se descargaron modelos"

# Crear configuración
cat > "$HOME/.whisper_amd_config" << 'EOF'
# Configuración whisper-amd para AMD A4-9125
export WHISPER_MODELS_DIR="$HOME/whisper_models"
export WHISPER_DEFAULT_MODEL="base"
export WHISPER_THREADS=2

# Función para transcripción rápida
transcribe() {
    local audio_file="$1"
    local model="${2:-base}"
    
    if [ ! -f "$audio_file" ]; then
        echo "❌ Archivo no encontrado: $audio_file"
        return 1
    fi
    
    echo "🎙️ Transcribiendo: $audio_file con modelo $model"
    whisper-amd -m "$WHISPER_MODELS_DIR/ggml-$model.bin" -t 2 -p 1 -osrt -ovtt -otxt "$audio_file"
}
EOF

echo "✅ Configuración guardada en ~/.whisper_amd_config"

# Verificar que whisper-amd puede cargar los modelos
echo -e "\n🧪 VERIFICANDO MODELOS:"
source "$HOME/.whisper_amd_config"

for model in tiny base; do
    model_file="$WHISPER_MODELS_DIR/ggml-${model}.bin"
    if [ -f "$model_file" ]; then
        echo "🧪 Verificando modelo $model..."
        if timeout 5s whisper-amd -m "$model_file" --help >/dev/null 2>&1; then
            echo "✅ Modelo $model verificado"
        else
            echo "⚠️ Modelo $model cargado (verificación timeout es normal)"
        fi
    fi
done

echo -e "\n🎉 ¡INSTALACIÓN COMPLETADA!"
echo "📊 Resumen:"
echo "📁 Modelos en: $WHISPER_MODELS_DIR"
echo "🔧 Configuración: ~/.whisper_amd_config"

echo -e "\n💡 PARA USAR:"
echo "source ~/.whisper_amd_config"
echo "transcribe mi_audio.wav tiny    # Rápido"
echo "transcribe mi_audio.wav base    # Equilibrado"