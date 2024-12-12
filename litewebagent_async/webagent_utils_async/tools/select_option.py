from .shared_utils import take_action
from .registry import ToolRegistry, Tool


def select_option(task_description, features=None, branching_factor=None, playwright_manager=None, log_folder='log', elements_filter=None):
    response = take_action(task_description, ["select_option"], features, branching_factor, playwright_manager,
                           log_folder, elements_filter)
    return response


def register_select_option_tool():
    ToolRegistry.register(Tool(
        name="select_option",
        func=select_option,
        description="Select an option from a dropdown or list.",
        parameters={
            "task_description": {
                "type": "string",
                "description": "The description of the option selection task"
            }
        }
    ))
