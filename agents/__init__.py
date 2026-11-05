# agents/__init__.py
import importlib
import pkgutil
import os
from typing import Dict
from .base_agent import BaseAgent

def discover_agents() -> Dict[str, BaseAgent]:
    """Auto-discover all agents in subfolders."""
    agents = {}
    
    for _, name, is_pkg in pkgutil.iter_modules(__path__):
        if not is_pkg:
            continue  # Skip files like base_agent.py
        
        # Try 'agent.py' first, then '{name}_agent.py', then any '*_agent.py'
        module_paths_to_try = [
            f".{name}.agent",
            f".{name}.{name}_agent",
            f".{name}.mail_agent",      # explicit for bussiness
            f".{name}.research_agent",  # explicit for researcher
        ]
        
        module = None
        for path in module_paths_to_try:
            try:
                module = importlib.import_module(path, package=__name__)
                break
            except ModuleNotFoundError:
                continue
        
        if module is None:
            print(f"Could not load agent '{name}' — no agent.py or *_agent.py found")
            continue
        
        # Find class that extends BaseAgent
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) 
                and issubclass(attr, BaseAgent) 
                and attr != BaseAgent):
                try:
                    instance = attr()
                    agents[attr.NAME] = instance
                    print(f"Loaded agent: {attr.NAME}")
                except Exception as e:
                    print(f"Failed to instantiate agent in '{name}': {e}")
    
    return agents

AGENTS_REGISTRY = discover_agents()