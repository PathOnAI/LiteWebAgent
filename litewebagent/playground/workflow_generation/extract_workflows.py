import openai
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
from openai import OpenAI
_ = load_dotenv()
openai_client = OpenAI()

import re

def clean_json_string(json_string):
    # Remove the triple backticks and "json" at the start and end
    cleaned = re.sub(r'^```json\s*|\s*```$', '', json_string.strip())
    # Replace any escaped double quotes with actual double quotes
    cleaned = cleaned.replace('\\"', '"')
    # Remove any leading/trailing whitespace
    cleaned = cleaned.strip()
    return cleaned
def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def extract_workflows(text_content):
    prompt = f"""
    Extract workflows from the following documentation text. Each workflow should have a title and a list of steps. Format the output as a JSON array of objects, where each object represents a workflow with 'title' and 'steps' keys. The 'steps' should be an array of strings.

    Documentation text:
    {text_content}

    Example format:
    [
        {{
            "title": "Workflow Title",
            "steps": [
                "Step 1",
                "Step 2",
                "Step 3"
            ]
        }}
    ]
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts workflows from documentation."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        n=1,
        temperature=0.5,
    )

    workflows_json = response.choices[0].message.content.strip()
    cleaned_json = clean_json_string(workflows_json)
    return json.loads(cleaned_json)

# Read the HTML file
with open('create_a_doc.htm', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Extract text from HTML
text_content = extract_text_from_html(html_content)

# Extract workflows using OpenAI API
workflows = extract_workflows(text_content)

# Save as JSON
with open('workflows.json', 'w', encoding='utf-8') as json_file:
    json.dump(workflows, json_file, indent=4, ensure_ascii=False)

# Save as formatted text
with open('workflows.txt', 'w', encoding='utf-8') as txt_file:
    for i, workflow in enumerate(workflows, 1):
        txt_file.write(f"Workflow {i}:\n")
        txt_file.write(f"Title: {workflow['title']}\n")
        txt_file.write("Steps:\n")
        for j, step in enumerate(workflow['steps'], 1):
            txt_file.write(f"  {j}. {step}\n")
        txt_file.write("\n")

# Print confirmation
print("Workflows saved to 'workflows.json' and 'workflows.txt'")

# Print the extracted workflows
for i, workflow in enumerate(workflows, 1):
    print(f"Workflow {i}:")
    print(f"Title: {workflow['title']}")
    print("Steps:")
    for j, step in enumerate(workflow['steps'], 1):
        print(f"  {j}. {step}")
    print()