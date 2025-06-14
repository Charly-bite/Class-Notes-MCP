#!/usr/bin/env python3
"""
Benchmark específico para sistemas AMD
"""

import time
import subprocess
import json
from pathlib import Path

def benchmark_amd_whisper():
    """Ejecutar benchmark optimizado para AMD"""
    
    # Cargar configuración del sistema
    profile_path = Path("system_profile_amd.json")
    if not profile_path.exists():
        print("❌ Ejecuta primero el detector AMD")
        return
    
    with open(profile_path) as f:
        profile = json.load(f)
    
    cpu_cores = profile["system_info"]["cpu"].get("physical_cores", 4)
    
    # Diferentes configuraciones para probar
    test_configs = [
        {"threads": 2, "model": "base", "name": "Conservador"},
        {"threads": cpu_cores // 2, "model": "base", "name": "Balanceado"},
        {"threads": cpu_cores, "model": "base", "name": "Máximo CPU"},
        {"threads": cpu_cores, "model": "small", "name": "Modelo Grande"}
    ]
    
    # Crear audio de prueba si no existe
    if not Path("test_audio.wav").exists():
        print("🎵 Creando audio de prueba...")
        subprocess.run([
            "espeak-ng", "-s", "150", "-v", "es",
            "-w", "test_audio.wav",
            "Esta es una prueba de rendimiento para procesadores AMD con whisper punto cpp"
        ])
    
    results = []
    
    for config in test_configs:
        print(f"\n🧪 Probando configuración: {config['name']}")
        print(f"   Threads: {config['threads']}, Modelo: {config['model']}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run([
                "whisper", "test_audio.wav",
                "--threads", str(config["threads"]),
                "--model", config["model"],
                "--language", "es",
                "--output_format", "txt"
            ], capture_output=True, text=True, timeout=120)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result.returncode == 0:
                results.append({
                    "config": config,
                    "processing_time": processing_time,
                    "success": True
                })
                print(f"   ⏱️ Tiempo: {processing_time:.2f}s")
            else:
                print(f"   ❌ Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout (>120s)")
    
    # Mostrar resultados
    print("\n📊 RESULTADOS DEL BENCHMARK AMD")
    print("=" * 40)
    
    if results:
        best_config = min(results, key=lambda x: x["processing_time"])
        
        for result in sorted(results, key=lambda x: x["processing_time"]):
            config = result["config"]
            time_taken = result["processing_time"]
            
            marker = "🏆" if result == best_config else "📈"
            print(f"{marker} {config['name']}: {time_taken:.2f}s")
            print(f"    Threads: {config['threads']}, Modelo: {config['model']}")
        
        print(f"\n🎯 CONFIGURACIÓN ÓPTIMA DETECTADA:")
        print(f"   {best_config['config']['name']}")
        print(f"   Threads: {best_config['config']['threads']}")
        print(f"   Modelo: {best_config['config']['model']}")
        print(f"   Tiempo: {best_config['processing_time']:.2f}s")
        
        # Guardar configuración óptima
        optimal_config = {
            "optimal_threads": best_config['config']['threads'],
            "optimal_model": best_config['config']['model'],
            "benchmark_time": best_config['processing_time'],
            "all_results": results
        }
        
        with open("amd_benchmark_results.json", "w") as f:
            json.dump(optimal_config, f, indent=2)
        
        print("💾 Resultados guardados en: amd_benchmark_results.json")
    
    else:
        print("❌ No se obtuvieron resultados válidos")

if __name__ == "__main__":
    benchmark_amd_whisper()
