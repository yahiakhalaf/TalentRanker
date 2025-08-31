import yaml
from pathlib import Path
from typing import Dict, Any
import os

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file and return as dictionary."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content=f.read()
            content=os.path.expandvars(content)
            return yaml.safe_load(content)
    except Exception as e:
        raise Exception(f"Error loading configuration: {str(e)}")


config = load_config()

