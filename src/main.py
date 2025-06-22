from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from typing import Dict, Any
import logging
import sys

from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass

class SecureConfig:
    """Secure configuration management with validation"""
    
    def __init__(self):
        self.openai_api_key = None
        self._load_and_validate_config()
    
    def _load_and_validate_config(self):
        """Load and validate all configuration"""
        try:
            # Load environment variables
            load_dotenv()
            
            # Get API key from environment variables (try multiple possible keys)
            api_key = (
                os.getenv('OPENAI_API_KEY') or 
                os.getenv('API_KEY') or 
                os.getenv('OPENAI_KEY')
            )
            
            if not api_key:
                raise ConfigurationError("OpenAI API key is missing. Please set OPENAI_API_KEY, API_KEY, or OPENAI_KEY environment variable.")
            
            # Validate API key format (basic validation)
            if not self._validate_api_key_format(api_key):
                raise ConfigurationError("Invalid API key format. OpenAI API keys should start with 'sk-' and have the correct length.")
            
            self.openai_api_key = api_key
            logger.info("Configuration loaded and validated successfully")
            
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during configuration loading: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate basic API key format"""
        if not isinstance(api_key, str):
            return False
        if not api_key.startswith('sk-'):
            return False
        if len(api_key) < 40:  # OpenAI keys are typically longer
            return False
        return True
    
    def get_openai_client(self) -> OpenAI:
        """Get configured OpenAI client"""
        try:
            client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client created successfully")
            return client
        except Exception as e:
            logger.error("Failed to create OpenAI client")
            raise ConfigurationError(f"Failed to create OpenAI client: {e}")

# Initialize secure configuration
try:
    config = SecureConfig()
    client = config.get_openai_client()
except ConfigurationError as e:
    logger.critical(f"Application startup failed: {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Unexpected error during startup: {e}")
    sys.exit(1)

class Message(BaseModel):
    message: str

class ChatGPTService:
    @staticmethod
    def get_response(prompt: str) -> str:
        """ChatGPTからの応答を取得する

        Args:
            prompt (str): プロンプトメッセージ

        Returns:
            str: 生成されたレスポンステキスト
        """
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt},
                ],
                model="gpt-4o-mini-2024-07-18",
                stream=True,
            )
            
            response_text = ""
            for chunk in response:
                for choice in chunk.choices:
                    if choice.delta.content is not None:
                        response_text += choice.delta.content
            
            logger.info("Successfully generated response from OpenAI")
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {type(e).__name__}")
            raise HTTPException(status_code=500, detail="Failed to generate response from AI service")

app = FastAPI(
    title="Chatbot Backend",
    description="A secure chatbot backend with enhanced API key management",
    version="1.0.0"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    logger.info("Application startup complete - configuration validated")

@app.get("/")
def read_root() -> str:
    return "Hello Root!"

@app.get("/hello")
async def read_hello() -> Dict[str, str]:
    return {"message": "Hello World"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "chatbot-backend"}

@app.get("/button/{button_name}")
async def read_chat(button_name: str) -> Dict[str, str]:
    prompt = f"{button_name}という数字にまつわる面白い小噺をして。100文字以内で"
    response_text = ChatGPTService.get_response(prompt)
    return {"response": response_text}

@app.post("/message/")
async def read_message(message: Message) -> Dict[str, str]:
    response_text = ChatGPTService.get_response(message.message)
    return {"message": response_text}
