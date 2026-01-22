"""
Cloudflare Turnstile CAPTCHA verification.

Provides server-side verification for Cloudflare Turnstile tokens,
offering a privacy-friendly alternative to traditional CAPTCHAs.
"""

import logging
from typing import Optional
import httpx

from agent_core.config import settings

logger = logging.getLogger(__name__)


class TurnstileVerifier:
    """
    Verify Cloudflare Turnstile tokens.
    
    Turnstile is a free, privacy-friendly CAPTCHA alternative that uses
    behavioral analysis instead of visual puzzles.
    """
    
    VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    
    def __init__(self):
        """Initialize the verifier with configuration."""
        self.enabled = bool(settings.turnstile_secret_key)
        self.secret_key = settings.turnstile_secret_key
        
        if not self.enabled:
            logger.info("Turnstile verification disabled (no secret key configured)")
    
    async def verify_token(
        self,
        token: str,
        remote_ip: Optional[str] = None
    ) -> bool:
        """
        Verify a Turnstile token with Cloudflare.
        
        Args:
            token: The Turnstile token from the client
            remote_ip: Optional client IP for additional validation
            
        Returns:
            True if token is valid, False otherwise
        """
        if not self.enabled:
            logger.warning("Turnstile verification attempted but not configured")
            return False
        
        if not token:
            logger.warning("Empty Turnstile token provided")
            return False
        
        try:
            # Prepare verification request
            payload = {
                "secret": self.secret_key,
                "response": token,
            }
            
            if remote_ip:
                payload["remoteip"] = remote_ip
            
            # Send verification request
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.VERIFY_URL,
                    data=payload
                )
                
                if response.status_code != 200:
                    logger.error(
                        f"Turnstile verification failed with status {response.status_code}"
                    )
                    return False
                
                result = response.json()
                
                # Check verification result
                success = result.get("success", False)
                
                if not success:
                    error_codes = result.get("error-codes", [])
                    logger.warning(
                        f"Turnstile verification failed: {', '.join(error_codes)}"
                    )
                    return False
                
                # Log successful verification
                logger.info(
                    f"Turnstile verification successful (challenge_ts: {result.get('challenge_ts')})"
                )
                return True
        
        except httpx.TimeoutException:
            logger.error("Turnstile verification timed out")
            return False
        
        except Exception as e:
            logger.error(f"Turnstile verification error: {e}")
            return False
    
    def verify_token_sync(
        self,
        token: str,
        remote_ip: Optional[str] = None
    ) -> bool:
        """
        Synchronous version of verify_token.
        
        Args:
            token: The Turnstile token from the client
            remote_ip: Optional client IP for additional validation
            
        Returns:
            True if token is valid, False otherwise
        """
        if not self.enabled:
            return False
        
        if not token:
            return False
        
        try:
            payload = {
                "secret": self.secret_key,
                "response": token,
            }
            
            if remote_ip:
                payload["remoteip"] = remote_ip
            
            # Use synchronous httpx client
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    self.VERIFY_URL,
                    data=payload
                )
                
                if response.status_code != 200:
                    return False
                
                result = response.json()
                return result.get("success", False)
        
        except Exception as e:
            logger.error(f"Turnstile verification error: {e}")
            return False


# Global verifier instance
_verifier: Optional[TurnstileVerifier] = None


def get_turnstile_verifier() -> TurnstileVerifier:
    """Get or create the global Turnstile verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = TurnstileVerifier()
    return _verifier


def reset_turnstile_verifier():
    """Reset the global verifier (mainly for testing)."""
    global _verifier
    _verifier = None
