from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from typing import Dict, Any

from dotenv import load_dotenv
import os

# 環境変数の設定
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('API_KEY')

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

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
            
            return response_text
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> str:
    return "Hello Root!"

@app.get("/hello")
async def read_hello() -> Dict[str, str]:
    return {"message": "Hello World"}

@app.get("/button/{button_name}")
async def read_chat(button_name: str) -> Dict[str, str]:
    prompt = f"{button_name}という数字にまつわる面白い小噺をして。100文字以内で"
    response_text = ChatGPTService.get_response(prompt)
    return {"response": response_text}

@app.post("/message/")
async def read_message(message: Message) -> Dict[str, str]:
    response_text = ChatGPTService.get_response(message.message)
    return {"message": response_text}
