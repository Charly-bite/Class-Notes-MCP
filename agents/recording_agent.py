import pyaudio # <--- ESTO ES IMPORTANTE: Asegúrate de que esta línea esté al principio
import time
import wave
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path para importar mcp
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the AgentFramework from your custom mcp package
try:
    from mcp.agent_framework import AgentFramework
except ImportError as e:
    print(f"Error importing AgentFramework: {e}")
    print("Asegúrate de que el archivo mcp/agent_framework.py existe y tiene la clase AgentFramework")
    sys.exit(1)

class RecordingAgent(AgentFramework):
    """
    Manages audio recording, including device selection,
    session detection, quality control, and metadata collection.
    """
    def __init__(self):
        super().__init__("RecordingAgent") # Initialize with agent name
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        
        self.config = self._load_config() # Load configs from AgentFramework
        self.audio_settings = self.config.get('audio_settings', {})
        self.class_schedule = self.config.get('classes', []) # Get class schedule

        # Recording parameters from config/audio_settings.yaml
        self.CHUNK = self.audio_settings.get('chunk_size', 1024)
        self.FORMAT = getattr(pyaudio, self.audio_settings.get('recording_format', 'paInt16'))
        self.CHANNELS = self.audio_settings.get('channels', 1)
        self.RATE = self.audio_settings.get('sample_rate', 44100)
        
        # Paths
        self.recordings_raw_dir = Path('recordings/raw')
        self.recordings_raw_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists

        print(f"[{self.agent_name}] Initialized with audio settings: {self.audio_settings}")

    def _get_device_by_name(self, device_name, is_input=True):
        """Helper to find device index by name."""
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if device_name.lower() in info['name'].lower():
                if (is_input and info['maxInputChannels'] > 0) or \
                   (not is_input and info['maxOutputChannels'] > 0):
                    return i
        return None

    def select_audio_source(self, class_type="presencial", preferred_device_name=None):
        """
        Selects the appropriate audio input device based on class type.
        Can be overridden by a preferred_device_name (e.g., 'HD-Audio Generic').
        """
        input_device_index = None

        if preferred_device_name:
            input_device_index = self._get_device_by_name(preferred_device_name, is_input=True)
            if input_device_index is not None:
                print(f"[{self.agent_name}] Selected preferred device: '{preferred_device_name}' (Index: {input_device_index})")
                return input_device_index
            else:
                print(f"[{self.agent_name}] Preferred device '{preferred_device_name}' not found. Falling back to default/class type detection.")

        if class_type.lower() == "presencial":
            # For presencial, try to use default input or a common mic
            try:
                default_input = self.p.get_default_input_device_info()
                input_device_index = default_input['index']
                print(f"[{self.agent_name}] Selected default input device for 'presencial': {default_input['name']} (Index: {input_device_index})")
            except Exception as e:
                print(f"[{self.agent_name}] Could not get default input device: {e}. Listing available devices...")
                input_devices = [
                    (i, self.p.get_device_info_by_index(i)['name']) 
                    for i in range(self.p.get_device_count()) 
                    if self.p.get_device_info_by_index(i)['maxInputChannels'] > 0
                ]
                if input_devices:
                    input_device_index = input_devices[0][0] # Pick the first available
                    print(f"[{self.agent_name}] Falling back to first available input device: {input_devices[0][1]} (Index: {input_device_index})")
                else:
                    print(f"[{self.agent_name}] No input devices found!")
                    return None
        elif class_type.lower() == "online":
            # For online, typically system audio, 'pulse' or 'default' often work
            # On Parrot OS, 'pulse' or 'default' are common choices for system audio
            input_device_index = self._get_device_by_name("pulse", is_input=True)
            if input_device_index is None:
                input_device_index = self._get_device_by_name("default", is_input=True)
            
            if input_device_index is not None:
                print(f"[{self.agent_name}] Selected system audio device for 'online': {self.p.get_device_info_by_index(input_device_index)['name']} (Index: {input_device_index})")
            else:
                print(f"[{self.agent_name}] Could not find 'pulse' or 'default' input for online classes. Please check your audio setup.")
                # Fallback to default input if no specific system audio found
                try:
                    default_input = self.p.get_default_input_device_info()
                    input_device_index = default_input['index']
                    print(f"[{self.agent_name}] Falling back to default input device: {default_input['name']} (Index: {input_device_index})")
                except Exception:
                    print(f"[{self.agent_name}] No suitable input device found for online classes.")
                    return None
        else:
            print(f"[{self.agent_name}] Unknown class type '{class_type}'. Defaulting to 'presencial' device selection.")
            return self.select_audio_source(class_type="presencial", preferred_device_name=preferred_device_name) # Recursive call to handle unknown type

        return input_device_index

    def start_recording(self, output_filename="raw_audio", input_device_index=None):
        """Starts recording audio from the selected input device."""
        if self.recording:
            print(f"[{self.agent_name}] Already recording.")
            return False

        if input_device_index is None:
            # Attempt to automatically select based on pre-configured preference or default
            # For now, let's assume default behavior for simplicity in this initial implementation
            # This will be enhanced later with schedule-based detection.
            selected_device_index = self.select_audio_source(class_type="presencial") # Placeholder
            if selected_device_index is None:
                print(f"[{self.agent_name}] Failed to select an audio input device. Cannot start recording.")
                return False
            input_device_index = selected_device_index

        try:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=input_device_index # Use the selected device
            )
            self.frames = []
            self.recording = True
            self.start_time = time.time()
            self.output_filename = self.recordings_raw_dir / f"{output_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            print(f"[{self.agent_name}] Started recording to {self.output_filename} from device index {input_device_index}...")
            return True
        except Exception as e:
            print(f"[{self.agent_name}] Error starting recording: {e}")
            self.recording = False
            return False

    def record_chunk(self):
        """Records a chunk of audio."""
        if not self.recording or self.stream is None:
            return None
        
        try:
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)
            return data
        except Exception as e:
            print(f"[{self.agent_name}] Error recording chunk: {e}")
            self.stop_recording() # Attempt to stop on error
            return None

    def stop_recording(self):
        """Stops recording and saves the audio to a WAV file."""
        if not self.recording:
            print(f"[{self.agent_name}] Not currently recording.")
            return None

        try:
            self.stream.stop_stream()
            self.stream.close()
            self.recording = False
            self.end_time = time.time()
            
            # Save to WAV file
            wf = wave.open(str(self.output_filename), 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            duration = self.end_time - self.start_time
            print(f"[{self.agent_name}] Recording stopped. Saved to {self.output_filename}. Duration: {duration:.2f} seconds.")
            
            # Get device info safely
            device_name = "Unknown"
            try:
                if hasattr(self.stream, 'get_input_device_info'):
                    device_info = self.stream.get_input_device_info()
                    device_name = self.p.get_device_info_by_index(device_info['index'])['name']
            except Exception:
                device_name = "Could not retrieve device info"
            
            # Basic metadata for now (will be expanded)
            metadata = {
                "filename": str(self.output_filename.name),
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "duration_seconds": round(duration, 2),
                "input_device": device_name,
                "channels": self.CHANNELS,
                "sample_rate": self.RATE,
                "format": str(self.FORMAT) # Stored as string for readability
            }
            
            return {"path": str(self.output_filename), "metadata": metadata}

        except Exception as e:
            print(f"[{self.agent_name}] Error stopping recording or saving file: {e}")
            self.recording = False
            return None
        finally:
            # Reinitialize PyAudio for next recording
            self.p = pyaudio.PyAudio()

    def run(self):
        """Main execution loop for the Recording Agent (for manual testing)."""
        print(f"[{self.agent_name}] Running Recording Agent in manual test mode.")
        print(f"[{self.agent_name}] Available input devices:")
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  Device {i}: {info['name']}")

        # Example: Try to record for a fixed duration
        # In a real scenario, this would be triggered by class schedule or manual start
        try:
            test_duration_seconds = 5
            
            print(f"[{self.agent_name}] Attempting to select audio source for 'presencial' class...")
            selected_input_device_index = self.select_audio_source(class_type="presencial")
            
            if selected_input_device_index is None:
                print(f"[{self.agent_name}] Could not select a suitable audio device. Exiting.")
                return
            
            if self.start_recording(output_filename="test_presencial_class", input_device_index=selected_input_device_index):
                print(f"[{self.agent_name}] Recording for {test_duration_seconds} seconds...")
                for _ in range(0, int(self.RATE / self.CHUNK * test_duration_seconds)):
                    self.record_chunk()
                    time.sleep(self.CHUNK / self.RATE) # Simulate real-time by waiting
                result = self.stop_recording()
                if result:
                    print(f"[{self.agent_name}] Test recording successful. File: {result['path']}")
                    print(f"[{self.agent_name}] Metadata: {result['metadata']}")
            else:
                print(f"[{self.agent_name}] Failed to start test recording.")
        except KeyboardInterrupt:
            print(f"\n[{self.agent_name}] Recording interrupted by user.")
            if self.recording:
                self.stop_recording()
        finally:
            if self.stream is not None and self.recording:
                self.stop_recording()
            if self.p is not None:
                self.p.terminate()


if __name__ == "__main__":
    # Ensure the virtual environment is sourced before running this directly
    # python agents/recording_agent.py
    
    recording_agent = RecordingAgent()
    recording_agent.run()
