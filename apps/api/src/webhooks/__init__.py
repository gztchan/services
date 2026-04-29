from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, Path, Body, Depends
from sqlalchemy.orm import Session
from typing import Callable
from providence_data import BrowserDataService, BrowserJobService
import logging

logger = logging.getLogger("api")

from src.deps import get_session_factory

router = APIRouter(prefix="/v1/webhooks")

@router.post("/browser_job", status_code=200)
def browser_job_webhook(
    status: str = Body(...),
    browser_id: str = Body(...),
    job_id: str = Body(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    browser_data_service = BrowserDataService()
    browser = browser_data_service.get_browser_by_id(session, browser_id)
    session.close()
    if browser is None:
        session.close()
        raise HTTPException(status_code=404, detail="Browser not found")
    browser_job_service = BrowserJobService()

    if status == "running":
        session = session_factory()
        browser_job_service.update_browser_job(session, browser_job_id=job_id, status=status)
        session.commit()
    elif status == "terminated":
        session = session_factory()
        browser_data_service.disconnect_browser_job(session, browser_id=browser_id)
        session.commit()
    session.close()
    return Response(status_code=200)