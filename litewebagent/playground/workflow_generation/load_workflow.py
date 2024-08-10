import json

# Load the workflows from the JSON file
with open('workflows.json', 'r', encoding='utf-8') as json_file:
    workflows = json.load(json_file)

# Access the 2nd workflow (index 1, since lists are 0-indexed)
workflow = workflows[5]

# Print the 2nd workflow
print("Workflow:")
print(f"Title: {workflow['title']}")
print("Steps:")
for i, step in enumerate(workflow['steps'], 1):
    print(f"  {i}. {step}")