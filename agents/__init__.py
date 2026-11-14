import importlib  #runtime p python file ko import karna ke liye
import pkgutil
import os
from typing import Dict #Python type hinting ke liye (batane ke liye ke function Dictionary return karega).
from .base_agent import BaseAgent 
 
def discover_agents() -> Dict[str, BaseAgent]: #keys strings hongi aur values BaseAgent objects honge).
    """Auto-discover all agents in subfolders."""
    agents = {} #agent registry dictionary 
    
    for _, name, is_pkg in pkgutil.iter_modules(__path__): #agent folder k ander hr chiz ko scan krta h 
        if not is_pkg:
            continue  # Skip files like base_agent.py
        
        # list diff nam try kr ri h
        module_paths_to_try = [
            f".{name}.agent",
            f".{name}.{name}_agent",
            f".{name}.mail_agent",      # explicit for bussiness
            f".{name}.research_agent",  # explicit for researcher
        ]
        
        module = None
        for path in module_paths_to_try: #list p loop 
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
                    instance = attr() #class ka object bana rha h
                    agents[attr.NAME] = instance
                    print(f"Loaded agent: {attr.NAME}")
                except Exception as e:
                    print(f"Failed to instantiate agent in '{name}': {e}")
    
    return agents

AGENTS_REGISTRY = discover_agents()