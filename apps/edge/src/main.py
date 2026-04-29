import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from providence_database import make_engine, make_session_factory
import logging

logging.basicConfig(level=logging.INFO)

from .proxy import router as proxy_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine(os.getenv("DATABASE_URL"))
    session_factory = make_session_factory(engine)

    app.state.session_factory = session_factory

    yield

app = FastAPI(lifespan=lifespan)
app.include_router(proxy_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    main()
