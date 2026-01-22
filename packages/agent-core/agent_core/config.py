"""
Configuration management for SparkyAI agent.
Uses pydantic-settings for environment variable parsing and validation.
"""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model for responses")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", 
        description="OpenAI model for embeddings"
    )
    
    # Langfuse (Observability)
    langfuse_public_key: str = Field(default="", description="Langfuse public key")
    langfuse_secret_key: str = Field(default="", description="Langfuse secret key")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com", 
        description="Langfuse host URL"
    )
    
    # MaximAI (Evaluation)
    maxim_api_key: str = Field(default="", description="MaximAI API key")
    
    # Upstash Redis
    upstash_redis_rest_url: str = Field(default="", description="Upstash Redis REST URL")
    upstash_redis_rest_token: str = Field(default="", description="Upstash Redis REST token")
    
    # AWS S3
    aws_access_key_id: str = Field(default="", description="AWS access key")
    aws_secret_access_key: str = Field(default="", description="AWS secret key")
    aws_s3_bucket: str = Field(default="sparky-ai-embeddings", description="S3 bucket name")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    
    # Budget Protection
    daily_budget_usd: float = Field(default=2.0, description="Daily budget cap in USD")
    monthly_budget_usd: float = Field(default=30.0, description="Monthly budget cap in USD")
    
    # Agent Configuration
    agent_config: Literal["personal", "buzzy"] = Field(
        default="personal",
        description="Agent persona: 'personal' for SparkyAI, 'buzzy' for EasyBee"
    )
    
    # RAG Configuration
    rag_top_k: int = Field(default=5, description="Number of chunks to retrieve")
    rag_similarity_threshold: float = Field(
        default=0.5, 
        description="Minimum similarity score for RAG results"
    )
    
    # Conversation Limits
    max_conversation_messages: int = Field(
        default=20, 
        description="Max messages before summarization"
    )
    max_message_length: int = Field(default=500, description="Max chars per user message")
    max_messages_per_session: int = Field(
        default=50, 
        description="Max total messages per session"
    )
    
    # Embeddings paths
    embeddings_dir: str = Field(
        default="data/embeddings",
        description="Directory for embedding files"
    )
    knowledge_dir: str = Field(
        default="knowledge",
        description="Directory for knowledge markdown files"
    )
    
    @property
    def langfuse_enabled(self) -> bool:
        """Check if Langfuse is configured."""
        return bool(self.langfuse_public_key and self.langfuse_secret_key)
    
    @property
    def redis_enabled(self) -> bool:
        """Check if Redis is configured."""
        return bool(self.upstash_redis_rest_url and self.upstash_redis_rest_token)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
