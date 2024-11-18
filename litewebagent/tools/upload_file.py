from .shared_utils import take_action
from .registry import ToolRegistry, Tool

def upload_file(task_description, **kwargs):
    response = take_action(task_description, ["file"], **kwargs)
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
