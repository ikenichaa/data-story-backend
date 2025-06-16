from fastapi import FastAPI
from api.upload import router as upload_router  # import your router
from ws.websocket import router as websocket_router

# from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaEmbeddings

app = FastAPI()
app.include_router(upload_router, prefix="/api")
app.include_router(websocket_router, prefix="/websocket")


# if __name__ == "__main__":
# print("Hello")
# embedding_function = OllamaEmbeddings(model="deepseek-r1:7b")
