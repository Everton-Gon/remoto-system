"""
RemotDesk Server - Schemas Pydantic
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ============ Device Schemas ============

class DeviceRegister(BaseModel):
    """Schema para registro de dispositivo"""
    name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(default="desktop", pattern="^(desktop|mobile)$")
    os_info: Optional[str] = None
    access_password: Optional[str] = None


class DeviceResponse(BaseModel):
    """Schema de resposta para dispositivo"""
    id: str
    name: str
    device_type: str
    os_info: Optional[str]
    is_online: bool
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeviceUpdate(BaseModel):
    """Schema para atualização de dispositivo"""
    name: Optional[str] = None
    access_password: Optional[str] = None
    unattended_password: Optional[str] = None


# ============ Session Schemas ============

class SessionCreate(BaseModel):
    """Schema para criar sessão de conexão"""
    target_device_id: str
    viewer_device_id: str
    access_password: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema de resposta para sessão"""
    id: str
    host_device_id: str
    viewer_device_id: str
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ WebSocket Signaling Schemas ============

class SignalMessage(BaseModel):
    """Schema para mensagens de sinalização WebRTC"""
    type: str  # offer, answer, ice_candidate, connection_request, etc
    data: dict
    from_device: Optional[str] = None
    to_device: Optional[str] = None


class ConnectionRequest(BaseModel):
    """Schema para pedido de conexão"""
    target_id: str
    requester_name: str


class ConnectionResponse(BaseModel):
    """Schema para resposta de conexão"""
    accepted: bool
    session_id: Optional[str] = None
    ice_servers: Optional[list] = None
    reason: Optional[str] = None


# ============ WebRTC Schemas ============

class RTCOffer(BaseModel):
    """Schema para SDP Offer"""
    sdp: str
    type: str = "offer"


class RTCAnswer(BaseModel):
    """Schema para SDP Answer"""
    sdp: str
    type: str = "answer"


class ICECandidate(BaseModel):
    """Schema para ICE Candidate"""
    candidate: str
    sdp_mid: Optional[str] = None
    sdp_m_line_index: Optional[int] = None
