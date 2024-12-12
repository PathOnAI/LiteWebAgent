from dotenv import load_dotenv

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.webagent_utils_sync.utils.playwright_manager import setup_playwright

agent_type = "FunctionCallingAgent"
starting_url = "https://www.google.com"
goal = 'search dining table, and scrape the search result page'
plan = None
log_folder = "log"
model = "gpt-4o-mini"
features = ["axtree"]
branching_factor = None
elements_filter = "som"
storage_state = None

playwright_manager = setup_playwright(log_folder=log_folder, storage_state='state.json', headless=False)
agent = setup_function_calling_web_agent(starting_url, goal, playwright_manager=playwright_manager, model_name=model, agent_type=agent_type, features=features, elements_filter=elements_filter,
                        tool_names = ["navigation", "select_option", "upload_file", "webscraping"], branching_factor=branching_factor, log_folder=log_folder)
response = agent.send_prompt(plan)
print(response)