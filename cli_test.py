import typer
from typing import List, Optional
from enum import Enum
from dotenv import load_dotenv
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
import time
from pathlib import Path

_ = load_dotenv()

from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.utils.playwright_manager import setup_playwright


import json
from dotenv import load_dotenv
from enum import Enum
from pathlib import Path

from pprint import pprint

from openai import OpenAI
load_dotenv()
client = OpenAI()


class AgentType(str, Enum):
    function_calling = "FunctionCallingAgent"
    high_level_planning = "HighLevelPlanningAgent"
    context_aware_planning = "ContextAwarePlanningAgent"
    prompt_search = "PromptSearchAgent"
    prompt = "PromptAgent"


class ToolName(str, Enum):
    navigation = "navigation"
    select_option = "select_option"
    upload_file = "upload_file"
    webscraping = "webscraping"

def deep_merge_configs(defaults, extracted):
    """
    Merges extracted configuration with defaults, preferring extracted values only when they are 
    explicitly specified and not None. The defaults serve as a base configuration that will only 
    be overridden by actual values from the extraction.
    
    Args:
        defaults (dict): The default configuration dictionary that serves as the base
        extracted (dict): The extracted configuration dictionary from user input
    
    Returns:
        dict: Merged configuration with proper types, preferring non-None extracted values
    """
    # Create a new dictionary to store our final configuration
    config = defaults.copy()
    
    # Get the inner defaults dictionary from the extracted data
    # If there's no 'defaults' key or if its value is None, we'll just use our default config
    extracted_defaults = extracted.get('defaults')
    if extracted_defaults is None:
        return config
    
    # For each key in our default configuration
    for key, default_value in config.items():
        # Only override the default if:
        # 1. The key exists in extracted_defaults
        # 2. The value is not None
        if key in extracted_defaults and extracted_defaults[key] is not None:
            config[key] = extracted_defaults[key]
    
    # After merging, convert the string values to their proper types
    try:
        # Convert agent_type to proper enum if it's a string
        if isinstance(config["agent_type"], str):
            config["agent_type"] = AgentType(config["agent_type"])
        
        # Convert tool_names to list of proper enums if it's a list
        if isinstance(config["tool_names"], list):
            config["tool_names"] = [ToolName(t) for t in config["tool_names"]]
        
        # Convert path strings to Path objects
        if isinstance(config["log_folder"], str):
            config["log_folder"] = Path(config["log_folder"])
        
        if isinstance(config["storage_state"], str):
            config["storage_state"] = Path(config["storage_state"])
            
    except (ValueError, KeyError) as e:
        # Add error handling for type conversions
        raise ValueError(f"Error converting types in configuration: {str(e)}")
    
    return config



def extract_config(description):
    # Default values
    defaults = {
        "url": "https://www.google.com",
        "goal": "search dining table",
        "agent_type": AgentType.function_calling,
        "model": "gpt-4-0613",
        "features": ["axtree"],
        "elements_filter": "som",
        "tool_names": list(ToolName),
        "branching_factor": None,
        "log_folder": Path("log"),
        "headless": False,
        "storage_state": Path("state.json")
    }

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You extract configuration details from the given description. Respond with JSON data of the extracted details."
            },
            {
                "role": "user",
                "content": f"Extract configuration details from this description: {description}"
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "extract_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "defaults": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "format": "uri"
                                },
                                "goal": {
                                    "type": "string"
                                },
                                "agent_type": {
                                    "type": "string",
                                    "enum": ["FunctionCallingAgent", "HighLevelPlanningAgent", "ContextAwarePlanningAgent", "PromptSearchAgent", "PromptAgent"]
                                },
                                "model": {
                                    "type": "string"
                                },
                                "features": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "elements_filter": {
                                    "type": "string"
                                },
                                "tool_names": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["navigation", "select_option", "upload_file", "webscraping"]
                                    }
                                },
                                "branching_factor": {
                                    "type": ["null", "number"]
                                },
                                "log_folder": {
                                    "type": "string"
                                },
                                "headless": {
                                    "type": "boolean"
                                },
                                "storage_state": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "url",
                                "goal",
                                "agent_type",
                                "model",
                                "features",
                                "elements_filter",
                                "tool_names",
                                "log_folder",
                                "headless",
                                "storage_state"
                            ],
                            "additionalProperties": False,
                            "nullable": True
                        }
                    },
                    "required": ["defaults"],
                    "additionalProperties": False,
                }
            }
        }
    )

    extracted = json.loads(response.choices[0].message.content)

    return deep_merge_configs(defaults, extracted)



