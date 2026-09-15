import os
import sys
import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# Add project root and src directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.models.schemas import (
    UploadResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ErrorResponse
)
from backend.services.session_service import session_store
from backend.utils.chart_helper import process_generated_chart, get_safe_chart_path

import data_inspector
import agent
from tools import make_json_safe

app = FastAPI(
    title="AI Data Analyst API",
    description="FastAPI Backend for AI Data Analyst Agentic System",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    """
    return HealthResponse(status="ok", service="AI Data Analyst")


@app.post("/api/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file, validate, create a dataset session, and return dataset profiling metadata.
    """
    # 1. Validate file extension
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .csv files are supported."
        )

    # 2. Read file content and check if empty
    contents = await file.read()
    if not contents or len(contents.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file is empty."
        )

    # 3. Safely load CSV into Pandas
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file contains no data."
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Malformed CSV file: {str(e)}"
        )

    if df.empty and len(df.columns) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file has no columns or data."
        )

    # 4. Create server-side session
    session = session_store.create_session(filename=file.filename, df=df)

    # 5. Run smart profiler
    profile = data_inspector.get_smart_profile(df)

    # 6. Format preview
    preview_raw = df.head(5).to_dict(orient="records")
    preview_safe = [make_json_safe(row) for row in preview_raw]

    return UploadResponse(
        dataset_id=session.dataset_id,
        filename=session.filename,
        rows=profile["rows"],
        columns=profile["columns"],
        column_names=profile["column_names"],
        missing_values=profile["missing_values"],
        duplicate_rows=profile["duplicate_rows"],
        dtypes=profile["data_types"],
        preview=preview_safe
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Interact with the AI Data Analyst agent for a given dataset session.
    Preserves active DataFrame state across multi-turn requests.
    """
    # 1. Find active session
    session = session_store.get_session(request.dataset_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset session '{request.dataset_id}' not found."
        )

    # 2. Validate message
    message = request.message.strip() if request.message else ""
    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message field cannot be empty."
        )

    # 3. Synchronize agent module globals with current session state
    agent.active_working_df = session.active_df.copy()
    agent.active_dataset_name = session.filename
    agent.conversation_history = list(session.conversation_history)

    # Check chart file timestamp before execution to detect newly generated chart
    chart_path = os.path.join(BASE_DIR, "outputs", "chart.png")
    chart_mtime_before = os.path.getmtime(chart_path) if os.path.exists(chart_path) else 0

    try:
        # 4. Execute run_agent
        answer, updated_df, completed_actions = agent.run_agent(
            user_question=message,
            df=session.active_df,
            dataset_name=session.filename,
            return_details=True
        )

        # 5. Update session with modified active_df and conversation history
        session_store.update_session(
            dataset_id=session.dataset_id,
            active_df=updated_df,
            conversation_history=agent.conversation_history
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent analysis failed: {str(e)}"
        )

    # 6. Check if chart was generated or updated during run_agent
    chart_url = None
    if os.path.exists(chart_path):
        chart_mtime_after = os.path.getmtime(chart_path)
        if chart_mtime_after > chart_mtime_before:
            chart_url = process_generated_chart("outputs/chart.png")

    # 7. Pass completed actions to React frontend
    actions_metadata = completed_actions if completed_actions else []

    return ChatResponse(
        answer=answer,
        dataset_id=session.dataset_id,
        chart=chart_url,
        actions=actions_metadata,
        success=True
    )


@app.get("/api/charts/{chart_id}")
def serve_chart(chart_id: str):
    """
    Safely serve generated chart image file from outputs/ directory.
    """
    safe_path = get_safe_chart_path(chart_id)
    if not safe_path:
        raise HTTPException(
            status_code=404,
            detail="Chart file not found."
        )
    return FileResponse(safe_path, media_type="image/png")
