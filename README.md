# WebAgent
repo owners: Danni (Danqing) Zhang (danqing.zhang.personal@gmail.com), and Balaji Rama (balajirw10@gmail.com)

## auto-interact demo
* Loom Url: https://www.loom.com/share/e01a236428b74de59c1f645fa86a575f?sid=72e2e51c-13c0-4ac3-82a1-dff59635e8d0

## Browser Gym
* loom video of the basic agent + browsergym env demo: https://www.loom.com/share/31d8f088106d4367a2a9d69e6fe5779f
* This is an entry point for us to integrate our web agent framework with the BrowserGym environment.

## Plan
### (1) open-source plan
* Danni to finish the initial version of hierarchical multi agent implementation of web agent, using Lavague as a baseline [done, 07/16]
* Balaji to finish the auto-interact framework and record videos [done, 07/19]
* Danni to add example of using a self-defined web agent with browsergym openended environment [done, 07/21]
* Danni and Balaji to consolidate the two frameworks into one [ddl: 07/24]
* integrate the web agent framework with browsergym environment [ddl: 07/2y]

### (2) Paper plan
* Balaji's research plan of bounding html [TBD]
  * parse html prematurely into a set of bounding regions 
  * target regions with llm 
  * use heuristic to write playwright code for given regions

### (3) product plan
* Balaji to work on the first version of the AI companion demo, integrating intent understanding with LLM-based web agent [ddl: 07/23]
  * demo: Amazon Shopping: initial exploration stage 
    * However, I propose building an improved version of the browsing agent. The customer journey could be as follows, using Amazon as an example: First, I log in to Amazon and search for a product, say “dining table.” I get the search results but don’t know which brand to choose, so I check out various brands. The AI agent monitors me, and after observing for a while, it proactively intervenes, saying it notices I am interested in brands and asks how it could help me. Then I tell it: "Help me organize a list to see what brands and products there are." The AI agent does the research for me and generates a file summarizing its findings. 
    * Please note that we don't want the agent to speak out its actions like Multion. We don't even need to visualize the page browsing or mouse movements
* Danni to add example of using self-defined web agent with browsergym workarena and visualwebarena environments [ddl: 07/23]
