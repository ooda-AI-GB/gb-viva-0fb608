from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import AIResponse, Ticket, TicketReply
from app.routes import get_active_subscription
from google import genai
import os
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ai", response_class=HTMLResponse)
async def ai_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    suggestions = db.query(AIResponse).order_by(desc(AIResponse.generated_at)).all()
    # Join with Ticket to show ticket subject? Or do it in template with lazy loading if efficient enough for prototype
    # Better to eager load or join, but let's stick to simple query for now.
    
    return templates.TemplateResponse("ai/dashboard.html", {
        "request": request,
        "user": user,
        "suggestions": suggestions
    })

@router.post("/api/ai/suggest")
async def generate_suggestion(
    request: Request,
    ticket_id: int = Form(...),
    suggestion_type: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    replies = db.query(TicketReply).filter(TicketReply.ticket_id == ticket_id).order_by(TicketReply.created_at).all()
    
    # Construct context
    context = f"Ticket Subject: {ticket.subject}\n"
    context += f"Description: {ticket.description}\n"
    context += f"Status: {ticket.status}, Priority: {ticket.priority}, Category: {ticket.category}\n"
    context += "History:\n"
    for r in replies:
        context += f"- {r.author}: {r.content}\n"
        
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return JSONResponse({"error": "GOOGLE_API_KEY not set"}, status_code=500)
        
    client = genai.Client(api_key=api_key)
    
    prompt = ""
    if suggestion_type == "reply_draft":
        prompt = f"You are a helpful support agent. Draft a professional and empathetic reply to this ticket. Context:\n{context}"
    elif suggestion_type == "summary":
        prompt = f"Summarize the key points of this support ticket conversation in 3-5 bullet points. Context:\n{context}"
    elif suggestion_type == "categorization":
        prompt = f"Analyze this ticket and suggest the most appropriate Category (bug, feature_request, question, billing, account, other) and Priority (low, medium, high, urgent). Provide reasoning. Context:\n{context}"
    else:
        return JSONResponse({"error": "Invalid suggestion type"}, status_code=400)
        
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        content = response.text
        
        # Save suggestion
        ai_resp = AIResponse(
            ticket_id=ticket_id,
            suggestion_type=suggestion_type,
            content=content,
            model_used="gemini-2.5-flash"
        )
        db.add(ai_resp)
        db.commit()
        db.refresh(ai_resp)
        
        return JSONResponse({
            "id": ai_resp.id,
            "content": content,
            "ticket_id": ticket_id
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/ai/suggest/{id}/accept")
async def accept_suggestion(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    suggestion = db.query(AIResponse).filter(AIResponse.id == id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
        
    suggestion.accepted = True
    db.commit()
    return JSONResponse({"status": "accepted"})
