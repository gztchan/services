from contextlib import asynccontextmanager
from os import getenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from providence_database import make_engine, make_session_factory
from providence_k8s import K8sManager, Settings as K8sSettings
import uvicorn
import logging

from .routers import browser_router, profile_router
from .webhooks import router as webhooks_router

logging.basicConfig(level=logging.INFO)

k8s_settings = K8sSettings()
k8s_manager = K8sManager(k8s_settings)
k8s_manager.configure()
k8s_manager.prepare()

class Settings:
    host: str = "0.0.0.0"
    port: int = int(getenv("PORT", 8000))
    cors_allow_origins: str = "*"
    database_url: str = getenv("DATABASE_URL", None)

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.k8s_manager = k8s_manager
    # app.state.telemetry

    yield

    # def sync_loop() -> None:
    #     while True:
    #         time.sleep(settings.sync_interval_seconds)
    #         with session_factory() as session:
    #             try:
    #                 sync_open_jobs(session, k8s)
    #             except Exception:
    #                 logger.exception("后台同步 Job 状态失败")

    # task = threading.Thread(target=sync_loop)
    # try:
    #     yield
    # finally:
    #     task.join()
    #     engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(title="Providence", lifespan=lifespan, root_path="/api")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(browser_router)
    app.include_router(profile_router)
    app.include_router(webhooks_router)
    return app

app = create_app()

def main() -> None:
    uvicorn.run(app, host=settings.host, port=settings.port)

if __name__ == "__main__":
    main()
