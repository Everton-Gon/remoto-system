"""
RemotDesk Server - WebSocket Signaling Server
Gerencia a sinalização WebRTC entre dispositivos.
"""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gerencia conexões WebSocket ativas.
    Responsável por rotear mensagens de sinalização entre dispositivos.
    """
    
    def __init__(self):
        # Mapeia device_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Mapeia session_id -> set of device_ids
        self.sessions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, device_id: str):
        """Aceita conexão WebSocket e registra o dispositivo"""
        await websocket.accept()
        self.active_connections[device_id] = websocket
        logger.info(f"Dispositivo conectado: {device_id}")
    
    def disconnect(self, device_id: str):
        """Remove dispositivo das conexões ativas"""
        if device_id in self.active_connections:
            del self.active_connections[device_id]
            logger.info(f"Dispositivo desconectado: {device_id}")
        
        # Limpar sessões do dispositivo
        for session_id, devices in list(self.sessions.items()):
            if device_id in devices:
                devices.remove(device_id)
                if not devices:
                    del self.sessions[session_id]
    
    def is_online(self, device_id: str) -> bool:
        """Verifica se dispositivo está online"""
        return device_id in self.active_connections
    
    async def send_personal_message(self, message: dict, device_id: str):
        """Envia mensagem para um dispositivo específico"""
        if device_id in self.active_connections:
            websocket = self.active_connections[device_id]
            await websocket.send_json(message)
            logger.debug(f"Mensagem enviada para {device_id}: {message.get('type')}")
    
    async def broadcast_to_session(self, message: dict, session_id: str, exclude: str = None):
        """Envia mensagem para todos os dispositivos de uma sessão"""
        if session_id in self.sessions:
            for device_id in self.sessions[session_id]:
                if device_id != exclude:
                    await self.send_personal_message(message, device_id)
    
    def add_to_session(self, session_id: str, device_id: str):
        """Adiciona dispositivo a uma sessão"""
        if session_id not in self.sessions:
            self.sessions[session_id] = set()
        self.sessions[session_id].add(device_id)
        logger.info(f"Dispositivo {device_id} adicionado à sessão {session_id}")


# Instância global do gerenciador
manager = ConnectionManager()


async def handle_signaling(websocket: WebSocket, device_id: str):
    """
    Handler principal para conexões WebSocket de sinalização.
    Processa mensagens de sinalização WebRTC.
    """
    await manager.connect(websocket, device_id)
    
    try:
        while True:
            # Receber mensagem
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            logger.debug(f"Mensagem recebida de {device_id}: {message_type}")
            
            # Processar diferentes tipos de mensagem
            if message_type == "ping":
                # Heartbeat para manter conexão ativa
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    device_id
                )
            
            elif message_type == "connection_request":
                # Pedido de conexão para outro dispositivo
                target_id = data.get("target_id")
                
                if not manager.is_online(target_id):
                    await manager.send_personal_message(
                        {
                            "type": "connection_response",
                            "success": False,
                            "error": "Dispositivo offline"
                        },
                        device_id
                    )
                else:
                    # Encaminhar pedido para o dispositivo alvo
                    await manager.send_personal_message(
                        {
                            "type": "connection_request",
                            "from_device": device_id,
                            "requester_name": data.get("requester_name", "Unknown")
                        },
                        target_id
                    )
            
            elif message_type == "connection_accept":
                # Host aceitou a conexão
                session_id = data.get("session_id")
                requester_id = data.get("requester_id")
                
                # Adicionar ambos à sessão
                manager.add_to_session(session_id, device_id)
                manager.add_to_session(session_id, requester_id)
                
                # Notificar requester
                await manager.send_personal_message(
                    {
                        "type": "connection_accepted",
                        "session_id": session_id,
                        "host_id": device_id,
                        "ice_servers": [
                            {"urls": "stun:stun.l.google.com:19302"},
                            {"urls": "stun:stun1.l.google.com:19302"}
                        ]
                    },
                    requester_id
                )
            
            elif message_type == "connection_reject":
                # Host rejeitou a conexão
                requester_id = data.get("requester_id")
                reason = data.get("reason", "Conexão rejeitada")
                
                await manager.send_personal_message(
                    {
                        "type": "connection_rejected",
                        "reason": reason
                    },
                    requester_id
                )
            
            elif message_type == "offer":
                # SDP Offer - encaminhar para o peer
                target_id = data.get("target_id")
                await manager.send_personal_message(
                    {
                        "type": "offer",
                        "sdp": data.get("sdp"),
                        "from_device": device_id
                    },
                    target_id
                )
            
            elif message_type == "answer":
                # SDP Answer - encaminhar para o peer
                target_id = data.get("target_id")
                await manager.send_personal_message(
                    {
                        "type": "answer",
                        "sdp": data.get("sdp"),
                        "from_device": device_id
                    },
                    target_id
                )
            
            elif message_type == "ice_candidate":
                # ICE Candidate - encaminhar para o peer
                target_id = data.get("target_id")
                await manager.send_personal_message(
                    {
                        "type": "ice_candidate",
                        "candidate": data.get("candidate"),
                        "sdp_mid": data.get("sdp_mid"),
                        "sdp_m_line_index": data.get("sdp_m_line_index"),
                        "from_device": device_id
                    },
                    target_id
                )
            
            elif message_type == "disconnect":
                # Encerrar sessão
                session_id = data.get("session_id")
                if session_id:
                    await manager.broadcast_to_session(
                        {"type": "peer_disconnected", "device_id": device_id},
                        session_id,
                        exclude=device_id
                    )
                break
            
            else:
                logger.warning(f"Tipo de mensagem desconhecido: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado: {device_id}")
    except Exception as e:
        logger.error(f"Erro no WebSocket {device_id}: {e}")
    finally:
        manager.disconnect(device_id)
