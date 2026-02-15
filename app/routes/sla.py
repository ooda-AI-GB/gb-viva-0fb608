from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import SLAPolicy, Ticket
from app.routes import get_active_subscription
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sla", response_class=HTMLResponse)
async def list_sla(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    policies = db.query(SLAPolicy).order_by(SLAPolicy.id).all()
    
    # SLA Breach Report
    # Tickets that are overdue (sla_due < now) and not resolved/closed
    now = datetime.utcnow()
    breached_tickets = db.query(Ticket).filter(
        Ticket.status.notin_(['resolved', 'closed']),
        Ticket.sla_due != None,
        Ticket.sla_due < now
    ).order_by(Ticket.sla_due).all()
    
    return templates.TemplateResponse("sla/list.html", {
        "request": request,
        "user": user,
        "policies": policies,
        "breached_tickets": breached_tickets
    })

@router.post("/sla")
async def create_update_sla(
    request: Request,
    id: int = Form(None),
    name: str = Form(...),
    priority: str = Form(...),
    response_hours: int = Form(...),
    resolution_hours: int = Form(...),
    active: bool = Form(True),
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    if id:
        policy = db.query(SLAPolicy).filter(SLAPolicy.id == id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        policy.name = name
        policy.priority = priority
        policy.response_hours = response_hours
        policy.resolution_hours = resolution_hours
        policy.active = active
    else:
        policy = SLAPolicy(
            name=name,
            priority=priority,
            response_hours=response_hours,
            resolution_hours=resolution_hours,
            active=active
        )
        db.add(policy)
        
    db.commit()
    return RedirectResponse(url="/sla", status_code=status.HTTP_303_SEE_OTHER)
