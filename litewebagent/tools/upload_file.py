from litewebagent.tools.shared_utils import take_action
from litewebagent.tools.registry import ToolRegistry, Tool


def upload_file(task_description, features=None, branching_factor=None, playwright_manager=None, log_folder='log'):
    response = take_action(task_description, ["file"], features, branching_factor, playwright_manager, log_folder)
    return response


def register_upload_file_tool():
    ToolRegistry.register(Tool(
        name="upload_file",
        func=upload_file,
        description="Upload a file.",
        parameters={
            "task_description": {
                "type": "string",
                "description": "The description of the file upload task"
            }
        }
    ))
