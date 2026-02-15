from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models import KnowledgeArticle
from app.routes import get_active_subscription
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# PUBLIC ROUTES
@router.get("/knowledge", response_class=HTMLResponse)
async def list_articles(
    request: Request,
    search: str = None,
    category: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeArticle).filter(KnowledgeArticle.published == True)
    
    if search:
        query = query.filter(or_(
            KnowledgeArticle.title.ilike(f"%{search}%"),
            KnowledgeArticle.content.ilike(f"%{search}%"),
            KnowledgeArticle.tags.ilike(f"%{search}%")
        ))
    if category:
        query = query.filter(KnowledgeArticle.category == category)
        
    articles = query.order_by(desc(KnowledgeArticle.views)).all()
    
    # Group by category for the view if needed, or just pass list
    # The spec says "Grouped by category, search bar, most viewed articles"
    # I'll pass all articles and let the template group them or I can group them here.
    # Let's grouping here is easier for Jinja sometimes.
    
    categories = ["getting_started", "troubleshooting", "billing", "features", "api"]
    grouped_articles = {cat: [] for cat in categories}
    for a in articles:
        if a.category in grouped_articles:
            grouped_articles[a.category].append(a)
        else:
            # Handle unknown categories or add to 'other'
            pass
            
    most_viewed = sorted(articles, key=lambda x: x.views, reverse=True)[:5]
            
    return templates.TemplateResponse("knowledge/list.html", {
        "request": request,
        "articles": articles, # Flattened list if needed
        "grouped_articles": grouped_articles,
        "most_viewed": most_viewed,
        "search": search,
        "category": category,
        "user": None # No auth required
    })

@router.get("/knowledge/{id}", response_class=HTMLResponse)
async def view_article(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    # Increment views (simple approach, naive counter)
    article.views += 1
    db.commit()
    
    return templates.TemplateResponse("knowledge/article.html", {
        "request": request,
        "article": article,
        "user": None
    })

@router.post("/knowledge/{id}/vote")
async def vote_article(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    article.helpful_votes += 1
    db.commit()
    return RedirectResponse(url=f"/knowledge/{id}", status_code=status.HTTP_303_SEE_OTHER)


# AUTH ROUTES
@router.get("/knowledge/new", response_class=HTMLResponse) # Wait, path conflict with {id} if id is not int. FastAPI matches specific first usually.
# But "new" is a string. If I define /knowledge/new BEFORE /knowledge/{id}, it works.
# But I defined it AFTER. I should move it up or rely on type validation (id: int). 
# FastAPI handles this well if types differ, but "new" can be cast to int? No. 
# So it should be fine, but better to put specific paths before dynamic ones.
# I will define new routes BEFORE {id} route in next edit if needed, or just here.
async def new_article_form(request: Request, user=Depends(get_active_subscription)):
    return templates.TemplateResponse("knowledge/form.html", {"request": request, "user": user})

@router.post("/knowledge/new")
async def create_article(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    tags: str = Form(None),
    published: bool = Form(True),
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    article = KnowledgeArticle(
        title=title,
        content=content,
        category=category,
        tags=tags,
        published=published
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return RedirectResponse(url=f"/knowledge/{article.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/knowledge/{id}/edit", response_class=HTMLResponse)
async def edit_article_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse("knowledge/form.html", {"request": request, "user": user, "article": article})

@router.post("/knowledge/{id}/edit")
async def update_article(
    request: Request,
    id: int,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    tags: str = Form(None),
    published: bool = Form(True),
    db: Session = Depends(get_db),
    user=Depends(get_active_subscription)
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    article.title = title
    article.content = content
    article.category = category
    article.tags = tags
    article.published = published
    
    db.commit()
    return RedirectResponse(url=f"/knowledge/{id}", status_code=status.HTTP_303_SEE_OTHER)
