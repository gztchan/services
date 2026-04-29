from uuid import UUID
from faker import Faker
from datetime import datetime
from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session, selectinload, noload

from providence_database import Browser, with_deleted_filter

class BrowserDataService:
    def list_browsers(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> tuple[list[Browser], int]:
        total_stmt = with_deleted_filter(
            select(func.count()).select_from(Browser),
            Browser,
            include_deleted,
        )
        total = session.scalar(total_stmt)
        rows = session.scalars(
            with_deleted_filter(
                select(Browser)
                .options(
                    selectinload(Browser.profile),
                    selectinload(Browser.browser_job),
                )
                .order_by(Browser.created_at.desc())
                .offset(offset)
                .limit(limit),
                Browser,
                include_deleted,
            )
        )
        return list(rows), int(total or 0)


    def get_browser_by_id(
        self,
        session: Session,
        browser_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Browser | None:
        rows = session.scalars(
            with_deleted_filter(
                select(Browser)
                .options(
                    selectinload(Browser.profile),
                    selectinload(Browser.browser_job),
                )
                .where(Browser.id == browser_id),
                Browser,
                include_deleted,
            )
        )
        return rows.one_or_none()

    def get_browser_by_profile_id(
        self,
        session: Session,
        profile_id: str,
    ):
        rows = session.scalars(
            with_deleted_filter(
                select(Browser)
                .options(
                    selectinload(Browser.profile),
                    selectinload(Browser.browser_job),
                )
                .where(Browser.profile_id == profile_id),
                Browser,
                include_deleted=False,
            )
        )
        return rows.one_or_none()

    def create_browser(
        self,
        session: Session,
        profile_id: str,
        name: str | None = None,
        description: str | None = None,
    ):
        browser = Browser(
            profile_id=profile_id,
            name=Faker().name() if name is None else name,
            description=description,
        )
        session.add(browser)
        return browser

    def update_browser(
        self,
        session: Session,
        browser_id: str,
        name: str | None = None,
        description: str | None = None,
        browser_job_id: UUID | None = None,
        include_profile: bool = False,
        include_browser_job: bool = False,
    ): 
        options = []
        if include_profile:
            options.append(selectinload(Browser.profile))
        
        if include_browser_job:
            options.append(selectinload(Browser.browser_job))
        
        browser = session.scalars(
            with_deleted_filter(
                select(Browser)
                .options(*options)
                .where(Browser.id == browser_id),
                Browser,
                include_deleted=False,
            )
        ).one_or_none()
        if browser is None:
            return None
        browser.name = browser.name if name is None else name
        browser.description = browser.description if description is None else description
        browser.browser_job_id = browser_job_id if browser_job_id is not None else browser.browser_job_id
        browser.updated_at = datetime.now()
        return browser
    
    def disconnect_browser_job(
        self,
        session: Session,
        browser_id: str,
    ):
        browser = self.get_browser_by_id(session, browser_id)
        if browser is not None:
            browser.browser_job = None

    def delete_browser(
        self,
        session: Session,
        browser_id: str,
    ):
        conditions = [
            Browser.id == browser_id,
            Browser.deleted_at is not None,
        ]
        browser = session.query(Browser).filter(and_(*conditions)).first()
        if browser is not None:
            session.delete(browser)
