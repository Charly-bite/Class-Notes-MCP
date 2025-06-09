import os
import yaml # <-- This is why PyYAML is needed
from pathlib import Path

class AgentFramework:
    """
    A foundational class for MCP agents, providing common functionalities
    like configuration loading and basic logging setup.
    """
    def __init__(self, agent_name, config_path='./config/'):
        self.agent_name = agent_name
        self.config_path = config_path
        self.config = self._load_config()
        print(f"[{self.agent_name}] Agent Framework initialized.")

    def _load_config(self):
        """Loads configuration from YAML files in the config directory."""
        full_config = {}
        # Ensure config_path is absolute or relative to where the script is run
        # For agents, assuming current working directory is project root
        abs_config_path = Path(self.config_path) if Path(self.config_path).is_absolute() else Path(os.getcwd()) / self.config_path

        for filename in os.listdir(abs_config_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = abs_config_path / filename
                try:
                    with open(filepath, 'r') as f:
                        config_data = yaml.safe_load(f)
                        if config_data:
                            # Merge top-level keys
                            for key, value in config_data.items():
                                if key in full_config and isinstance(full_config[key], dict) and isinstance(value, dict):
                                    full_config[key].update(value)
                                else:
                                    full_config[key] = value
                        print(f"[{self.agent_name}] Loaded config from: {filepath}")
                except yaml.YAMLError as e:
                    print(f"[{self.agent_name}] Error loading YAML from {filepath}: {e}")
                except Exception as e:
                    print(f"[{self.agent_name}] Unexpected error loading config from {filepath}: {e}")
        return full_config

    def run(self):
        """Abstract method to be implemented by child agents."""
        raise NotImplementedError("The 'run' method must be implemented by the child agent.")

if __name__ == '__main__':
    # Example usage for testing the framework's config loading
    from pathlib import Path # Added this import for Path usage in example
    class TestAgent(AgentFramework):
        def __init__(self):
            super().__init__("TestAgent")

        def run(self):
            print(f"[{self.agent_name}] Running with config:")
            print(yaml.dump(self.config, indent=2))
            if 'classes' in self.config:
                print(f"[{self.agent_name}] Detected {len(self.config['classes'])} classes in schedule.")
            if 'audio_settings' in self.config:
                print(f"[{self.agent_name}] Sample rate from config: {self.config['audio_settings'].get('sample_rate')}")


    test_agent = TestAgent()
    test_agent.run()
