import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from src.answer_generator import generate_cited_answer
from src.regulation_retriever import retrieve_relevant_regulation_chunks

app = FastAPI(title="FARSight API")

# The Vercel frontend origin is set here once it exists; empty by default
# so no cross-origin requests are allowed until explicitly configured.
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class Citation(BaseModel):
    document: str
    section_number: str
    section_title: str
    page_number: int | None
    corpus_version: str | None


class AskResponse(BaseModel):
    found: bool
    answer: str
    excerpt: str | None
    citation: Citation | None


def build_ask_response(cited_answer: dict) -> AskResponse:
    citation = None
    if cited_answer.get("citation") and cited_answer["citation"].get("available"):
        raw = cited_answer["citation"]
        citation = Citation(
            document=raw["document"],
            section_number=raw["section_number"],
            section_title=raw["section_title"],
            page_number=raw.get("page_number"),
            corpus_version=raw.get("corpus_version"),
        )

    return AskResponse(
        found=cited_answer["answer_was_found"],
        answer=cited_answer["plain_language_summary"],
        excerpt=cited_answer.get("verbatim_excerpt"),
        citation=citation,
    )


@app.post("/api/ask")
async def ask(request: AskRequest) -> AskResponse:
    chunks = retrieve_relevant_regulation_chunks(request.question)
    cited_answer = generate_cited_answer(request.question, chunks)
    return build_ask_response(cited_answer)
