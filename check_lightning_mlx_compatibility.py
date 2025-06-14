#!/usr/bin/env python3
"""
Verificar compatibilidad con Lightning Whisper MLX
"""

import platform
import sys

def check_system_compatibility():
    """Verificar si el sistema puede ejecutar Lightning Whisper MLX"""
    
    print("🔍 Verificando compatibilidad con Lightning Whisper MLX...")
    print("=" * 60)
    
    system = platform.system()
    machine = platform.machine()
    version = platform.version()
    
    print(f"Sistema Operativo: {system}")
    print(f"Arquitectura: {machine}")
    print(f"Versión: {version}")
    
    # Verificar Apple Silicon
    if system == "Darwin" and machine in ["arm64", "aarch64"]:
        print("\n✅ ¡COMPATIBLE! Tu sistema puede ejecutar Lightning Whisper MLX")
        print("🚀 Ventajas esperadas:")
        print("   - Velocidad ultra rápida con Apple MLX")
        print("   - Uso eficiente de memoria unificada")
        print("   - Optimización nativa para Apple Silicon")
        return True
    
    elif system == "Darwin" and machine == "x86_64":
        print("\n⚠️ PARCIALMENTE COMPATIBLE")
        print("💡 Tu Mac Intel puede ejecutar Lightning MLX pero sin optimizaciones:")
        print("   - Rendimiento similar a whisper.cpp")
        print("   - Recomendación: Mantener whisper.cpp")
        return "partial"
    
    else:
        print("\n❌ NO COMPATIBLE")
        print("📝 Lightning Whisper MLX requiere macOS con Apple Silicon")
        print("💡 Recomendaciones para tu sistema:")
        print("   - Continuar con whisper.cpp (excelente opción)")
        print("   - O usar OpenAI Whisper como fallback")
        return False

if __name__ == "__main__":
    compatibility = check_system_compatibility()
    
    if compatibility is True:
        print("\n🎯 PRÓXIMOS PASOS:")
        print("1. Instalar Lightning Whisper MLX")
        print("2. Comparar rendimiento vs whisper.cpp")
        print("3. Integrar como motor principal")
    
    elif compatibility == "partial":
        print("\n🎯 RECOMENDACIÓN:")
        print("1. Completar instalación de whisper.cpp")
        print("2. Probar Lightning MLX como alternativa")
        print("3. Comparar rendimiento")
    
    else:
        print("\n🎯 PLAN ALTERNATIVO:")
        print("1. Completar instalación de whisper.cpp")
        print("2. Optimizar configuración para tu hardware")
        print("3. Considerar actualización a Apple Silicon en el futuro")