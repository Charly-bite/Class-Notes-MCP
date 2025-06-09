import os
import sys
from pathlib import Path
# For audio transcription - ensure you have openai-whisper installed
try:
    import whisper
    print(f"Whisper version: {whisper.__version__ if hasattr(whisper, '__version__') else 'Unknown'}")
    print(f"Available methods: {[method for method in dir(whisper) if not method.startswith('_')]}")
except ImportError as e:
    print("Error: Could not import whisper.")
    print("Please install with: pip install openai-whisper")
    sys.exit(1)
import datetime

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
        
        # Load Whisper model (multi-language 'base' model)
        print(f"[{self.agent_name}] Loading Whisper model 'base'...")
        try:
            # Check if whisper has the load_model function
            if not hasattr(whisper, 'load_model'):
                raise AttributeError("whisper module doesn't have 'load_model' function. Wrong whisper package installed.")
            
            # Create models directory if it doesn't exist
            self.whisper_model_dir.mkdir(parents=True, exist_ok=True)
            
            # Load the model - it will download automatically if not present
            # Note: download_root is the correct parameter name, not download_dir
            self.whisper_model = whisper.load_model("base", download_root=str(self.whisper_model_dir))
            print(f"[{self.agent_name}] Whisper model 'base' loaded successfully.")
            
        except Exception as e:
            print(f"[{self.agent_name}] Error loading Whisper model: {e}")
            print(f"[{self.agent_name}] Please ensure you have installed: pip install openai-whisper")
            print(f"[{self.agent_name}] And that you have ffmpeg installed on your system")
            self.whisper_model = None # Set to None if loading fails

    def transcribe_audio(self, audio_filepath: Path, output_filename: str = None, language: str = None) -> dict:
        """
        Transcribes an audio file using the loaded Whisper model.
        
        Args:
            audio_filepath (Path): Path to the input audio file.
            output_filename (str, optional): Base name for the output transcript file.
            language (str, optional): Language hint for Whisper (e.g., 'es', 'en').
        Returns:
            dict: A dictionary containing the transcript text and file path,
                  or None if transcription fails.
        """
        if not self.whisper_model:
            print(f"[{self.agent_name}] Whisper model not loaded. Cannot transcribe.")
            return None
        
        if not audio_filepath.exists():
            print(f"[{self.agent_name}] Audio file not found: {audio_filepath}")
            return None

        print(f"[{self.agent_name}] Starting transcription for {audio_filepath.name}...")
        
        try:
            # Improved transcription with better parameters
            result = self.whisper_model.transcribe(
                str(audio_filepath), 
                language=language,
                # Additional parameters for better accuracy
                word_timestamps=True,  # Get word-level timestamps
                verbose=True,          # Show progress
                temperature=0.0,       # More deterministic output
                best_of=5,            # Try multiple decodings
                beam_size=5,          # Beam search for better results
                patience=1.0,         # Wait for better results
                length_penalty=1.0,   # Prefer longer sequences
                suppress_tokens=[-1], # Suppress certain tokens
                initial_prompt="",    # You can add context here
                condition_on_previous_text=True,  # Use context from previous segments
            )
            
            transcript_text = result["text"]
            detected_language = result.get("language", "unknown")
            
            print(f"[{self.agent_name}] Detected language: {detected_language}")
            
            # Check if transcription seems valid
            if len(transcript_text.strip()) < 10:
                print(f"[{self.agent_name}] Warning: Very short transcription. Audio might be empty or unclear.")
            
            # Check for repeated patterns (might indicate poor audio quality)
            words = transcript_text.split()
            if len(words) > 3 and len(set(words)) < len(words) * 0.3:
                print(f"[{self.agent_name}] Warning: High repetition detected. Audio quality might be poor.")
            
            # Determine output filename
            if output_filename is None:
                output_filename = audio_filepath.stem
            
            transcript_filepath = self.transcripts_dir / f"{output_filename}_transcript.txt"
            
            # Save detailed transcription to file
            with open(transcript_filepath, "w", encoding="utf-8") as f:
                f.write(f"Audio File: {audio_filepath.name}\n")
                f.write(f"Detected Language: {detected_language}\n")
                f.write(f"Transcription Date: {datetime.datetime.now().isoformat()}\n")
                f.write("-" * 50 + "\n")
                f.write(transcript_text)
                
                # Also save segments with timestamps if available
                if "segments" in result:
                    f.write("\n\n" + "=" * 50 + "\n")
                    f.write("DETAILED SEGMENTS:\n")
                    f.write("=" * 50 + "\n")
                    for segment in result["segments"]:
                        start_time = segment.get("start", 0)
                        end_time = segment.get("end", 0)
                        text = segment.get("text", "")
                        f.write(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
            
            print(f"[{self.agent_name}] Transcription complete. Saved to: {transcript_filepath}")
            print(f"[{self.agent_name}] Detected language: {detected_language}")
            print(f"[{self.agent_name}] Transcript preview: \n---BEGIN---\n{transcript_text[:200]}...\n---END---")
            
            return {
                "text": transcript_text, 
                "path": str(transcript_filepath),
                "language": detected_language,
                "segments": result.get("segments", [])
            }
        
        except Exception as e:
            print(f"[{self.agent_name}] Error during transcription: {e}")
            return None

    def run(self):
        """Main execution loop for the Processing Agent (for manual testing)."""
        print(f"[{self.agent_name}] Running Processing Agent in manual test mode.")

        # --- TESTING ---
        # You need an audio file to test transcription.
        # Use one of the .wav files previously recorded by the RecordingAgent.
        # Example: Find the most recent .wav file in recordings/raw/
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
        
        # Example usage of transcribe_audio
        # Test with Spanish specifically for cybersecurity classes
        print(f"[{self.agent_name}] Testing transcription with Spanish language hint...")
        transcription_result = self.transcribe_audio(latest_audio_file, language='es')
        
        if transcription_result:
            print(f"[{self.agent_name}] Test transcription successful. Transcript path: {transcription_result['path']}")
            print(f"[{self.agent_name}] Detected language: {transcription_result.get('language', 'unknown')}")
        else:
            print(f"[{self.agent_name}] Test transcription failed.")
            
        # Also test with auto-detection
        print(f"\n[{self.agent_name}] Testing transcription with auto-detection...")
        transcription_result_auto = self.transcribe_audio(latest_audio_file, output_filename=f"{latest_audio_file.stem}_auto", language=None)
        
        if transcription_result_auto:
            print(f"[{self.agent_name}] Auto-detection successful. Language: {transcription_result_auto.get('language', 'unknown')}")
        else:
            print(f"[{self.agent_name}] Auto-detection failed.")


if __name__ == "__main__":
    # Ensure the virtual environment is sourced before running this directly
    # python agents/processing_agent.py
    
    processing_agent = ProcessingAgent()
    processing_agent.run()
