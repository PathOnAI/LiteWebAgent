from dotenv import load_dotenv

_ = load_dotenv()
from litewebagent.agents.webagent import setup_web_agent

agent_type = "FunctionCallingAgent"
starting_url = "https://www.google.com"
goal = 'search dining table'
plan = ''
log_folder = "log"
model = "gpt-4o-mini"
features = "axtree"
branching_factor = None
storage_state = 'state.json'

agent = setup_web_agent(starting_url, goal, model_name=model, agent_type=agent_type, features=features,
                        branching_factor=branching_factor, log_folder=log_folder, storage_state=storage_state)
response = agent.send_prompt(plan)
print(response)
print(agent.messages)
