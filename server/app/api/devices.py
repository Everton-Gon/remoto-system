"""
RemotDesk Server - Device Routes
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import get_db, Device
from ..schemas import DeviceRegister, DeviceResponse, DeviceUpdate
from ..core.security import get_password_hash, verify_password

router = APIRouter(prefix="/devices", tags=["Devices"])


def generate_device_id() -> str:
    """Gera ID único para dispositivo no formato XXX-XXX-XXX"""
    raw_id = uuid.uuid4().hex[:9].upper()
    return f"{raw_id[:3]}-{raw_id[3:6]}-{raw_id[6:9]}"


@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_data: DeviceRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra um novo dispositivo no servidor.
    Retorna o ID único do dispositivo.
    """
    device_id = generate_device_id()
    
    # Hash da senha se fornecida
    password_hash = None
    if device_data.access_password:
        password_hash = get_password_hash(device_data.access_password)
    
    device = Device(
        id=device_id,
        name=device_data.name,
        device_type=device_data.device_type,
        os_info=device_data.os_info,
        access_password_hash=password_hash,
        is_online=True,
        last_seen=datetime.utcnow()
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém informações de um dispositivo pelo ID.
    """
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    return device


@router.put("/{device_id}/online")
async def set_device_online(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Marca dispositivo como online.
    """
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    device.is_online = True
    device.last_seen = datetime.utcnow()
    await db.commit()
    
    return {"status": "online", "device_id": device_id}


@router.put("/{device_id}/offline")
async def set_device_offline(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Marca dispositivo como offline.
    """
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    device.is_online = False
    device.last_seen = datetime.utcnow()
    await db.commit()
    
    return {"status": "offline", "device_id": device_id}


@router.post("/{device_id}/verify-password")
async def verify_device_password(
    device_id: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica a senha de acesso do dispositivo.
    """
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    if not device.access_password_hash:
        return {"valid": True, "message": "Dispositivo não requer senha"}
    
    is_valid = verify_password(password, device.access_password_hash)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta"
        )
    
    return {"valid": True}
