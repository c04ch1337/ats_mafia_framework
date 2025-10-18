"""
ATS MAFIA Framework Agent Communication Protocol

This module provides the communication infrastructure for agent-to-agent messaging
within the ATS MAFIA framework. It supports various communication patterns including
direct messaging, broadcasting, pub/sub, and hierarchical communication.
"""

import asyncio
import json
import uuid
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import queue
import websockets
import ssl
from concurrent.futures import ThreadPoolExecutor
import logging

from ..config.settings import FrameworkConfig
from .logging import AuditLogger, AuditEventType, SecurityLevel


class MessageType(Enum):
    """Types of messages that can be sent between agents."""
    DIRECT = "direct"
    BROADCAST = "broadcast"
    REQUEST = "request"
    RESPONSE = "response"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PUBLISH = "publish"
    HEARTBEAT = "heartbeat"
    SYSTEM = "system"
    ERROR = "error"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ConnectionStatus(Enum):
    """Connection status for agents."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class Message:
    """Message data structure for agent communication."""
    id: str
    type: MessageType
    sender: str
    recipient: Optional[str]  # None for broadcast messages
    topic: Optional[str]  # For pub/sub messages
    payload: Dict[str, Any]
    timestamp: datetime
    priority: MessagePriority = MessagePriority.NORMAL
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize message after dataclass creation."""
        if self.metadata is None:
            self.metadata = {}
        
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        
        if self.expires_at and self.expires_at.tzinfo is None:
            self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        data['type'] = MessageType(data['type'])
        data['priority'] = MessagePriority(data['priority'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class AgentInfo:
    """Agent information for communication registry."""
    id: str
    name: str
    type: str
    status: ConnectionStatus
    last_heartbeat: datetime
    endpoint: Optional[str] = None
    capabilities: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize agent info after dataclass creation."""
        if self.capabilities is None:
            self.capabilities = []
        
        if self.metadata is None:
            self.metadata = {}
        
        if self.last_heartbeat.tzinfo is None:
            self.last_heartbeat = self.last_heartbeat.replace(tzinfo=timezone.utc)
    
    def is_alive(self, timeout: int = 60) -> bool:
        """Check if agent is alive based on heartbeat."""
        return (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds() < timeout


class MessageHandler:
    """Message handler for processing incoming messages."""
    
    def __init__(self, agent_id: str):
        """
        Initialize message handler.
        
        Args:
            agent_id: ID of the agent this handler belongs to
        """
        self.agent_id = agent_id
        self.handlers: Dict[MessageType, List[Callable]] = {}
        self.request_handlers: Dict[str, Callable] = {}
        self.subscriptions: Dict[str, List[Callable]] = {}
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
    
    def register_request_handler(self, request_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific request type.
        
        Args:
            request_type: Type of request to handle
            handler: Handler function
        """
        self.request_handlers[request_type] = handler
    
    def subscribe(self, topic: str, handler: Callable) -> None:
        """
        Subscribe to a topic with a handler.
        
        Args:
            topic: Topic to subscribe to
            handler: Handler function for topic messages
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(handler)
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """
        Handle an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Optional response message
        """
        try:
            # Handle direct message types
            if message.type in self.handlers:
                for handler in self.handlers[message.type]:
                    try:
                        result = await self._call_handler(handler, message)
                        if isinstance(result, Message):
                            return result
                    except Exception as e:
                        logging.error(f"Error in message handler: {e}")
            
            # Handle request/response pattern
            if message.type == MessageType.REQUEST:
                request_type = message.payload.get('request_type')
                if request_type in self.request_handlers:
                    try:
                        result = await self._call_handler(
                            self.request_handlers[request_type], 
                            message
                        )
                        if isinstance(result, Message):
                            return result
                    except Exception as e:
                        logging.error(f"Error in request handler: {e}")
            
            # Handle pub/sub messages
            if message.type == MessageType.PUBLISH and message.topic:
                if message.topic in self.subscriptions:
                    for handler in self.subscriptions[message.topic]:
                        try:
                            await self._call_handler(handler, message)
                        except Exception as e:
                            logging.error(f"Error in subscription handler: {e}")
            
            return None
            
        except Exception as e:
            logging.error(f"Error handling message {message.id}: {e}")
            return Message.create_error_response(
                sender=self.agent_id,
                recipient=message.sender,
                original_message_id=message.id,
                error=str(e)
            )
    
    async def _call_handler(self, handler: Callable, message: Message) -> Any:
        """
        Call a handler function with the message.
        
        Args:
            handler: Handler function
            message: Message to pass to handler
            
        Returns:
            Handler result
        """
        if asyncio.iscoroutinefunction(handler):
            return await handler(message)
        else:
            # Run synchronous handlers in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, handler, message)


class CommunicationProtocol:
    """
    Main communication protocol for agent-to-agent messaging.
    
    Supports various communication patterns and provides reliable message delivery
    with acknowledgment, retry logic, and security features.
    """
    
    def __init__(self, 
                 agent_id: str,
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize communication protocol.
        
        Args:
            agent_id: ID of the agent
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.agent_id = agent_id
        self.config = config
        self.audit_logger = audit_logger
        
        # Message handling
        self.message_handler = MessageHandler(agent_id)
        self.message_queue = asyncio.Queue()
        self.response_futures: Dict[str, asyncio.Future] = {}
        
        # Agent registry
        self.agents: Dict[str, AgentInfo] = {}
        self.subscriptions: Set[str] = set()
        
        # Connection management
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.websocket = None
        self.server = None
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # Background tasks
        self.heartbeat_task = None
        self.message_processor_task = None
        self.cleanup_task = None
        
        # Thread pool for synchronous operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'connections_made': 0,
            'connections_lost': 0
        }
    
    async def start_server(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Start the communication server.
        
        Args:
            host: Host to bind to (default from config)
            port: Port to bind to (default from config)
        """
        host = host or self.config.communication_host
        port = port or self.config.communication_port
        
        try:
            self.server = await websockets.serve(
                self._handle_client_connection,
                host,
                port,
                ssl=self._get_ssl_context() if self.config.ssl_enabled else None
            )
            
            self.connection_status = ConnectionStatus.CONNECTED
            
            # Start background tasks
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.message_processor_task = asyncio.create_task(self._message_processor_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="server_started",
                    details={'host': host, 'port': port}
                )
            
            logging.info(f"Communication server started on {host}:{port}")
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            logging.error(f"Failed to start communication server: {e}")
            raise
    
    async def stop_server(self) -> None:
        """Stop the communication server."""
        try:
            # Cancel background tasks
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            if self.message_processor_task:
                self.message_processor_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Close all client connections
            for client in self.clients.values():
                await client.close()
            self.clients.clear()
            
            # Stop the server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            self.connection_status = ConnectionStatus.DISCONNECTED
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="server_stopped",
                    details={}
                )
            
            logging.info("Communication server stopped")
            
        except Exception as e:
            logging.error(f"Error stopping communication server: {e}")
    
    async def connect_to_agent(self, agent_info: AgentInfo) -> bool:
        """
        Connect to another agent.
        
        Args:
            agent_info: Information about the agent to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        if not agent_info.endpoint:
            logging.error(f"No endpoint specified for agent {agent_info.id}")
            return False
        
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            
            # Create SSL context if needed
            ssl_context = self._get_ssl_context() if self.config.ssl_enabled else None
            
            # Connect to agent
            self.websocket = await websockets.connect(
                agent_info.endpoint,
                ssl=ssl_context
            )
            
            # Register agent
            self.agents[agent_info.id] = agent_info
            
            # Start message listener
            asyncio.create_task(self._listen_for_messages())
            
            self.connection_status = ConnectionStatus.CONNECTED
            self.stats['connections_made'] += 1
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="agent_connected",
                    details={'agent_id': agent_info.id, 'endpoint': agent_info.endpoint}
                )
            
            logging.info(f"Connected to agent {agent_info.id} at {agent_info.endpoint}")
            return True
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.stats['connections_lost'] += 1
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="connection_failed",
                    details={'agent_id': agent_info.id, 'error': str(e)}
                )
            
            logging.error(f"Failed to connect to agent {agent_info.id}: {e}")
            return False
    
    async def disconnect_from_agent(self, agent_id: str) -> None:
        """
        Disconnect from an agent.
        
        Args:
            agent_id: ID of the agent to disconnect from
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.stats['connections_lost'] += 1
        
        if self.audit_logger:
            self.audit_logger.communication_event(
                action="agent_disconnected",
                details={'agent_id': agent_id}
            )
        
        logging.info(f"Disconnected from agent {agent_id}")
    
    async def send_message(self, message: Message) -> bool:
        """
        Send a message to another agent.
        
        Args:
            message: Message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Check if message is expired
            if message.is_expired():
                logging.warning(f"Message {message.id} has expired, not sending")
                return False
            
            # Serialize message
            message_data = message.to_dict()
            message_json = json.dumps(message_data)
            
            # Send via WebSocket if available
            if self.websocket:
                await self.websocket.send(message_json)
            else:
                # Send via server to connected clients
                if message.recipient and message.recipient in self.clients:
                    await self.clients[message.recipient].send(message_json)
                elif message.recipient is None:
                    # Broadcast to all clients
                    for client in self.clients.values():
                        await client.send(message_json)
                else:
                    logging.warning(f"Recipient {message.recipient} not found")
                    return False
            
            self.stats['messages_sent'] += 1
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="message_sent",
                    details={
                        'message_id': message.id,
                        'type': message.type.value,
                        'recipient': message.recipient,
                        'topic': message.topic
                    }
                )
            
            return True
            
        except Exception as e:
            self.stats['messages_failed'] += 1
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="message_send_failed",
                    details={
                        'message_id': message.id,
                        'error': str(e)
                    }
                )
            
            logging.error(f"Failed to send message {message.id}: {e}")
            return False
    
    async def send_request(self,
                          recipient: str,
                          request_type: str,
                          payload: Dict[str, Any],
                          timeout: float = 30.0) -> Optional[Message]:
        """
        Send a request and wait for response.
        
        Args:
            recipient: ID of the recipient agent
            request_type: Type of request
            payload: Request payload
            timeout: Timeout in seconds
            
        Returns:
            Response message or None if timeout/error
        """
        correlation_id = str(uuid.uuid4())
        
        # Create request message
        request = Message(
            id=str(uuid.uuid4()),
            type=MessageType.REQUEST,
            sender=self.agent_id,
            recipient=recipient,
            payload={
                'request_type': request_type,
                **payload
            },
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id
        )
        
        # Create future for response
        response_future = asyncio.Future()
        self.response_futures[correlation_id] = response_future
        
        try:
            # Send request
            if not await self.send_message(request):
                return None
            
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            logging.warning(f"Request {request.id} timed out")
            return None
        except Exception as e:
            logging.error(f"Error sending request {request.id}: {e}")
            return None
        finally:
            # Clean up future
            self.response_futures.pop(correlation_id, None)
    
    async def broadcast(self,
                       message_type: MessageType,
                       payload: Dict[str, Any],
                       topic: Optional[str] = None) -> None:
        """
        Broadcast a message to all agents or to a specific topic.
        
        Args:
            message_type: Type of message
            payload: Message payload
            topic: Optional topic for pub/sub
        """
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            sender=self.agent_id,
            recipient=None,  # Broadcast
            topic=topic,
            payload=payload,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.send_message(message)
    
    async def subscribe(self, topic: str) -> None:
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
        """
        self.subscriptions.add(topic)
        
        # Send subscription message
        await self.broadcast(
            MessageType.SUBSCRIBE,
            {'topic': topic}
        )
        
        if self.audit_logger:
            self.audit_logger.communication_event(
                action="topic_subscribed",
                details={'topic': topic}
            )
    
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
        """
        self.subscriptions.discard(topic)
        
        # Send unsubscription message
        await self.broadcast(
            MessageType.UNSUBSCRIBE,
            {'topic': topic}
        )
        
        if self.audit_logger:
            self.audit_logger.communication_event(
                action="topic_unsubscribed",
                details={'topic': topic}
            )
    
    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            payload: Message payload
        """
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.PUBLISH,
            sender=self.agent_id,
            recipient=None,
            topic=topic,
            payload=payload,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.send_message(message)
    
    def register_agent(self, agent_info: AgentInfo) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent_info: Information about the agent
        """
        self.agents[agent_info.id] = agent_info
        
        if self.audit_logger:
            self.audit_logger.communication_event(
                action="agent_registered",
                details={'agent_id': agent_info.id, 'type': agent_info.type}
            )
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="agent_unregistered",
                    details={'agent_id': agent_id}
                )
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        Get information about an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent information or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentInfo]:
        """
        Get information about all registered agents.
        
        Returns:
            List of agent information
        """
        return list(self.agents.values())
    
    def get_alive_agents(self, timeout: int = 60) -> List[AgentInfo]:
        """
        Get information about all alive agents.
        
        Args:
            timeout: Heartbeat timeout in seconds
            
        Returns:
            List of alive agent information
        """
        return [agent for agent in self.agents.values() if agent.is_alive(timeout)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            **self.stats,
            'registered_agents': len(self.agents),
            'alive_agents': len(self.get_alive_agents()),
            'connected_clients': len(self.clients),
            'subscriptions': len(self.subscriptions),
            'connection_status': self.connection_status.value
        }
    
    async def _handle_client_connection(self,
                                       websocket: websockets.WebSocketServerProtocol,
                                       path: str) -> None:
        """
        Handle a new client connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_id = None
        
        try:
            # Wait for client identification
            identification = await websocket.recv()
            identification_data = json.loads(identification)
            
            client_id = identification_data.get('agent_id')
            if not client_id:
                await websocket.close(1008, "Agent ID required")
                return
            
            # Register client
            self.clients[client_id] = websocket
            
            # Create agent info
            agent_info = AgentInfo(
                id=client_id,
                name=identification_data.get('name', client_id),
                type=identification_data.get('type', 'unknown'),
                status=ConnectionStatus.CONNECTED,
                last_heartbeat=datetime.now(timezone.utc),
                endpoint=f"{websocket.remote_address[0]}:{websocket.remote_address[1]}",
                capabilities=identification_data.get('capabilities', []),
                metadata=identification_data.get('metadata', {})
            )
            
            self.register_agent(agent_info)
            
            # Send acknowledgment
            await websocket.send(json.dumps({
                'type': 'connection_acknowledged',
                'agent_id': self.agent_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
            # Listen for messages
            async for message in websocket:
                await self._handle_received_message(message, client_id)
                
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"Client {client_id} disconnected")
        except Exception as e:
            logging.error(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client
            if client_id:
                self.clients.pop(client_id, None)
                self.unregister_agent(client_id)
    
    async def _handle_received_message(self, message: str, sender_id: str) -> None:
        """
        Handle a received message.
        
        Args:
            message: JSON message string
            sender_id: ID of the sender
        """
        try:
            message_data = json.loads(message)
            message_obj = Message.from_dict(message_data)
            
            # Update sender heartbeat
            if sender_id in self.agents:
                self.agents[sender_id].last_heartbeat = datetime.now(timezone.utc)
            
            # Handle response messages
            if (message_obj.type == MessageType.RESPONSE and
                message_obj.correlation_id in self.response_futures):
                
                future = self.response_futures[message_obj.correlation_id]
                if not future.done():
                    future.set_result(message_obj)
                return
            
            # Process message through handler
            response = await self.message_handler.handle_message(message_obj)
            
            # Send response if available
            if response:
                await self.send_message(response)
            
            self.stats['messages_received'] += 1
            
            if self.audit_logger:
                self.audit_logger.communication_event(
                    action="message_received",
                    details={
                        'message_id': message_obj.id,
                        'type': message_obj.type.value,
                        'sender': sender_id
                    }
                )
                
        except Exception as e:
            logging.error(f"Error handling received message: {e}")
            self.stats['messages_failed'] += 1
    
    async def _listen_for_messages(self) -> None:
        """Listen for messages from connected WebSocket."""
        try:
            async for message in self.websocket:
                await self._handle_received_message(message, self.agent_id)
        except websockets.exceptions.ConnectionClosed:
            logging.info("WebSocket connection closed")
        except Exception as e:
            logging.error(f"Error listening for messages: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages."""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                heartbeat = Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.HEARTBEAT,
                    sender=self.agent_id,
                    recipient=None,
                    payload={'timestamp': datetime.now(timezone.utc).isoformat()},
                    timestamp=datetime.now(timezone.utc)
                )
                
                await self.send_message(heartbeat)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in heartbeat loop: {e}")
    
    async def _message_processor_loop(self) -> None:
        """Process messages from the queue."""
        while True:
            try:
                message = await self.message_queue.get()
                await self.send_message(message)
                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in message processor loop: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Clean up expired messages and dead agents."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up dead agents
                current_time = datetime.now(timezone.utc)
                dead_agents = [
                    agent_id for agent_id, agent in self.agents.items()
                    if not agent.is_alive(120)  # 2 minute timeout
                ]
                
                for agent_id in dead_agents:
                    self.unregister_agent(agent_id)
                    logging.info(f"Removed dead agent: {agent_id}")
                
                # Clean up expired response futures
                expired_futures = [
                    correlation_id for correlation_id, future in self.response_futures.items()
                    if future.done()
                ]
                
                for correlation_id in expired_futures:
                    self.response_futures.pop(correlation_id, None)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")
    
    def _get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Get SSL context for secure connections.
        
        Returns:
            SSL context or None if SSL not enabled
        """
        if not self.config.ssl_enabled:
            return None
        
        # Create SSL context
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Load certificates (placeholder - implement based on your cert setup)
        # context.load_cert_chain('server.crt', 'server.key')
        
        return context


# Static methods for Message class
Message.create_error_response = classmethod(
    lambda cls, sender, recipient, original_message_id, error: cls(
        id=str(uuid.uuid4()),
        type=MessageType.ERROR,
        sender=sender,
        recipient=recipient,
        payload={
            'error': error,
            'original_message_id': original_message_id
        },
        timestamp=datetime.now(timezone.utc),
        reply_to=original_message_id
    )
)