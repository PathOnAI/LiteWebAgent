import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from queue import Queue
import boto3
from botocore.exceptions import ClientError
import json
import re
import os
_ = load_dotenv()
from .litewebagent.core.agent_factory import setup_function_calling_web_agent
from .litewebagent.utils.playwright_manager import setup_playwright

app = FastAPI()

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    session_id: str
    starting_url: str
    goal: str
    plan: Optional[str] = None
    s3_path: Optional[str] = None
    storage_state_s3_path: Optional[str] = None

def download_storage_state(s3_path: str) -> Optional[str]:
   if not s3_path:
       return None
       
   try:
       s3_client = boto3.client('s3')
       parts = s3_path.replace('s3://', '').split('/')
       bucket = parts[0]
       key = '/'.join(parts[1:])
       
       # First check if the file exists
       try:
           s3_client.head_object(Bucket=bucket, Key=key)
       except ClientError as e:
           if e.response['Error']['Code'] == '404':
               return None
           else:
               raise e
               
       local_path = '/tmp/state.json'
       s3_client.download_file(bucket, key, local_path)
       return local_path
       
   except ClientError as e:
       return None
   except Exception as e:
       return None

class StartBrowserRequest(BaseModel):
    storage_state_s3_path: Optional[str] = None



@app.post("/start-browserbase")
async def start_browserbase(request: StartBrowserRequest):
    storage_state = download_storage_state(request.storage_state_s3_path)
    playwright_manager = await setup_playwright(storage_state=storage_state)
    live_browser_url = await playwright_manager.get_live_browser_url()
    session_id = playwright_manager.get_session_id()
    return {
        "live_browser_url": live_browser_url, 
        "session_id": session_id, 
        "status": "started",
        "storage_state_path": storage_state
    }

class ConnectBrowserRequest(BaseModel):
    session_id: str
    storage_state_s3_path: Optional[str] = None

