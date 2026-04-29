from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from providence_database import BrowserJob, with_deleted_filter

logger = logging.getLogger(__name__)


class BrowserJobCreateParams(BaseModel):
    job_name: str | None = None
    namespace: str
    k8s_uid: str | None = None

def _apply_job_summary(
    row: BrowserJob,
    *,
    status: str,
    uid: str | None,
    message: str | None,
) -> None:
    row.status = status
    if uid:
        row.k8s_uid = uid
    row.k8s_message = message


def _commit_and_refresh(session: Session, row: BrowserJob) -> BrowserJob:
    session.commit()
    session.refresh(row)
    return row


def _mark_job_failed(
    session: Session,
    row: BrowserJob,
    *,
    message: str,
    error: Exception,
    log_with_traceback: bool = False,
) -> None:
    row.status = "failed"
    row.k8s_message = message[:4000]
    session.commit()
    if log_with_traceback:
        logger.exception("创建 K8s Job 失败")
    else:
        status = getattr(error, "status", "unknown")
        reason = getattr(error, "reason", str(error))
        logger.warning("创建 K8s Job 失败: %s %s", status, reason)


class BrowserJobService:
    def create_browser_job(
        self,
        session: Session,
        *,
        params: BrowserJobCreateParams,
    ) -> BrowserJob:
        row = BrowserJob(
            id=uuid4(),
            status="pending",
            meta={
                **params.model_dump(),
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(row)
        return row

    def update_browser_job(
        self,
        session: Session,
        *,
        browser_job_id: str,
        status: str,
    ):
        row = session.scalars(
            with_deleted_filter(
                select(BrowserJob).where(
                    BrowserJob.id == browser_job_id,
                ),
                BrowserJob,
                include_deleted=False,
            )
        ).one_or_none()
        if row is None:
            return None
        row.status = status
        row.updated_at = datetime.now()
        return row

    # def refresh_record_from_cluster(
    #     self,
    #     session: Session,
    #     k8s: K8sJobManager,
    #     row: BrowserJob,
    # ) -> None:
    #     job = k8s.read_job(name=row.job_name, namespace=row.namespace)
    #     status, uid, message = K8sJobManager.summarize(job)
    #     _apply_job_summary(row, status=status, uid=uid, message=message)
    #     _commit_and_refresh(session, row)

    # def sync_browser_job(self, session: Session, k8s: K8sJobManager) -> int:
    #     """刷新仍处于进行中的 Job 状态，返回更新条数。"""

    #     res = session.scalars(
    #         select(BrowserJob).where(
    #             BrowserJob.status.in_(("pending", "running", "unknown"))
    #         )
    #     )
    #     rows = list(res)
    #     for row in rows:
    #         try:
    #             self.refresh_record_from_cluster(session, k8s, row)
    #         except Exception:
    #             logger.exception("同步 Job 状态失败 id=%s", row.id)
    #     return len(rows)


# def sync_open_jobs(session: Session, k8s: K8sJobManager) -> int:
#     return BrowserJobService().sync_open_jobs(session, k8s)
