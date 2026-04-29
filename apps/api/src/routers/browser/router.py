from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response, Path
from kubernetes.client import ApiException
from sqlalchemy.orm import Session
from typing import Callable
from providence_data import BrowserDataService, BrowserJobService, BrowserJobCreateParams
from providence_database import BrowserSchema
from providence_k8s import K8sManager
from uuid import uuid4
from os import getenv

from src.deps import get_k8s_manager, get_session_factory

from .common import delete_browser_job

router = APIRouter(prefix="/v1", tags=["browsers"])

@router.get("/browsers")
def list_browsers(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    browser_data_service = BrowserDataService()
    session = session_factory()
    items, total = browser_data_service.list_browsers(
        session,
        limit=limit,
        offset=offset,
    )
    session.close()
    return {
        "items": [BrowserSchema.model_validate(item).model_dump() for item in items],
        "total": total,
    }


@router.get("/browsers/{browser_id}", response_model=BrowserSchema)
def get_browser(
    browser_id: str = Path(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    browser_data_service = BrowserDataService()
    browser = browser_data_service.get_browser_by_id(
        session,
        browser_id,
    )
    if browser is None:
        session.close()
        raise HTTPException(status_code=404, detail="Browser not found")
    session.close()
    return BrowserSchema.model_validate(browser).model_dump()


@router.post("/browsers")
def create_browser(
    profile_id: str = Body(...),
    name: str | None = Body(default=None),
    description: str | None = Body(default=None),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    browser_data_service = BrowserDataService()
    session = session_factory()
    try:
        browser = browser_data_service.get_browser_by_profile_id(
            session,
            profile_id,
        )
        if browser is not None:
            raise HTTPException(status_code=400, detail=f"Profile {profile_id} already has a browser")

        browser = browser_data_service.create_browser(
            session,
            profile_id=profile_id,
            name=name,
            description=description,
        )
        session.commit()
        return BrowserSchema.model_validate(browser).model_dump()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to create browser: {str(e)}")
    finally:
        session.rollback()
        session.close()

@router.patch("/browsers/{browser_id}")
def update_browser(
    browser_id: str = Path(...),
    name: str | None = Body(default=None),
    description: str | None = Body(default=None),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    browser_data_service = BrowserDataService()
    session = session_factory()
    try:
        browser = browser_data_service.update_browser(
            session,
            browser_id=browser_id,
            name=name,
            description=description,
            include_profile=True,
            include_browser_job=True,
        )
        if browser is None:
            raise HTTPException(status_code=404, detail="Browser not found")
        session.commit()
        return BrowserSchema.model_validate(browser).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update browser: {str(e)}")
    finally:
        session.rollback()
        session.close()

@router.post("/browsers/{browser_id}/launch")
def launch_browser(
    browser_id: str = Path(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    k8s_manager: K8sManager = Depends(get_k8s_manager),
):
    session = session_factory()
    browser_data_service = BrowserDataService()
    browser_job_service = BrowserJobService()

    browser = browser_data_service.get_browser_by_id(
            session,
            browser_id,
        )
    if browser is None:
        raise HTTPException(status_code=404, detail="Browser not found")

    if browser.browser_job is not None:
        raise HTTPException(status_code=400, detail="Browser already has a job")

    try:
        browser_job = browser_job_service.create_browser_job(
            session,
            params=BrowserJobCreateParams(
                job_name=None,
                namespace=k8s_manager.settings.namespace,
                k8s_uid=None,
            ),
        )

        job = k8s_manager.create_job(profile_id=str(browser.profile_id), env={
            "USER_DATA_DIR": str(browser.profile_id),
            "BROWSER_ID": browser_id,
            "JOB_ID": str(browser_job.id),
            "WEBHOOK_URL": getenv("WEBHOOK_URL"),
        })
        job_name = job.metadata.name if job.metadata else None
        job_uid = job.metadata.uid if job.metadata else None

        browser_job.meta["job_name"] = job_name
        browser_job.meta["namespace"] = k8s_manager.settings.namespace
        browser_job.meta["k8s_uid"] = job_uid

        browser = browser_data_service.update_browser(
            session,
            str(browser.id),
            browser_job_id=browser_job.id,
        )

        session.commit()
        session.refresh(browser)
        session.close()
        return BrowserSchema.model_validate(browser).model_dump()
    except Exception as e:
        print(e)
        try:
            k8s_manager.delete_job(name=job_name, namespace=k8s_manager.settings.namespace)
        except Exception as e:
            print(e)
            pass
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to launch browser: {str(e)}")
    finally:
        session.close()


@router.post("/browsers/{browser_id}/halt")
def stop_browser(
    browser_id: str = Path(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    k8s_manager: K8sManager = Depends(get_k8s_manager),
):
    session = session_factory()
    browser_data_service = BrowserDataService()

    browser = browser_data_service.get_browser_by_id(session, browser_id)
    if browser is None:
        session.close()
        raise HTTPException(status_code=404, detail="Browser not found")

    try:
        delete_browser_job(session=session, browser=browser, k8s_manager=k8s_manager)
        session.commit()
        session.refresh(browser)
        return BrowserSchema.model_validate(browser).model_dump()
    except Exception as e:
        print(e)
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to stop browser: {str(e)}")
    finally:
        session.close()

@router.delete("/browsers/{browser_id}", status_code=200)
def delete_browser(
    browser_id: str = Path(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    k8s_manager: K8sManager = Depends(get_k8s_manager),
):
    session = session_factory()
    browser_data_service = BrowserDataService()

    browser = browser_data_service.get_browser_by_id(session, browser_id)
    if browser is None:
        raise HTTPException(status_code=404, detail="Browser not found")

    try:
        delete_browser_job(session=session, browser=browser, k8s_manager=k8s_manager)

        browser_data_service.delete_browser(session, str(browser.id))
        session.commit()
        return Response(status_code=200)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete browser: {str(e)}")
    finally:
        session.close()
