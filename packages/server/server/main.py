"""
SparkyAI FastAPI Server
=======================

Main application entry point with:
- REST API endpoints
- WebSocket support for real-time visualization
- Rate limiting and security middleware
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from agent_core import create_agent_graph, AgentGraph, settings
from agent_core.state import get_node_graph_data
from agent_core.utils import sanitize_input, sanitize_session_id, is_valid_session_id
from agent_core.nodes.rag_retriever import embedding_store

from server.websocket import ConnectionManager
from server.middleware.security import SecurityHeadersMiddleware
from server.utils.redis import RedisClient, get_redis
from server.utils.budget import BudgetTracker


# ============================================
# Application Setup
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    print("🚀 Starting SparkyAI server...")
    
    # Load embeddings
    try:
        embedding_store.load(settings.embeddings_dir)
        print(f"✅ Loaded {len(embedding_store.chunks)} knowledge chunks")
    except Exception as e:
        print(f"⚠️ Could not load embeddings: {e}")
    
    # Initialize agent
    app.state.agent = AgentGraph(domain=settings.agent_config)
    print(f"✅ Agent initialized (domain: {settings.agent_config})")
    
    yield
    
    # Shutdown
    print("👋 Shutting down SparkyAI server...")


# Initialize FastAPI app
app = FastAPI(
    title="SparkyAI API",
    description="AI-powered portfolio assistant with real-time visualization",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://roshan.dev",  # Your portfolio domain
        "https://www.roshan.dev",
        "https://easybee.ai",  # Buzzy demo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# WebSocket connection manager
ws_manager = ConnectionManager()


# ============================================
# Request/Response Models
# ============================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, min_length=8, max_length=64)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    trace_id: str
    intent: Optional[str] = None
    retrieval_confidence: Optional[float] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    version: str
    openai_connected: bool
    redis_connected: bool
    embeddings_loaded: bool
    chunks_count: int


class GraphStructureResponse(BaseModel):
    """Response model for graph structure."""
    nodes: list
    edges: list


class EmbeddingPoint(BaseModel):
    """A single point in the embedding space."""
    id: str
    x: float
    y: float
    content: str
    source: str
    category: str


class EmbeddingsResponse(BaseModel):
    """Response model for embeddings visualization data."""
    points: list[EmbeddingPoint]
    total_count: int


# ============================================
# REST API Endpoints
# ============================================

@app.get("/health", response_model=HealthResponse)
async def health_check(redis: RedisClient = Depends(get_redis)):
    """
    Health check endpoint with dependency status.
    
    Checks:
    - OpenAI API connectivity (basic)
    - Redis connectivity
    - Embeddings loaded
    """
    # Check OpenAI (basic - just verify key exists)
    openai_ok = bool(settings.openai_api_key)
    
    # Check Redis
    try:
        redis_ok = await redis.ping() if redis else False
    except Exception:
        redis_ok = False
    
    # Check embeddings
    embeddings_loaded = len(embedding_store.chunks) > 0
    
    return HealthResponse(
        status="healthy" if (openai_ok and embeddings_loaded) else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        openai_connected=openai_ok,
        redis_connected=redis_ok,
        embeddings_loaded=embeddings_loaded,
        chunks_count=len(embedding_store.chunks),
    )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    redis: RedisClient = Depends(get_redis),
):
    """
    Chat endpoint for non-streaming responses.
    
    Rate limited to 10 requests per minute per IP.
    """
    # Sanitize input
    sanitized_message, warning = sanitize_input(body.message, max_length=500)
    
    if not sanitized_message:
        raise HTTPException(
            status_code=400,
            detail=warning or "Invalid message"
        )
    
    # Get or create session ID
    session_id = body.session_id
    if not session_id or not is_valid_session_id(session_id):
        import uuid
        session_id = str(uuid.uuid4())
    else:
        session_id = sanitize_session_id(session_id)
    
    # Check budget
    if redis:
        budget = BudgetTracker(redis)
        if not await budget.can_spend():
            raise HTTPException(
                status_code=429,
                detail="Daily budget exceeded. Please try again tomorrow or contact Roshan directly."
            )
    
    # Get agent from app state
    agent: AgentGraph = request.app.state.agent
    
    # Invoke agent
    try:
        result = agent.invoke(sanitized_message, session_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your request."
        )
    
    # Track costs in Redis
    if redis:
        estimated_cost = result.get("trace_metadata", {}).get("estimated_cost_usd", 0)
        await budget.record_spend(estimated_cost)
    
    return ChatResponse(
        response=result.get("response", ""),
        session_id=session_id,
        trace_id=result.get("trace_metadata", {}).get("trace_id", ""),
        intent=result.get("user_intent"),
        retrieval_confidence=result.get("retrieval_confidence"),
    )


@app.get("/graph/structure", response_model=GraphStructureResponse)
async def get_graph_structure():
    """
    Get the static agent graph structure for D3.js visualization.
    
    Returns nodes and edges that define the agent workflow.
    """
    data = get_node_graph_data()
    return GraphStructureResponse(
        nodes=data["nodes"],
        edges=data["edges"],
    )


@app.get("/embeddings/knowledge", response_model=EmbeddingsResponse)
async def get_embedding_points():
    """
    Get all knowledge base points with 2D projections.
    
    Used by the Embedding Space Explorer visualization.
    """
    points = embedding_store.get_all_points_for_visualization()
    
    return EmbeddingsResponse(
        points=[EmbeddingPoint(**p) for p in points],
        total_count=len(points),
    )


# ============================================
# WebSocket Endpoint
# ============================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time chat with visualization events.
    
    Events sent to client:
    - start: Processing started
    - node_enter: Entering a node
    - node_complete: Node finished
    - rag_results: RAG retrieval results (for embedding explorer)
    - token: Streaming token
    - complete: Processing finished
    - error: An error occurred
    - state_sync: Current state (for reconnection)
    """
    # Validate session ID
    if not is_valid_session_id(session_id):
        await websocket.close(code=4001, reason="Invalid session ID")
        return
    
    session_id = sanitize_session_id(session_id)
    
    # Accept connection
    await ws_manager.connect(websocket, session_id)
    
    try:
        # Get agent
        agent: AgentGraph = websocket.app.state.agent
        
        while True:
            # Wait for message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await ws_manager.send_error(
                    session_id, 
                    "INVALID_JSON", 
                    "Message must be valid JSON"
                )
                continue
            
            # Handle different message types
            msg_type = message.get("type", "message")
            
            if msg_type == "ping":
                # Heartbeat
                await ws_manager.send_event(session_id, "pong", {})
                
            elif msg_type == "state_sync_request":
                # Client requesting current state (after reconnect)
                state = agent.get_session_state(session_id)
                if state:
                    await ws_manager.send_event(session_id, "state_sync", {
                        "current_node": state.get("current_node"),
                        "node_states": state.get("node_states"),
                        "streaming_response": state.get("response"),
                    })
                else:
                    await ws_manager.send_event(session_id, "state_sync", {
                        "current_node": None,
                        "node_states": None,
                        "streaming_response": None,
                    })
                
            elif msg_type == "message":
                # User message - process with streaming
                payload = message.get("payload", {})
                user_text = payload.get("text", "")
                
                # Sanitize
                sanitized, warning = sanitize_input(user_text)
                
                if not sanitized:
                    await ws_manager.send_error(
                        session_id,
                        "INVALID_INPUT",
                        warning or "Invalid message"
                    )
                    continue
                
                # Stream agent response
                try:
                    async for event in agent.stream(sanitized, session_id):
                        await ws_manager.send_event(
                            session_id,
                            event["event"],
                            event["payload"]
                        )
                        
                        # Small delay to prevent flooding
                        await asyncio.sleep(0.01)
                        
                except Exception as e:
                    await ws_manager.send_error(
                        session_id,
                        "PROCESSING_ERROR",
                        "An error occurred processing your message."
                    )
            
            else:
                await ws_manager.send_error(
                    session_id,
                    "UNKNOWN_TYPE",
                    f"Unknown message type: {msg_type}"
                )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
    except Exception as e:
        ws_manager.disconnect(session_id)
        raise


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred.",
            "status_code": 500,
        },
    )


# ============================================
# Development Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
