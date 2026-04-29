# import importlib
# import os


# def test_settings_defaults() -> None:
#     from k8s.config import Settings

#     settings = Settings()
#     assert settings.k8s_namespace == "providence"
#     assert settings.job_image == "providence:latest"
#     assert settings.job_prefix == "providence-"


# def test_settings_in_cluster_reads_env() -> None:
#     old_value = os.environ.get("IN_CLUSTER")
#     os.environ["IN_CLUSTER"] = "true"
#     try:
#         import k8s.config as config_module

#         config_module = importlib.reload(config_module)
#         assert config_module.Settings().in_cluster is True
#     finally:
#         if old_value is None:
#             os.environ.pop("IN_CLUSTER", None)
#         else:
#             os.environ["IN_CLUSTER"] = old_value
#         import k8s.config as config_module

#         importlib.reload(config_module)
