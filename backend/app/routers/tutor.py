import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.database import get_session
from app.modules.module3_tutor.service import tutor_answer

router = APIRouter(prefix="/tutor", tags=["Module 3 - Tutor"])

class TutorRequest(BaseModel):
    course_id: int
    message: str = Field(min_length=1, max_length=2000)
    hint: bool = False
    analogy: str = ""


class TutorSource(BaseModel):
    id: int
    label: str
    score: float
    text: str


class TutorResponse(BaseModel):
    answer: str
    sources: list[TutorSource]
    redirected: bool
    badges: list[str]
    generation_mode: str

@router.post("/chat", response_model=TutorResponse)
def chat(data: TutorRequest, session: Session = Depends(get_session)):
    return tutor_answer(session, data.course_id, data.message, data.hint, data.analogy)

@router.post("/chat/stream")
def chat_stream(data: TutorRequest, session: Session = Depends(get_session)):
    result = TutorResponse.model_validate(tutor_answer(session, data.course_id, data.message, data.hint, data.analogy)).model_dump()
    def events():
        for start in range(0, len(result["answer"]), 32):
            yield "data: " + json.dumps({"text": result["answer"][start:start + 32]}, ensure_ascii=False) + "\n\n"
        yield "data: " + json.dumps({"done": True, "sources": result["sources"], "redirected": result["redirected"], "badges": result["badges"], "generation_mode": result["generation_mode"]}, ensure_ascii=False) + "\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
