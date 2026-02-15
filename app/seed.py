from sqlalchemy.orm import Session
from app.models import Ticket, TicketReply, KnowledgeArticle, SLAPolicy, AIResponse
from datetime import datetime, timedelta

def seed_app_data(db: Session):
    # Check if we need to seed
    if db.query(Ticket).count() > 0:
        return

    # 1. SLA Policies
    sla_policies_data = [
        {"name": "Urgent", "priority": "urgent", "response_hours": 1, "resolution_hours": 4, "active": True},
        {"name": "High", "priority": "high", "response_hours": 4, "resolution_hours": 12, "active": True},
        {"name": "Medium", "priority": "medium", "response_hours": 8, "resolution_hours": 24, "active": True},
        {"name": "Low", "priority": "low", "response_hours": 24, "resolution_hours": 72, "active": True}
    ]
    for data in sla_policies_data:
        db.add(SLAPolicy(**data))
    db.commit()

    # 2. Tickets
    # We need to assign user_id. Since we don't have a user, we'll use a placeholder or dummy ID.
    # The prompt says "user_id: str — who created this ticket (from auth)".
    # Let's use "seed_user" for now.
    tickets_data = [
        {"subject": "Cannot login to my account", "description": "I keep getting 'invalid credentials' error even after resetting my password twice. Browser is Chrome 120.", "status": "open", "priority": "high", "category": "account", "assigned_to": "Support Team", "customer_email": "sarah@example.com", "customer_name": "Sarah Chen"},
        {"subject": "Billing charged twice this month", "description": "My credit card was charged $29 on Feb 1 and again on Feb 3. Please refund the duplicate charge.", "status": "in_progress", "priority": "urgent", "category": "billing", "assigned_to": "Billing Team", "customer_email": "james@startup.io", "customer_name": "James Wilson"},
        {"subject": "Feature request: dark mode", "description": "Would love to see a dark mode option. Working late at night and the bright UI is hard on the eyes.", "status": "open", "priority": "low", "category": "feature_request", "assigned_to": "Product Team", "customer_email": "alex@design.co", "customer_name": "Alex Rivera"},
        {"subject": "API returns 500 on bulk import", "description": "When importing more than 100 records via POST /api/import, the server returns a 500 error. Works fine with smaller batches.", "status": "in_progress", "priority": "high", "category": "bug", "assigned_to": "Engineering", "customer_email": "dev@techfirm.com", "customer_name": "Mike Zhang"},
        {"subject": "How to set up SSO?", "description": "We just upgraded to the enterprise plan. Can you walk us through setting up SAML SSO with Okta?", "status": "waiting", "priority": "medium", "category": "question", "assigned_to": "Support Team", "customer_email": "it@bigcorp.com", "customer_name": "Lisa Park"},
        {"subject": "Data export not working", "description": "CSV export button does nothing when clicked. No file downloads. Tried Firefox and Chrome.", "status": "open", "priority": "medium", "category": "bug", "assigned_to": "Engineering", "customer_email": "maria@retail.shop", "customer_name": "Maria Gonzalez"},
        {"subject": "Cancel subscription", "description": "Please cancel my subscription effective end of current billing period. Moving to a different solution.", "status": "resolved", "priority": "low", "category": "billing", "assigned_to": "Billing Team", "customer_email": "tom@freelance.me", "customer_name": "Tom Baker"},
        {"subject": "Integration with Slack", "description": "Is there a way to get ticket notifications in our Slack workspace? Would be very useful for our team.", "status": "open", "priority": "low", "category": "feature_request", "assigned_to": "Product Team", "customer_email": "nina@agency.pro", "customer_name": "Nina Patel"},
        {"subject": "Page loads very slowly", "description": "Dashboard takes 15+ seconds to load. Started happening two days ago. Our internet is fine — other sites load fast.", "status": "in_progress", "priority": "high", "category": "bug", "assigned_to": "Engineering", "customer_email": "ops@logistics.co", "customer_name": "David Kim"},
        {"subject": "Need invoice for tax purposes", "description": "Can you send me invoices for the last 6 months? Need them for our annual tax filing. Company name: GreenTech Solutions.", "status": "resolved", "priority": "medium", "category": "billing", "assigned_to": "Billing Team", "customer_email": "accounting@greentech.eco", "customer_name": "Rachel Adams"}
    ]
    
    created_tickets = []
    for i, data in enumerate(tickets_data):
        # Calculate SLA due based on priority
        # Simplified lookup for seeding
        resolution_hours = 24 # default
        if data['priority'] == 'urgent': resolution_hours = 4
        elif data['priority'] == 'high': resolution_hours = 12
        elif data['priority'] == 'medium': resolution_hours = 24
        elif data['priority'] == 'low': resolution_hours = 72
        
        sla_due = datetime.utcnow() + timedelta(hours=resolution_hours)
        if data['status'] in ['resolved', 'closed']:
            sla_due = datetime.utcnow() - timedelta(hours=1) # Past due/met
            
        ticket = Ticket(user_id="seed_user", sla_due=sla_due, **data)
        if data['status'] == 'resolved':
            ticket.resolved_at = datetime.utcnow()
            
        db.add(ticket)
        created_tickets.append(ticket)
        
    db.commit()
    # Refresh to get IDs
    for t in created_tickets:
        db.refresh(t)
        
    # Map original index (1-based) to actual ID
    ticket_map = {i+1: t.id for i, t in enumerate(created_tickets)}

    # 3. Ticket Replies
    ticket_replies_data = [
        {"ticket_id": 1, "author": "Support Team", "content": "Hi Sarah, sorry to hear about the login issues. Can you try clearing your browser cache and cookies? Also, are you using the correct email address for your account?", "is_internal": False},
        {"ticket_id": 1, "author": "Support Team", "content": "Internal: Checked auth logs — seeing repeated failed attempts from different IP. Possible rate limiting issue.", "is_internal": True},
        {"ticket_id": 2, "author": "Billing Team", "content": "Hi James, I can see the duplicate charge. Processing a refund now — should appear in 3-5 business days.", "is_internal": False},
        {"ticket_id": 2, "author": "Billing Team", "content": "Refund of $29 processed via Stripe. Refund ID: re_1abc123.", "is_internal": True},
        {"ticket_id": 4, "author": "Engineering", "content": "Hi Mike, we've identified the issue — the bulk import endpoint has a 100-record batch size limit that wasn't documented. We're increasing it to 1000. Fix will be in next release.", "is_internal": False},
        {"ticket_id": 5, "author": "Support Team", "content": "Hi Lisa, here's our SSO setup guide: [link]. You'll need your Okta metadata URL and entity ID. Let me know once you have those and I'll walk you through the remaining steps.", "is_internal": False},
        {"ticket_id": 5, "author": "Lisa Park", "content": "Thanks! I have the metadata URL but I'm not sure where to find the entity ID in Okta. Can you point me in the right direction?", "is_internal": False},
        {"ticket_id": 7, "author": "Billing Team", "content": "Hi Tom, your subscription has been set to cancel at end of billing period (Feb 28). You'll retain access until then. Sorry to see you go!", "is_internal": False},
        {"ticket_id": 9, "author": "Engineering", "content": "Hi David, we identified a slow database query on the dashboard. Deploying a fix now — should resolve within the hour.", "is_internal": False},
        {"ticket_id": 10, "author": "Billing Team", "content": "Hi Rachel, I've emailed the last 6 invoices to your address. Company name updated to GreenTech Solutions on all of them.", "is_internal": False}
    ]
    
    for data in ticket_replies_data:
        original_id = data.pop('ticket_id')
        if original_id in ticket_map:
            reply = TicketReply(ticket_id=ticket_map[original_id], **data)
            db.add(reply)
            
    # 4. Knowledge Articles
    knowledge_articles_data = [
        {"title": "Getting Started with Your Account", "content": "Welcome! Here's everything you need to know to get up and running.\n\n## Creating Your Account\nSign up using your email address. You'll receive a magic link to verify your account.\n\n## Setting Up Your Profile\nOnce logged in, click your avatar in the top right to set your name and preferences.\n\n## Creating Your First Ticket\nClick 'New Ticket' from the dashboard. Fill in the subject, description, and select a priority level.", "category": "getting_started", "tags": "setup,account,onboarding", "published": True, "views": 234, "helpful_votes": 45},
        {"title": "Troubleshooting Login Issues", "content": "Having trouble logging in? Try these steps:\n\n## Clear Browser Cache\nGo to Settings → Clear Browsing Data → Select Cookies and Cache → Clear.\n\n## Check Your Email\nMake sure you're using the email address you registered with.\n\n## Magic Link Expiry\nMagic links expire after 15 minutes. Request a new one if yours has expired.\n\n## Still Stuck?\nContact support with your email address and browser version.", "category": "troubleshooting", "tags": "login,password,auth", "published": True, "views": 567, "helpful_votes": 89},
        {"title": "Understanding Your Bill", "content": "Here's how billing works:\n\n## Plans\n- **Free**: Basic features, up to 50 tickets/month\n- **Premium ($29/mo)**: Unlimited tickets, AI assistance, SLA tracking\n\n## Payment Methods\nWe accept all major credit cards via Stripe.\n\n## Invoices\nInvoices are automatically generated and emailed on each billing date.", "category": "billing", "tags": "pricing,payment,invoice", "published": True, "views": 189, "helpful_votes": 32},
        {"title": "Using the API", "content": "Our REST API lets you integrate tickets into your workflow.\n\n## Authentication\nAll API requests require a Bearer token in the Authorization header.\n\n## Endpoints\n- GET /api/tickets — List all tickets\n- POST /api/tickets — Create a ticket\n- GET /api/tickets/{id} — Get ticket details\n- POST /api/tickets/{id}/reply — Add a reply\n\n## Rate Limits\n100 requests per minute per API key.", "category": "api", "tags": "api,integration,developer", "published": True, "views": 312, "helpful_votes": 67}
    ]
    for data in knowledge_articles_data:
        db.add(KnowledgeArticle(**data))
        
    # 5. AI Responses
    ai_responses_data = [
        {"ticket_id": 1, "suggestion_type": "reply_draft", "content": "Hi Sarah, I understand how frustrating login issues can be. Based on the error you're seeing, here are a few things to try: 1) Clear your browser cache and cookies, 2) Try an incognito/private window, 3) Ensure caps lock is off. If none of these work, I can manually reset your account credentials. Would you like me to do that?", "model_used": "seed_data", "accepted": False},
        {"ticket_id": 4, "suggestion_type": "categorization", "content": "Suggested category: BUG (confidence: 95%). Suggested priority: HIGH. Reasoning: Customer reports a server error (500) on a specific endpoint with reproducible steps. This is a functional regression that affects data import workflows.", "model_used": "seed_data", "accepted": True}
    ]
    
    for data in ai_responses_data:
        original_id = data.pop('ticket_id')
        if original_id in ticket_map:
            resp = AIResponse(ticket_id=ticket_map[original_id], **data)
            db.add(resp)
            
    db.commit()
