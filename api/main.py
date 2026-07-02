from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import re
from clients.client_memory import (
    save_client_profile,
    save_analysis_session,
    load_client_history,
    get_client_profile
)

from agents.graph import run_workflow, resume_workflow


app = FastAPI(
    title="WealthAdvisor AI API",
    description="Multi-agent AI system for wealth management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models — what the client sends
class AnalyzeRequest(BaseModel):
    user_input: str
    portfolio_data: str = ""
    client_name: str = "Valued Client"
    client_id: str = "default"
    thread_id: Optional[str] = None

class ReviewRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: str = ""
    client_id: str = "default"

# Response model — what we send back
class WorkflowResponse(BaseModel):
    thread_id: str
    status: str
    risk_output: str = ""
    planning_output: str = ""
    client_summary: str = ""
    next_agent: str = ""
    human_approved: bool = False

def extract_risk_score(risk_output: str) -> str:
    """Extract risk score from risk report text."""
    if not risk_output:
        return "UNKNOWN"
    match = re.search(r'\b(LOW|MODERATE|HIGH|CRITICAL)\b', risk_output, re.IGNORECASE)
    return match.group(1).upper() if match else "UNKNOWN"
    
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze", response_model=WorkflowResponse)
def analyze(request: AnalyzeRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    try:
        state = run_workflow(
            user_input=request.user_input,
            portfolio_data=request.portfolio_data,
            client_name=request.client_name,
            client_id=request.client_id,
            thread_id=thread_id
        )
        
        save_client_profile(client_id=request.client_id,
                            client_name=request.client_name)
        
        save_analysis_session(
            client_id=request.client_id,
            session_id=thread_id,
            portfolio_data=request.portfolio_data,
            risk_output=state.get("risk_output",""),
            planning_output=state.get("planning_output",""),
            risk_score=extract_risk_score(state.get("risk_output",""))
        )
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="awaiting_review",
            risk_output=state.get("risk_output",""),
            planning_output=state.get("planning_output",""),
            client_summary=state.get("client_summary",""),
        )
    except Exception as e:
        import traceback
        print("FULL ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500,detail=str(e))

@app.post("/review", response_model=WorkflowResponse)
def review(request: ReviewRequest):
    try:
        state = resume_workflow(
            thread_id=request.thread_id,
            approved=request.approved,
            feedback=request.feedback
        )
        
        save_analysis_session(
            client_id=request.client_id,
            session_id=request.thread_id,
            portfolio_data="",
            client_summary=state.get("client_summary",""),
            risk_score=extract_risk_score(state.get("risk_output",""))
        )
        
        return WorkflowResponse(
            thread_id=request.thread_id,
            status="completed" if state.get("client_summary") else "processing",
            risk_output=state.get("risk_output",""),
            planning_output=state.get("planning_output",""),
            client_summary=state.get("client_summary",""),
        )
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
    
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)