from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from app.database import get_db
from app.models import Ticket
from app.routes import get_active_subscription
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    # Overview: Count per status
    status_counts = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    status_dict = {s: c for s, c in status_counts}
    
    # Priority breakdown
    priority_counts = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    priority_dict = {p: c for p, c in priority_counts}
    
    # SLA status
    now = datetime.utcnow()
    two_hours_from_now = now + timedelta(hours=2)
    
    # Approaching SLA: due within 2 hours and not resolved/closed
    approaching_sla = db.query(Ticket).filter(
        Ticket.status.notin_(['resolved', 'closed']),
        Ticket.sla_due != None,
        Ticket.sla_due <= two_hours_from_now,
        Ticket.sla_due > now
    ).count()
    
    # Breached SLA: overdue and not resolved/closed
    breached_sla = db.query(Ticket).filter(
        Ticket.status.notin_(['resolved', 'closed']),
        Ticket.sla_due != None,
        Ticket.sla_due < now
    ).count()
    
    # Quick stats
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status == 'open').count()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    resolved_today = db.query(Ticket).filter(
        Ticket.status == 'resolved',
        Ticket.resolved_at >= today_start
    ).count()
    
    # Recent tickets
    recent_tickets = db.query(Ticket).order_by(desc(Ticket.created_at)).limit(10).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": user,
        "status_dict": status_dict,
        "priority_dict": priority_dict,
        "approaching_sla": approaching_sla,
        "breached_sla": breached_sla,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_today": resolved_today,
        "recent_tickets": recent_tickets
    })
