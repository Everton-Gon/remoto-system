"""
RemotDesk Server - Session Routes
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import get_db, Device, Session, ConnectionLog
from ..schemas import SessionCreate, SessionResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/create", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova sessão de conexão entre dois dispositivos.
    """
    # Verificar se o dispositivo alvo existe
    result = await db.execute(
        select(Device).where(Device.id == session_data.target_device_id)
    )
    target_device = result.scalar_one_or_none()
    
    if not target_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo alvo não encontrado"
        )
    
    if not target_device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispositivo alvo está offline"
        )
    
    # Criar sessão
    session_id = str(uuid.uuid4())
    session = Session(
        id=session_id,
        host_device_id=session_data.target_device_id,
        viewer_device_id=session_data.viewer_device_id,
        status="pending"
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém informações de uma sessão.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    return session


@router.put("/{session_id}/accept")
async def accept_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Aceita uma sessão de conexão.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    session.status = "active"
    session.started_at = datetime.utcnow()
    
    # Log da conexão
    log = ConnectionLog(
        session_id=session_id,
        host_device_id=session.host_device_id,
        viewer_device_id=session.viewer_device_id,
        action="connected"
    )
    db.add(log)
    
    await db.commit()
    
    # Retornar configurações ICE para WebRTC
    return {
        "status": "active",
        "session_id": session_id,
        "ice_servers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"}
        ]
    }


@router.put("/{session_id}/reject")
async def reject_session(
    session_id: str,
    reason: str = "Rejeitado pelo usuário",
    db: AsyncSession = Depends(get_db)
):
    """
    Rejeita uma sessão de conexão.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    session.status = "rejected"
    session.ended_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": "rejected", "reason": reason}


@router.put("/{session_id}/end")
async def end_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Encerra uma sessão ativa.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    session.status = "ended"
    session.ended_at = datetime.utcnow()
    
    # Log da desconexão
    log = ConnectionLog(
        session_id=session_id,
        host_device_id=session.host_device_id,
        viewer_device_id=session.viewer_device_id,
        action="disconnected"
    )
    db.add(log)
    
    await db.commit()
    
    return {"status": "ended", "session_id": session_id}
