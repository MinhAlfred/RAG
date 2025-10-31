"""Eureka Service Discovery Configuration"""

import os
import socket
from typing import Optional
import py_eureka_client.eureka_client as eureka_client


class EurekaConfig:
    """Configuration for Eureka service registration"""
    
    def __init__(
        self,
        eureka_server: str = "http://localhost:8761/eureka/",
        app_name: str = "python-rag-service",
        instance_port: int = 8000,
        instance_host: Optional[str] = None,
        instance_ip: Optional[str] = None
    ):
        """
        Initialize Eureka configuration
        
        Args:
            eureka_server: Eureka server URL
            app_name: Application name registered in Eureka
            instance_port: Port where FastAPI is running
            instance_host: Hostname (auto-detect if None)
            instance_ip: IP address (auto-detect if None)
        """
        self.eureka_server = eureka_server
        self.app_name = app_name
        self.instance_port = instance_port
        self.instance_host = instance_host or self._get_hostname()
        self.instance_ip = instance_ip or self._get_ip()
        
    def _get_hostname(self) -> str:
        """Get hostname"""
        return socket.gethostname()
    
    def _get_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create a socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    @classmethod
    def from_env(cls) -> "EurekaConfig":
        """Create configuration from environment variables"""
        return cls(
            eureka_server=os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka/"),
            app_name=os.getenv("APP_NAME", "python-rag-service"),
            instance_port=int(os.getenv("APP_PORT", "8000")),
            instance_host=os.getenv("INSTANCE_HOST"),
            instance_ip=os.getenv("INSTANCE_IP")
        )


async def register_with_eureka_async(config: EurekaConfig, health_check_url: str = "/health"):
    """
    Register FastAPI service with Eureka (async version)
    
    Args:
        config: EurekaConfig instance
        health_check_url: Health check endpoint path
    """
    try:
        print(f"🔍 Registering with Eureka server: {config.eureka_server}")
        print(f"📝 Service name: {config.app_name}")
        print(f"🌐 Instance: {config.instance_host}:{config.instance_port} ({config.instance_ip})")
        
        # Initialize Eureka client (async)
        await eureka_client.init_async(
            eureka_server=config.eureka_server,
            app_name=config.app_name,
            instance_port=config.instance_port,
            instance_host=config.instance_host,
            instance_ip=config.instance_ip,
            # Health check configuration
            health_check_url=health_check_url,
            # Heartbeat configuration
            renewal_interval_in_secs=30,  # Send heartbeat every 30s
            duration_in_secs=90,  # Lease duration
            # Metadata
            metadata={
                "version": "1.0.0",
                "type": "rag-service",
                "framework": "fastapi",
                "description": "Python RAG Service for SGK Informatics"
            }
        )
        
        print("✅ Successfully registered with Eureka!")
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to register with Eureka: {e}")
        print("   Service will run without service discovery")
        return False


async def stop_eureka_async():
    """Stop Eureka client and deregister (async version)"""
    try:
        await eureka_client.stop_async()
        print("👋 Deregistered from Eureka")
    except Exception as e:
        print(f"⚠️ Error during Eureka deregistration: {e}")
