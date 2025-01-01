import base64
import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
_ = load_dotenv()

logger = logging.getLogger(__name__)
openai_client = OpenAI()


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_task_file(file_name):
    """
    Load and parse task information from a file.
    
    Args:
        file_name (str): Name of the file to read
        
    Returns:
        dict: Dictionary containing:
            - goal: The task goal (str)
            - starting_url: The initial URL (str)
            - step_info: Parsed JSON step information (dict)
            
    Raises:
        FileNotFoundError: If the file cannot be found
        ValueError: If file format is invalid or JSON parsing fails
    """
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            # Split content into lines and remove empty lines
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {file_name}")
    
    # Extract goal and starting URL
    goal = lines[0]
    starting_url = lines[1]
    
    # Parse each remaining line as a separate JSON step
    steps = []
    for i, line in enumerate(lines[2:]):
        try:
            step_info = json.loads(line)
            steps.append(step_info)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format on line {i}: {str(e)}")
    
    return {
        "goal": goal,
        "starting_url": starting_url,
        "step_info": steps
    }

def query_openai_model(system_msg, prompt, screenshot, num_outputs):
    # base64_image = encode_image(screenshot_path)
    base64_image = base64.b64encode(screenshot).decode('utf-8')

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",
             "content": [
                 {"type": "text", "text": prompt},
                 {"type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}",
                      "detail": "high"
                  }
                  }
             ]
             },
        ],
        n=num_outputs
    )

    answer: list[str] = [x.message.content for x in response.choices]
    return answer


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def search_interactive_elements(interactive_elements, extracted_number):
    for element in interactive_elements:
        if element.get('bid') == extracted_number:
            return {
                'text': element.get('text'),
                'type': element.get('type'),
                'tag': element.get('tag'),
                'id': element.get('id'),
                'href': element.get('href'),
                'title': element.get('title'),
                'ariaLabel': element.get('ariaLabel')
            }
    return {}  # Return empty dictionary if no matching element is found

def locate_element(page, extracted_number):
    """
    Safely locate and extract information about an element on a page using Playwright.
    Synchronous version.
    
    Args:
        page: Playwright page object
        extracted_number: ID or data-unique-test-id to search for
        
    Returns:
        dict: Element information or empty dict if not found
    """
    try:
        # Define selectors for potentially interactive elements
        selectors = [
            'a', 'button', 'input', 'select', 'textarea', 'summary', 
            'video', 'audio', 'iframe', 'embed', 'object', 'menu', 
            'label', 'fieldset', 'datalist', 'output', 'details', 
            'dialog', 'option', '[role="button"]', '[role="link"]', 
            '[role="checkbox"]', '[role="radio"]', '[role="menuitem"]', 
            '[role="tab"]', '[tabindex]', '[contenteditable="true"]'
        ]
        
        # Verify page is valid
        if not page or not page.evaluate('() => document.readyState') == 'complete':
            print("Page is not ready or invalid")
            return {}

        # Search for element by ID first (more efficient)
        element = page.query_selector(f'[data-unique-test-id="{extracted_number}"], [id="{extracted_number}"]')
        
        # If not found, then search through individual selectors
        if not element:
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if not elements:
                        continue
                        
                    for el in elements:
                        bid = el.get_attribute('data-unique-test-id') or el.get_attribute('id') or ''
                        if bid == extracted_number:
                            element = el
                            break
                    if element:
                        break
                except Exception as e:
                    print(f"Error searching selector {selector}: {str(e)}")
                    continue
        
        if not element:
            print(f"No element found with ID {extracted_number}")
            return {}
            
        # Extract element properties
        result = {}
        try:
            result = {
                'text': element.inner_text(),
                'type': element.get_attribute('type'),
                'tag': element.evaluate('el => el.tagName.toLowerCase()'),
                'id': element.get_attribute('id'),
                'href': element.get_attribute('href'),
                'title': element.get_attribute('title'),
                'ariaLabel': element.get_attribute('aria-label'),
                'name': element.get_attribute('name'),
                'value': element.get_attribute('value'),
                'placeholder': element.get_attribute('placeholder'),
                'class': element.get_attribute('class'),
                'role': element.get_attribute('role')
            }
            
            # Clean up None values
            result = {k: v for k, v in result.items() if v is not None}
            
        except Exception as e:
            print(f"Error extracting element properties: {str(e)}")
            return {}
                
        return result

    except Exception as e:
        print(f"Error in locate_element: {str(e)}")
        return {}

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
