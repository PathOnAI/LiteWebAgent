from dotenv import load_dotenv

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.utils.playwright_manager import setup_playwright

agent_type = "FunctionCallingAgent"
starting_url = "https://www.google.com"
goal = 'go to new page: amazon.com'
plan = None
log_folder = "log"
model = "gpt-4o-mini"
features = "axtree"
branching_factor = None
storage_state = None

playwright_manager = setup_playwright(log_folder=log_folder, storage_state='state.json', headless=False)

agent = setup_function_calling_web_agent(starting_url, goal, playwright_manager=playwright_manager, model_name=model, agent_type=agent_type, features=features,
                        tool_names = ["navigation", "select_option", "upload_file", "webscraping"], branching_factor=branching_factor, log_folder=log_folder)
response = agent.send_prompt(plan)
print(response)


## PromptAgent, not recommended
# from litewebagent.core.agent_factory import setup_prompting_web_agent
#
# agent_type = "PromptAgent"
# starting_url = "https://www.google.com"
# goal = 'go to new page: amazon.com'
# plan = None
# log_folder = "log"
# model = "gpt-4o-mini"
# features = "axtree"
# branching_factor = None
# storage_state = None
#
# agent = setup_prompting_web_agent(starting_url, goal, model_name=model, agent_type=agent_type, features=features, branching_factor=branching_factor, log_folder=log_folder, storage_state=storage_state)
# response = agent.send_prompt(plan)
# print(response)