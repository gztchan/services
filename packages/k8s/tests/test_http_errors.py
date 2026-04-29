# from kubernetes.client import ApiException

# from k8s.http_errors import kubernetes_bad_gateway


# def test_kubernetes_bad_gateway_uses_error_body_first() -> None:
#     error = ApiException(status=500, reason="Internal")
#     error.body = "upstream body"

#     response = kubernetes_bad_gateway(error)

#     assert response.status_code == 502
#     assert response.detail == "upstream body"


# def test_kubernetes_bad_gateway_truncates_long_message() -> None:
#     error = ApiException(status=500, reason="R" * 9000)

#     response = kubernetes_bad_gateway(error)

#     assert response.status_code == 502
#     assert len(response.detail) == 8000
