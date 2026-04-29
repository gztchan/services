from .config import Settings
from .setup import K8sSetup
from .job import K8sJobManager
from kubernetes import client, config

class K8sManager(K8sSetup, K8sJobManager):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._apps: client.AppsV1Api | None = None
        self._core: client.CoreV1Api | None = None

    def configure(self) -> None:
        if self.settings.in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self._apps = client.AppsV1Api()
        self._core = client.CoreV1Api()

    def _api(self) -> client.AppsV1Api:
        if self._apps is None:
            raise RuntimeError("K8s 客户端尚未初始化，请在 lifespan 中调用 configure()")
        return self._apps

    def _core_api(self) -> client.CoreV1Api:
        if self._core is None:
            raise RuntimeError("K8s 客户端尚未初始化，请在 lifespan 中调用 configure()")
        return self._core

__all__ = ["K8sManager", "Settings"]