@app.post("/connect-browserbase")
async def connect_browserbase(request: ConnectBrowserRequest):  # Changed from (session_id: str, storage_state_s3_path: Optional[str] = None)
    try:
        storage_state = download_storage_state(request.storage_state_s3_path)
        playwright_manager = await setup_playwright(session_id=request.session_id, storage_state=storage_state)
        live_browser_url = await playwright_manager.get_live_browser_url()
        session_id = playwright_manager.get_session_id()
        return {
            "live_browser_url": live_browser_url,
            "session_id": session_id,
            "status": "connected",
            "storage_state_path": storage_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-agent-initial-steps")
async def run_agent_initial_steps(request: AgentRequest):
    try:
        storage_state = download_storage_state(request.storage_state_s3_path)
        playwright_manager = await setup_playwright(session_id=request.session_id, storage_state=storage_state)
        live_browser_url = await playwright_manager.get_live_browser_url()
        session_id = playwright_manager.get_session_id()

        agent_type = "FunctionCallingAgent"
        model = "gpt-4o-mini"
        features = "axtree"
        log_folder = "log"
        elements_filter="som"

        agent = await setup_function_calling_web_agent(
            request.starting_url,
            request.goal,
            playwright_manager=playwright_manager,
            model_name=model,
            agent_type=agent_type,
            features=features,
            tool_names=["navigation", "select_option", "upload_file"],
            log_folder=log_folder,
            s3_path=request.s3_path,
            elements_filter=elements_filter
        )

        response = await agent.send_prompt(request.plan if request.plan else request.goal)
        return {"live_browser_url": live_browser_url, "session_id": session_id, "status": "agent running", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AgentFollowUpRequest(BaseModel):
    session_id: str
    goal: str
    s3_path: Optional[str] = None
    storage_state_s3_path: Optional[str] = None


# TODO: debug run-agent-followup-steps
@app.post("/run-agent-followup-steps")
async def run_agent_followup_steps(request: AgentFollowUpRequest):
    try:
        storage_state = download_storage_state(request.storage_state_s3_path)
        playwright_manager = await setup_playwright(session_id=request.session_id, storage_state=storage_state, reinitialization=False)
        live_browser_url = await playwright_manager.get_live_browser_url()
        session_id = playwright_manager.get_session_id()

        agent_type = "FunctionCallingAgent"
        model = "gpt-4o-mini"
        features = "axtree"
        log_folder = "log"
        elements_filter="som"

        agent = await setup_function_calling_web_agent(
            None,
            request.goal,
            playwright_manager=playwright_manager,
            model_name=model,
            agent_type=agent_type,
            features=features,
            tool_names=["navigation", "select_option", "upload_file"],
            log_folder=log_folder,
            s3_path=request.s3_path,
            elements_filter=elements_filter
        )

        response = await agent.send_prompt(request.goal)
        return {"live_browser_url": live_browser_url, "session_id": session_id, "status": "agent running", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/terminate-browserbase")
async def terminate_browserbase(session_id: str):
    try:
        playwright_manager = await setup_playwright(session_id=session_id)
        await playwright_manager.close()
        return {"status": "terminated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

logger = logging.getLogger(__name__)

class RealTimeEmitter:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._is_closed = False

    async def emit(self, data: str):
        if self._is_closed:
            return
            
        if isinstance(data, (list, dict)):
            data = json.dumps(data)
        await self._queue.put(data)

    async def close(self):
        self._is_closed = True
        await self._queue.put(None)

    async def __aiter__(self):
        while not self._is_closed:
            try:
                data = await self._queue.get()
                if data is None:
                    break
                    
                # Yield each event individually and flush immediately
                yield f"data: {data}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                break
            finally:
                self._queue.task_done()

@app.post("/run-agent-initial-steps-stream")
async def run_agent_initial_steps_stream(request: AgentRequest):
    emitter = RealTimeEmitter()
    
    async def stream_generator():
        try:
            # Start processing in a background task
            process_task = asyncio.create_task(process_agent_steps(request, emitter))
            
            # Stream events as they are emitted
            async for event in emitter:
                yield event

            # Check if task raised any exceptions
            if process_task.done() and process_task.exception():
                raise process_task.exception()
                
            # Cancel task if it's still running
            if not process_task.done():
                process_task.cancel()
                try:
                    await process_task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            await emitter.emit({"type": "error", "message": str(e)})
        finally:
            await emitter.close()

    # Set response headers for streaming
    response = StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
    
    return response

def extract_choices(model_response):
    return [
        {
            "finish_reason": choice.finish_reason,
            "index": choice.index,
            "message": {
                "content": choice.message.content,
                "role": choice.message.role,
                "tool_calls": choice.message.tool_calls,
                "function_call": choice.message.function_call
            }
        }
        for choice in model_response.choices
    ]

async def process_agent_steps(request: AgentRequest, emitter: RealTimeEmitter):
    try:
        await emitter.emit({"type": "status", "message": "Starting setup..."})
        
        # Storage state setup
        storage_state = download_storage_state(request.storage_state_s3_path)
        await emitter.emit({"type": "status", "message": "Storage state loaded"})
        
        # Playwright setup
        playwright_manager = await setup_playwright(
            session_id=request.session_id,
            storage_state=storage_state
        )
        live_browser_url = await playwright_manager.get_live_browser_url()
        session_id = playwright_manager.get_session_id()
        
        await emitter.emit({
            "type": "browser",
            "message": f"Browser connected at {live_browser_url}"
        })

        # Agent setup
        agent = await setup_function_calling_web_agent(
            request.starting_url,
            request.goal,
            playwright_manager=playwright_manager,
            model_name="gpt-4o-mini",
            agent_type="FunctionCallingAgent",
            features="axtree",
            tool_names=["navigation", "select_option", "upload_file"],
            log_folder="log",
            s3_path=request.s3_path,
            elements_filter="som"
        )
        
        await emitter.emit({"type": "status", "message": "Agent setup complete"})

        # Run the agent with real-time updates
        async def real_time_emit(data):
            await emitter.emit(data)
            
        response = await agent.send_prompt(
            request.plan if request.plan else request.goal,
            emitter=real_time_emit
        )
        
        await emitter.emit({
            "type": "complete",
            "message": "Task completed",
            "response": extract_choices(response)
        })
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        await emitter.emit({
            "type": "error",
            "message": f"Error during processing: {str(e)}"
        })
    finally:
        await emitter.close()  # Ensure emitter is closed after processing

# TODO: debug run-agent-followup-steps
@app.post("/run-agent-followup-steps-stream")
async def run_agent_followup_steps_stream(request: AgentFollowUpRequest):
    async def stream():
        emitter = RealTimeEmitter()
        try:
            storage_state = download_storage_state(request.storage_state_s3_path)
            playwright_manager = await setup_playwright(session_id=request.session_id, storage_state=storage_state, reinitialization=False)
            live_browser_url = await playwright_manager.get_live_browser_url()
            session_id = playwright_manager.get_session_id()

            emitter.emit(f"Reconnected to browser. Live URL: {live_browser_url}")

            agent_type = "FunctionCallingAgent"
            model = "gpt-4o-mini"
            features = "axtree"
            log_folder = "log"
            elements_filter="som"

            agent = await setup_function_calling_web_agent(
                None,
                request.goal,
                playwright_manager=playwright_manager,
                model_name=model,
                agent_type=agent_type,
                features=features,
                tool_names=["navigation", "select_option", "upload_file"],
                log_folder=log_folder,
                s3_path=request.s3_path,
                elements_filter=elements_filter
            )

            emitter.emit("Agent setup completed")

            response = await agent.send_prompt(request.goal, emitter=emitter.emit)
            emitter.emit(f"Final Response: {response}")

        except Exception as e:
            emitter.emit(f"Error: {str(e)}")
        finally:
            emitter.emit(None)

        async for chunk in emitter.get_emitter():
            yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")

s3_client = boto3.client('s3')

class CodeConversionRequest(BaseModel):
    input_s3_path: str
    output_s3_path: str

def parse_s3_path(s3_path: str):
    parts = s3_path.replace('s3://', '').split('/')
    return parts[0], '/'.join(parts[1:])

def read_s3_file_to_string(s3_path: str):
    try:
        bucket, key = parse_s3_path(s3_path)
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def upload_to_s3(content: str, s3_path: str):
    try:
        bucket, key = parse_s3_path(s3_path)
        s3_client.put_object(Bucket=bucket, Key=key, Body=content.encode('utf-8'))
        return f"Successfully uploaded to s3://{bucket}/{key}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_playwright_script(content: str):
    entries = content.split("<<<ENTRY_START>>>")[1:]
    
    script_lines = [
        "from playwright.sync_api import sync_playwright, TimeoutError",
        "",
        "def run(playwright):",
        "    browser = playwright.chromium.launch(headless=False)",
        "    page = browser.new_page()",
        ""
    ]
    
    for entry in entries:
        lines = entry.strip().split("\n")
        goal = lines[0].replace("GOAL: ", "")
        script_lines.append(f"    # {goal}")
        
        url = lines[1].replace("URL: ", "")
        if url.lower() != "none":
            script_lines.append(f'    page.goto("{url}")')
            script_lines.append('    page.wait_for_load_state("networkidle")')
        
        for step in lines[2:]:
            step_data = json.loads(step)
            selector = step_data.get("unique_selector", "body")
            selector = selector.replace('"', "'")
            
            script_lines.append(f'    element = page.locator("{selector}")')
            script_lines.append('    element.wait_for(state="visible", timeout=5000)')
            
            action = step_data["action"]
            if "fill" in action:
                match = re.search(r"fill\('(\d+)', '(.+?)'\)", action)
                if match:
                    value = match.group(2)
                    script_lines.append(f'    element.fill("{value}")')
            elif "click" in action:
                script_lines.append('    element.click()')
            
            script_lines.append('    page.wait_for_load_state("networkidle")')
        
        script_lines.append("")
    
    script_lines.extend([
        "    # Add a delay to keep the browser open",
        "    page.wait_for_timeout(5000)",
        "",
        "    browser.close()",
        "",
        "with sync_playwright() as playwright:",
        "    run(playwright)"
    ])
    
    return "\n".join(script_lines)

@app.post("/convert-to-playwright")
async def convert_to_playwright(request: CodeConversionRequest):
    try:
        file_content = read_s3_file_to_string(request.input_s3_path)
        playwright_script = generate_playwright_script(file_content)
        upload_message = upload_to_s3(playwright_script, request.output_s3_path)
        
        return {
            "status": "success",
            "message": upload_message,
            "generated_script": playwright_script
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_js_playwright_script(content):
    entries = content.split("<<<ENTRY_START>>>")[1:]  # Skip the first empty part
    
    script_lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        "const environmentUrl = process.env.PLAYWRIGHT_ENV_URL;",
        ""
    ]
    
    # Start a single test that combines all entries
    script_lines.append("test('complete workflow', async ({ page }) => {")
    
    first_url = None
    for index, entry in enumerate(entries):
        lines = entry.strip().split("\n")
        goal = lines[0].replace("GOAL: ", "")
        url = lines[1].replace("URL: ", "")
        
        # Only handle URL navigation for the first entry
        if index == 0 and url.lower() != "none":
            first_url = url
            script_lines.append("  // Navigate to the specified URL")
            if url == "${environmentUrl}":
                script_lines.append("  await page.goto(environmentUrl);")
            else:
                script_lines.append(f"  await page.goto('{url}');")
            script_lines.append("  await page.waitForLoadState('networkidle');")
        
        # Add a comment for each goal
        script_lines.append(f"  // Step: {goal}")
        
        # Process all steps after the second line
        for step in lines[2:]:
            step_data = json.loads(step)
            
            selector = step_data.get("unique_selector", "body")
            selector = selector.replace('"', "'")
            
            if 'nth-of-type' in selector:
                selector = selector.replace("'", "\\'")
            
            script_lines.append("  // Wait for element to be visible")
            script_lines.append(f"  await page.waitForSelector('{selector}', {{ state: 'visible', timeout: 5000 }});")
            
            action = step_data["action"]
            if "fill" in action:
                match = re.search(r"fill\('(\d+)', '(.+?)'\)", action)
                if match:
                    value = match.group(2)
                    script_lines.append("  // Fill in the input field")
                    script_lines.append(f"  await page.fill('{selector}', '{value}');")
            elif "click" in action:
                script_lines.append("  // Click the element")
                script_lines.append(f"  await page.click('{selector}');")
            
            script_lines.append("  await page.waitForLoadState('networkidle');")
    
    # Add final timeout at the end of the combined test
    script_lines.append("  // Add final timeout")
    script_lines.append("  await page.waitForTimeout(5000);")
    script_lines.append("});")
    
    return "\n".join(script_lines)

@app.post("/convert-to-js-playwright")
async def convert_to_js_playwright(request: CodeConversionRequest):
    try:
        file_content = read_s3_file_to_string(request.input_s3_path)
        playwright_script = generate_js_playwright_script(file_content)
        upload_message = upload_to_s3(playwright_script, request.output_s3_path)
        
        return {
            "status": "success",
            "message": upload_message,
            "generated_script": playwright_script
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)