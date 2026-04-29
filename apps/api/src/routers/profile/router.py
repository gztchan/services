from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, Path, Body, Depends
from sqlalchemy.orm import Session
from typing import Callable
from providence_data import ProfileDataService

from src.deps import get_session_factory
from providence_database import ProfileSchema

router = APIRouter(prefix="/v1", tags=["profiles"])

@router.get("/profiles")
def list_profiles(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: Optional[int] = Query(0, ge=0),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    profile_data_service = ProfileDataService()
    items, total = profile_data_service.list_profiles(
        session,
        limit=limit,
        offset=offset,
    )
    session.close()
    return {
        "items": [ProfileSchema.model_validate(item).model_dump() for item in items],
        "total": total,
    }

@router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: str = Path(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    profile_data = ProfileDataService()
    profile = profile_data.get_profile_by_id(
        session,
        profile_id,
    )
    session.close()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileSchema.model_validate(profile).model_dump()

@router.post("/profiles")
def create_profile(
    name: str = Body(...),
    description: str | None = Body(default=None),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    profile_data = ProfileDataService()
    profile = profile_data.create_profile(
        session,
        name=name,
        description=description,
    )
    session.commit()
    session.close()
    return ProfileSchema.model_validate(profile).model_dump()

@router.patch("/profiles/{profile_id}")
def update_profile(
    profile_id: str = Path(...),
    name: str | None = Body(default=None),
    description: str | None = Body(default=None),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    profile_data_service = ProfileDataService()
    profile = profile_data_service.update_profile(
        session,
        profile_id,
        name=name,
        description=description,
    )
    session.commit()
    session.close()
    return ProfileSchema.model_validate(profile).model_dump()

@router.delete("/profiles/{profile_id}", status_code=200)
def delete_profile(
    profile_id: str = Path(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
):
    session = session_factory()
    profile_data_service = ProfileDataService()
    profile = profile_data_service.get_profile_by_id(
        session,
        profile_id,
        include_browser=True,
    )
    if profile.browser is not None:
        raise HTTPException(status_code=400, detail="Profile has browser associated, cannot be deleted")
    profile_data_service.delete_profile(
        session,
        profile_id,
    )
    session.commit()
    session.close()
    return Response(status_code=200)
