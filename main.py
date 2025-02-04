from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return "Hello Root!"

@app.get("/hello")
def read_hello():
    return {"hello": "world!"}