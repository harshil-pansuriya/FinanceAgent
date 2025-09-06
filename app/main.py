import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn 
from typing import Dict, Any,  AsyncContextManager
from database.database import init_db, dispose_engine
from routes.api_endpoints import router
from config.logger import logger
from config.setting import Config

async def lifespan(app: FastAPI) -> AsyncContextManager:
    
    await init_db()
    yield
    await dispose_engine()

app= FastAPI(title="Personal Finance Agent", version="1.0.0", lifespan=lifespan)

allowed_origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str,Any]:
    return {"message": "AI Personal Finance Agent is running"}

if __name__ == "__main__":
    logger.info("Finance Agent FastAPI server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=Config.port,
        reload=False,
        # log_level="info"
    )