"""
ATS MAFIA WebSocket Server
Handles real-time communication for training sessions, system updates, and notifications
"""

import asyncio
import json
import logging
import uvicorn
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.websockets import WebSocketState
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        # Store active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Store subscriptions by topic
        self.subscriptions: Dict[str, Set[str]] = {}
        # Store session subscribers
        self.session_subscribers: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send connection confirmation
        await self.send_personal_message(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        # Remove from all subscriptions
        for topic_subscribers in self.subscriptions.values():
            topic_subscribers.discard(client_id)
            
        # Remove from session subscriptions
        for session_subscribers in self.session_subscribers.values():
            session_subscribers.discard(client_id)
            
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, client_id: str, message: dict) -> None:
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
                
    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None) -> None:
        """Broadcast a message to all connected clients"""
        exclude = exclude or set()
        disconnected = []
        
        for client_id, websocket in self.active_connections.items():
            if client_id not in exclude:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append(client_id)
                    
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
            
    async def broadcast_to_topic(self, topic: str, message: dict) -> None:
        """Broadcast a message to all subscribers of a topic"""
        if topic in self.subscriptions:
            subscribers = self.subscriptions[topic].copy()
            for client_id in subscribers:
                await self.send_personal_message(client_id, message)
                
    async def broadcast_to_session(self, session_id: str, message: dict) -> None:
        """Broadcast a message to all subscribers of a training session"""
        if session_id in self.session_subscribers:
            subscribers = self.session_subscribers[session_id].copy()
            for client_id in subscribers:
                await self.send_personal_message(client_id, message)
                
    def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe a client to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(client_id)
        logger.info(f"Client {client_id} subscribed to topic: {topic}")
        
    def unsubscribe(self, client_id: str, topic: str) -> None:
        """Unsubscribe a client from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)
            logger.info(f"Client {client_id} unsubscribed from topic: {topic}")
            
    def subscribe_to_session(self, client_id: str, session_id: str) -> None:
        """Subscribe a client to a training session"""
        if session_id not in self.session_subscribers:
            self.session_subscribers[session_id] = set()
        self.session_subscribers[session_id].add(client_id)
        logger.info(f"Client {client_id} subscribed to session: {session_id}")
        
    def unsubscribe_from_session(self, client_id: str, session_id: str) -> None:
        """Unsubscribe a client from a training session"""
        if session_id in self.session_subscribers:
            self.session_subscribers[session_id].discard(client_id)
            logger.info(f"Client {client_id} unsubscribed from session: {session_id}")


# Global connection manager instance
manager = ConnectionManager()


async def handle_client_message(client_id: str, message: dict) -> None:
    """Handle incoming messages from clients"""
    message_type = message.get("type")
    
    try:
        if message_type == "subscribe":
            topic = message.get("topic")
            if topic:
                manager.subscribe(client_id, topic)
                await manager.send_personal_message(client_id, {
                    "type": "subscribed",
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        elif message_type == "unsubscribe":
            topic = message.get("topic")
            if topic:
                manager.unsubscribe(client_id, topic)
                await manager.send_personal_message(client_id, {
                    "type": "unsubscribed",
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        elif message_type == "join_session":
            session_id = message.get("session_id")
            if session_id:
                manager.subscribe_to_session(client_id, session_id)
                await manager.send_personal_message(client_id, {
                    "type": "session_joined",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        elif message_type == "leave_session":
            session_id = message.get("session_id")
            if session_id:
                manager.unsubscribe_from_session(client_id, session_id)
                await manager.send_personal_message(client_id, {
                    "type": "session_left",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        elif message_type == "ping":
            await manager.send_personal_message(client_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        elif message_type == "voice_command":
            command = message.get("command")
            logger.info(f"Voice command from {client_id}: {command}")
            # Handle voice commands
            await manager.send_personal_message(client_id, {
                "type": "voice_command_received",
                "command": command,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        else:
            logger.warning(f"Unknown message type from {client_id}: {message_type}")
            await manager.send_personal_message(client_id, {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error handling message from {client_id}: {e}")
        await manager.send_personal_message(client_id, {
            "type": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """WebSocket endpoint handler"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(client_id, message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {data}")
                await manager.send_personal_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


# Helper functions for broadcasting events

async def broadcast_training_update(session_id: str, update_data: dict) -> None:
    """Broadcast a training session update"""
    message = {
        "type": "training_update",
        "session_id": session_id,
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_session(session_id, message)


async def broadcast_system_status(status_data: dict) -> None:
    """Broadcast system status update"""
    message = {
        "type": "system_status",
        "data": status_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_topic("system_status", message)


async def broadcast_notification(notification: dict, target: Optional[str] = None) -> None:
    """Broadcast a notification"""
    message = {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if target:
        await manager.send_personal_message(target, message)
    else:
        await manager.broadcast(message)


async def broadcast_voice_event(event_data: dict, target: Optional[str] = None) -> None:
    """Broadcast a voice system event"""
    message = {
        "type": "voice_event",
        "data": event_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if target:
        await manager.send_personal_message(target, message)
    else:
        await manager.broadcast_to_topic("voice", message)


async def broadcast_tool_execution(tool_name: str, execution_data: dict) -> None:
    """Broadcast tool execution event"""
    message = {
        "type": "tool_execution",
        "tool": tool_name,
        "data": execution_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast_to_topic("tools", message)


async def broadcast_cost_alert(alert_data: dict, target: Optional[str] = None) -> None:
    """Broadcast cost alert"""
    message = {
        "type": "cost_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if target:
        await manager.send_personal_message(target, message)
    else:
        await manager.broadcast(message)


# Background task for periodic updates
async def periodic_system_status_update(interval: int = 30):
    """Periodically broadcast system status updates"""
    while True:
        try:
            # Get system status (implement actual status retrieval)
            status = {
                "status": "operational",
                "active_sessions": 0,
                "cpu_usage": 0,
                "memory_usage": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await broadcast_system_status(status)
            await asyncio.sleep(interval)
            
        except Exception as e:
            logger.error(f"Error in periodic status update: {e}")
            await asyncio.sleep(interval)


# Create FastAPI application for WebSocket server
app = FastAPI(
    title="ATS MAFIA WebSocket Server",
    description="Real-time communication server for training sessions",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ATS MAFIA WebSocket Server", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "connections": len(manager.active_connections)}


@app.websocket("/ws")
async def websocket_endpoint_route(websocket: WebSocket, client_id: str = Query(...)):
    """WebSocket endpoint with client_id query parameter"""
    await websocket_endpoint(websocket, client_id)


@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    logger.info("WebSocket server starting up...")
    
    # Start periodic system status updates
    asyncio.create_task(periodic_system_status_update())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("WebSocket server shutting down...")
    
    # Disconnect all clients
    for client_id in list(manager.active_connections.keys()):
        manager.disconnect(client_id)


# Export connection manager and key functions
__all__ = [
    'app',
    'manager',
    'websocket_endpoint',
    'broadcast_training_update',
    'broadcast_system_status',
    'broadcast_notification',
    'broadcast_voice_event',
    'broadcast_tool_execution',
    'broadcast_cost_alert',
    'periodic_system_status_update'
]


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the WebSocket server
    uvicorn.run(
        "websocket_server:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )