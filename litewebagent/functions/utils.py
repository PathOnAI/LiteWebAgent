import base64
import json

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def parse_function_args(function_args):
    if not function_args or not isinstance(function_args, list):
        return None
    first_arg = function_args[0]
    return first_arg if isinstance(first_arg, str) and first_arg.replace('.', '', 1).isdigit() else None


def append_to_steps_json(result, file_path):
    json_line = json.dumps(result)
    with open(file_path, 'a') as file:
        file.write(json_line + '\n')
    print(f"Appended result to {file_path}")