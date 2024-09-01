from pydantic import BaseModel
import math

def parse_oai_logprob(response):
    response_logprob = 0
    try:
        for content in response.choices[0].logprobs.content:
            response_logprob += content.logprob
        return round(math.exp(response_logprob),5)
    except Exception as e:
        print(f"An error occurred when checking oai logprob: {e}") 


def goal_finished_evaluator(messages, openai_client):    
    class Plan(BaseModel):
        goal_finished: bool


    new_response = openai_client.beta.chat.completions.parse(
        model='gpt-4o-mini',
        messages=messages,
        response_format=Plan,
        logprobs=True,        
    )
    message = new_response.choices[0].message.parsed
    score = parse_oai_logprob(new_response)

    goal_finished = message.goal_finished
    return goal_finished, score