from __future__ import annotations

import logging
import uuid

from kubernetes import client, config
from kubernetes.client import ApiException

from ..config import Settings

from .resource import JobResource

logger = logging.getLogger(__name__)

PROVISION_JOB_NAME = "providence-browser"

# def _job_status_from_v1(deployment: client.V1Deployment) -> tuple[str, str | None]:
#     """根据 Job.status 推导业务状态与说明。"""
#     st = job.status
#     if st is None:
#         return "pending", None

#     conditions = st.conditions or []
#     for c in conditions:
#         if c.type == "Failed" and c.status == "True":
#             return "failed", c.message or c.reason
#         if c.type == "Complete" and c.status == "True":
#             return "succeeded", c.message

#     active = st.active or 0
#     succeeded = st.succeeded or 0
#     failed = st.failed or 0

#     if succeeded > 0:
#         return "succeeded", None
#     if failed > 0:
#         return "failed", None
#     if active > 0:
#         return "running", None
#     return "pending", None

class K8sJobManager(JobResource):
    @staticmethod
    def create_unique_job_name() -> str:
        return PROVISION_JOB_NAME + "-" + uuid.uuid4().hex[:12]

    def _rollback_job(self, *, name: str) -> None:
        try:
            self.delete_job(name=name, namespace=self.settings.namespace)
        except ApiException:
            logger.exception("回滚 Deployment 失败")

    def create_job(self, profile_id: str, env: dict[str, str]) -> client.V1Deployment:
        name = K8sJobManager.create_unique_job_name()
        deployment_body = self.build_deployment_resource(name=name, image=self.settings.job_image, profile_id=profile_id, env=env)
        apps_api = self._api()
        core_api = self._core_api()
        try:
            created = apps_api.create_namespaced_deployment(self.settings.namespace, deployment_body)
        except ApiException as error:
            print(error)
            logger.warning("创建 Deployment 失败: %s %s", error.status, error.reason)
            raise

        dep_uid = created.metadata.uid if created.metadata else None
        if not dep_uid:
            logger.error("创建 Deployment 成功但缺少 metadata.uid，回滚 Deployment")
            self._rollback_job(name=name)
            raise RuntimeError("Deployment 创建响应缺少 uid，无法为 Service 设置 ownerReferences")

        svc = self.build_clusterip_service(deployment=created)
        try:
            core_api.create_namespaced_service(self.settings.namespace, svc)
        except ApiException as error:
            print(error)
            logger.warning(
                "创建 ClusterIP Service 失败，回滚 Deployment: %s %s",
                error.status,
                error.reason,
            )
            self._rollback_job(name=name)
            raise

        return created

    def read_job(self, *, name: str) -> client.V1Deployment | None:
        try:
            return self._api().read_namespaced_deployment(name, self.settings.namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def delete_job(self, *, name: str, namespace: str) -> bool:
        self._api().delete_namespaced_deployment(
            name,
            namespace,
            propagation_policy="Background",
        )

    # @staticmethod
    # def summarize(deployment: client.V1Deployment | None) -> tuple[str, str | None, str | None]:
    #     if job is None:
    #         return "stopped", None, "集群中已无对应 Job（可能已删除）"
    #     uid = job.metadata.uid if job.metadata else None
    #     status, msg = _job_status_from_v1(job)
    #     return status, uid, msg
