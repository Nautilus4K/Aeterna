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
import datetime

NAVBAR_SNIPPET = open(WEB_ROOT / "templates" / "navbar.html", "r", encoding='utf-8').read()
ERROR_PATH = WEB_ROOT / "error.html"
PROFILE_PATH = WEB_ROOT / "profile.html"

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

def serve_basic_site(db: DatabaseManager, sessions_list: dict[str, dict], path: pathlib.Path, cookies: ImmutableMultiDict[str, str], return_code: int = 200) -> tuple[Response, int]:
    if path.exists() and path.is_file():
        locale = get_locale(cookies)

        try:
            relative_path = path.relative_to(WEB_ROOT)
        except ValueError:
            return serve_error(db, sessions_list, 404, "Not Found", cookies)
        template = templates_env.get_template(str(relative_path))

        session_token = cookies.get("SESSION_TOKEN")
        username = "NULL"
        exists = session_token in sessions_list and db.user_exists(sessions_list[session_token]["user"])
        if exists:
            userbutton_snippet = f'<img src="/img/user/{sessions_list[session_token]["user"]}/100">' # type: ignore
            username = sessions_list[session_token]["user"] # type: ignore
        else:
            userbutton_snippet = LOCALES[locale]["login"]
        
        response = Response(template.render(
            username=username, locale=LOCALES[locale], user_pfp_button=userbutton_snippet,
            usermenu_mode=("login" if username == "NULL" else "")
        ))
        if not exists: response.set_cookie("SESSION_TOKEN", "", max_age=0, expires=0) # Remove the token
        
        return response, return_code
    else:
        return serve_error(db, sessions_list, 404, "Not Found", cookies)

def serve_error(db: DatabaseManager, sessions_list: dict[str, dict], error: int, message: str, cookies: ImmutableMultiDict[str, str]) -> tuple[Response, int]:
    # return serve_basic_site(NOT_FOUND_PATH, 404)
    locale = get_locale(cookies)

    relative_path = ERROR_PATH.relative_to(WEB_ROOT)
    template = templates_env.get_template(str(relative_path))

    session_token = cookies.get("SESSION_TOKEN")
    username = "NULL"
    exists = session_token in sessions_list and db.user_exists(sessions_list[session_token]["user"])
    if exists:
        userbutton_snippet = f'<img src="/img/user/{sessions_list[session_token]["user"]}/100">' # type: ignore
        username = sessions_list[session_token]["user"] # type: ignore
    else:
        userbutton_snippet = LOCALES[locale]["login"]
    
    response = Response(template.render(
        code=str(error), message=str(message), username=username, locale=LOCALES[locale], user_pfp_button=userbutton_snippet,
        usermenu_mode=("login" if username == "NULL" else "")
    ))
    if not exists: response.set_cookie("SESSION_TOKEN", "", max_age=0, expires=0) # Remove the token

    return response, error

def serve_profile(db: DatabaseManager, sessions_list: dict[str, dict], target_profile_username: str, cookies: ImmutableMultiDict[str, str]) -> tuple[Response, int]:
    if not db.user_exists(target_profile_username): return serve_error(db, sessions_list, 404, "User Not Found", cookies)

    locale = get_locale(cookies)
    
    relative_path = PROFILE_PATH.relative_to(WEB_ROOT)
    template = templates_env.get_template(str(relative_path))

    session_token = cookies.get("SESSION_TOKEN")
    username = "NULL"

    exists = session_token in sessions_list and db.user_exists(sessions_list[session_token]["user"])
    if exists:
        userbutton_snippet = f'<img src="/img/user/{sessions_list[session_token]["user"]}/100">' # type: ignore
        username = sessions_list[session_token]["user"] # type: ignore
    else:
        userbutton_snippet = LOCALES[locale]["login"]

    userdata = db.get_user_data(target_profile_username)
    response = Response(template.render(
        profile_username=target_profile_username, profile_realname=userdata[0], profile_bio=userdata[1],
        profile_gender=LOCALES[locale]["label"]["female" if userdata[2] else "male"],
        profile_createddate=userdata[3].date(), profile_birthday=userdata[4].date() if userdata[4] else LOCALES[locale]["not_provided"],
        
        username=username, locale=LOCALES[locale], user_pfp_button=userbutton_snippet,
        usermenu_mode=("login" if username == "NULL" else "")
    ))
    if not exists: response.set_cookie("SESSION_TOKEN", "", max_age=0, expires=0) # Remove the token

    return response, 200

def authenticate_user(db: DatabaseManager, username: str, password: str) -> bool:
    if db.user_exists(username):
        current_pass = db.get_user_password_hash(username)
        return bcrypt.checkpw(password.encode('utf-8'), current_pass)
    else: return False

def change_user_passwd(db: DatabaseManager, username: str, password: str) -> None:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # print("> Hashed: " + hashed.decode('utf-8'))
    
    db.change_user_passwd(username, hashed)