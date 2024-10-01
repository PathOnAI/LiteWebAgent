import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from litewebagent.browser_env.observation import (
    _pre_extract,
    _post_extract,
    extract_dom_snapshot,
    extract_dom_extra_properties,
    extract_merged_axtree,
    extract_focused_element_bid,
)
from litewebagent.browser_env.extract_elements import extract_interactive_elements
from openai import OpenAI
import os
import re
import json
from litewebagent.utils.utils import encode_image
from dotenv import load_dotenv
_ = load_dotenv()
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Initialize the Eleven Labs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import argparse
from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.utils.playwright_manager import PlaywrightManager
from litewebagent.action.base import execute_python_code
import time
import logging
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str

logger = logging.getLogger(__name__)
from litewebagent.utils.utils import setup_logger


def read_steps_json(file_path):
    goal = None
    starting_url = None
    steps = []

    # Ensure the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return goal, starting_url, steps

    with open(file_path, 'r') as file:
        for i, line in enumerate(file):
            if i == 0:
                # First line is the starting_url (plain string)
                goal = line.strip()
            if i == 1:
                # First line is the starting_url (plain string)
                starting_url = line.strip()
            else:
                try:
                    # Subsequent lines are JSON objects
                    step = json.loads(line.strip())
                    steps.append(step)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON on line {i + 1}: {line}")
                    print(f"Error message: {str(e)}")

    return goal, starting_url, steps


def find_matching_element(interactive_elements, target):
    for element in interactive_elements:
        if (element.get('text', '').lower() == target.get('text', '').lower() and
                element.get('tag') == target.get('tag') and
                target.get('id') == element.get('id')):
            return element
    return None


def find_match(interactive_elements, key, value):
    for element in interactive_elements:
        if element.get(key, '') == value:
            return element
    return None


def replace_number(text, new_number):
    # Find the first number in the string and replace it
    return re.sub(r'\d+', str(new_number), text)


def take_action(step, playwright_manager, is_replay, log_folder):
    # Setup
    time.sleep(5)
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    action_set = HighLevelActionSet(
        subsets=["bid", "nav"],
        strict=False,
        multiaction=True,
        demo_mode="default"
    )

    _pre_extract(page)
    dom = extract_dom_snapshot(page)
    axtree = extract_merged_axtree(page)
    focused_element_bid = extract_focused_element_bid(page)
    extra_properties = extract_dom_extra_properties(dom)
    # Import necessary utilities
    dom_txt = flatten_dom_to_str(dom)
    axtree_txt = flatten_axtree_to_str(axtree)
    interactive_elements = extract_interactive_elements(page)
    screenshot_path_pre = os.path.join(log_folder, 'screenshots', 'screenshot_pre.png')
    page.screenshot(path=screenshot_path_pre)
    _post_extract(page)
    url = page.url
    element = find_matching_element(interactive_elements, step)
    if element:
        action = replace_number(step["action"], element['bid'])
    else:
        action = step["action"]
    code, function_calls = action_set.to_python_code(action)
    logger.info("Executing action script")
    if is_replay:
        audio = elevenlabs_client.generate(
            text=action,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from threading import Event

        audio_finished = Event()

        def play_audio():
            play(audio)
            audio_finished.set()

        with ThreadPoolExecutor(max_workers=1) as executor:
            audio_future = executor.submit(play_audio)

            # Execute code in the main thread
            execute_python_code(
                code,
                page,
                context,
                send_message_to_user=None,
                report_infeasible_instructions=None,
            )

            # Wait for audio to finish if it hasn't already
            audio_finished.wait()

        # Check for any exceptions in the audio thread
        try:
            audio_future.result()
        except Exception as e:
            logger.error(f"An error occurred during audio playback: {str(e)}")
    else:
        # Execute code in the main thread
        execute_python_code(
            code,
            page,
            context,
            send_message_to_user=None,
            report_infeasible_instructions=None,
        )

    if is_replay:
        task_description = step["task_description"]
        page = playwright_manager.get_page()
        screenshot_path_post = os.path.join(log_folder, 'screenshots', 'screenshot_post.png')
        time.sleep(3)
        page.screenshot(path=screenshot_path_post)
        base64_image = encode_image(screenshot_path_post)
        prompt = f"""
                    After we take action {action}, a screenshot was captured.
    
                    # Screenshot description:
                    The image provided is a screenshot of the application state after the action was performed.
    
                    # The original goal:
                    {task_description}
    
                    Based on the screenshot and the updated Accessibility Tree, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant.
                    """

        # Query OpenAI model
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
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
        )

        feedback = response.choices[0].message.content
        return action, feedback
    else:
        return action, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
    args = parser.parse_args()

    log_folder = args.log_folder
    logger = setup_logger(log_folder, log_file="replay_log.txt")
    # Example usage
    playwright_manager = PlaywrightManager(storage_state=None, video_dir=os.path.join(args.log_folder, 'videos'))
    browser = playwright_manager.get_browser()
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    file_path = os.path.join(log_folder, 'flow', 'steps.json')
    goal, starting_url, steps = read_steps_json(file_path)
    page.goto(starting_url)
    page.set_viewport_size({"width": 1440, "height": 900})
    messages = [{"role": "system",
                 "content": "You are a smart web search agent to perform search and click task, upload files for customers"}]
    for i, step in enumerate(steps, 1):
        print(f"Step {i}:")
        print(json.dumps(step))
        task_description = step["task_description"]
        action, feedback = take_action(step, playwright_manager, True, log_folder)
        content = "The task_description is: {}, the action is: {} and the feedback is: {}".format(task_description,
                                                                                                  action, feedback)
        messages.append({"role": "assistant", "content": content})
    messages.append({"role": "user", "content": "summarize the status of the task, be concise"})
    response = openai_client.chat.completions.create(model="gpt-4o", messages=messages)
    summary = response.choices[0].message.content
    playwright_manager.close()
    print(summary)
    audio = elevenlabs_client.generate(
        text=summary,
        voice="Rachel",
        model="eleven_multilingual_v2"
    )
    play(audio)
