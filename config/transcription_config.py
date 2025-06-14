#!/usr/bin/env python3
# Crear config/transcription_settings.yaml

cat > config/transcription_settings.yaml << 'EOF'
transcription_settings:
  default_model: "base"
  default_language: "es"
  default_formats: ["txt", "srt", "vtt"]
  
  # Configuración optimizada para AMD A4-9125
  model_configs:
    tiny:
      threads: 2
      processors: 1
      timeout: 300
      use_case: "tiempo_real"
    base:
      threads: 2  
      processors: 1
      timeout: 600
      use_case: "produccion"
      
  # Idiomas soportados
  languages:
    spanish: "es"
    english: "en"
    auto_detect: "auto"
EOF

echo "✅ Configuración de transcripción creada"
