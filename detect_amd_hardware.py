#!/usr/bin/env python3
"""
Detectar hardware AMD y generar configuración optimizada
"""

import subprocess
import platform
import psutil
import re
import json
from pathlib import Path

def quick_amd_detection():
    """Detección rápida de especificaciones AMD"""
    print("🔧 DETECCIÓN RÁPIDA DE HARDWARE AMD")
    print("=" * 50)
    
    # CPU Info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
        if model_match:
            cpu_model = model_match.group(1).strip()
            print(f"🖥️  CPU: {cpu_model}")
            
            # Detectar Zen architecture
            if "ryzen" in cpu_model.lower():
                if any(x in cpu_model for x in ["5000", "6000"]):
                    print("🏗️  Arquitectura: Zen 3 (Excelente rendimiento)")
                elif "4000" in cpu_model:
                    print("🏗️  Arquitectura: Zen 2 (Muy buen rendimiento)")
                elif "3000" in cpu_model:
                    print("🏗️  Arquitectura: Zen 2 (Muy buen rendimiento)")
    except:
        print("⚠️ No se pudo leer información del CPU")
    
    # Cores
    cores_physical = psutil.cpu_count(logical=False)
    cores_logical = psutil.cpu_count(logical=True)
    print(f"🔢 Núcleos: {cores_physical} físicos / {cores_logical} lógicos")
    
    # Memory
    memory_gb = round(psutil.virtual_memory().total / (1024**3), 1)
    print(f"💾 RAM: {memory_gb} GB")
    
    # GPU Detection
    try:
        lspci_output = subprocess.check_output(['lspci'], text=True)
        amd_gpu_found = False
        
        for line in lspci_output.split('\n'):
            if 'VGA' in line and ('AMD' in line or 'ATI' in line):
                print(f"🎮 GPU: {line.split(':')[-1].strip()}")
                amd_gpu_found = True
                break
        
        if not amd_gpu_found:
            print("🎮 GPU: No se detectó GPU AMD discreta")
            
    except:
        print("⚠️ No se pudo detectar GPU")
    
    # Recomendaciones optimización
    print(f"\n⚡ RECOMENDACIONES PARA WHISPER.CPP:")
    print(f"   🧵 Threads recomendados: {min(cores_physical, 6)}")
    
    if memory_gb >= 16:
        print("   📊 Modelo recomendado: small")
    elif memory_gb >= 8:
        print("   📊 Modelo recomendado: base") 
    else:
        print("   📊 Modelo recomendado: tiny")
    
    if cores_physical >= 6:
        print("   🚀 Rendimiento esperado: Excelente")
    elif cores_physical >= 4:
        print("   🚀 Rendimiento esperado: Muy bueno")
    else:
        print("   🚀 Rendimiento esperado: Bueno")

if __name__ == "__main__":
    quick_amd_detection()
