"""
Utilities for WSGI application. Like serving sites for instance.
"""
import pathlib
from flask import Response, redirect, render_template_string, send_from_directory, abort
from werkzeug.datastructures import ImmutableMultiDict
from consts import WEB_ROOT
from jinja2 import Environment, FileSystemLoader
import json
import bcrypt
from db import DatabaseManager

NAVBAR_SNIPPET = open(WEB_ROOT / "templates" / "navbar.html", "r", encoding='utf-8').read()
ERROR_PATH = WEB_ROOT / "error.html"

LOCALE_PREFIXES = {
    "en": WEB_ROOT / "locale.en.json",
    "vi": WEB_ROOT / "locale.vi.json"
}

LOCALES = {}

# set up locale datas
for localed in LOCALE_PREFIXES:
    LOCALES[localed] = json.load(open(LOCALE_PREFIXES[localed], "r", encoding='utf-8'))

templates_env = Environment(loader=FileSystemLoader(WEB_ROOT))

def get_locale(cookies: ImmutableMultiDict[str, str]):
    locale = cookies.get("locale")
    if locale not in LOCALE_PREFIXES: locale = "en"
    return locale

def serve_basic_site(sessions_list: dict[str, str], path: pathlib.Path, cookies: ImmutableMultiDict[str, str], return_code: int = 200) -> tuple[Response, int]:
    if path.exists() and path.is_file():
        locale = get_locale(cookies)

        try:
            relative_path = path.relative_to(WEB_ROOT)
        except ValueError:
            return serve_error(sessions_list, 404, "Not Found", cookies)
        template = templates_env.get_template(str(relative_path))

        session_token = cookies.get("SESSION_TOKEN")
        username = "NULL"
        if session_token in sessions_list:
            userbutton_snippet = f'<img src="/img/user/{sessions_list[session_token]}/100">'
            username = sessions_list[session_token]
        else:
            userbutton_snippet = LOCALES[locale]["login"]
        
        response = Response(template.render(
            username=username, locale=LOCALES[locale], user_pfp_button=userbutton_snippet,
            usermenu_mode=("login" if username == "NULL" else "")
        ))
        if session_token not in sessions_list: response.set_cookie("SESSION_TOKEN", "", max_age=0, expires=0) # Remove the token
        
        return response, return_code
    else:
        return serve_error(sessions_list, 404, "Not Found", cookies)

def serve_error(sessions_list: dict[str, str], error: int, message: str, cookies: ImmutableMultiDict[str, str]) -> tuple[Response, int]:
    # return serve_basic_site(NOT_FOUND_PATH, 404)
    locale = get_locale(cookies)

    relative_path = ERROR_PATH.relative_to(WEB_ROOT)
    template = templates_env.get_template(str(relative_path))

    session_token = cookies.get("SESSION_TOKEN")
    username = "NULL"
    if session_token in sessions_list:
        userbutton_snippet = f'<img src="/img/user/{sessions_list[session_token]}/100">'
        username = sessions_list[session_token]
    else:
        userbutton_snippet = LOCALES[locale]["login"]
    
    response = Response(template.render(
        code=str(error), message=str(message), username=username, locale=LOCALES[locale], user_pfp_button=userbutton_snippet,
        usermenu_mode=("login" if username == "NULL" else "")
    ))
    if session_token not in sessions_list: response.set_cookie("SESSION_TOKEN", "", max_age=0, expires=0) # Remove the token

    return response, error

def authenticate_user(db: DatabaseManager, username: str, password: str) -> bool:
    if db.user_exists(username):
        current_pass = db.get_user_password_hash(username)
        return bcrypt.checkpw(password.encode('utf-8'), current_pass)
    else: return False