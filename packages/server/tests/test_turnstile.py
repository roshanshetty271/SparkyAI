"""
Tests for Cloudflare Turnstile verification.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from server.utils.turnstile import (
    TurnstileVerifier,
    get_turnstile_verifier,
    reset_turnstile_verifier,
)


class TestTurnstileVerifier:
    """Test TurnstileVerifier class."""

    def test_verifier_disabled_without_secret(self):
        """Test verifier is disabled without secret key."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = ""
            
            verifier = TurnstileVerifier()
            assert verifier.enabled is False
    
    def test_verifier_enabled_with_secret(self):
        """Test verifier is enabled with secret key."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret-key"
            
            verifier = TurnstileVerifier()
            assert verifier.enabled is True
            assert verifier.secret_key == "test-secret-key"
    
    @pytest.mark.asyncio
    async def test_verify_token_disabled(self):
        """Test verification returns False when disabled."""
        verifier = TurnstileVerifier()
        verifier.enabled = False
        
        result = await verifier.verify_token("test-token")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_token_empty_token(self):
        """Test verification rejects empty token."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            verifier = TurnstileVerifier()
            verifier.enabled = True
            
            result = await verifier.verify_token("")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful token verification."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            # Mock httpx client
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "challenge_ts": "2026-01-22T10:00:00Z",
                "hostname": "example.com"
            }
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("valid-token")
                
                assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_token_failure(self):
        """Test failed token verification."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            # Mock failed response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["invalid-input-response"]
            }
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("invalid-token")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_token_with_remote_ip(self):
        """Test verification includes remote IP when provided."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            
            mock_post = AsyncMock(return_value=mock_response)
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = mock_post
                
                verifier = TurnstileVerifier()
                await verifier.verify_token("token", remote_ip="192.168.1.1")
                
                # Check that remote IP was included in request
                call_args = mock_post.call_args
                assert call_args[1]["data"]["remoteip"] == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_verify_token_http_error(self):
        """Test verification handles HTTP errors."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            # Mock HTTP error response
            mock_response = Mock()
            mock_response.status_code = 500
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("token")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_token_timeout(self):
        """Test verification handles timeouts."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=httpx.TimeoutException("Timeout")
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("token")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_token_network_error(self):
        """Test verification handles network errors."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=Exception("Network error")
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("token")
                
                assert result is False
    
    def test_verify_token_sync(self):
        """Test synchronous token verification."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            # Mock httpx synchronous client
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.post = Mock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = verifier.verify_token_sync("valid-token")
                
                assert result is True
    
    def test_verify_token_sync_disabled(self):
        """Test sync verification returns False when disabled."""
        verifier = TurnstileVerifier()
        verifier.enabled = False
        
        result = verifier.verify_token_sync("token")
        assert result is False
    
    def test_verify_token_sync_empty(self):
        """Test sync verification rejects empty token."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            verifier = TurnstileVerifier()
            result = verifier.verify_token_sync("")
            
            assert result is False


class TestGlobalVerifier:
    """Test global verifier instance management."""

    def test_get_verifier_returns_singleton(self):
        """Test get_turnstile_verifier returns same instance."""
        reset_turnstile_verifier()
        
        verifier1 = get_turnstile_verifier()
        verifier2 = get_turnstile_verifier()
        
        assert verifier1 is verifier2
    
    def test_reset_verifier(self):
        """Test reset creates new instance."""
        verifier1 = get_turnstile_verifier()
        reset_turnstile_verifier()
        verifier2 = get_turnstile_verifier()
        
        assert verifier1 is not verifier2


class TestTurnstileErrorCodes:
    """Test handling of various Turnstile error codes."""

    @pytest.mark.asyncio
    async def test_missing_input_secret(self):
        """Test handling of missing-input-secret error."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["missing-input-secret"]
            }
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("token")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_invalid_input_response(self):
        """Test handling of invalid-input-response error."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["invalid-input-response"]
            }
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("bad-token")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_timeout_or_duplicate(self):
        """Test handling of timeout-or-duplicate error."""
        with patch("server.utils.turnstile.settings") as mock_settings:
            mock_settings.turnstile_secret_key = "test-secret"
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["timeout-or-duplicate"]
            }
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                verifier = TurnstileVerifier()
                result = await verifier.verify_token("expired-token")
                
                assert result is False


@pytest.mark.integration
class TestTurnstileIntegration:
    """Integration tests requiring Cloudflare Turnstile keys."""

    @pytest.mark.skipif(
        True,  # Skip by default - requires Turnstile keys
        reason="Integration tests require Cloudflare Turnstile keys"
    )
    @pytest.mark.asyncio
    async def test_verify_real_token(self):
        """Test verification with real Cloudflare API."""
        # This test requires TURNSTILE_SECRET_KEY environment variable
        verifier = get_turnstile_verifier()
        
        if not verifier.enabled:
            pytest.skip("Turnstile not configured")
        
        # Note: You need a real token from the frontend to test this
        # This is just a placeholder test structure
        pytest.skip("Requires real Turnstile token from frontend")
