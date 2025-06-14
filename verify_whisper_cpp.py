#!/usr/bin/env python3
"""
Script para verificar la instalación de whisper.cpp
"""

import subprocess
import os
import sys
from pathlib import Path

def check_whisper_cpp_binary():
    """Verificar si el binario whisper está disponible"""
    try:
        result = subprocess.run(['whisper', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ whisper.cpp binario encontrado")
            return True
        else:
            print("❌ whisper.cpp no responde correctamente")
            return False
    except FileNotFoundError:
        print("❌ whisper.cpp no encontrado en PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ whisper.cpp no responde (timeout)")
        return False

def check_whisper_models():
    """Verificar modelos disponibles"""
    model_paths = [
        Path.home() / ".cache" / "whisper",
        Path("/usr/local/share/whisper"),
        Path("./models")
    ]
    
    for path in model_paths:
        if path.exists():
            models = list(path.glob("*.bin"))
            if models:
                print(f"✅ Modelos encontrados en {path}:")
                for model in models:
                    print(f"   - {model.name}")
                return True
    
    print("⚠️ No se encontraron modelos de whisper.cpp")
    return False

def test_basic_transcription():
    """Probar transcripción básica si hay audio de prueba"""
    test_files = [
        "recordings/raw/test*.wav",
        "test_audio.wav"
    ]
    
    for pattern in test_files:
        files = list(Path(".").glob(pattern))
        if files:
            test_file = files[0]
            print(f"🎯 Probando transcripción con {test_file}")
            try:
                result = subprocess.run([
                    'whisper', str(test_file),
                    '--language', 'es',
                    '--output_format', 'txt',
                    '--model', 'base'
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print("✅ Transcripción de prueba exitosa")
                    return True
                else:
                    print(f"❌ Error en transcripción: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print("❌ Transcripción timeout")
                return False
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    print("⚠️ No hay archivos de audio para probar transcripción")
    return None

if __name__ == "__main__":
    print("🔍 Verificando instalación de whisper.cpp...")
    print("=" * 50)
    
    # Verificaciones
    binary_ok = check_whisper_cpp_binary()
    models_ok = check_whisper_models()
    
    if binary_ok:
        transcription_test = test_basic_transcription()
        
        print("\n" + "=" * 50)
        print("📊 RESUMEN:")
        print(f"  Binario: {'✅' if binary_ok else '❌'}")
        print(f"  Modelos: {'✅' if models_ok else '❌'}")
        if transcription_test is not None:
            print(f"  Transcripción: {'✅' if transcription_test else '❌'}")
        
        if binary_ok and models_ok:
            print("\n🎉 whisper.cpp está listo para usar!")
        else:
            print("\n⚠️ Instalación incompleta")
    else:
        print("\n❌ whisper.cpp no está instalado correctamente")
        sys.exit(1)