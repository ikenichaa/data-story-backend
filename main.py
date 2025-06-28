from fastapi import FastAPI

from api.upload import router as upload_router  # import your router
from api.generate_story import router as generate_story_router
from api.visualize import router as visualize_router
from api.ask_question_from_stat import router as ask_question_stat_router
from api.ask_question_from_rag import router as ask_question_rag_router
from api.affective_narrative import router as affective_narrative_router


from ws.websocket import router as websocket_router


app = FastAPI()
app.include_router(upload_router, prefix="/api")
app.include_router(generate_story_router, prefix="/api")
app.include_router(visualize_router, prefix="/api")
app.include_router(ask_question_stat_router, prefix="/api")
app.include_router(ask_question_rag_router, prefix="/api")
app.include_router(affective_narrative_router, prefix="/api")
app.include_router(websocket_router, prefix="/websocket")
