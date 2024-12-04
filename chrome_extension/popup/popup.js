document.getElementById('startAutomation').addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        const config = {
            starting_url: tab.url,
            goal: document.getElementById('goal').value,
            plan: document.getElementById('plan').value,
            model: document.getElementById('model').value,
            features: document.getElementById('features').value,
            elements_filter: document.getElementById('elementsFilter').value,
            branching_factor: parseInt(document.getElementById('branchingFactor').value),
            agent_type: "PromptAgent",
            storage_state: "state.json",
            log_folder: "log"
        };

        console.log('Sending config:', config);

        const response = await fetch('http://localhost:5001/automate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            mode: 'cors',  // Added this line
            body: JSON.stringify(config)
        });

        const result = await response.json();
        console.log('Automation result:', result);
    } catch (error) {
        console.error('Error:', error);
    }
});