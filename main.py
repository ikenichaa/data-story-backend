from fastapi import FastAPI
from api.upload import router as upload_router  # import your router

app = FastAPI()
app.include_router(upload_router, prefix="/api")


if __name__ == "__main__":
   print("hello")
