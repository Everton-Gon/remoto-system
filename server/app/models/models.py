"""
RemotDesk Server - Modelos do Banco de Dados
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Device(Base):
    """Modelo de dispositivo registrado"""
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    device_type = Column(String(50), default="desktop")  # desktop, mobile
    os_info = Column(String(100), nullable=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Segurança
    access_password_hash = Column(String(255), nullable=True)
    unattended_password_hash = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, online={self.is_online})>"


class Session(Base):
    """Modelo de sessão de conexão"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    host_device_id = Column(String(36), nullable=False)
    viewer_device_id = Column(String(36), nullable=False)
    status = Column(String(20), default="pending")  # pending, active, ended, rejected
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Session(id={self.id}, status={self.status})>"


class ConnectionLog(Base):
    """Log de conexões para auditoria"""
    __tablename__ = "connection_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False)
    host_device_id = Column(String(36), nullable=False)
    viewer_device_id = Column(String(36), nullable=False)
    action = Column(String(50), nullable=False)  # connected, disconnected, file_transfer, etc
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConnectionLog(session={self.session_id}, action={self.action})>"
