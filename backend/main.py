"""FastAPI backend for LLM Council."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from contextlib import asynccontextmanager

from . import storage
from .logging_config import setup_logging, custom_loop_exception_handler
from .routers import auth, conversations

# Apply logging filters
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directory exists on startup
    storage.ensure_data_dir()
    yield

app = FastAPI(title="LLM Council API", lifespan=lifespan)
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    url = request.url
    print(f"Request: {method} {url} | Origin: {origin}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response

# Configure CORS
# When allow_credentials=True, allow_origins cannot be ["*"]
# We use allow_origin_regex to support dynamic IPs/hostnames
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(conversations.router)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "LLM Council API"}

# DELETED the old redundant routes below this point

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    # Parse command line arguments for the server
    parser = argparse.ArgumentParser(description="LLM Council Backend")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--ssl-keyfile", default=None, help="Path to SSL key file")
    parser.add_argument("--ssl-certfile", default=None, help="Path to SSL certificate file")
    
    args = parser.parse_args()
    
    print(f"Starting LLM Council Backend on {args.host}:{args.port}")
    if args.ssl_keyfile and args.ssl_certfile:
        print(f"  SSL: Enabled (using {args.ssl_certfile})")
    
    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
        reload=True
    )
