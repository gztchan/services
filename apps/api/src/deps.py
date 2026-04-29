from fastapi import Request
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from typing import Callable
from providence_k8s import K8sManager

def get_engine(request: Request) -> Engine:
    return request.app.state.engine

def get_session_factory(request: Request) -> Callable[[], Session]:
    return request.app.state.session_factory

def get_k8s_manager(request: Request) -> K8sManager:
    return request.app.state.k8s_manager