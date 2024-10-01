import time
import os
import logging
from openai import OpenAI
from litewebagent.utils.utils import encode_image

logger = logging.getLogger(__name__)
openai_client = OpenAI()


def capture_post_action_feedback(page, action, goal, log_folder):
    screenshot_path_post = os.path.join(log_folder, 'screenshots', 'screenshot_post.png')
    time.sleep(3)
    page.screenshot(path=screenshot_path_post)
    base64_image = encode_image(screenshot_path_post)
    prompt = f"""
    After we take action {action}, a screenshot was captured.

    # Screenshot description:
    The image provided is a screenshot of the application state after the action was performed.

    # The original goal:
    {goal}

    Based on the screenshot and the updated Accessibility Tree, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant.
    """

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

    return response.choices[0].message.content
