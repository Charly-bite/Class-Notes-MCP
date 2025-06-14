import os
import sys
import subprocess
import json
from pathlib import Path
import datetime

# For audio transcription - ensure you have openai-whisper installed
try:
    import whisper
    print(f"Whisper version: {whisper.__version__ if hasattr(whisper, '__version__') else 'Unknown'}")
    print(f"Available methods: {[method for method in dir(whisper) if not method.startswith('_')]}")
    OPENAI_WHISPER_AVAILABLE = True
except ImportError as e:
    print("Warning: Could not import openai-whisper.")
    print("OpenAI Whisper fallback will not be available.")
    OPENAI_WHISPER_AVAILABLE = False

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import the AgentFramework
try:
    from mcp.agent_framework import AgentFramework
except ImportError:
    print("Error: Could not import AgentFramework.")
    print("Please ensure:")
    print("1. The 'mcp' directory exists in the project root")
    print("2. The 'agent_framework.py' file exists in the mcp directory")
    print("3. Both directories have __init__.py files")
    sys.exit(1)

class ProcessingAgent(AgentFramework):
    """
    Manages the audio processing pipeline, including transcription,
    speaker diarization, and audio enhancement.
    Supports multiple whisper engines with automatic fallback.
    """
    def __init__(self):
        super().__init__("ProcessingAgent") # Initialize with agent name
        
        self.config = self._load_config() # Load configs from AgentFramework
        # Audio settings from config/audio_settings.yaml might be useful later
        self.audio_settings = self.config.get('audio_settings', {})

        # Paths for models and transcripts
        self.whisper_model_dir = Path('models/whisper_model')
        self.transcripts_dir = Path('recordings/transcripts')
        self.transcripts_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        
        # Initialize available engines
        self.available_engines = self._detect_available_engines()
        self.preferred_engine = self._select_preferred_engine()
        
        print(f"[{self.agent_name}] Engines disponibles: {list(self.available_engines.keys())}")
        print(f"[{self.agent_name}] Motor preferido: {self.preferred_engine}")
        
        # Load OpenAI Whisper model if available and needed
        self.whisper_model = None
        if OPENAI_WHISPER_AVAILABLE and (self.preferred_engine == "openai_whisper" or "whisper_cpp" not in self.available_engines):
            self._load_openai_whisper_model()

    def _detect_available_engines(self):
        """Detectar motores de whisper disponibles en el sistema"""
        engines = {}
        
        # Verificar whisper.cpp optimizado para AMD
        if self._check_whisper_cpp_amd():
            engines["whisper_cpp_amd"] = {
                "binary": "whisper-amd",
                "description": "whisper.cpp optimizado para AMD A4-9125",
                "priority": 1
            }
        
        # Verificar whisper.cpp estándar
        if self._check_whisper_cpp():
            engines["whisper_cpp"] = {
                "binary": "whisper",
                "description": "whisper.cpp estándar",
                "priority": 2
            }
        
        # Verificar OpenAI Whisper
        if OPENAI_WHISPER_AVAILABLE:
            engines["openai_whisper"] = {
                "binary": None,
                "description": "OpenAI Whisper (Python)",
                "priority": 3
            }
        
        return engines
    
    def _check_whisper_cpp_amd(self):
        """Verificar si whisper-amd está disponible"""
        try:
            result = subprocess.run(["whisper-amd", "--help"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _check_whisper_cpp(self):
        """Verificar si whisper está disponible"""
        try:
            result = subprocess.run(["whisper", "--help"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _select_preferred_engine(self):
        """Seleccionar el motor preferido basado en prioridad"""
        if not self.available_engines:
            return None
        
        # Ordenar por prioridad y seleccionar el mejor
        sorted_engines = sorted(self.available_engines.items(), 
                              key=lambda x: x[1]["priority"])
        return sorted_engines[0][0]
    
    def _load_openai_whisper_model(self):
        """Cargar modelo OpenAI Whisper"""
        print(f"[{self.agent_name}] Loading OpenAI Whisper model 'base'...")
        try:
            # Check if whisper has the load_model function
            if not hasattr(whisper, 'load_model'):
                raise AttributeError("whisper module doesn't have 'load_model' function.")
            
            # Create models directory if it doesn't exist
            self.whisper_model_dir.mkdir(parents=True, exist_ok=True)
            
            # Load the model - it will download automatically if not present
            self.whisper_model = whisper.load_model("base", download_root=str(self.whisper_model_dir))
            print(f"[{self.agent_name}] OpenAI Whisper model 'base' loaded successfully.")
            
        except Exception as e:
            print(f"[{self.agent_name}] Error loading OpenAI Whisper model: {e}")
            print(f"[{self.agent_name}] Please ensure you have installed: pip install openai-whisper")
            print(f"[{self.agent_name}] And that you have ffmpeg installed on your system")
            self.whisper_model = None

    def transcribe_audio(self, audio_filepath: Path, output_filename: str = None, language: str = None) -> dict:
        """
        Transcribes an audio file using the best available whisper engine.
        
        Args:
            audio_filepath (Path): Path to the input audio file.
            output_filename (str, optional): Base name for the output transcript file.
            language (str, optional): Language hint for Whisper (e.g., 'es', 'en').
        Returns:
            dict: A dictionary containing the transcript text and file path,
                  or None if transcription fails.
        """
        if not audio_filepath.exists():
            print(f"[{self.agent_name}] Audio file not found: {audio_filepath}")
            return None

        print(f"[{self.agent_name}] Starting transcription for {audio_filepath.name}...")
        print(f"[{self.agent_name}] Using engine: {self.preferred_engine}")
        
        # Try preferred engine first, then fallback
        if self.preferred_engine == "whisper_cpp_amd":
            result = self._transcribe_with_whisper_cpp_amd(audio_filepath, language, output_filename)
            if result:
                return result
            print(f"[{self.agent_name}] AMD transcription failed, trying fallback...")
        
        if "whisper_cpp" in self.available_engines:
            result = self._transcribe_with_whisper_cpp(audio_filepath, language, output_filename)
            if result:
                return result
            print(f"[{self.agent_name}] whisper.cpp failed, trying OpenAI Whisper...")
        
        if "openai_whisper" in self.available_engines:
            result = self._transcribe_with_openai_whisper(audio_filepath, language, output_filename)
            if result:
                return result
        
        print(f"[{self.agent_name}] All transcription engines failed.")
        return None

    def _transcribe_with_whisper_cpp_amd(self, audio_filepath: Path, language: str = None, output_filename: str = None):
        """Transcripción optimizada para AMD A4-9125 usando whisper.cpp"""
        
        print(f"[{self.agent_name}] Iniciando transcripción AMD optimizada...")
        
        # Configuración específica para A4-9125
        amd_config = {
            "binary_path": "whisper-amd",
            "optimal_threads": 2,
            "optimal_model": "base",  # Cambiar a "small" si está disponible
            "use_opencl": True
        }
        
        # Comando optimizado para A4-9125
        cmd = [
            amd_config["binary_path"],
            str(audio_filepath),
            "--model", amd_config["optimal_model"],
            "--threads", str(amd_config["optimal_threads"]),
            "--output_format", "json"
        ]
        
        # Añadir idioma si se especifica
        if language:
            cmd.extend(["--language", language])
        
        # Añadir OpenCL si está disponible
        if amd_config["use_opencl"]:
            cmd.extend(["--use_gpu"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    # Parsear resultado JSON
                    whisper_result = json.loads(result.stdout)
                    transcript_text = whisper_result.get("text", "").strip()
                    detected_language = whisper_result.get("language", language or "unknown")
                    
                    if transcript_text:
                        print(f"[{self.agent_name}] Transcripción AMD completada exitosamente")
                        
                        # Guardar resultado
                        saved_result = self._save_transcription_result(
                            audio_filepath, transcript_text, detected_language,
                            output_filename, whisper_result.get("segments", []),
                            engine="whisper-amd-optimized"
                        )
                        
                        return {
                            "text": transcript_text,
                            "path": saved_result["path"],
                            "language": detected_language,
                            "segments": whisper_result.get("segments", []),
                            "engine": "whisper-amd-optimized",
                            "model": amd_config["optimal_model"],
                            "threads_used": amd_config["optimal_threads"]
                        }
                    else:
                        print(f"[{self.agent_name}] Transcripción AMD vacía")
                        return None
                        
                except json.JSONDecodeError as e:
                    print(f"[{self.agent_name}] Error parsing JSON from whisper-amd: {e}")
                    return None
            else:
                print(f"[{self.agent_name}] Error en whisper-amd: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"[{self.agent_name}] Timeout en transcripción AMD")
            return None
        except FileNotFoundError:
            print(f"[{self.agent_name}] whisper-amd no encontrado")
            return None

    def _transcribe_with_whisper_cpp(self, audio_filepath: Path, language: str = None, output_filename: str = None):
        """Transcripción usando whisper.cpp estándar"""
        
        print(f"[{self.agent_name}] Usando whisper.cpp estándar...")
        
        cmd = [
            "whisper",
            str(audio_filepath),
            "--model", "base",
            "--threads", "2",
            "--output_format", "json"
        ]
        
        if language:
            cmd.extend(["--language", language])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    whisper_result = json.loads(result.stdout)
                    transcript_text = whisper_result.get("text", "").strip()
                    detected_language = whisper_result.get("language", language or "unknown")
                    
                    if transcript_text:
                        saved_result = self._save_transcription_result(
                            audio_filepath, transcript_text, detected_language,
                            output_filename, whisper_result.get("segments", []),
                            engine="whisper-cpp"
                        )
                        
                        return {
                            "text": transcript_text,
                            "path": saved_result["path"],
                            "language": detected_language,
                            "segments": whisper_result.get("segments", []),
                            "engine": "whisper-cpp"
                        }
                    
                except json.JSONDecodeError as e:
                    print(f"[{self.agent_name}] Error parsing JSON from whisper: {e}")
                    return None
            else:
                print(f"[{self.agent_name}] Error en whisper.cpp: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"[{self.agent_name}] Timeout en whisper.cpp")
            return None
        except FileNotFoundError:
            print(f"[{self.agent_name}] whisper no encontrado")
            return None

    def _transcribe_with_openai_whisper(self, audio_filepath: Path, language: str = None, output_filename: str = None):
        """Transcripción usando OpenAI Whisper (fallback)"""
        
        if not self.whisper_model:
            print(f"[{self.agent_name}] OpenAI Whisper model not loaded. Cannot transcribe.")
            return None
        
        print(f"[{self.agent_name}] Usando OpenAI Whisper como fallback...")
        
        try:
            # Transcripción con parámetros optimizados para A4-9125
            result = self.whisper_model.transcribe(
                str(audio_filepath), 
                language=language,
                word_timestamps=True,
                verbose=False,          # Menos verbose para CPU limitado
                temperature=0.0,        # Determinístico
                best_of=1,             # Reducido para A4-9125
                beam_size=1,           # Reducido para A4-9125
                condition_on_previous_text=True
            )
            
            transcript_text = result["text"]
            detected_language = result.get("language", "unknown")
            
            print(f"[{self.agent_name}] OpenAI Whisper transcription completed")
            
            # Validaciones básicas
            if len(transcript_text.strip()) < 10:
                print(f"[{self.agent_name}] Warning: Very short transcription.")
            
            # Guardar resultado
            saved_result = self._save_transcription_result(
                audio_filepath, transcript_text, detected_language,
                output_filename, result.get("segments", []),
                engine="openai-whisper"
            )
            
            return {
                "text": transcript_text, 
                "path": saved_result["path"],
                "language": detected_language,
                "segments": result.get("segments", []),
                "engine": "openai-whisper"
            }
        
        except Exception as e:
            print(f"[{self.agent_name}] Error during OpenAI Whisper transcription: {e}")
            return None

    def _save_transcription_result(self, audio_filepath: Path, transcript_text: str, 
                                 detected_language: str, output_filename: str = None, 
                                 segments: list = None, engine: str = "unknown"):
        """Guardar resultado de transcripción en archivo"""
        
        # Determinar nombre de archivo
        if output_filename is None:
            output_filename = audio_filepath.stem
        
        transcript_filepath = self.transcripts_dir / f"{output_filename}_transcript.txt"
        
        # Guardar transcripción detallada
        with open(transcript_filepath, "w", encoding="utf-8") as f:
            f.write(f"Audio File: {audio_filepath.name}\n")
            f.write(f"Transcription Engine: {engine}\n")
            f.write(f"Detected Language: {detected_language}\n")
            f.write(f"Transcription Date: {datetime.datetime.now().isoformat()}\n")
            f.write("-" * 50 + "\n")
            f.write(transcript_text)
            
            # Guardar segmentos con timestamps si están disponibles
            if segments:
                f.write("\n\n" + "=" * 50 + "\n")
                f.write("DETAILED SEGMENTS:\n")
                f.write("=" * 50 + "\n")
                for segment in segments:
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "")
                    f.write(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
        
        print(f"[{self.agent_name}] Transcription saved to: {transcript_filepath}")
        print(f"[{self.agent_name}] Engine used: {engine}")
        print(f"[{self.agent_name}] Detected language: {detected_language}")
        print(f"[{self.agent_name}] Transcript preview: \n---BEGIN---\n{transcript_text[:200]}...\n---END---")
        
        return {"path": str(transcript_filepath)}

    def run(self):
        """Main execution loop for the Processing Agent (for manual testing)."""
        print(f"[{self.agent_name}] Running Processing Agent in manual test mode.")
        print(f"[{self.agent_name}] Available engines: {list(self.available_engines.keys())}")
        print(f"[{self.agent_name}] Preferred engine: {self.preferred_engine}")

        # --- TESTING ---
        raw_recordings_path = Path('recordings/raw')
        if not raw_recordings_path.exists():
            print(f"[{self.agent_name}] Directory not found: {raw_recordings_path}")
            print(f"[{self.agent_name}] Please create the directory and add audio files, or run RecordingAgent first.")
            return
            
        raw_recordings = list(raw_recordings_path.glob('*.wav'))
        if not raw_recordings:
            print(f"[{self.agent_name}] No raw audio recordings found in {raw_recordings_path}.")
            print(f"[{self.agent_name}] Please run RecordingAgent first to generate audio files.")
            return

        # Get the most recent recording
        raw_recordings.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_audio_file = raw_recordings[0]

        print(f"[{self.agent_name}] Attempting to transcribe latest audio file: {latest_audio_file.name}")
        
        # Test transcription with Spanish language hint
        print(f"[{self.agent_name}] Testing transcription with Spanish language hint...")
        transcription_result = self.transcribe_audio(latest_audio_file, language='es')
        
        if transcription_result:
            print(f"[{self.agent_name}] Test transcription successful!")
            print(f"[{self.agent_name}] Engine used: {transcription_result.get('engine', 'unknown')}")
            print(f"[{self.agent_name}] Transcript path: {transcription_result['path']}")
            print(f"[{self.agent_name}] Detected language: {transcription_result.get('language', 'unknown')}")
        else:
            print(f"[{self.agent_name}] Test transcription failed.")


# Clase de compatibilidad para mantener la interfaz existente
class OptimizedAMDProcessingAgent(ProcessingAgent):
    """
    Alias para ProcessingAgent optimizado.
    Esta clase existe para mantener compatibilidad con el código existente.
    """
    def __init__(self):
        super().__init__()
        print(f"[{self.agent_name}] OptimizedAMDProcessingAgent initialized (using base ProcessingAgent)")


if __name__ == "__main__":
    # Ensure the virtual environment is sourced before running this directly
    # python agents/processing_agent.py
    
    processing_agent = ProcessingAgent()
    processing_agent.run()
