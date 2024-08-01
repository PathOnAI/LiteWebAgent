import gymnasium as gym
import browsergym.webarena  # register webarena tasks as gym environments

# action_mapping
# env_args = EnvArgs(
#     task_name="openended",
#     task_kwargs={"start_url": "https://www.google.com/"},
#     headless=False,
#     wait_for_user_message=True
# )
# env = env_args.make_env(action_mapping=demo_agent.action_set.to_python_code)  # Replace None with your action mapping if needed
#

env = gym.make("browsergym/webarena.310")
obs, info = env.reset()
done = False
while not done:
    action = ...  # implement your agent here
    obs, reward, terminated, truncated, info = env.step(action)