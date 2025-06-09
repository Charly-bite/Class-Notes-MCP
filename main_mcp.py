import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path if not already handled
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import your agents
try:
    from agents.recording_agent import RecordingAgent
    from agents.processing_agent import ProcessingAgent
    from agents.analysis_agent import AnalysisAgent
    from agents.obsidian_agent import ObsidianAgent
except ImportError as e:
    print(f"Error importing agents: {e}")
    print("Please ensure all agent files exist and the mcp package is correctly set up.")
    sys.exit(1)

def run_full_pipeline(class_name="Cybersecurity Test Class", 
                      class_type="presencial", 
                      instructor="Prof. MCP",
                      language_hint="es", # 'es' for Spanish, 'en' for English, None for auto-detect
                      record_duration_seconds=10): # Shorter duration for full pipeline test
    """
    Runs the full MCP Agent pipeline: Record -> Transcribe -> Analyze -> Generate Note.
    """
    print("🚀 Starting Cybersecurity Class MCP Pipeline...")
    print("=" * 50)

    # Initialize Agents
    print("\n[Pipeline] Initializing agents...")
    try:
        recording_agent = RecordingAgent()
        processing_agent = ProcessingAgent()
        analysis_agent = AnalysisAgent()
        obsidian_agent = ObsidianAgent()
        print("[Pipeline] All agents initialized successfully.")
    except Exception as e:
        print(f"[Pipeline] CRITICAL ERROR: Could not initialize agents: {e}")
        return

    # --- 1. Audio Recording ---
    print("\n[Pipeline] Step 1: Recording Audio...")
    # Use preferred device if set in config, otherwise let RecordingAgent select
    # For this test, we let select_audio_source in RecordingAgent handle it.
    # You could pass a specific device_index if known and preferred.
    
    # Determine audio input device based on class type
    # The recording_agent's run method already has a simple selection,
    # but for a real pipeline, we'd make this more robust or configurable.
    selected_input_device_index = recording_agent.select_audio_source(class_type=class_type)
    if selected_input_device_index is None:
        print("[Pipeline] ERROR: Could not select audio input device. Aborting.")
        return

    # Start recording
    # Generate a unique filename based on class_name and current time
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_audio_filename_base = f"{class_name.replace(' ', '_')}_{timestamp}"

    if not recording_agent.start_recording(output_filename=raw_audio_filename_base, 
                                           input_device_index=selected_input_device_index):
        print("[Pipeline] ERROR: Failed to start recording. Aborting.")
        return
    
    print(f"[Pipeline] Recording for {record_duration_seconds} seconds. Speak now!")
    for _ in range(0, int(recording_agent.RATE / recording_agent.CHUNK * record_duration_seconds)):
        recording_agent.record_chunk()
        # A more precise sleep would be (recording_agent.CHUNK / recording_agent.RATE)
        # but for simplicity and to avoid busy-waiting, a small fixed sleep is okay for testing.
        # However, for real-time chunk processing, the loop should run as fast as possible.
        # The current recording_agent.run() method has a time.sleep() that might be removed
        # if we are doing continuous chunk processing. For a single block recording, it's fine.

    recording_result = recording_agent.stop_recording()
    if not recording_result:
        print("[Pipeline] ERROR: Failed to stop/save recording. Aborting.")
        return
    
    recorded_audio_path = Path(recording_result["path"])
    recording_metadata = recording_result["metadata"]
    print(f"[Pipeline] Audio recorded successfully: {recorded_audio_path}")

    # --- 2. Audio Processing (Transcription) ---
    print("\n[Pipeline] Step 2: Transcribing Audio...")
    transcription_result = processing_agent.transcribe_audio(
        recorded_audio_path, 
        output_filename=raw_audio_filename_base, # Use the same base name
        language=language_hint
    )
    if not transcription_result or "text" not in transcription_result:
        print("[Pipeline] ERROR: Transcription failed. Aborting.")
        return
    
    transcript_text = transcription_result["text"]
    detected_language = transcription_result.get("language", language_hint if language_hint else "unknown")
    print(f"[Pipeline] Transcription successful. Detected language: {detected_language}")

    # --- 3. Content Analysis ---
    print("\n[Pipeline] Step 3: Analyzing Content...")
    analysis_results = analysis_agent.analyze_text(transcript_text, language=detected_language)
    if not analysis_results or "error" in analysis_results:
        print(f"[Pipeline] ERROR: Content analysis failed: {analysis_results.get('error', 'Unknown reason')}. Proceeding with available data.")
        # Create a default empty analysis if it fails, so note generation can still proceed
        analysis_results = {
            "key_concepts": [], "named_entities": [], 
            "mentioned_cybersecurity_terms": [], "action_items": [], 
            "extracted_links": [], "security_concepts": []
        }


    # --- 4. Obsidian Note Generation ---
    print("\n[Pipeline] Step 4: Generating Obsidian Note...")
    
    # Prepare data for the Obsidian template
    # The keys here MUST match the {{ placeholders }} in your class_note_template.md
    note_data = {
        "class_name": class_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "class_type": class_type.capitalize(),
        "duration": f"{recording_metadata.get('duration_seconds', 0) // 60} min {recording_metadata.get('duration_seconds', 0) % 60:.0f} sec",
        "quality_score": "N/A (Pending Implementation)", # Placeholder
        "instructor_name": instructor,
        
        "extracted_topics": "\n".join(f"- {concept.capitalize()}" for concept in analysis_results.get("key_concepts", [])),
        "structured_transcript": transcript_text, # The full transcript
        "technical_references": "\n".join(f"- {term.capitalize()}" for term in analysis_results.get("mentioned_cybersecurity_terms", [])),
        "security_concepts": "\n".join(f"- {concept}" for concept in analysis_results.get("security_concepts", [])),
        "action_items": "\n".join(f"- {item}" for item in analysis_results.get("action_items", [])),
        "extracted_links": "\n".join(f"- <{link}>" for link in analysis_results.get("extracted_links", [])),
        "generated_tags": f"#clase #{class_name.lower().replace(' ', '')} #{detected_language}" # Basic tags
    }
    
    note_path = obsidian_agent.generate_note(note_data)
    if not note_path:
        print("[Pipeline] ERROR: Failed to generate Obsidian note.")
        return
        
    print(f"[Pipeline] Obsidian note generated successfully: {note_path}")
    print("\n" + "=" * 50)
    print("✅ MCP Pipeline finished successfully!")
    print("=" * 50)

if __name__ == "__main__":
    # --- Configuration for the test run ---
    TEST_CLASS_NAME = "Introducción a Redes Seguras"
    TEST_CLASS_TYPE = "presencial" # "presencial" or "online"
    TEST_INSTRUCTOR = "Prof. Eva Byte"
    TEST_LANGUAGE = "es" # "es" for Spanish, "en" for English, or None for Whisper auto-detect
    TEST_DURATION_SEC = 15 # Make it a bit longer to say something meaningful

    # Check if Jinja2 is installed, as ObsidianAgent depends on it
    try:
        import jinja2
    except ImportError:
        print("CRITICAL ERROR: Jinja2 is not installed. Please install it with: pip install Jinja2")
        sys.exit(1)
    
    run_full_pipeline(
        class_name=TEST_CLASS_NAME,
        class_type=TEST_CLASS_TYPE,
        instructor=TEST_INSTRUCTOR,
        language_hint=TEST_LANGUAGE,
        record_duration_seconds=TEST_DURATION_SEC
    )
