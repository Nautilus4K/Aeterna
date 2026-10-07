"""
Utilities for WSGI application. Like serving sites for instance.
"""
import pathlib
from flask import Response, redirect, render_template_string, send_from_directory, abort
from consts import WEB_ROOT

NAVBAR_SNIPPET = open(WEB_ROOT / "templates" / "navbar.html", "r", encoding='utf-8').read()
ERROR_PATH = WEB_ROOT / "templates" / "error.html"

def serve_basic_site(path: pathlib.Path, return_code: int = 200) -> tuple[Response, int]:
    if path.exists() and path.is_file():
        return Response(render_template_string(
            open(path, "r", encoding='utf-8').read(), 
            navbar=NAVBAR_SNIPPET, username="NULL"
        )), return_code
    else:
        return serve_error(404, "Not Found")

def serve_error(error: int, message: str) -> tuple[Response, int]:
    # return serve_basic_site(NOT_FOUND_PATH, 404)
    return Response(render_template_string(
        open(ERROR_PATH, "r", encoding='utf-8').read(), 
        navbar=NAVBAR_SNIPPET, code=str(error), message=str(message), username="NULL"
    )), error