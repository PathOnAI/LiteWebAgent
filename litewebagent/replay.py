import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from litewebagent.observation.constants import TEXT_MAX_LENGTH, BROWSERGYM_ID_ATTRIBUTE, EXTRACT_OBS_MAX_TRIES
from litewebagent.observation.observation import (
    _pre_extract,
    _post_extract,
    extract_screenshot,
    extract_dom_snapshot,
    extract_dom_extra_properties,
    extract_merged_axtree,
    extract_focused_element_bid,
    MarkingError,
)
from litewebagent.observation.extract_elements import (extract_interactive_elements, highlight_elements)
# , extract_interactive_elements_more_info
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI
# from litellm import completion
import os
import re
import json

_ = load_dotenv()
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Initialize the Eleven Labs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
openai_client = OpenAI()
import argparse
from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.playwright_manager import PlaywrightManager
from litewebagent.playwright_manager import get_browser, get_context, get_page, playwright_manager, close_playwright
from litewebagent.action.base import execute_python_code

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import time
import inspect
from bs4 import BeautifulSoup
import logging
from litewebagent.agents.DemoAgent import DemoAgent
from litewebagent.agents.HighLevelPlanningAgent import HighLevelPlanningAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

# Create a logger
logger = logging.getLogger(__name__)
# "extract all product names of the website screenshot"

import base64

browser = get_browser()
context = get_context()
page = get_page()
playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

file_path = os.path.join('litewebagent', 'flow', 'steps.json')


def read_steps_json(file_path):
    starting_url = None
    steps = []

    # Ensure the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return starting_url, steps

    with open(file_path, 'r') as file:
        for i, line in enumerate(file):
            if i == 0:
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

    return starting_url, steps


# Example usage
starting_url, steps = read_steps_json(file_path)
page.goto(starting_url)
page.set_viewport_size({"width": 1440, "height": 900})


def find_matching_element(interactive_elements, target):
    for element in interactive_elements:
        if (element.get('text', '').lower() == target.get('text', '').lower() and
                element.get('tag') == target.get('tag') and
                target.get('id') == element.get('id')):
            return element
    return None


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def find_match(interactive_elements, key, value):
    for element in interactive_elements:
        if element.get(key, '') == value:
            return element
    return None


def replace_number(text, new_number):
    # Find the first number in the string and replace it
    return re.sub(r'\d+', str(new_number), text)


def take_action(step):
    # Setup
    time.sleep(5)
    context = get_context()
    page = get_page()
    action_set = HighLevelActionSet(
        subsets=["bid", "nav"],
        strict=False,
        multiaction=True,
        demo_mode="default"
    )

    # Extract page information
    # screenshot = extract_screenshot(page)
    _pre_extract(page)
    dom = extract_dom_snapshot(page)
    axtree = extract_merged_axtree(page)
    focused_element_bid = extract_focused_element_bid(page)
    extra_properties = extract_dom_extra_properties(dom)
    # Import necessary utilities
    from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
    dom_txt = flatten_dom_to_str(dom)
    axtree_txt = flatten_axtree_to_str(axtree)
    interactive_elements = extract_interactive_elements(page)
    # highlight_elements(page, interactive_elements)
    screenshot_path_pre = os.path.join(os.getcwd(), 'litewebagent', 'screenshots', 'screenshot_pre.png')
    page.screenshot(path=screenshot_path_pre)
    _post_extract(page)
    url = page.url
    element = find_matching_element(interactive_elements, step)
    print(element)
    print(step["action"])
    print(element['bid'])
    goal = step["goal"]
    action = replace_number(step["action"], element['bid'])
    print(action)
    audio = elevenlabs_client.generate(
        text=action,
        voice="Rachel",
        model="eleven_multilingual_v2"
    )
    # play(audio)
    code, function_calls = action_set.to_python_code(action)
    logger.info("Executing action script")
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

    page = get_page()
    print(page.url)
    screenshot_path_post = os.path.join(os.getcwd(), 'litewebagent', 'screenshots', 'screenshot_post.png')
    time.sleep(3)
    page.screenshot(path=screenshot_path_post)
    base64_image = encode_image(screenshot_path_post)
    # import pdb; pdb.set_trace()
    prompt = f"""
                After we take action {action}, a screenshot was captured.

                # Screenshot description:
                The image provided is a screenshot of the application state after the action was performed.

                # The original goal:
                {goal}

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


messages = [{"role": "system",
             "content": "You are a smart web search agent to perform search and click task, upload files for customers"}]
for i, step in enumerate(steps, 1):
    print(f"Step {i}:")
    print(json.dumps(step))
    goal = step["goal"]
    action, feedback = take_action(step)
    content = "The goal is: {}, the action is: {} and the feedback is: {}".format(goal, action, feedback)
    messages.append({"role": "assistant", "content": content})
messages.append({"role": "user", "content": "summarize the status of the task, be concise"})
response = openai_client.chat.completions.create(model="gpt-4o", messages=messages)
summary = response.choices[0].message.content
close_playwright()
print(summary)
audio = elevenlabs_client.generate(
    text=summary,
    voice="Rachel",
    model="eleven_multilingual_v2"
)
play(audio)
