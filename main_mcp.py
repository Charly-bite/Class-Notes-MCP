import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path if not already handled
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import your agents - USANDO EL NUEVO TranscriptionAgent HÍBRIDO
try:
    from agents.recording_agent import RecordingAgent
    from agents.transcription_agent import TranscriptionAgent  # <-- HÍBRIDO
    from agents.analysis_agent import AnalysisAgent
    from agents.obsidian_agent import ObsidianAgent
except ImportError as e:
    print(f"Error importing agents: {e}")
    print("Please ensure all agent files exist and the mcp package is correctly set up.")
    sys.exit(1)

def run_full_pipeline(class_name="Cybersecurity Test Class", 
                      class_type="presencial", 
                      instructor="Prof. MCP",
                      language_hint="es", 
                      record_duration_seconds=15,
                      force_transcription_engine=None): # <-- NUEVA OPCIÓN
    """
    Runs the full MCP Agent pipeline: Record -> Transcribe -> Analyze -> Generate Note.
    Now using the new Hybrid TranscriptionAgent!
    """
    print("🚀 Starting Cybersecurity Class MCP Pipeline...")
    print("=" * 50)

    # Initialize Agents
    print("\n[Pipeline] Initializing agents...")
    try:
        recording_agent = RecordingAgent()
        transcription_agent = TranscriptionAgent()  # <-- HÍBRIDO!
        analysis_agent = AnalysisAgent()
        obsidian_agent = ObsidianAgent()
        print("[Pipeline] All agents initialized successfully.")
        print(f"[Pipeline] 🚀 Using Hybrid TranscriptionAgent (AMD + OpenAI fallback)")
    except Exception as e:
        print(f"[Pipeline] CRITICAL ERROR: Could not initialize agents: {e}")
        return

    # --- 1. Audio Recording ---
    print("\n[Pipeline] Step 1: Recording Audio...")
    
    selected_input_device_index = recording_agent.select_audio_source(class_type=class_type)
    if selected_input_device_index is None:
        print("[Pipeline] ERROR: Could not select audio input device. Aborting.")
        return

    # Start recording
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_audio_filename_base = f"{class_name.replace(' ', '_')}_{timestamp}"

    if not recording_agent.start_recording(output_filename=raw_audio_filename_base, 
                                           input_device_index=selected_input_device_index):
        print("[Pipeline] ERROR: Failed to start recording. Aborting.")
        return
    
    print(f"[Pipeline] Recording for {record_duration_seconds} seconds. Speak now!")
    for _ in range(0, int(recording_agent.RATE / recording_agent.CHUNK * record_duration_seconds)):
        recording_agent.record_chunk()

    recording_result = recording_agent.stop_recording()
    if not recording_result:
        print("[Pipeline] ERROR: Failed to stop/save recording. Aborting.")
        return
    
    recorded_audio_path = Path(recording_result["path"])
    recording_metadata = recording_result["metadata"]
    print(f"[Pipeline] Audio recorded successfully: {recorded_audio_path}")

    # --- 2. Audio Transcription (HÍBRIDO) ---
    print("\n[Pipeline] Step 2: Transcribing Audio with Hybrid Engine...")
    print(f"[Pipeline] 🎯 Primary: whisper-amd, Fallback: OpenAI Whisper")
    
    transcription_result = transcription_agent.transcribe_audio_file(
        recorded_audio_path, 
        language=language_hint,
        output_name=raw_audio_filename_base,
        force_engine=force_transcription_engine,  # None = auto, "amd" = force AMD, "openai" = force OpenAI
        enable_fallback=True
    )
    
    if not transcription_result or not transcription_result["success"]:
        print(f"[Pipeline] ERROR: Hybrid transcription failed: {transcription_result.get('error', 'Unknown')}")
        return
    
    transcript_text = transcription_result["text"]
    detected_language = transcription_result.get("language", language_hint)
    engine_used = transcription_result.get("engine", "unknown")
    processing_time = transcription_result.get("processing_time", 0)
    
    print(f"[Pipeline] ✅ Transcription successful!")
    print(f"[Pipeline] Engine used: {engine_used}")
    print(f"[Pipeline] Processing time: {processing_time:.2f}s")
    print(f"[Pipeline] Detected language: {detected_language}")
    print(f"[Pipeline] Text preview: {transcript_text[:100]}...")

    # --- 3. Content Analysis ---
    print("\n[Pipeline] Step 3: Analyzing Content...")
    analysis_results = analysis_agent.analyze_text(transcript_text, language=detected_language)
    if not analysis_results or "error" in analysis_results:
        print(f"[Pipeline] ERROR: Content analysis failed: {analysis_results.get('error', 'Unknown reason')}. Proceeding with available data.")
        # Create a default empty analysis if it fails
        analysis_results = {
            "key_concepts": [], "named_entities": [], 
            "mentioned_cybersecurity_terms": [], "action_items": [], 
            "extracted_links": [], "security_concepts": []
        }

    # --- 4. Obsidian Note Generation ---
    print("\n[Pipeline] Step 4: Generating Obsidian Note...")
    
    # Prepare data for the Obsidian template
    note_data = {
        "class_name": class_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "class_type": class_type.capitalize(),
        "duration": f"{recording_metadata.get('duration_seconds', 0) // 60} min {recording_metadata.get('duration_seconds', 0) % 60:.0f} sec",
        "quality_score": f"{transcription_result.get('quality_score', 'N/A')} (Engine: {engine_used})",
        "instructor_name": instructor,
        
        "extracted_topics": "\n".join(f"- {concept.capitalize()}" for concept in analysis_results.get("key_concepts", [])),
        "structured_transcript": transcript_text,
        "technical_references": "\n".join(f"- {term.capitalize()}" for term in analysis_results.get("mentioned_cybersecurity_terms", [])),
        "security_concepts": "\n".join(f"- {concept}" for concept in analysis_results.get("security_concepts", [])),
        "action_items": "\n".join(f"- {item}" for item in analysis_results.get("action_items", [])),
        "extracted_links": "\n".join(f"- <{link}>" for link in analysis_results.get("extracted_links", [])),
        "generated_tags": f"#clase #{class_name.lower().replace(' ', '')} #{detected_language} #{engine_used.replace('-', '')}"
    }
    
    note_path = obsidian_agent.generate_note(note_data)
    if not note_path:
        print("[Pipeline] ERROR: Failed to generate Obsidian note.")
        return
        
    print(f"[Pipeline] Obsidian note generated successfully: {note_path}")
    
    # --- 5. Pipeline Summary ---
    print("\n" + "=" * 50)
    print("✅ MCP HYBRID PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"🎙️ Recording: {recorded_audio_path.name} ({recording_metadata.get('duration_seconds', 0):.1f}s)")
    print(f"🔤 Transcription: {engine_used} ({processing_time:.2f}s)")
    print(f"🧠 Analysis: {len(analysis_results.get('key_concepts', []))} concepts")
    print(f"📝 Note: {note_path.name}")
    print(f"🏆 Quality: {transcription_result.get('quality_score', 'N/A')}")
    
    # Show performance stats
    stats = transcription_agent.get_performance_stats()
    if isinstance(stats, dict):
        print(f"\n📊 Transcription Performance:")
        print(f"   AMD Success Rate: {stats['amd_success_rate']}")
        print(f"   Fallback Usage: {stats['fallback_rate']}")
    
    print("=" * 50)

if __name__ == "__main__":
    # --- Configuration for the test run ---
    TEST_CLASS_NAME = "Introducción a Redes Seguras HÍBRIDO"
    TEST_CLASS_TYPE = "presencial" 
    TEST_INSTRUCTOR = "Prof. Eva Byte"
    TEST_LANGUAGE = "es" 
    TEST_DURATION_SEC = 15
    
    # Test different engines:
    # None = auto (AMD first, fallback to OpenAI)
    # "amd" = force whisper-amd only
    # "openai" = force OpenAI Whisper only
    FORCE_ENGINE = None  # <-- Cambiar para probar diferentes motores

    # Check dependencies
    try:
        import jinja2
    except ImportError:
        print("CRITICAL ERROR: Jinja2 is not installed. Please install it with: pip install Jinja2")
        sys.exit(1)
    
    print(f"🎯 Testing Hybrid Pipeline with Engine: {FORCE_ENGINE or 'AUTO (AMD->OpenAI)'}")
    print()
    
    run_full_pipeline(
        class_name=TEST_CLASS_NAME,
        class_type=TEST_CLASS_TYPE,
        instructor=TEST_INSTRUCTOR,
        language_hint=TEST_LANGUAGE,
        record_duration_seconds=TEST_DURATION_SEC,
        force_transcription_engine=FORCE_ENGINE
    )
