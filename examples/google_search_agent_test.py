from dotenv import load_dotenv

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_search_agent

agent_type = "PromptSearchAgent"
starting_url = "https://www.google.com"
goal = 'search dining table'
plan = None
log_folder = "log"
model = "gpt-4o-mini"
features = "axtree"
branching_factor = None
storage_state = None

agent = setup_search_agent(starting_url, goal, model_name=model, agent_type=agent_type, features=features,
                           branching_factor=branching_factor, log_folder=log_folder, storage_state=storage_state)
trajectories = agent.send_prompt(plan)
print(trajectories)
