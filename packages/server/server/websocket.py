"""
WebSocket Connection Manager
============================

Manages WebSocket connections for real-time visualization updates.
Supports multiple concurrent connections and session-based messaging.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections for real-time streaming.
    
    Features:
    - Session-based connection tracking
    - Broadcast support
    - Graceful disconnection handling
    - Event formatting
    """

    def __init__(self):
        """Initialize the connection manager."""
        # Active connections: session_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}

        # Connection metadata
        self._metadata: Dict[str, Dict[str, Any]] = {}

    @property
    def active_connections(self) -> int:
        """Get count of active connections."""
        return len(self._connections)

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            session_id: Session identifier
        """
        await websocket.accept()

        # If session already has a connection, close the old one
        if session_id in self._connections:
            old_ws = self._connections[session_id]
            try:
                await old_ws.close(code=4000, reason="New connection opened")
            except Exception:
                pass

        self._connections[session_id] = websocket
        self._metadata[session_id] = {
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "message_count": 0,
        }

        # Send connection confirmation
        await self.send_event(session_id, "connected", {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def disconnect(self, session_id: str) -> None:
        """
        Remove a connection.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._connections:
            del self._connections[session_id]

        if session_id in self._metadata:
            del self._metadata[session_id]

    def is_connected(self, session_id: str) -> bool:
        """Check if a session has an active connection."""
        return session_id in self._connections

    async def send_event(
        self, 
        session_id: str, 
        event_type: str, 
        payload: Dict[str, Any]
    ) -> bool:
        """
        Send an event to a specific session.
        
        Args:
            session_id: Target session
            event_type: Event type (e.g., "node_enter", "token")
            payload: Event data
            
        Returns:
            True if sent successfully, False otherwise
        """
        if session_id not in self._connections:
            return False

        websocket = self._connections[session_id]

        message = {
            "event": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            await websocket.send_text(json.dumps(message))

            # Update metadata
            if session_id in self._metadata:
                self._metadata[session_id]["message_count"] += 1

            return True

        except Exception:
            # Connection likely closed
            self.disconnect(session_id)
            return False

    async def send_error(
        self, 
        session_id: str, 
        code: str, 
        message: str,
        retry_after: Optional[int] = None,
    ) -> bool:
        """
        Send an error event to a session.
        
        Args:
            session_id: Target session
            code: Error code (e.g., "RATE_LIMITED", "INVALID_INPUT")
            message: Human-readable error message
            retry_after: Optional seconds to wait before retry
            
        Returns:
            True if sent successfully
        """
        payload = {
            "code": code,
            "message": message,
        }

        if retry_after is not None:
            payload["retry_after_seconds"] = retry_after

        return await self.send_event(session_id, "error", payload)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> int:
        """
        Send an event to all connected sessions.
        
        Args:
            event_type: Event type
            payload: Event data
            
        Returns:
            Number of successful sends
        """
        success_count = 0

        # Copy keys to avoid modification during iteration
        session_ids = list(self._connections.keys())

        for session_id in session_ids:
            if await self.send_event(session_id, event_type, payload):
                success_count += 1

        return success_count

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a session's connection."""
        return self._metadata.get(session_id)


# Global connection manager instance
connection_manager = ConnectionManager()
