from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from main.core.templating import templates
from main.utils.security import get_current_user
from typing import Dict, Any

page_router = APIRouter(dependencies=[Depends(get_current_user)])


@page_router.get("/vinfiniti", response_class=HTMLResponse, name="vinfiniti_page")
async def get_vinfiniti_page(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Vinfiniti 링크 페이지 렌더링"""
    vinfiniti_links = [
        {
            "title": "LENOVO Vinfiniti",
            "url": "https://lev.vinfiniti.biz:8231/",
            "department": "LENOVO",
        },
        {
            "title": "HES(EMC) Vinfiniti",
            "url": "https://emc.vinfiniti.biz/",
            "department": "HES",
        },
        {
            "title": "CS Vinfiniti",
            "url": "https://cs.vinfiniti.biz:8227/",
            "department": "CS",
        },
    ]
    context = {
        "request": request,
        "current_user": current_user,
        "vinfiniti_links": vinfiniti_links,
    }
    return templates.TemplateResponse("vinfiniti.html", context)
