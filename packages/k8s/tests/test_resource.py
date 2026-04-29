# from k8s.job.resource import (
#     PROFILES_PVC_NAME,
#     PROFILES_VOLUME_NAME,
#     JobResource,
# )


# def test_browser_labels() -> None:
#     assert JobResource.browser_labels() == {
#         "app.kubernetes.io/name": "providence",
#         # "app.kubernetes.io/managed-by": "browser-controller",
#     }


# def test_build_headless_service() -> None:
#     resource = JobResource()
#     service = resource.build_headless_service(name="job-a", job_uid="uid-1")

#     assert service.metadata is not None
#     assert service.metadata.name == "job-a"
#     assert service.metadata.owner_references[0].uid == "uid-1"
#     assert service.spec is not None
#     assert service.spec.cluster_ip == "None"
#     assert service.spec.selector == {"job-name": "job-a"}
#     assert service.spec.ports[0].port == 9222


# def test_build_job_resource() -> None:
#     resource = JobResource()
#     job = resource.build_job_resource(name="job-a", image="providence:latest")

#     assert job.metadata is not None
#     assert job.metadata.name == "job-a"
#     assert job.spec is not None
#     assert job.spec.backoff_limit == 0
#     assert job.spec.ttl_seconds_after_finished == 3600
#     assert job.spec.template.spec is not None
#     pod_spec = job.spec.template.spec
#     assert pod_spec.restart_policy == "Never"
#     assert pod_spec.containers[0].image == "providence:latest"
#     assert pod_spec.volumes[0].name == PROFILES_VOLUME_NAME
#     assert pod_spec.volumes[0].persistent_volume_claim.claim_name == PROFILES_PVC_NAME
