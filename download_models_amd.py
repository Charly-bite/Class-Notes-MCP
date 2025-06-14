#!/usr/bin/env python3
"""
Descarga y configuración de modelos optimizada para AMD A4-9125
"""

import subprocess
import requests
import os
from pathlib import Path

def download_optimal_models():
    """Descargar modelos óptimos para A4-9125"""
    
    print("📥 Descargando modelos optimizados para AMD A4-9125...")
    
    # Crear directorio de modelos
    models_dir = Path.home() / ".cache" / "whisper"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Modelos recomendados para A4-9125
    recommended_models = [
        {
            "name": "base",
            "size": "~142MB",
            "description": "Modelo principal recomendado",
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
            "priority": 1
        },
        {
            "name": "small", 
            "size": "~466MB",
            "description": "Mejor calidad (aprovecha la RAM abundante)",
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
            "priority": 2
        }
    ]
    
    for model in recommended_models:
        model_file = models_dir / f"ggml-{model['name']}.bin"
        
        if model_file.exists():
            print(f"✅ Modelo {model['name']} ya existe")
            continue
            
        print(f"\n📦 Descargando modelo {model['name']} ({model['size']})...")
        print(f"📝 {model['description']}")
        
        try:
            response = requests.get(model['url'], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r[{'='*int(progress//5)}{' '*(20-int(progress//5))}] {progress:.1f}%", end='', flush=True)
            
            print(f"\n✅ Modelo {model['name']} descargado exitosamente")
            
        except Exception as e:
            print(f"\n❌ Error descargando {model['name']}: {e}")
            if model_file.exists():
                model_file.unlink()
    
    print("\n🎯 MODELOS INSTALADOS:")
    for model_file in models_dir.glob("ggml-*.bin"):
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"   📁 {model_file.name}: {size_mb:.1f} MB")

def test_transcription():
    """Probar transcripción con configuración optimizada"""
    
    print("\n🧪 PROBANDO TRANSCRIPCIÓN...")
    
    # Crear audio de prueba específico para español
    test_audio = "test_amd_a4.wav"
    
    if not Path(test_audio).exists():
        print("🎵 Creando audio de prueba...")
        try:
            subprocess.run([
                "espeak-ng", "-s", "140", "-v", "es-es",
                "-w", test_audio,
                "Hola, esta es una prueba de transcripción optimizada para procesador AMD A4-9125 con gráficos Radeon R3"
            ], check=True)
            print("✅ Audio de prueba creado")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ espeak-ng no disponible. Instalar con: sudo apt install espeak-ng")
            return
    
    # Probar con modelo base
    print("\n🔍 Probando modelo base...")
    try:
        result = subprocess.run([
            "whisper-amd", test_audio,
            "--model", "base",
            "--language", "es", 
            "--threads", "2",
            "--output_format", "txt"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Transcripción base exitosa")
        else:
            print(f"❌ Error en transcripción base: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout en transcripción base")
    except FileNotFoundError:
        print("❌ whisper-amd no encontrado. Ejecutar instalación primero.")

if __name__ == "__main__":
    download_optimal_models()
    test_transcription()
