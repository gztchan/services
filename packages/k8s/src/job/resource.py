from __future__ import annotations

from kubernetes import client

PROFILES_VOLUME_NAME = "profiles"
DEFAULT_PROFILES_PVC_DIR = "profiles"


class JobResource:
    @staticmethod
    def browser_labels() -> dict[str, str]:
        return {
            "app.kubernetes.io/name": "providence",
            # "app.kubernetes.io/managed-by": "providence-manager",
        }

    def build_clusterip_service(self, *, deployment: client.V1Deployment) -> client.V1Service:
        name = deployment.metadata.name if deployment.metadata else ""
        uid = deployment.metadata.uid if deployment.metadata else None
        return client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=name,
                labels=JobResource.browser_labels(),
                owner_references=[
                    client.V1OwnerReference(
                        api_version="apps/v1",
                        kind="Deployment",
                        name=name,
                        uid=uid,
                        controller=True,
                        block_owner_deletion=True,
                    )
                ]
                if uid
                else None,
            ),
            spec=client.V1ServiceSpec(
                type="ClusterIP",
                selector={"job-name": name},
                ports=[
                    client.V1ServicePort(
                        name="http",
                        port=8002,
                        target_port=8002,
                        protocol="TCP",
                        # node_port=31009,
                    ),
                    client.V1ServicePort(
                        name="vnc",
                        port=6080,
                        target_port=6080,
                        protocol="TCP",
                        # node_port=31010,
                    ),
                ],
            ),
        )

    def build_deployment_resource(self, *, name: str, image: str, profile_id: str, env: dict[str, str]) -> client.V1Deployment:
        labels = {"job-name": name}
        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=name,
                labels={**JobResource.browser_labels(), **labels},
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels=labels),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                env=[client.V1EnvVar(name=key, value=value) for key, value in env.items()],
                                name="providence",
                                image=image,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    client.V1ContainerPort(name="http", container_port=8000, protocol="TCP"),
                                    client.V1ContainerPort(name="vnc", container_port=6080, protocol="TCP"),
                                ],
                                volume_mounts=[
                                    client.V1VolumeMount(
                                        name=PROFILES_VOLUME_NAME,
                                        mount_path=f"/data/{profile_id}",
                                        sub_path=f"{DEFAULT_PROFILES_PVC_DIR}/{profile_id}",
                                    )
                                ],
                            )
                        ],
                        volumes=[
                            client.V1Volume(
                                name=PROFILES_VOLUME_NAME,
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                    claim_name=self.settings.pvc_name
                                ),
                            )
                        ],
                    ),
                ),
            ),
        )
