import os
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel,Field
from google import genai
from typing import Literal
from google.genai import types
from dotenv import load_dotenv
import json
from fastapi.responses import StreamingResponse

from dependencies import get_current_user

router=APIRouter(prefix="/ai",tags=["AI"])
load_dotenv(

)
if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is not set in.env")

client=genai.Client()

MODEL_NAME="gemini-3.1-flash-lite"
GENERATION_CONFIG=types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=512,
)
SYSTEM_CONTEXT = """You are a helpful programming assistant for college
students learning Python full stack development. Explain concepts clearly
and concisely using simple real-world analogies. Use short code examples
when helpful. Keep answers beginner-friendly and under 200 words unless
the question genuinely requires more detail."""


chat_session:dict[int,object]={}

def get_or_create_session(user_id:int):
    if user_id not in chat_session:
        chat_session[user_id]=client.chats.create(
            model=MODEL_NAME,
            history=[
                {"role":"user","parts":[{"text":SYSTEM_CONTEXT}]},
                {"role":"model","parts":[{"text":"Understood.Ready to help."}]},

            ]
        )
    return chat_session[user_id]

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

class AskResponse(BaseModel):
    answer: str


#---------Generatec

class ChatRequest(BaseModel):
    message:str=Field(min_lenght=1,max_length=1000)

class ChatResponse(BaseModel):
    reply:str


@router.post("/chat",response_model=ChatResponse)
def chat_with_ai(
    request:ChatRequest,
    current_user=Depends(get_current_user),

):
    session=get_or_create_session(current_user.id)
    try:
        response=session.send_message(request.message)
        return ChatResponse(reply=response.text.strip())
    except ValueError:
        raise HTTPException(status_code=400,detail="Message could not be prcessed - try rephrasiing.")
    except Exception as exc:
        print(f"[chat] Gemini error:{exc}")
        raise HTTPException(status_code=503,detail="AI service unavailable.")


#------------------------------------------------------------




@router.post("/ask", response_model=AskResponse)
def ask_ai(
    request: AskRequest,
    current_user=Depends(get_current_user)   # JWT protection
):
    # Combine system context with the user's question
    full_prompt = f"{SYSTEM_CONTEXT}\n\nStudent question: {request.question}"

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt,
            config=GENERATION_CONFIG,
        )
        return AskResponse(answer=response.text)

    except ValueError:
        # Safety filter blocked the response
        raise HTTPException(
            status_code=400,
            detail="This question could not be answered. Please rephrase it."
        )
    except Exception as e:
        print(f"Gemini error: {e}")   # log to server console
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Try again in a moment."
        )

    
@router.delete("/chat/reset",status_code=204)
def reset_chat(current_user=Depends(get_current_user)):
    chat_session.pop(current_user.id,None)
    return AskResponse(status_code=204)


###
### SUMMARIZE ENDPOINT
###

class SummariseRequest(BaseModel):
    text:str=Field(min_lenght=20,max_length=5000)
    max_words:int = Field(default=150,ge=30,le=500)

class SummariseResponse(BaseModel):
    summary:str


@router.post("/summarize",response_model=SummariseResponse)
def summarize_text(
    request:SummariseRequest,
    current_user=Depends(get_current_user),
):
    prompt=(
        f"Summarise the following text in no morl than {request.max_words} words."
        f"Return only the summary - no heading, no preamble, on commentary.\n\n"
        f"TEXT:\n{request.text}"
    )
    try:
        response=client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3,max_output_tokens=600),

        )
        return SummariseResponse(summary=response.text.strip())
    except ValueError:
        raise HTTPException(status_code=400,detail="content could not processed.")
    except Exception as exc:
        print(f"[summarize] Gemini error:{exc}")
        raise HTTPException(status_code=503,detail="AI service unavailable.")
    


###
### EXPLANI ENDPOINT
    ###

class ExplainRequest(BaseModel):
    topic:str=Field(min_length=2,max_length=300)
    level:Literal["beginner","intermediate","expert"]
    

class ExplainResponse(BaseModel):
        explanation:str

LEVEL_PERSONAS={
    "beginner":  "a school student who has never programmed before",
    "intermediate":"a college student who knows python basics",
    "expert":"a senior software engineer who wants implementation deetails",
}

@router.post("/explain",response_model=ExplainResponse)
def explain_topoic(
    request:ExplainRequest,
    current_user=Depends(get_current_user),
):
    persona=LEVEL_PERSONAS[request.level]
    prompt=(
        f"Explian the following to {persona}.\n"
        f"Include a real-world ananlogy."
        f"If relevent,add a shor python code example (5 lines max.).\n"
        f"Keep the explanation under 200 words.\n\n"
        f"TOPIC:{request.topic}"
    )
    try:
        response=client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=GENERATION_CONFIG,
        )
        raise ExplainResponse(explanation=response.text.strip())
    except ValueError:
        raise HTTPException(status_code=400,detail="content not be processed.")
    except Exception as exc:
        print(f"[explain] Gemini error:{exc}")
        raise HTTPException(status_code=503,detail="AI service unavailable.")
    



class StreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

# ── Generator that yields SSE-formatted chunks ───────────────────────
def stream_chat_response(user_id: int, message: str):
    """
    Generator: yields SSE events as Gemini produces tokens.
    Uses the user's existing ChatSession so history is maintained.
    """
    session = get_or_create_session(user_id)
    try:
        for chunk in session.send_message_stream(message):
            if chunk.text:
                data = json.dumps({"chunk": chunk.text})
                yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    except ValueError:
        error = json.dumps({"error": "Content blocked — try rephrasing."})
        yield f"data: {error}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as exc:
        print(f"[stream] Gemini error: {exc}")
        error = json.dumps({"error": "AI service temporarily unavailable."})
        yield f"data: {error}\n\n"
        yield "data: [DONE]\n\n"

# ── POST /ai/stream ──────────────────────────────────────────────────
@router.post("/stream")
def stream_ai_response(
    request: StreamRequest,
    current_user=Depends(get_current_user),
):
    return StreamingResponse(
        stream_chat_response(current_user.id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",    # prevents nginx from buffering chunks
        }
    )