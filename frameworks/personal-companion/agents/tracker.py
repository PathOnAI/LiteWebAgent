from groq import Groq
from groq.types.chat import ChatCompletion
import os
import json

from .reader import ReaderAgent

from dotenv import load_dotenv

load_dotenv()


class TrackerAgent:
    def __init__(self, api_key=os.getenv('GROQ_API+KEY')):
        self._client = Groq(api_key=api_key)
        self.conversation = [{
            "role": "system",
            "content": """
            You are an AI assistant capable of taking in information of the user\'s previously visited websites and then understanding their goal and purpose.
            
            Use the following schema = 
                {
                    'goal_known': {boolean either true or false if user goal is 100% known},
                    'purpose': {if goal_known is true, a string containing a description of the purpose with all necessary details, if goal_known is false, is null},
                    'should_jump_in': {boolean either true or false if AI assistant should jummp in}
                }
            """
        }]

    def track(self, tokens=1024, seed=None, filepath=''):

        path_data: list[dict] = ReaderAgent.read_webpage_info(filepath)

        path_data = '\n\n<====>\n\n'.join([
            f"Website Name: {pd.get('name')}\nDescription: {pd.get('description')}\nUser Purpose Guess: {pd.get('venture_guess')}"
            for pd in path_data
        ])

        conversation = self.conversation + [{
            "role": "user",
            "content": f"""
                Given the following sequence of webpages the user visited, including the description of the webpage, along with a *hypothetical* (may not be true, just a guess) explanation of the why user is there \
                , out put a JSON object containing a boolean whether or not you have 100% determined the user's purpose/goal, what that purpose is if known (description) \
                , and a boolean containing whether or not you as an AI assistant should "jump in" and complete the process for the user.

                The AI Assistant should ONLY jump if IT KNOWS EXACTLY WHAT TASK TO BE DONE. FOR EXAMPLE, shooping for items isn't a task, but shopping for \
                dining tables is a task.

                Webpage Sequence: {path_data}
            """
        }]

        completion: ChatCompletion = self._client.chat.completions.create(
            model="llama3-8b-8192",
            messages=conversation,
            temperature=0.2,
            max_tokens=tokens,
            top_p=1,
            stream=False,
            stop=None,
            seed=seed,
            response_format={"type": "json_object"}
        )

        return json.loads(completion.choices[0].message.content)


if __name__ == '__main__':
    t = TrackerAgent()
    s = t.track(filepath='cache/path.txt')
    print(s)
