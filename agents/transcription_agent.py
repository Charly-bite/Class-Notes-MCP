import subprocess
import json
import time
from pathlib import Path
import sys
import os
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.agent_framework import AgentFramework

class TranscriptionAgent(AgentFramework):
    """
    Hybrid Transcription Agent: whisper-amd primary, OpenAI Whisper fallback
    
    Strategy:
    1. Try whisper-amd first (ultra-fast, AMD optimized)
    2. If fails or detects music -> fallback to OpenAI Whisper (reliable)
    3. Always return best possible transcription
    
    Best performance for Charly-bite's AMD system!
    """
    def __init__(self):
        super().__init__("TranscriptionAgent")
        self.config = self._load_config()
        
        # Paths and settings
        self.whisper_amd_path = "/usr/local/bin/whisper-amd"
        self.models_dir = Path("/home/byte/whisper_models")
        self.transcripts_dir = Path("recordings/transcripts")
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI Whisper for fallback
        self.whisper_openai = None
        self.openai_model = None
        try:
            import whisper
            self.whisper_openai = whisper
            print(f"[{self.agent_name}] ✅ OpenAI Whisper available for fallback")
        except ImportError:
            print(f"[{self.agent_name}] ⚠️ OpenAI Whisper not available - AMD only mode")
        
        # Optimal whisper-amd configuration (validated working)
        self.amd_config = {
            "model": "ggml-base.bin",
            "threads": 2,
            "processors": 1,
            "temperature": 0.0,
            "best_of": 5,
            "beam_size": 5,  # Max without "too many decoders" error
            "no_speech_threshold": 0.2,
            "suppress_non_speech_tokens": True
        }
        
        # Performance tracking
        self.stats = {
            "amd_success": 0,
            "amd_failed": 0,
            "openai_fallback": 0,
            "total_transcriptions": 0
        }
        
        print(f"[{self.agent_name}] 🚀 Hybrid transcription agent initialized")
        print(f"[{self.agent_name}] Primary: whisper-amd, Fallback: OpenAI Whisper")

    def _verify_whisper_amd(self):
        """Verify whisper-amd availability"""
        try:
            result = subprocess.run([self.whisper_amd_path, "--help"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _get_model_path(self, model_name):
        """Get full path to whisper-amd model"""
        model_path = self.models_dir / model_name
        return str(model_path) if model_path.exists() else None

    def _find_generated_files(self, base_path, audio_file_name):
        """Smart file detection for whisper-amd output"""
        possible_names = [
            base_path,
            audio_file_name.replace('.wav', ''),
            Path(audio_file_name).stem,
        ]
        
        search_dirs = [
            self.transcripts_dir,
            Path.cwd(),
            Path("recordings/raw").parent,
        ]
        
        found_files = {"txt": None, "srt": None}
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            for name in possible_names:
                # Check .txt files
                txt_patterns = [
                    search_dir / f"{name}.txt",
                    search_dir / f"{Path(name).name}.txt",
                    search_dir / f"{Path(name).stem}.txt",
                ]
                
                for txt_file in txt_patterns:
                    if txt_file.exists() and found_files["txt"] is None:
                        found_files["txt"] = str(txt_file)
                        break
                
                # Check .srt files
                srt_patterns = [
                    search_dir / f"{name}.srt",
                    search_dir / f"{Path(name).name}.srt",
                    search_dir / f"{Path(name).stem}.srt",
                ]
                
                for srt_file in srt_patterns:
                    if srt_file.exists() and found_files["srt"] is None:
                        found_files["srt"] = str(srt_file)
                        break
        
        return found_files

    def _transcribe_with_whisper_amd(self, audio_path, language="es", custom_prompt=None, output_name=None):
        """
        Primary transcription method using optimized whisper-amd
        
        Returns result with success/failure and detailed info
        """
        model_path = self._get_model_path(self.amd_config["model"])
        if not model_path:
            return {
                "success": False, 
                "error": f"Model {self.amd_config['model']} not found",
                "engine": "whisper-amd"
            }
        
        if output_name is None:
            output_name = audio_path.stem
            
        output_base = self.transcripts_dir / output_name
        
        if custom_prompt is None:
            if language == "es":
                custom_prompt = "Esta es una persona hablando en español sobre ciberseguridad"
            else:
                custom_prompt = "This is a person speaking about cybersecurity"
        
        print(f"[{self.agent_name}] 🚀 whisper-amd: {audio_path.name} ({audio_path.stat().st_size // 1024}KB)")
        
        # Build optimized command with validated parameters
        command = [
            self.whisper_amd_path,
            "-m", model_path,
            "-t", str(self.amd_config["threads"]),
            "-p", str(self.amd_config["processors"]),
            "-l", language,
            "--prompt", custom_prompt,
            "--temperature", str(self.amd_config["temperature"]),
            "--best-of", str(self.amd_config["best_of"]),
            "--beam-size", str(self.amd_config["beam_size"]),
            "--no-speech-thold", str(self.amd_config["no_speech_threshold"]),
            "--suppress-nst",
            "--output-txt",
            "--output-srt",
            "--output-file", str(output_base),
            str(audio_path)
        ]
        
        try:
            start_time = time.time()
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                # Look for generated files
                found_files = self._find_generated_files(str(output_base), audio_path.name)
                
                if found_files["txt"]:
                    with open(found_files["txt"], 'r', encoding='utf-8') as f:
                        transcribed_text = f.read().strip()
                    
                    # Check for music classification (main reason for fallback)
                    is_music_classification = any(music_term in transcribed_text.lower() 
                                                for music_term in ["[música]", "[music]", "música", "music"])
                    
                    # Move files to correct location if needed
                    final_txt = self.transcripts_dir / f"{output_name}.txt"
                    final_srt = self.transcripts_dir / f"{output_name}.srt"
                    
                    if Path(found_files["txt"]) != final_txt:
                        import shutil
                        shutil.move(found_files["txt"], final_txt)
                        found_files["txt"] = str(final_txt)
                    
                    if found_files["srt"] and Path(found_files["srt"]) != final_srt:
                        import shutil
                        shutil.move(found_files["srt"], final_srt)
                        found_files["srt"] = str(final_srt)
                    
                    word_count = len(transcribed_text.split()) if transcribed_text else 0
                    
                    print(f"[{self.agent_name}] ✅ whisper-amd success: {processing_time:.2f}s, {word_count} words")
                    if is_music_classification:
                        print(f"[{self.agent_name}] ⚠️ Music classification detected - will try fallback")
                    
                    return {
                        "success": True,
                        "engine": "whisper-amd",
                        "text": transcribed_text,
                        "word_count": word_count,
                        "processing_time": processing_time,
                        "txt_file": found_files["txt"],
                        "srt_file": found_files["srt"],
                        "language": language,
                        "audio_file": str(audio_path),
                        "is_music_classification": is_music_classification,
                        "quality_score": "good" if word_count > 0 and not is_music_classification else "poor"
                    }
                else:
                    return {
                        "success": False,
                        "error": "No output files generated",
                        "engine": "whisper-amd",
                        "return_code": result.returncode,
                        "stderr": result.stderr[:200] if result.stderr else ""
                    }
            else:
                return {
                    "success": False,
                    "error": f"Return code {result.returncode}",
                    "engine": "whisper-amd",
                    "stderr": result.stderr[:200] if result.stderr else "",
                    "stdout": result.stdout[:200] if result.stdout else ""
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout (5 minutes)",
                "engine": "whisper-amd"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "engine": "whisper-amd"
            }

    def _transcribe_with_openai_whisper(self, audio_path, language="es", custom_prompt=None, output_name=None):
        """
        Fallback transcription method using OpenAI Whisper
        
        More reliable but slower than whisper-amd
        """
        if not self.whisper_openai:
            return {
                "success": False,
                "error": "OpenAI Whisper not available",
                "engine": "openai-whisper"
            }
        
        # Load model if needed
        if self.openai_model is None:
            try:
                print(f"[{self.agent_name}] 📥 Loading OpenAI Whisper model...")
                self.openai_model = self.whisper_openai.load_model("base")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to load OpenAI model: {e}",
                    "engine": "openai-whisper"
                }
        
        if output_name is None:
            output_name = audio_path.stem
            
        if custom_prompt is None:
            if language == "es":
                custom_prompt = "Esta es una persona hablando en español sobre ciberseguridad"
            else:
                custom_prompt = "This is a person speaking about cybersecurity"
        
        print(f"[{self.agent_name}] 🔄 OpenAI Whisper fallback: {audio_path.name}")
        
        try:
            start_time = time.time()
            
            # Use Spanish language name for OpenAI Whisper
            openai_language = "Spanish" if language == "es" else language
            
            result = self.openai_model.transcribe(
                str(audio_path),
                language=openai_language,
                initial_prompt=custom_prompt,
                temperature=0.0,
                best_of=5,
                beam_size=5,
                word_timestamps=True,
                verbose=False
            )
            
            processing_time = time.time() - start_time
            transcribed_text = result["text"].strip()
            detected_language = result.get("language", language)
            
            # Save to file
            txt_file = self.transcripts_dir / f"{output_name}.txt"
            srt_file = self.transcripts_dir / f"{output_name}.srt"
            
            # Save detailed transcript
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"Audio File: {audio_path.name}\n")
                f.write(f"Engine: OpenAI Whisper (fallback)\n")
                f.write(f"Detected Language: {detected_language}\n")
                f.write(f"Transcription Date: {datetime.now().isoformat()}\n")
                f.write("-" * 50 + "\n")
                f.write(transcribed_text)
            
            # Generate SRT with timestamps if available
            if "segments" in result and result["segments"]:
                with open(srt_file, 'w', encoding='utf-8') as f:
                    for i, segment in enumerate(result["segments"], 1):
                        start = segment.get("start", 0)
                        end = segment.get("end", start + 1)
                        text = segment.get("text", "").strip()
                        
                        # Convert to SRT format
                        start_time = f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{start%60:06.3f}".replace('.', ',')
                        end_time = f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{end%60:06.3f}".replace('.', ',')
                        
                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
            
            word_count = len(transcribed_text.split()) if transcribed_text else 0
            
            print(f"[{self.agent_name}] ✅ OpenAI Whisper success: {processing_time:.2f}s, {word_count} words")
            print(f"[{self.agent_name}] Detected language: {detected_language}")
            
            return {
                "success": True,
                "engine": "openai-whisper",
                "text": transcribed_text,
                "word_count": word_count,
                "processing_time": processing_time,
                "txt_file": str(txt_file),
                "srt_file": str(srt_file),
                "language": detected_language,
                "audio_file": str(audio_path),
                "is_music_classification": False,  # OpenAI rarely misclassifies
                "quality_score": "excellent" if word_count > 0 else "poor",
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI Whisper error: {str(e)}",
                "engine": "openai-whisper"
            }

    def transcribe_audio_file(self, audio_path, language="es", custom_prompt=None, 
                            output_name=None, force_engine=None, enable_fallback=True):
        """
        Hybrid transcription with intelligent fallback strategy
        
        Args:
            audio_path: Path to audio file
            language: Language code ("es", "en", etc.)
            custom_prompt: Context prompt for better accuracy
            output_name: Custom output filename base
            force_engine: Force specific engine ("amd" or "openai")
            enable_fallback: Enable automatic fallback (default: True)
        
        Returns:
            dict: Transcription results with success status and metadata
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            return {
                "success": False, 
                "error": f"Audio file not found: {audio_path}",
                "audio_file": str(audio_path)
            }
        
        self.stats["total_transcriptions"] += 1
        
        print(f"[{self.agent_name}] 🎯 Starting hybrid transcription...")
        print(f"[{self.agent_name}] Audio: {audio_path.name} ({audio_path.stat().st_size // 1024}KB)")
        print(f"[{self.agent_name}] Language: {language}")
        print(f"[{self.agent_name}] Fallback enabled: {enable_fallback}")
        
        # Strategy 1: Try whisper-amd first (unless forced to OpenAI)
        if force_engine != "openai" and self._verify_whisper_amd():
            amd_result = self._transcribe_with_whisper_amd(audio_path, language, custom_prompt, output_name)
            
            if amd_result["success"]:
                # Check if result is good quality (not music classification)
                if not amd_result.get("is_music_classification", False):
                    self.stats["amd_success"] += 1
                    print(f"[{self.agent_name}] 🏆 whisper-amd success - no fallback needed!")
                    return amd_result
                else:
                    print(f"[{self.agent_name}] ⚠️ whisper-amd detected music - trying fallback...")
                    self.stats["amd_failed"] += 1
            else:
                print(f"[{self.agent_name}] ⚠️ whisper-amd failed: {amd_result.get('error', 'Unknown')}")
                self.stats["amd_failed"] += 1
        
        # Strategy 2: Fallback to OpenAI Whisper
        if enable_fallback and force_engine != "amd":
            print(f"[{self.agent_name}] 🔄 Activating OpenAI Whisper fallback...")
            openai_result = self._transcribe_with_openai_whisper(audio_path, language, custom_prompt, output_name)
            
            if openai_result["success"]:
                self.stats["openai_fallback"] += 1
                print(f"[{self.agent_name}] 🏆 OpenAI Whisper fallback successful!")
                return openai_result
            else:
                print(f"[{self.agent_name}] ❌ OpenAI Whisper fallback failed: {openai_result.get('error')}")
        
        # Both engines failed
        self.stats["amd_failed"] += 1
        return {
            "success": False,
            "error": "All transcription engines failed",
            "amd_error": amd_result.get("error") if 'amd_result' in locals() else "Not attempted",
            "openai_error": openai_result.get("error") if 'openai_result' in locals() else "Not attempted",
            "audio_file": str(audio_path)
        }

    def transcribe_latest_recording(self, language="es", force_engine=None):
        """Convenience method to transcribe the most recent recording"""
        recordings_dir = Path("recordings/raw")
        if not recordings_dir.exists():
            return {"success": False, "error": "No recordings directory found"}
        
        audio_files = list(recordings_dir.glob("*.wav"))
        if not audio_files:
            return {"success": False, "error": "No audio files found in recordings/raw"}
        
        latest_audio = max(audio_files, key=lambda x: x.stat().st_mtime)
        print(f"[{self.agent_name}] 📁 Transcribing latest: {latest_audio.name}")
        
        return self.transcribe_audio_file(latest_audio, language=language, force_engine=force_engine)

    def get_performance_stats(self):
        """Get performance statistics"""
        total = self.stats["total_transcriptions"]
        if total == 0:
            return "No transcriptions performed yet"
        
        amd_success_rate = (self.stats["amd_success"] / total) * 100
        fallback_rate = (self.stats["openai_fallback"] / total) * 100
        
        return {
            "total_transcriptions": total,
            "amd_success": self.stats["amd_success"],
            "amd_success_rate": f"{amd_success_rate:.1f}%",
            "fallback_used": self.stats["openai_fallback"],
            "fallback_rate": f"{fallback_rate:.1f}%",
            "amd_failed": self.stats["amd_failed"]
        }

    def run(self):
        """Test hybrid transcription system"""
        print(f"[{self.agent_name}] 🚀 Testing Hybrid Transcription System...")
        print("=" * 70)
        
        # System check
        amd_available = self._verify_whisper_amd()
        openai_available = self.whisper_openai is not None
        
        print(f"[{self.agent_name}] 🔍 System Status:")
        print(f"[{self.agent_name}] whisper-amd available: {'✅' if amd_available else '❌'}")
        print(f"[{self.agent_name}] OpenAI Whisper available: {'✅' if openai_available else '❌'}")
        print(f"[{self.agent_name}] Hybrid mode: {'✅ Active' if amd_available and openai_available else '⚠️ Limited'}")
        print()
        
        # Test transcription
        result = self.transcribe_latest_recording(language="es")
        
        if result["success"]:
            print(f"[{self.agent_name}] ✅ Hybrid transcription successful!")
            print(f"[{self.agent_name}] Engine used: {result['engine']}")
            print(f"[{self.agent_name}] Text: '{result['text']}'")
            print(f"[{self.agent_name}] Words: {result['word_count']}")
            print(f"[{self.agent_name}] Processing time: {result['processing_time']:.2f}s")
            print(f"[{self.agent_name}] Quality: {result['quality_score']}")
            print(f"[{self.agent_name}] Files: {result['txt_file']}")
        else:
            print(f"[{self.agent_name}] ❌ Hybrid transcription failed:")
            print(f"[{self.agent_name}] Error: {result['error']}")
        
        # Show performance stats
        print(f"\n[{self.agent_name}] 📊 Performance Stats:")
        stats = self.get_performance_stats()
        if isinstance(stats, dict):
            for key, value in stats.items():
                print(f"[{self.agent_name}] {key.replace('_', ' ').title()}: {value}")
        else:
            print(f"[{self.agent_name}] {stats}")
        
        print("=" * 70)


if __name__ == "__main__":
    agent = TranscriptionAgent()
    agent.run()