# # Example usage
# description = """
# I want to search for the best restaurants in New York City. Use the high-level planning agent with GPT-4 model.
# I need navigation and webscraping tools. Run it in headless mode and save logs in the 'nyc_food' folder.
# """

# config = extract_config(description)
# pprint(config)

# Initialize Rich console
console = Console()

class AgentType(str, Enum):
    function_calling = "FunctionCallingAgent"
    high_level_planning = "HighLevelPlanningAgent"
    context_aware_planning = "ContextAwarePlanningAgent"
    prompt_search = "PromptSearchAgent"
    prompt = "PromptAgent"

class ToolName(str, Enum):
    navigation = "navigation"
    select_option = "select_option"
    upload_file = "upload_file"
    webscraping = "webscraping"

def validate_url(url: str) -> str:
    """Validate URL has proper format"""
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url

def get_interactive_config():
    """Get all configuration parameters interactively"""
    console.print("\n[bold cyan]Welcome to Web Agent Setup![/bold cyan]")
    console.print("Press Enter to accept default values or input your own.\n")

    # URL and Goal
    url = Prompt.ask("Enter the starting URL", default="https://www.google.com")
    goal = Prompt.ask("Enter the goal", default="search dining table")

    # Agent Type
    agent_types = [t.value for t in AgentType]
    agent_type_str = Prompt.ask(
        "Select agent type",
        choices=agent_types,
        default=AgentType.function_calling.value
    )
    agent_type = AgentType(agent_type_str)

    # Model
    model = Prompt.ask("Enter model name", default="gpt-4o-mini")

    # Features
    features_str = Prompt.ask("Enter features (comma-separated)", default="axtree")
    features = [f.strip() for f in features_str.split(",")]

    # Elements Filter
    elements_filter = Prompt.ask("Enter elements filter", default="som")

    # Tool Names
    available_tools = [t.value for t in ToolName]
    tools_str = Prompt.ask(
        "Enter tool names (comma-separated)",
        default=",".join(available_tools)
    )
    tool_names = [ToolName(t.strip()) for t in tools_str.split(",")]

    # Branching Factor
    branching_factor_str = Prompt.ask("Enter branching factor (optional)", default="")
    branching_factor = int(branching_factor_str) if branching_factor_str.isdigit() else None

    # Log Folder
    log_folder = Path(Prompt.ask("Enter log folder path", default="log"))

    # Headless Mode
    headless = Confirm.ask("Run in headless mode?", default=False)

    # Storage State
    storage_state = Prompt.ask("Enter storage state file path", default="state.json")
    storage_state = Path(storage_state)

    return {
        "url": url,
        "goal": goal,
        "agent_type": agent_type,
        "model": model,
        "features": features,
        "elements_filter": elements_filter,
        "tool_names": tool_names,
        "branching_factor": branching_factor,
        "log_folder": log_folder,
        "headless": headless,
        "storage_state": storage_state
    }

import typer
from typing import List, Optional
from enum import Enum
from dotenv import load_dotenv
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
import time
from pathlib import Path
from typing import Optional

_ = load_dotenv()

from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.utils.playwright_manager import setup_playwright

# Initialize Rich console
console = Console()

