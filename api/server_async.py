from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import argparse

# Import your playwright manager
from litewebagent_async.webagent_utils_async.utils.playwright_manager import setup_playwright, AsyncPlaywrightManager
from litewebagent_async.core.agent_factory import setup_function_calling_web_agent

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store playwright managers
playwright_managers: Dict[str, AsyncPlaywrightManager] = {}

class PlaywrightConfig(BaseModel):
    session_id: str
    storage_state: Optional[str] = 'state.json'
    headless: Optional[bool] = False
    mode: Optional[str] = "cdp"

class ConnectConfig(BaseModel):
    session_id: str

@app.post("/create-playwright-manager")
async def create_playwright_manager(config: PlaywrightConfig):
    """Create a new playwright manager instance without initializing it"""
    if config.session_id in playwright_managers:
        raise HTTPException(status_code=400, detail="Session ID already exists")
    print(config)
    
    playwright_manager = await setup_playwright(storage_state=config.storage_state, headless=config.headless, mode=config.mode)
    
    playwright_managers[config.session_id] = playwright_manager
    
    return {"status": "success", "message": f"Created playwright manager with session ID: {config.session_id}"}

@app.post("/connect-playwright-manager")
async def connect_playwright_manager(config: ConnectConfig):
    """Initialize and connect to an existing playwright manager instance"""
    if config.session_id not in playwright_managers:
        raise HTTPException(status_code=404, detail="Session ID not found")
    
    playwright_manager = playwright_managers[config.session_id]
    
    try:
        return {
            "status": "success",
            "message": f"Connected to playwright manager with session ID: {config.session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")

@app.post("/close-playwright-manager")
async def close_playwright_manager(config: ConnectConfig):
    """Close and cleanup a playwright manager instance"""
    if config.session_id not in playwright_managers:
        raise HTTPException(status_code=404, detail="Session ID not found")
    
    playwright_manager = playwright_managers[config.session_id]
    
    try:
        await playwright_manager.close()
        del playwright_managers[config.session_id]
        return {
            "status": "success",
            "message": f"Closed playwright manager with session ID: {config.session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close: {str(e)}")

class AgentRequest(BaseModel):
    session_id: str
    starting_url: str
    goal: str
    plan: Optional[str] = None

@app.post("/run-agent-initial-steps")
async def run_agent_initial_steps(request: AgentRequest):
    """Initialize and connect to an existing playwright manager instance"""
    if request.session_id not in playwright_managers:
        raise HTTPException(status_code=404, detail="Session ID not found")
    
    playwright_manager = playwright_managers[request.session_id]
    agent_type = "FunctionCallingAgent"
    model = "gpt-4o-mini"
    features = "axtree"
    log_folder = "log"
    elements_filter = "som"

    agent = await setup_function_calling_web_agent(
        starting_url=request.starting_url,
        goal=request.goal,
        playwright_manager=playwright_manager,
        model_name=model,
        agent_type=agent_type,
        features=features,
        tool_names=["navigation", "select_option", "upload_file"],
        log_folder=log_folder,
        elements_filter=elements_filter
    )
    response = await agent.send_prompt(request.plan)  # Added await here
    print(response)
    return {"status": "agent running", "response": response}

class AgentFollowUpRequest(BaseModel):
    session_id: str
    plan: str

@app.post("/run-agent-followup-steps")
async def run_agent_followup_steps(request: AgentFollowUpRequest):
    """Initialize and connect to an existing playwright manager instance"""
    if request.session_id not in playwright_managers:
        raise HTTPException(status_code=404, detail="Session ID not found")
    
    playwright_manager = playwright_managers[request.session_id]
    agent_type = "FunctionCallingAgent"
    model = "gpt-4o-mini"
    features = "axtree"
    log_folder = "log"
    elements_filter = "som"

    agent = await setup_function_calling_web_agent(
        None,
        goal=request.plan,
        playwright_manager=playwright_manager,
        model_name=model,
        agent_type=agent_type,
        features=features,
        tool_names=["navigation", "select_option", "upload_file"],
        log_folder=log_folder,
        elements_filter=elements_filter
    )
    response = await agent.send_prompt(request.plan) 
    print(response)
    return {"status": "agent running", "response": response}


@app.get("/list-sessions")
async def list_sessions():
    """List all active playwright manager sessions"""
    return {
        "sessions": list(playwright_managers.keys()),
        "count": len(playwright_managers)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=args.port, reload=True)