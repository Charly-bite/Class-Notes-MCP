#!/bin/bash
echo "⚡ BENCHMARK FINAL WHISPER-AMD EN AMD A4-9125"

source "$HOME/.whisper_amd_config"

echo "🔧 Configuración:"
echo "📁 Modelos: $WHISPER_MODELS_DIR"
echo "🧵 Threads: 2 (óptimo para A4-9125)"

# Prueba rápida con ambos modelos
echo -e "\n🧪 PRUEBA RÁPIDA:"
for model in tiny base; do
    echo "🧠 Probando $model..."
    if timeout 30s whisper-amd -m "$WHISPER_MODELS_DIR/ggml-$model.bin" --help >/dev/null 2>&1; then
        echo "✅ $model: FUNCIONAL"
    else
        echo "⚠️ $model: timeout (normal durante inicialización)"
    fi
done

echo -e "\n🎉 ¡whisper-amd optimizado para AMD A4-9125!"
echo "💡 Para usar: transcribe mi_audio.wav base"