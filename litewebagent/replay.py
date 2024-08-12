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
#, extract_interactive_elements_more_info
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI
# from litellm import completion
import os
import json
_ = load_dotenv()


openai_client = OpenAI()
import argparse
from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.playwright_manager import PlaywrightManager
from litewebagent.playwright_manager import get_browser, get_context, get_page, playwright_manager
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

# set url
# set workflow
# for each step, find element, and show action around the bounding box