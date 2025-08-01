from fastapi import FastAPI

from api.upload import router as upload_router  # import your router
from fastapi.middleware.cors import CORSMiddleware
from api.visualize import router as visualize_router
from api.ask_question_from_rag import router as ask_question_rag_router
from api.affective_narrative_v2 import router as affective_narrative_router_v2
from api.affective_narrative_v3 import router as affective_narrative_router_v3


from ws.websocket import router as websocket_router


app = FastAPI()

# --- Configure CORS middleware on the main app instance ---
origins = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"], # Allows all headers
)

app.include_router(upload_router, prefix="/api")
app.include_router(visualize_router, prefix="/api")
app.include_router(ask_question_rag_router, prefix="/api")
app.include_router(affective_narrative_router_v2, prefix="/api")
app.include_router(affective_narrative_router_v3, prefix="/api")
app.include_router(websocket_router, prefix="/websocket")
