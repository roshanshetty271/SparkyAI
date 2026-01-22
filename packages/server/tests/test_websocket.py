"""Tests for WebSocket functionality."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from server.main import app
from server.websocket import ConnectionManager


client = TestClient(app)


class TestConnectionManager:
    """Test WebSocket connection manager."""

    def test_manager_initialization(self):
        """Test that ConnectionManager initializes correctly."""
        manager = ConnectionManager()
        assert manager is not None
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test adding a connection."""
        manager = ConnectionManager()
        mock_websocket = Mock()

        await manager.connect("test-session", mock_websocket)

        assert "test-session" in manager.active_connections
        assert manager.active_connections["test-session"] == mock_websocket

    def test_disconnect(self):
        """Test removing a connection."""
        manager = ConnectionManager()
        mock_websocket = Mock()
        manager.active_connections["test-session"] = mock_websocket

        manager.disconnect("test-session")

        assert "test-session" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_event(self):
        """Test sending an event to a connection."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        manager.active_connections["test-session"] = mock_websocket

        await manager.send_event(
            "test-session",
            "test_event",
            {"data": "value"}
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["event"] == "test_event"
        assert call_args["data"]["data"] == "value"

    @pytest.mark.asyncio
    async def test_send_event_to_nonexistent_session(self):
        """Test sending event to non-existent session doesn't crash."""
        manager = ConnectionManager()

        # Should not raise an exception
        await manager.send_event(
            "nonexistent-session",
            "test_event",
            {"data": "value"}
        )

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to all connections."""
        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        manager.active_connections["session1"] = mock_ws1
        manager.active_connections["session2"] = mock_ws2

        await manager.broadcast("test_event", {"message": "hello"})

        assert mock_ws1.send_json.called
        assert mock_ws2.send_json.called


class TestWebSocketEndpoint:
    """Test WebSocket endpoint."""

    @pytest.mark.skip(reason="WebSocket testing requires special setup")
    def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        # WebSocket testing with TestClient requires special handling
        # This is a placeholder for proper WebSocket testing
        pass

    @pytest.mark.skip(reason="WebSocket testing requires special setup")
    def test_websocket_message_flow(self):
        """Test message flow through WebSocket."""
        # TODO: Implement proper WebSocket testing
        # Consider using pytest-asyncio with websockets library
        pass

    @pytest.mark.skip(reason="WebSocket testing requires special setup")
    def test_websocket_disconnection(self):
        """Test WebSocket disconnection handling."""
        pass


# Mock-based WebSocket tests
class TestWebSocketWithMocks:
    """Test WebSocket behavior with mocked components."""

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        """Test full connection lifecycle."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        session_id = "test-123"

        # Connect
        await manager.connect(session_id, mock_ws)
        assert session_id in manager.active_connections

        # Send event
        await manager.send_event(session_id, "connected", {})
        assert mock_ws.send_json.called

        # Disconnect
        manager.disconnect(session_id)
        assert session_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test managing multiple concurrent connections."""
        manager = ConnectionManager()

        sessions = ["session1", "session2", "session3"]
        websockets = [AsyncMock() for _ in sessions]

        # Connect all
        for session, ws in zip(sessions, websockets):
            await manager.connect(session, ws)

        assert len(manager.active_connections) == 3

        # Disconnect one
        manager.disconnect("session2")
        assert len(manager.active_connections) == 2
        assert "session2" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_event_types(self):
        """Test sending different event types."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        session_id = "test"

        await manager.connect(session_id, mock_ws)

        # Test different event types
        events = [
            ("connected", {"session_id": session_id}),
            ("node_enter", {"node": "greeter"}),
            ("token", {"token": "Hello"}),
            ("complete", {"response": "Done"}),
        ]

        for event_type, data in events:
            await manager.send_event(session_id, event_type, data)

        assert mock_ws.send_json.call_count == len(events)


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""

    @pytest.mark.asyncio
    async def test_send_to_closed_connection(self):
        """Test sending to a closed connection."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = RuntimeError("Connection closed")

        manager.active_connections["test"] = mock_ws

        # Should not raise exception
        await manager.send_event("test", "test", {})

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connection(self):
        """Test broadcast when one connection fails."""
        manager = ConnectionManager()

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.send_json.side_effect = RuntimeError("Connection error")
        mock_ws3 = AsyncMock()

        manager.active_connections["s1"] = mock_ws1
        manager.active_connections["s2"] = mock_ws2
        manager.active_connections["s3"] = mock_ws3

        # Should continue broadcasting to other connections
        await manager.broadcast("test", {})

        assert mock_ws1.send_json.called
        assert mock_ws3.send_json.called