class Mode(str, Enum):
    description = "description"
    voice = "voice"
    interactive = "interactive"

def run_description_mode(description: str, config=None):
    """Run the web agent using a natural language description"""
    try:
        if config is None:
            config = extract_config(description)
        
        console.print("\n[bold cyan]Extracted Configuration:[/bold cyan]")
        for key, value in config.items():
            console.print(f"{key}: {value}")
            
        return run_agent_with_config(config)
        
    except Exception as e:
        console.print(f"[bold red]Error in description mode: {str(e)}")
        raise typer.Exit(1)

def run_voice_mode():
    """Placeholder for voice mode implementation"""
    console.print("[bold yellow]Voice mode is not yet implemented[/bold yellow]")
    raise typer.Exit(0)

def run_interactive_mode():
    """Run the web agent in interactive configuration mode"""
    try:
        config = get_interactive_config()
        return run_agent_with_config(config)
        
    except Exception as e:
        console.print(f"[bold red]Error in interactive mode: {str(e)}")
        raise typer.Exit(1)

def run_agent_with_config(config):
    """Common function to run the agent with a given configuration"""
    try:
        # Create log folder if it doesn't exist
        config["log_folder"].mkdir(parents=True, exist_ok=True)
        
        # Validate and clean URL
        starting_url = validate_url(config["url"])
        
        with console.status("[bold green]Setting up playwright...") as status:
            playwright_manager = setup_playwright(
                log_folder=str(config["log_folder"]),
                storage_state=str(config["storage_state"]),
                headless=config["headless"]
            )
            
            status.update("[bold green]Initializing agent...")
            agent = setup_function_calling_web_agent(
                starting_url,
                config["goal"],
                playwright_manager=playwright_manager,
                model_name=config["model"],
                agent_type=config["agent_type"].value,
                features=config["features"],
                elements_filter=config["elements_filter"],
                tool_names=[t.value for t in config["tool_names"]],
                branching_factor=config["branching_factor"],
                log_folder=str(config["log_folder"])
            )
            
            status.update("[bold green]Agent ready!")
            
        # Initial response
        with console.status("[bold green]Getting initial response..."):
            response = agent.send_prompt(None)
            console.print("[bold green]Initial response:[/bold green]")
            console.print(response)
        
        # Interactive command loop
        console.print("\n[bold cyan]Entering interactive mode. Type 'exit' or 'quit' to end the session.[/bold cyan]")
        
        while True:
            try:
                user_input = typer.prompt("\n[bold cyan]Enter your command")
                
                if user_input.lower() in ('exit', 'quit', 'q'):
                    console.print("[bold green]Goodbye!")
                    break
                    
                with console.status("[bold green]Processing...") as status:
                    response = agent.send_prompt(user_input)
                    console.print("[bold green]Response:[/bold green]")
                    console.print(response)
                    
            except KeyboardInterrupt:
                console.print("\n[bold red]Interrupted by user. Exiting...")
                break
            except Exception as e:
                console.print(f"[bold red]Error: {str(e)}")
                
    except Exception as e:
        console.print(f"[bold red]Error running agent: {str(e)}")
        raise typer.Exit(1)
    finally:
        if 'playwright_manager' in locals():
            playwright_manager.cleanup()

def main(
    mode: Mode = typer.Option(Mode.interactive, help="Mode to run the agent in"),
    description: Optional[str] = typer.Option(None, help="Natural language description of what you want the agent to do")
):
    """
    Run the web agent in different modes:
    - description: Use natural language to describe what you want
    - voice: Use voice commands (not implemented yet)
    - interactive: Configure the agent step by step
    """
    try:
        if mode == Mode.description:
            if description is None:
                description = typer.prompt("Enter your description")
            run_description_mode(description)
        elif mode == Mode.voice:
            run_voice_mode()
        else:  # interactive mode
            run_interactive_mode()
            
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    typer.run(main)
