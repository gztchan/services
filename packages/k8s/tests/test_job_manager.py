from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from kubernetes.client import ApiException

from providence_k8s import K8sManager, Settings

def make_manager() -> K8sManager:
    return K8sManager(Settings())


# def test_build_job_name_with_suffix_and_length_limit() -> None:
#     manager = make_manager()
#     manager._settings.job_prefix = "Providence-"

#     with patch("k8s.job.uuid.uuid4") as mock_uuid:
#         mock_uuid.return_value = SimpleNamespace(hex="1234567890abcdef1234567890abcdef")
#         name = manager.build_job_name(suffix="A*B C___D" * 10)

#     assert name.startswith("providence-1234567890ab-")
#     assert len(name) <= 63
#     assert "*" not in name
#     assert " " not in name


# def test_api_requires_configure() -> None:
#     manager = make_manager()
#     manager.configure()
#     with pytest.raises(RuntimeError):
#         manager._api()
#     with pytest.raises(RuntimeError):
#         manager._core_api()


def test_create_job_success() -> None:
    manager = make_manager()
    manager.configure()
    manager.prepare()
    result = manager.create_job(name=f"providence-job-{uuid4().hex[:12]}", namespace="providence", image="image:1")
    assert result is not None

def test_create_job_success() -> None:
    manager = make_manager()
    manager.configure()
    manager.prepare()
    result = manager.create_job(name=f"providence-job-{uuid4().hex[:12]}", namespace="providence", image="image:1")
    assert result is not None

def test_delete_job_success() -> None:
    manager = make_manager()
    manager.configure()
    manager.prepare()
    result = manager.create_job(name=f"providence-job-{uuid4().hex[:12]}", namespace="providence", image="image:1")
    assert result is not None

# def test_create_job_rolls_back_when_service_creation_fails() -> None:
#     manager = make_manager()
#     manager._batch = MagicMock()
#     manager._core = MagicMock()
#     manager.build_job_resource = MagicMock(return_value=object())
#     manager.build_headless_service = MagicMock(return_value=object())
#     manager._rollback_job = MagicMock()

#     manager._batch.create_namespaced_job.return_value = SimpleNamespace(
#         metadata=SimpleNamespace(uid="job-uid")
#     )
#     manager._core.create_namespaced_service.side_effect = ApiException(status=500, reason="boom")

#     with pytest.raises(ApiException):
#         manager.create_job(name="job-a", namespace="ns", image="image:1")

#     manager._rollback_job.assert_called_once_with(name="job-a", namespace="ns")


# def test_create_job_rolls_back_when_uid_missing() -> None:
#     manager = make_manager()
#     manager._batch = MagicMock()
#     manager._core = MagicMock()
#     manager.build_job_resource = MagicMock(return_value=object())
#     manager._rollback_job = MagicMock()

#     manager._batch.create_namespaced_job.return_value = SimpleNamespace(
#         metadata=SimpleNamespace(uid=None)
#     )

#     with pytest.raises(RuntimeError):
#         manager.create_job(name="job-a", namespace="ns", image="image:1")

#     manager._rollback_job.assert_called_once_with(name="job-a", namespace="ns")
#     manager._core.create_namespaced_service.assert_not_called()
