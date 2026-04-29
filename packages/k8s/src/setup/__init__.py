from kubernetes import client

from logging import getLogger

logger = getLogger(__name__)

class K8sSetup:
    def prepare(self) -> None:
        logger.debug("Preparing Kubernetes setup")
        self.prepare_namespace()
        self.prepare_pvc()

    def prepare_namespace(self) -> None:
        ns = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=self.settings.namespace)
        )
        
        try:
            self._core_api().create_namespace(body=ns)
        except client.exceptions.ApiException as e:
            if e.status == 409: logger.debug(f"Namespace '{self.settings.namespace}' already exists")
            else: raise

    def prepare_pvc(self) -> None:
        pvc_name = self.settings.pvc_name
        namespace = self.settings.namespace
        pvc = client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name=pvc_name),
            spec=client.V1PersistentVolumeClaimSpec(
                # 关键：指定使用 local-path 存储类
                storage_class_name="local-path",
                access_modes=["ReadWriteOnce"],
                resources=client.V1ResourceRequirements(
                    requests={"storage": "10Gi"}
                )
            )
        )
        
        try:
            self._core_api().create_namespaced_persistent_volume_claim(namespace, pvc)
        except client.exceptions.ApiException as e:
            if e.status == 409: logger.debug(f"PVC {pvc_name} already exists")
            else: raise

