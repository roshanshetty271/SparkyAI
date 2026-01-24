from langchain.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field
from typing import Optional, Type, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agent_core.config import settings

# --- Calendly Tool ---

class CalendlyInput(BaseModel):
    pass

def get_calendly_link() -> str:
    """Returns Roshan's booking link."""
    # Hardcoded or from env
    return "Here is his booking link: https://calendly.com/roshanshetty271"

calendly_tool = StructuredTool.from_function(
    func=get_calendly_link,
    name="get_calendly_link",
    description="Use this tool when the user wants to book a meeting, schedule a call, or see Roshan's calendar.",
)

# --- Gmail Tool (Real SMTP) ---

class SendEmailInput(BaseModel):
    subject: str = Field(description="The subject of the email.")
    body: str = Field(description="The main content of the email.")
    sender_email: Optional[str] = Field(description="The user's email address if they provided it.", default=None)

def send_email(subject: str, body: str, sender_email: Optional[str] = None) -> str:
    """Sends a REAL email to Roshan using SMTP."""
    
    # Configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Agent's email (Sender)
    # We assume these are set in .env
    # For now, we will fail gracefully if not set
    sender_user = settings.smtp_user or "agent@sparkyai.dev"
    sender_password = settings.smtp_pass
    
    recipient = "roshanshetty271@gmail.com"
    
    if not sender_password:
        return "Error: SMTP_PASS not set in environment variables. I cannot send a real email yet."

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_user
        msg['To'] = recipient
        msg['Subject'] = f"[SparkyAI] {subject}"
        
        # Append user's contact info if available
        final_body = body
        if sender_email:
            final_body += f"\n\n---\nUser Contact: {sender_email}"
            
        msg.attach(MIMEText(final_body, 'plain'))
        
        # Send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_user, sender_password)
            server.send_message(msg)
            
        return "Email sent successfully! Roshan has been notified."
        
    except Exception as e:
        return f"Failed to send email: {str(e)}"

gmail_tool = StructuredTool.from_function(
    func=send_email,
    name="send_email",
    description="Use this tool to send a REAL email to Roshan. Use this when the user wants to contact him, leave a message, or hire him.",
    args_schema=SendEmailInput
)

# Export list
tools_list = [calendly_tool, gmail_tool]
