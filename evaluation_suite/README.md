# Evaluation
The evaluation suite is a standalone module, extracted and modified from the VisualWebArena and Tree Search Agent repository: https://github.com/kohjingyu/search-agents/tree/main/evaluation_harness.

## evaluation script
```
export DATASET=visualwebarena
export CLASSIFIEDS="http://128.105.146.86:9980"
export CLASSIFIEDS_RESET_TOKEN="4b61655535e7ed388f0d40a93600254c"
export SHOPPING="http://128.105.146.86:7770"
export REDDIT="http://128.105.146.86:9999"
export WIKIPEDIA="http://128.105.146.86:8888"
export HOMEPAGE="http://128.105.146.86:4399"

python3.11 -m run_webarena_evaluate --agent_type FunctionCallingAgent --log_folder log
python3.11 -m run_webarena_evaluate --agent_type FunctionCallingAgent --log_folder log --config_file evaluation_suite/configs/wa_117.json
```

## WebArena
### WebArena 117
```
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url http://128.105.146.86:7770 --goal 'What is the date when I made my first purchase on this site?' --plan 'What is the date when I made my first purchase on this site?' --log_folder log --storage_state evaluation_suite/auth/shopping.json

python3.11 -m function_calling_main --agent_type ContextAwarePlanningAgent --starting_url http://128.105.146.86:7770 --goal 'What is the date when I made my first purchase on this site?' --plan 'What is the date when I made my first purchase on this site?' --log_folder log --storage_state evaluation_suite/auth/shopping.json

python3.11 -m prompting_main --agent_type PromptAgent --starting_url http://128.105.146.86:7770 --goal 'What is the date when I made my first purchase on this site?' --plan 'What is the date when I made my first purchase on this site?' --log_folder log --storage_state evaluation_suite/auth/shopping.json
```

```
## ContextAwarePlanningAgent
Updated Plan:\n1. Confirm the first purchase date from the detailed order view.\n\nCompleted Tasks:\n- Logged into the account on the specific website.\n- Accessed order history by clicking on "My Orders."\n- Used pagination to navigate to the oldest orders.\n- Reviewed order details for the earliest purchase.\n\nExplanation of Changes:\nThe necessary information, including the confirmation of the first purchase date, has been gathered. The plan now focuses on finalizing the task by confirming this detail.\n\n**Next Step:** The first purchase date is confirmed as March 2, 2022. Task complete.'

## function calling agent
'Updated Plan:\n- Step 1: Examine the list of orders to identify and select the earliest date.\n- Step 2: Report the earliest order date as the date of the first purchase.\n\nCompleted Tasks:\n- Task 1: Clicked on "My Account" to access account details.\n- Task 2: Accessed "My Orders" to view order history.\n\nExplanation of Changes:\nThe current focus is to accurately identify the earliest purchase date from the visible order history list, ensuring the primary goal of determining the first purchase date is met efficiently. Let\'s analyze the dates listed.\n\n### Identifying the First Purchase Date:\n- The earliest date visible is **2/11/23**.\n\nWith this information, I will now confirm the date of the first purchase.\n\nTERMINATE: The task is complete.

## prompting agent
The web agent instructed navigating to "My Orders" and clicking the link, resulting in the identification of the first purchase date as February 11, 2023.


## visual webarena prompt agent
2024-12-30 00:54:23,174 - INFO - [Config file]: config_files/wa/test_webarena/117.json
2024-12-30 00:54:23,174 - INFO - [Intent]: What is the date when I made my first purchase on this site?
/Users/danqingzhang/Desktop/LLMWebAgentTreeSearch/shopping.json
2024-12-30 00:54:41,318 - INFO - {'action_type': <ActionTypes.CLICK: 6>, 'coords': array([0., 0.], dtype=float32), 'element_role': 31, 'element_name': '', 'text': [], 'page_number': 0, 'url': '', 'nth': 0, 'pw_code': '', 'element_id': '1129', 'key_comb': '', 'direction': '', 'answer': '', 'raw_prediction': 'To find the date of your first purchase on this site, you\'ll typically need to check your account history or order history. The relevant link to access that information is "My Account." \n\nIn summary, the next action I will perform is ```click [1129]``` to navigate to your account details.'}
[env.step()] get_obs() time taken 4.150367021560669
2024-12-30 00:54:55,337 - INFO - {'action_type': <ActionTypes.STOP: 17>, 'coords': array([0., 0.], dtype=float32), 'element_role': 0, 'element_name': '', 'text': [], 'page_number': 0, 'url': '', 'nth': 0, 'pw_code': '', 'element_id': '', 'key_comb': '', 'direction': '', 'answer': '3/11/23', 'raw_prediction': 'Let\'s analyze the available information. The table under "Recent Orders" shows several orders made with their corresponding dates. \n\nThe earliest order listed is on **3/11/23**. This indicates the date of your first purchase on the site. \n\nIn summary, the next action I will perform is ```stop [3/11/23]```'}
2024-12-30 00:54:56,441 - INFO - [Result] (FAIL) config_files/wa/test_webarena/117.json
2024-12-30 00:54:56,677 - INFO - Average score: 0.0
```

### WebArena 118

### WebArena 124

### WebArena 125

### WebArena 126