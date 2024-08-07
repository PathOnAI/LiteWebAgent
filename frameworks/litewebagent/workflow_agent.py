import os
import json
from openai import OpenAI
from dotenv import load_dotenv
_ = load_dotenv()

def create_step_functions(step_dict: dict):
    def get_step_description(step_number):
        return step_dict.get(str(step_number), "Step not found")

    def get_step_number(description):
        for key, value in step_dict.items():
            if value == description:
                return int(key)
        return -1

    return get_step_description, get_step_number


class WorkflowAgent:
    def __init__(self, path: str = 'cache'):
        self.client = OpenAI()
        self.model = "gpt-4o"

        # self.webpage_path = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/{path}.txt'

        self.workflow = None

    def set_goal(self, goal: str):
        template = f"""
        Your goal is to determine a workflow for a given task, that can be performed by a browser automation agent in a sequence of tasks, starting at the Google homepage.

        {goal}

        Output the workflow as a JSON object where the keys are numbers and their values are the instructions. For example:

        {{
        "1": "Open Google homepage",
        "2": "Search for 'dining tables on Amazon'",
        "3": "Click on the Amazon link in search results"
        }}
        """

        messages = [
            {"role": "system", "content": "You are a workflow generator that outputs results in JSON."},
            {"role": "user", "content": template}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        workflow_json = json.loads(response.choices[0].message.content)

        self.workflow = {
            **workflow_json,
            # 'finished_steps': [],
            # 'current_step': '',
            # 'overall_goal': goal,
        }

        return self

    def propose_action(self):
        get_description, get_number = create_step_functions(self.workflow)
        # print(self.workflow)
        # c_step = self.workflow.get('current_step')

        # if c_step == '':
        #     self.workflow['current_step'] = get_description(1)
        # else:
        #     number = get_number(c_step)
        #     number += 1
        #     self.workflow['finished_steps'].append(c_step)
        #     self.workflow['current_step'] = get_description(number)

        return self.workflow



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




def main():
    workflow = WorkflowAgent()

    workflow.set_goal('add a random dining table from amazon to my cart')

    step = workflow.propose_action()
    print(step)

if __name__ == "__main__":
    main()
