from dotenv import load_dotenv

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_function_calling_web_agent

agent_type = "FunctionCallingAgent"
starting_url = "https://www.google.com"
goal = 'search dining table, and scrape the search result page'
plan = None
log_folder = "log"
model = "gpt-4o-mini"
features = "axtree"
branching_factor = None
storage_state = None

agent = setup_function_calling_web_agent(starting_url, goal, model_name=model, agent_type=agent_type, features=features,
                        tool_names = ["navigation", "select_option", "upload_file", "webscraping"], branching_factor=branching_factor, log_folder=log_folder, storage_state=storage_state)
response = agent.send_prompt(plan)
print(response)