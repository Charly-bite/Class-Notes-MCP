from pathlib import Path
from datetime import datetime
import jinja2 # For template rendering
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.agent_framework import AgentFramework

class ObsidianAgent(AgentFramework):
    """
    Generates structured Markdown notes for Obsidian using
    the processed and analyzed class data.
    """
    def __init__(self):
        super().__init__("ObsidianAgent")
        self.config = self._load_config()
        
        self.obsidian_templates_dir = Path('config/obsidian_templates')
        self.obsidian_vault_notes_dir = Path('vault_integration/generated_notes') # Output directory
        self.obsidian_vault_notes_dir.mkdir(parents=True, exist_ok=True)

        # Setup Jinja2 environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.obsidian_templates_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml', 'md']) # Autoescape for md
        )
        print(f"[{self.agent_name}] Initialized. Templates from: {self.obsidian_templates_dir}, Output to: {self.obsidian_vault_notes_dir}")

    def load_template(self, template_name="class_note_template.md"):
        """Loads a Jinja2 template."""
        try:
            template = self.template_env.get_template(template_name)
            return template
        except jinja2.TemplateNotFound:
            print(f"[{self.agent_name}] Error: Template '{template_name}' not found in {self.obsidian_templates_dir}")
            return None
        except Exception as e:
            print(f"[{self.agent_name}] Error loading template '{template_name}': {e}")
            return None

    def generate_note(self, data: dict, template_name="class_note_template.md") -> Path | None:
        """
        Generates a Markdown note from the provided data and template.
        
        Args:
            data (dict): A dictionary containing all data to populate the template.
                         Expected keys match placeholders in class_note_template.md
                         (e.g., class_name, date, structured_transcript, etc.)
            template_name (str): The name of the template file to use.
        
        Returns:
            Path: The path to the generated note file, or None if generation fails.
        """
        template = self.load_template(template_name)
        if not template:
            return None

        # Ensure all expected keys have default values if not provided in data
        # to prevent Jinja2 rendering errors.
        default_data_keys = {
            "class_name": "Clase Desconocida",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "class_type": "No especificado",
            "duration": "N/A",
            "quality_score": "N/A",
            "instructor_name": "No especificado",
            "extracted_topics": "No se extrajeron temas.",
            "structured_transcript": "Transcripción no disponible.",
            "technical_references": "No se mencionaron referencias técnicas.",
            "security_concepts": "No se identificaron conceptos de seguridad.",
            "action_items": "No se detectaron elementos de acción.",
            "extracted_links": "No se extrajeron enlaces.",
            "generated_tags": "#clase #notas" # Default tags
        }
        
        # Merge provided data with defaults, provided data takes precedence
        render_data = {**default_data_keys, **data}


        try:
            rendered_note_content = template.render(render_data)
            
            # Create a filename (e.g., Cybersecurity_101_2023-10-27.md)
            # Sanitize class_name for filename
            safe_class_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in render_data['class_name'])
            note_filename = f"{safe_class_name}_{render_data['date']}.md"
            output_path = self.obsidian_vault_notes_dir / note_filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_note_content)
            
            print(f"[{self.agent_name}] Note generated successfully: {output_path}")
            return output_path
        except Exception as e:
            print(f"[{self.agent_name}] Error rendering or writing note: {e}")
            return None

    def run(self):
        """Main execution loop for the Obsidian Agent (for manual testing)."""
        print(f"[{self.agent_name}] Running Obsidian Agent in manual test mode.")

        # --- TESTING ---
        # Create some dummy data that mimics what previous agents would produce
        # In a real pipeline, this data would come from Recording, Processing, and Analysis agents
        
        # Dummy data from RecordingAgent (metadata of the recording)
        dummy_recording_metadata = {
            "filename": "test_audio_20231027_100000.wav",
            "start_time": datetime.now().isoformat(),
            "duration_seconds": 300, # 5 minutes
            "input_device": "HD-Audio Generic",
        }

        # Dummy data from ProcessingAgent (transcription)
        dummy_transcript_data = {
            "text": "Esto es una transcripción de prueba para la clase de Ciberseguridad.\n\nHablamos sobre firewalls y la importancia de las contraseñas seguras.\n\nTarea: Revisar la configuración del firewall personal antes del viernes.",
            "language": "es"
        }
        
        # Dummy data from AnalysisAgent
        dummy_analysis_data = {
            "key_concepts": ["firewalls", "contraseñas seguras", "configuración del firewall"],
            "named_entities": [{"text": "viernes", "label": "DATE"}],
            "mentioned_cybersecurity_terms": ["firewall", "contraseñas", "ciberseguridad"],
            "action_items": ["Revisar la configuración del firewall personal antes del viernes"], # Placeholder
            "extracted_links": ["https://ejemplo.com/firewall-guide"], # Placeholder
            "security_concepts": ["Defensa en profundidad", "Autenticación fuerte"] # Placeholder
        }

        # Combine all data for the template
        # The keys here MUST match the {{ placeholders }} in your class_note_template.md
        test_note_data = {
            "class_name": "Ciberseguridad 101",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "class_type": "Presencial", # Auto-detect or from schedule
            "duration": f"{dummy_recording_metadata['duration_seconds'] // 60} minutos",
            "quality_score": "Buena (Placeholder)", # From quality control
            "instructor_name": "Prof. Byte", # From schedule or detected
            
            "extracted_topics": "\n".join(f"- {concept.capitalize()}" for concept in dummy_analysis_data["key_concepts"]),
            "structured_transcript": dummy_transcript_data["text"],
            "technical_references": "\n".join(f"- {term.capitalize()}" for term in dummy_analysis_data["mentioned_cybersecurity_terms"]),
            "security_concepts": "\n".join(f"- {concept}" for concept in dummy_analysis_data.get("security_concepts", [])),
            "action_items": "\n".join(f"- {item}" for item in dummy_analysis_data.get("action_items", [])),
            "extracted_links": "\n".join(f"- <{link}>" for link in dummy_analysis_data.get("extracted_links", [])),
            "generated_tags": "#ciberseguridad #clase #notas #firewall"
        }
        
        generated_file_path = self.generate_note(test_note_data)
        
        if generated_file_path:
            print(f"[{self.agent_name}] Test note generation successful. Check: {generated_file_path}")
        else:
            print(f"[{self.agent_name}] Test note generation failed.")


if __name__ == "__main__":
    # Ensure the virtual environment is sourced before running this directly
    # python agents/obsidian_agent.py
    
    # We need Jinja2 for this agent
    try:
        import jinja2
    except ImportError:
        print("Error: Jinja2 is not installed. Please install it with: pip install Jinja2")
        sys.exit(1)
        
    obsidian_agent = ObsidianAgent()
    obsidian_agent.run()
