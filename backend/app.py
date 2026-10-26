from flask import Flask, Response, request, redirect, render_template_string, send_file, abort, send_from_directory, url_for
from utils import serve_basic_site, serve_error, authenticate_user, get_locale, LOCALES, change_user_passwd, serve_profile
from consts import WEB_ROOT, SESSIONS_SAVED_PATH, SESSIONS_MAX_AGE
from cachetools import TTLCache
from PIL import Image
import os
import pathlib
import shutil
import secrets
import json
import threading
from db import DatabaseManager
db = DatabaseManager()
db.initdb()

app = Flask(__name__)
app.config["SECURE_SERVER"] = False # HTTPS
app.config["DEVELOPMENT"] = False # In development?

# Also authentication. Sessions list actually.
sessions_list: dict[str, dict] = {}
sessions_list_lock = threading.Lock()
if os.path.exists(SESSIONS_SAVED_PATH):
    sessions_list = json.load(open(SESSIONS_SAVED_PATH, "r", encoding='utf-8'))

def save_sessions_async():
    thread = threading.Thread(target=save_sessions)
    thread.start()

def save_sessions():
    with sessions_list_lock:
        with open(SESSIONS_SAVED_PATH, "w", encoding='utf-8') as f:
            json.dump(sessions_list, f)

# Routing basic sites
@app.route("/")
def page_main():
    # print(WEB_ROOT)
    return serve_basic_site(db, sessions_list, WEB_ROOT / "index.html", request.cookies)

@app.route("/login")
def page_login():
    if request.cookies.get("SESSION_TOKEN") not in sessions_list:
        return serve_basic_site(db, sessions_list, WEB_ROOT / "login.html", request.cookies)
    return redirect(url_for('page_main'))

@app.route("/config")
def page_config():
    if request.cookies.get("SESSION_TOKEN") not in sessions_list:
        return redirect(url_for('page_login'))
    return serve_basic_site(db, sessions_list, WEB_ROOT / "config.html", request.cookies)

@app.route("/user/<username>")
def page_profile(username: str):
    return serve_profile(db, sessions_list, username, request.cookies)

# Routing css
@app.route("/css/<path:filename>")
def css_serve(filename: str):
    # send_from_directory securely ensures the file is strictly inside the directory
    directory = WEB_ROOT / "css"
    
    if app.config["DEVELOPMENT"]:
        # Disable caching entirely in development
        return send_from_directory(directory, filename, max_age=0)
    else:
        # Caches for 5 minutes in production
        response = send_from_directory(directory, filename, max_age=300)
        # Add the 'immutable' and 'public' directives manually since max_age only sets max-age
        response.headers["Cache-Control"] = "max-age=300, public"
        return response

# Routing JavaScript
@app.route("/js/<path:filename>")
def js_serve(filename: str):
    directory = WEB_ROOT / "js"
    
    if app.config["DEVELOPMENT"]:
        return send_from_directory(directory, filename, max_age=0)
    else:
        response = send_from_directory(directory, filename, max_age=300)
        response.headers["Cache-Control"] = "max-age=300, public"
        return response
    
# Images section
pfp_sizes = ["500", "250", "100"]
user_default_pfp_paths: list[pathlib.Path] = [
    WEB_ROOT / "templates" / "default_user_img_100.webp",
    WEB_ROOT / "templates" / "default_user_img_250.webp",
    WEB_ROOT / "templates" / "default_user_img_500.webp"
]

# Routing user profile pictures
@app.route("/img/user/<username>/<size>")
def img_user_serve(username: str, size: str):
    if size not in pfp_sizes:
        return serve_error(db, sessions_list, 404, "Not Found", request.cookies)

    target_path = WEB_ROOT / "img" / f"user.{username}.{size}.webp"

    # If the requested size already exists, serve it directly
    if target_path.exists():
        return send_file(target_path, max_age=1000)

    # Self-Healing: Try to find ANY existing size variant to resize from (500 -> 250 -> 100)
    source_path = None
    for fallback_size in ["500", "250", "100"]:
        candidate = WEB_ROOT / "img" / f"user.{username}.{fallback_size}.webp"
        if candidate.exists():
            source_path = candidate
            break

    if source_path:
        try:
            with Image.open(source_path) as img:
                img = img.resize((int(size), int(size)))
                img.save(target_path, "WEBP")
            return send_file(target_path, max_age=1000)
        except Exception:
            # If the image file is corrupted, fall through to defaults
            pass

    # If no custom images exist at all, but the user is valid, provision defaults
    if db.user_exists(username):
        try:
            shutil.copyfile(user_default_pfp_paths[0], WEB_ROOT / "img" / f"user.{username}.100.webp")
            shutil.copyfile(user_default_pfp_paths[1], WEB_ROOT / "img" / f"user.{username}.250.webp")
            shutil.copyfile(user_default_pfp_paths[2], WEB_ROOT / "img" / f"user.{username}.500.webp")
            if target_path.exists():
                return send_file(target_path, max_age=1000)
        except Exception:
            pass

    return serve_error(db, sessions_list, 404, "Not Found", request.cookies)

# Routing images
@app.route("/img/<filename>")
def img_serve(filename: str):
    target_path = WEB_ROOT / "img" / filename
    if target_path.is_file():
        return send_file(target_path, max_age=31536000)   # 1 year
    return serve_error(db, sessions_list, 404, "Not Found", request.cookies)

# Error handling
@app.errorhandler(404)
def error_handler_404(e):
    return serve_error(db, sessions_list, 404, "Not Found", request.cookies)

# Authentication
import time
rate_limiter = TTLCache(maxsize=10000, ttl=30)

@app.route("/loginauth", methods=['POST'])
def auth():
    if request.remote_addr in rate_limiter:
        if rate_limiter[request.remote_addr] > 3: return LOCALES[get_locale(request.cookies)]["login_rate_limited"], 429 # type: ignore
        else: rate_limiter[request.remote_addr] += 1 # type: ignore
    else:
        rate_limiter[request.remote_addr] = 1

    locale = get_locale(request.cookies)
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    if authenticate_user(db, username, password):
        new_token = secrets.token_hex(16)
        sessions_list[new_token] = {
            "user": username,
            "time": int(time.time())
        }
        save_sessions_async()

        response = Response("Authorized")
        response.set_cookie(
            key="SESSION_TOKEN",
            max_age=SESSIONS_MAX_AGE, # 30 days
            httponly=True, # Prevents client side javascript from reading
            samesite='Lax',
            secure=app.config["SECURE_SERVER"],
            value=new_token
        )

        return response, 200
    return LOCALES[locale]["login_credentials"], 401

@app.route("/logout")
def logout_session():
    session_token = request.cookies.get("SESSION_TOKEN")
    if session_token in sessions_list:
        del sessions_list[session_token]
        save_sessions_async()

    response = redirect(url_for("page_main"))
    response.set_cookie("SESSION_TOKEN", "", max_age=0, expires=0)
    return response

@app.route("/api/changepass")
def changepass_session():
    session_token = request.cookies.get("SESSION_TOKEN")
    if session_token not in sessions_list:
        return "Forbidden", 403
    username = sessions_list[session_token]["user"]

    current_pass = request.headers.get("cpass", "")
    if current_pass == "": return "Forbidden", 403

    if authenticate_user(db, username, current_pass):
        new_pass = request.headers.get("npass", "")
        if new_pass == "": return "Forbidden", 403

        change_user_passwd(db, username, new_pass)
    return "Forbidden", 403