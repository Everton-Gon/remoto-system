"""
RemotDesk Server - Main Application
Entry point para o servidor FastAPI.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .models import init_db
from .api import devices_router, sessions_router
from .websocket import handle_signaling

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hooks da aplicação"""
    # Startup
    logger.info("Iniciando RemotDesk Server...")
    await init_db()
    logger.info("Banco de dados inicializado")
    
    yield
    
    # Shutdown
    logger.info("Encerrando RemotDesk Server...")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Servidor de sinalização para RemotDesk - Acesso Remoto",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(devices_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


# ============ Endpoints Básicos ============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {"status": "healthy"}


# ============ WebSocket Signaling ============

@app.websocket("/ws/signal/{device_id}")
async def websocket_signaling(websocket: WebSocket, device_id: str):
    """
    Endpoint WebSocket para sinalização WebRTC.
    Cada dispositivo conecta usando seu ID único.
    """
    await handle_signaling(websocket, device_id)


# ============ Run Application ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
