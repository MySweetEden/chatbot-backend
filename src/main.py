from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('API_KEY')

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def response_chatgpt(
    button_name: str,
):
    """ChatGPTのレスポンスを取得

    Args:
        user_msg (str): ユーザーメッセージ。
    """
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": f"{button_name}という数字にまつわる面白い小噺をして。100文字以内で"},
        ],
        model="gpt-4o-mini-2024-07-18",
        stream=True,
    )
    return response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return "Hello Root!"

@app.get("/hello")
async def read_hello():
    return {"message": "Hello World"}

@app.get("/{button_name}")
async def read_chat(button_name: str) -> dict:
    print(button_name)
    try:
        response_text = ""
        
        for chunk in response_chatgpt(button_name):
            for choice in chunk.choices:
                if choice.delta.content is not None:
                    response_text += choice.delta.content
        
        return {"response": response_text}
    except Exception as e:
        return {"error": str(e)}
