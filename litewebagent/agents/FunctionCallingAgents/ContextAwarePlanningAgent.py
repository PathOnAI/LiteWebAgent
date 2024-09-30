# Reference: https://github.com/OSU-NLP-Group/SeeAct/blob/main/seeact_package/seeact/agent.py#L163
from litellm import completion
from litewebagent.agents.FunctionCallingAgents.BaseAgent import BaseAgent
from typing import Dict
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
import os
from litewebagent.utils.utils import encode_image
import time
from litewebagent.browser_env.observation import (
    _pre_extract,
    extract_dom_snapshot,
    extract_merged_axtree,
)

_ = load_dotenv()

openai_client = OpenAI()
logger = logging.getLogger(__name__)


class ContextAwarePlanningAgent(BaseAgent):

    def send_completion_request(self, plan: str, depth: int = 0) -> Dict:
        if plan is None and depth == 0:
            plan = self.make_plan()
        if depth >= 8:
            return None

        if not self.tools:
            response = completion(model=self.model_name, messages=self.messages)
            logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                        str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
            logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        logger.info("last message: %s", json.dumps(self.messages[-1]))
        logger.info('current plan: %s', plan)

        if depth > 0:
            from pydantic import BaseModel
            class Plan(BaseModel):
                goal_finished: bool

            # TODO: adapt prompt
            context = self.playwright_manager.get_context()
            page = self.playwright_manager.get_page()
            time.sleep(3)
            _pre_extract(page)
            dom = extract_dom_snapshot(page)
            axtree = extract_merged_axtree(page)
            # update plan, and next action generation
            screenshot_path_post = os.path.join(self.log_folder, 'screenshots', 'screenshot_next.png')
            time.sleep(3)
            page.screenshot(path=screenshot_path_post)
            base64_image = encode_image(screenshot_path_post)
            prompt = f"""
            After we take action, a screenshot was captured.

            # Screenshot description:
            The image provided is a screenshot of the application state after the action was performed.

            # The current goal:
            {self.goal}
            
            # The original goal:
            {plan}

            Based on the progress made so far, please provide:

            1. An updated complete plan
            2. A list of tasks that have already been completed
            3. An explanation of changes and their rationale

            Format your response as follows:

            Updated Plan:
            - [Step 1]
            - [Step 2]
            - ...

            Completed Tasks:
            - [Task 1]
            - [Task 2]
            - ...
            """

            system_prompt = '''
            You are assisting humans doing web navigation tasks step by step. At each stage, you can see the webpage by a screenshot and know the previous actions before the current step decided by yourself that have been executed for this task through recorded history. You need to decide on the first following action to take.
            '''

            action_space_prompt = '''
            Here are the descriptions of all allowed actions:

            No Value Operations:
            - CLICK: Click on a webpage element using the mouse.
            - HOVER: Move the mouse over a webpage element without clicking.
            - PRESS ENTER: Press the Enter key, typically to submit a form or confirm an input.
            - SCROLL UP: Scroll the webpage upwards by half of the window height.
            - SCROLL DOWN: Scroll the webpage downwards by half of the window height.
            - PRESS HOME: Scroll to the top of the webpage.
            - PRESS END: Scroll to the bottom of the webpage.
            - PRESS PAGEUP: Scroll up by one window height.
            - PRESS PAGEDOWN: Scroll down by one window height.
            - CLOSE TAB: Close the current tab in the browser.
            - NEW TAB: Open a new tab in the browser.
            - GO BACK: Navigate to the previous page in the browser history.
            - GO FORWARD: Navigate to the next page in the browser history.
            - TERMINATE: End the current task, typically used when the task is considered complete or requires potentially harmful actions.
            - NONE: Indicates that no action is necessary at this stage. Used to skip an action or wait.

            With Value Operations:
            - SELECT: Choose an option from a dropdown menu or <select> element. The value indicates the option to select.
            - TYPE: Enter text into a text area or text box. The value is the text to be typed.
            - GOTO: Navigate to a specific URL. The value is the URL to navigate to.
            - SAY: Output answers or other information you want to tell the user.
            - MEMORIZE: Keep some content into action history to memorize it.
            '''

            question_description_prompt = '''The screenshot below shows the webpage you see. Think step by step before outlining the next action step at the current stage. Clearly outline which element in the webpage users will operate with as the first next target element, its detailed location, and the corresponding operation.

            To be successful, it is important to follow the following rules: 
            1. You should only issue a valid action given the current browser_env. 
            2. You should only issue one action at a time
            3. For handling the select dropdown elements on the webpage, it's not necessary for you to provide completely accurate options right now. The full list of options for these elements will be supplied later.
            4. Unlike humans, for typing (e.g., in text areas, text boxes) and selecting (e.g., from dropdown menus or <select> elements), you should try directly typing the input or selecting the choice, bypassing the need for an initial click. 
            5. You should not attempt to create accounts, log in or do the final submission. 
            6. Terminate when you deem the task complete or if it requires potentially harmful actions.
            7. Do not generate same action as the previous one, try different ways if keep failing
            8. When there is a floating banner like ads, login, or survey floating taking more than 30% of the page, close the floating banner to proceed, the close button could look like a x on the right top corner, or choose NO THANKS to close it.
            9. When there is a floating banner on top or bottom of the page like cookie policy taking less than 30% of the page, ignore the banner to proceed.  
            10. After typing text into search or text input area, the next action is normally PRESS ENTER
            11. When there are bouding boxes in the screenshot, interact with the elements in the bounding boxes
            '''

            # Query OpenAI model
            self.messages.append({"role": "system", "content": system_prompt})
            self.messages.append({"role": "user", "content": action_space_prompt})
            self.messages.append({"role": "user", "content": question_description_prompt})
            self.messages.append({"role": "user",
                                  "content": [
                                      {"type": "text", "text": prompt},
                                      {"type": "image_url",
                                       "image_url": {
                                           "url": f"data:image/jpeg;base64,{base64_image}",
                                           "detail": "high"
                                       }
                                       }
                                  ]
                                  })
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=self.messages
            )

            plan = response.choices[0].message.content
            new_response = openai_client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[{"role": "system", "content": "Is the overall goal finished?"},
                          {"role": "user", "content": plan}],
                response_format=Plan
            )
            message = new_response.choices[0].message.parsed
            goal_finished = message.goal_finished
            if goal_finished:
                logger.info("goal finished")
                return response
            else:
                self.messages.append({"role": "user", "content": plan})

        logger.info('updated plan: %s', plan)
        response = completion(model=self.model_name, messages=self.messages, tools=self.tools, tool_choice="auto")

        logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                    str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)

        if hasattr(response.choices[0].message, 'tool_calls'):
            tool_calls = response.choices[0].message.tool_calls
        else:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        if tool_calls is None or len(tool_calls) == 0:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response
        # limit one function calling at a time
        tool_calls = [tool_calls[0]]

        tool_call_message = {"content": response.choices[0].message.content,
                             "role": response.choices[0].message.role,
                             "tool_calls": tool_calls}

        self.messages.append(tool_call_message)
        tool_responses = self.process_tool_calls(tool_calls)
        self.messages.extend(tool_responses)

        return self.send_completion_request(plan, depth + 1)
