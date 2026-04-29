from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime
from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session, selectinload, noload

from providence_database import Profile, Browser, BrowserJob, with_deleted_filter


class ProfileDataService:
    def list_profiles(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> tuple[list[Profile], int]:
        total_stmt = with_deleted_filter(
            select(func.count()).select_from(Profile),
            Profile,
            include_deleted,
        )
        total = session.scalar(total_stmt)
        rows = session.scalars(
            with_deleted_filter(
                select(Profile)
                .order_by(Profile.created_at.desc())
                .offset(offset)
                .limit(limit),
                Profile,
                include_deleted,
            )
        )
        return list(rows), int(total or 0)


    def get_profile_by_id(
        self,
        session: Session,
        profile_id: str,
        *,
        include_deleted: bool = False,
        include_browser: bool = False,
    ) -> Profile | None:
        if include_browser:
            options = [
                selectinload(Profile.browser)
                .options(
                    noload(Browser.browser_job),
                    noload(Browser.profile)
                )
            ]
        else:
            options = []
        rows = session.scalars(
            with_deleted_filter(
                select(Profile)
                .options(*options)
                .where(Profile.id == profile_id),
                Profile,
                include_deleted,
            )
        )
        return rows.one_or_none()

    def create_profile(
        self,
        session: Session,
        name: str,
        description: str | None = None,
    ) -> Profile:
        profile = Profile(
            id=uuid4(),
            name=name,
            description=description,
            meta={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(profile)
        return profile

    def update_profile(
        self,
        session: Session,
        profile_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Profile:
        profile = session.scalars(
            with_deleted_filter(
                select(Profile)
                .options(
                    noload(Profile.browser)
                    # .options(noload(Browser.browser_job), noload(Browser.profile))
                )
                .where(Profile.id == profile_id),
                Profile,
                include_deleted=False,
            )
        ).one_or_none()
        if profile is None:
            return None
        profile.name = profile.name if name is None else name
        profile.description = profile.description if description is None else description
        profile.updated_at = datetime.now()
        return profile

    def delete_profile(
        self,
        session: Session,
        profile_id: str,
    ) -> None:
        conditions = [
            Profile.id == profile_id,
            Profile.deleted_at is not None,
        ]
        profile = session.query(Profile).filter(and_(*conditions)).first()
        if profile is None:
            return
        session.delete(profile)

    def disconnect_browser(
        self,
        session: Session,
        profile_id: str,
    ) -> None:
        conditions = [
            Profile.id == profile_id,
            Profile.deleted_at.is_(None),
        ]
        session.query(Profile).filter(and_(*conditions)).update({ Profile.browser: None })