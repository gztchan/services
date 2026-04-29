from providence_data import BrowserDataService
from providence_database import Browser
from providence_k8s import K8sManager
from sqlalchemy.orm import Session

def delete_browser_job(
    *,
    session: Session,
    browser: Browser,
    k8s_manager: K8sManager,
):
    browser_data_service = BrowserDataService()
    browser_job = browser.browser_job
    if browser_job is None:
        return
    job_name = browser_job.meta.get("job_name")
    namespace = browser_job.meta.get("namespace")
    k8s_manager.delete_job(name=job_name, namespace=namespace)
    browser_data_service.disconnect_browser_job(session, str(browser.id))