from fastapi import Request
from sqlalchemy.orm import Session
from typing import Callable

def get_session_factory(request: Request) -> Callable[[], Session]:
    return request.app.state.session_factory