from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import json
from agentcore_main import lambda_handler

app = FastAPI(title="St Marys Class Rep Bot - AgentCore")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("chat.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/chat")
async def chat_handler(request: Request):
    body = await request.body()
    
    # Create Lambda-like event structure for AgentCore
    event = {
        "body": body.decode("utf-8"),
        "headers": dict(request.headers)
    }
    
    # Call the AgentCore handler
    response = lambda_handler(event, {})
    
    return JSONResponse(
        content=json.loads(response["body"]),
        status_code=response["statusCode"],
        headers=response.get("headers", {})
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
