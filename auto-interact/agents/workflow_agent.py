import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from playwright.async_api import Page
import os
import json

def create_step_functions(step_dict: dict):
    def get_step_description(step_number):
        return step_dict.get(str(step_number), None)

    def get_step_number(description):
        for key, value in step_dict.items():
            if value == description:
                return int(key)
        return -1

    return get_step_description, get_step_number


class WorkflowAgent:
    def __init__(self, path: str = 'cache'):
        self.config = {
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        self.models = {
            'proposal': genai.GenerativeModel('gemini-1.5-flash', generation_config=self.config, safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
                system_instruction="""
                You are a workflow generator that outputs results in JSON. The output is a JSON object is in the same format as passed to you. You are basically "going down" the workflow list and "checking things off" 
                """
            ),
            'workflow': genai.GenerativeModel('gemini-1.5-flash', generation_config=self.config, safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
                system_instruction="You are a workflow generator that outputs results in JSON. The output is a JSON object where the keys are numbers and their values are the instructions. Be sure to never repeat steps. For example\n\n{\n1: 'Open door',\n2: 'Walk through door',\n3: 'Clean up mess'\n}"
            )}

        self.webpage_path = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/{path}.txt'
        self.steps_path = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/steps.txt'

        self.workflow = None

    def set_goal(self, goal: str):
        # "Help me organize a list to see what brands and products for dining tables there are on Amazon, and give me what you think is the qualitative best choice"

        template = f"""
        Your goal is to determine a workflow for a given task, that can be performed by a browser automation agent in a sequence of tasks, starting at the Google homepage.

        {goal}
        """

        response = self.models.get('workflow').generate_content(template)

        self.workflow: dict[str, str] = {
            **json.loads(response.text),
            'finished_steps': [],
            'current_step': '',
            'overall_goal': goal,
        }

        return self
    
    def propose_resolution(self, template: str = 'cache', code_path: str = ''):
        with open(f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/{template}.txt', 'r+', encoding="utf-8") as f:
            content = f.read()

        with open(self.steps_path, 'r') as file:
            lines = file.readlines()

        with open(code_path, 'r') as file:
            code = file.read()
        
        lines = [line.strip() for line in lines]

        uploaded_file = genai.upload_file(path=f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/snapshot.png', display_name='__')

        template = f"""
        Your goal is to determine a workflow for a given task, that can be performed by a browser automation agent in a sequence of tasks. You will be given \
        the current HTML page, a snapshot of the screen, and a list of the previous steps that have been done successfully, as well as the failed step\
        and the failed code. Ensure that no steps are repeated! Remember to modify workflow as needed\
        so that the overall goal is accomplished. 

        You are to generate a set of instructions to complete the remainder goal. REMEMBER TO USE THE HTML CODE AND SNAPSHOT FOR CONTEXT, AND PLANNING FURTHER STEPS

        Goal: {self.workflow.get('overall_goal')}
        Finished Steps: {', '.join(lines)}
        Failed Step: {self.workflow.get('current_step')}

        HTML Page Code: {content}
        """

        print(f"")

        response = self.models.get('workflow').generate_content([uploaded_file, template])
        

        self.workflow: dict[str, str] = {
            **json.loads(response.text),
            'finished_steps': [],
            'current_step': '',
            'overall_goal': self.workflow.get('overall_goal'),
        }

        return self


    def propose_action(self):
        # with open(self.webpage_path, 'r+') as f:
        #     webpage_content = f.read()

        # response = self.models.get('proposal').generate_content(template)
        # self.workflow = json.loads(response.text)

        get_description, get_number = create_step_functions(self.workflow)
        c_step = self.workflow.get('current_step')

        if c_step == '':
            self.workflow['current_step'] = get_description(1)
        else:
            number = get_number(c_step)
            number += 1
            self.workflow['finished_steps'].append(c_step)
            self.workflow['current_step'] = get_description(number)
        
        if self.workflow['current_step'] == None:
            return None

        print(self.workflow)

        return self.workflow.get('current_step')



        # For example, if you were passed in

        #     {{
        #         'overall_goal': 'find the height of the australian lemur',
        #         'current_step': click on the 'facts of autralian lemur' page,
        #         'finished_steps': ['search up "australian lemur information"'],
        #         '1': 'search up "australian lemur information"',
        #         '2': 'click on the "facts of autralian lemur" page',
        #         '3': 'extract relevant information from the page',
        #     }}

        #     a potential output could be

        #     {{
        #         'overall_goal': 'find the height of the australian lemur',
        #         'current_step': 'search page for information about height',
        #         'finished_steps': ['search up "australian lemur information"', 'click on the "facts of autralian lemur" page'],
        #         '1': 'search up "australian lemur information"',
        #         '2': 'click on the "facts of autralian lemur" page',
        #         '3': 'search page for information about height',
        #         '4': 'extract information about height'
        #     }}

                # template = f"""
        #     HTML Code: {webpage_content}

        #     Current Workflow: {self.workflow}

        #     Given the current workflow, and the current HTML code, read and understand it.
        #     Then, in relation to the current HTML state, the previously finished steps, and the aligned workflow (so like 1,2,3,4,5, etc), modify the workflow so that \
        #     the next step is made the 'current_step'
            
            
        #     Don't change the overall_goal. When the workflow is done, \
        #     set current_step to 'done'. 

        # """
