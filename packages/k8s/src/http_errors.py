from fastapi import HTTPException
from kubernetes.client import ApiException


def kubernetes_bad_gateway(error: ApiException) -> HTTPException:
    return HTTPException(
        status_code=502,
        detail=(error.body or error.reason or str(error))[:8000],
    )
