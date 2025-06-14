from agents.recording_agent import RecordingAgent
from agents.transcription_agent import TranscriptionAgent
from pathlib import Path
import time

print('🎙️ TEST DE GRABACIÓN CON MÁXIMA SENSIBILIDAD')
print('='*55)
print()
print('⚠️ CONFIGURACIÓN OPTIMIZADA:')
print('   ✅ Volumen del micrófono: 150%')
print('   ✅ Chunk size aumentado: 4096')
print('   ✅ Dispositivo: [4] default (PulseAudio)')
print()
print('🎯 INSTRUCCIONES ESPECÍFICAS:')
print('   • Ponte MUY CERCA del micrófono (2-5cm)')
print('   • Habla CLARAMENTE y en voz ALTA')
print('   • NO susurres, habla con PROYECCIÓN')
print()
print('📝 FRASE DE PRUEBA (di exactamente esto):')
print('   "PROBANDO MICRÓFONO PARA CIBERSEGURIDAD"')
print()

input('🎯 Presiona ENTER cuando estés listo para grabar (7 segundos)...')
print()

# Configurar recording agent con parámetros optimizados
agent = RecordingAgent()
agent.CHUNK = 4096  # Chunk más grande
agent.RATE = 44100  # Asegurar sample rate estándar

print('⏱️ Iniciando en 3 segundos...')
for i in range(3, 0, -1):
    print(f'   {i}...', flush=True)
    time.sleep(1)

if agent.start_recording('test_max_volume', input_device_index=4):
    print()
    print('🔴 GRABANDO 7 segundos...')
    print('🎙️ ¡HABLA AHORA MUY FUERTE!')
    print('📢 "PROBANDO MICRÓFONO PARA CIBERSEGURIDAD"')
    
    for i in range(7):
        chunk_data = agent.record_chunk()
        bars = '█' * (i + 1) + '░' * (6 - i)
        print(f'⏱️ [{bars}] {i+1}/7s - ¡SIGUE HABLANDO FUERTE!', end='\r', flush=True)
        time.sleep(1)
    
    result = agent.stop_recording()
    print()
    print()
    
    if result:
        audio_path = Path(result['path'])
        file_size = audio_path.stat().st_size
        duration = result['metadata']['duration_seconds']
        
        print(f'📊 ANÁLISIS DE GRABACIÓN:')
        print(f'   📁 Archivo: {audio_path.name}')
        print(f'   📏 Tamaño: {file_size:,} bytes')
        print(f'   ⏱️ Duración: {duration:.2f}s')
        
        # Calcular ratio de contenido esperado vs real
        expected_size = duration * 44100 * 2  # 44.1kHz * 16bit = 2 bytes per sample
        ratio = file_size / expected_size if expected_size > 0 else 0
        
        print(f'   📈 Ratio de contenido: {ratio:.3f}')
        
        # Determinar calidad de grabación
        if file_size > 200000:  # > 200KB para 7 segundos
            print('   ✅ EXCELENTE: Archivo con contenido significativo')
            quality = 'high'
        elif file_size > 100000:  # > 100KB
            print('   ⚠️ BUENO: Contenido moderado')
            quality = 'medium'
        elif file_size > 50000:   # > 50KB
            print('   ⚠️ BAJO: Contenido mínimo')
            quality = 'low'
        else:
            print('   ❌ CRÍTICO: Casi sin contenido')
            quality = 'critical'
        
        print()
        print('🎯 TRANSCRIPCIÓN INMEDIATA:')
        print('-' * 30)
        
        # Transcribir con modelo base para máxima precisión
        trans_agent = TranscriptionAgent()
        start_time = time.time()
        trans_result = trans_agent.transcribe_audio_file(
            audio_path, 
            model='base',  # Usar modelo más preciso
            language='es'
        )
        trans_time = time.time() - start_time
        
        if trans_result['success']:
            text = trans_result['text'].strip()
            word_count = trans_result['word_count']
            
            print(f'📝 RESULTADO: "{text}"')
            print(f'📊 Palabras detectadas: {word_count}')
            print(f'⏱️ Tiempo de transcripción: {trans_time:.2f}s')
            print()
            
            # Análisis de calidad
            is_music = '[música]' in text.lower() or '[music]' in text.lower()
            has_speech = word_count > 1 and not is_music
            
            if has_speech:
                print('🎉 ¡ÉXITO TOTAL! Voz detectada correctamente')
                
                # Verificar palabras clave
                target_words = ['probando', 'micrófono', 'ciberseguridad']
                detected_words = []
                text_lower = text.lower()
                
                for word in target_words:
                    if word in text_lower:
                        detected_words.append(word)
                
                accuracy = len(detected_words) / len(target_words) * 100
                print(f'🎯 Precisión de palabras clave: {accuracy:.1f}%')
                print(f'🔍 Palabras detectadas: {detected_words}')
                
                if accuracy >= 66:
                    print('✅ SISTEMA LISTO PARA PRODUCCIÓN')
                    print('🎓 Puedes usar este sistema para transcribir clases')
                else:
                    print('⚠️ Precisión moderada, pero funcional')
                    
            elif is_music:
                print('❌ Aún detecta como música')
                print('💡 SOLUCIONES ADICIONALES:')
                if quality == 'critical':
                    print('   • Problema de hardware: micrófono defectuoso')
                    print('   • Usar auriculares con micrófono externo')
                    print('   • Verificar drivers de audio')
                else:
                    print('   • Hablar más cerca del micrófono')
                    print('   • Aumentar ganancia en configuración del sistema')
                    print('   • Probar con auriculares')
            else:
                print('⚠️ Detecta audio pero muy poco contenido')
                print('💡 Necesita optimización adicional')
        else:
            print(f'❌ Error en transcripción: {trans_result["error"]}')
            
    else:
        print('❌ Error en grabación')
        print('💡 Verifica permisos de micrófono en el sistema')
else:
    print('❌ No se pudo iniciar grabación')
    print('💡 Problema con dispositivo de audio')
