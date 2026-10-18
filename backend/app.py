from flask import Flask, Response, request, redirect, render_template_string, send_file, abort
from utils import *
from consts import WEB_ROOT
from PIL import Image
import os
import pathlib
import shutil
from db import DatabaseManager
db = DatabaseManager()
db.initdb()

app = Flask(__name__)

# Routing basic sites
@app.route("/")
def page_main():
    # print(WEB_ROOT)
    return serve_basic_site(WEB_ROOT / "index.html")

# Routing css
@app.route("/css/<filename>")
def css_serve(filename: str):
    target_path = WEB_ROOT / "css" / filename
    if target_path.exists() and target_path.is_file():
        return Response(open(target_path, "r", encoding='utf-8').read(), mimetype="text/css"), 200
    else:
        return serve_error(404, "Not Found")

# Routing JavaScript
@app.route("/js/<filename>")
def js_serve(filename: str):
    target_path = WEB_ROOT / "js" / filename
    if target_path.exists() and target_path.is_file():
        return Response(open(target_path, "r", encoding='utf-8').read(), mimetype="text/javascript"), 200
    else:
        return serve_error(404, "Not Found")

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
    target_path = WEB_ROOT / "img" / ("user." + username + "." + size + ".webp")
    user_original_path = WEB_ROOT / "img" / ("user." + username + ".500.webp") # Original file is size 500

    if size in pfp_sizes:
        if target_path.exists():
            return send_file(target_path, max_age=1000) # 1000 seconds
        elif user_original_path.exists():
            # Self recovery
            img = Image.open(user_original_path)
            img = img.resize((int(size), int(size))) # Yeah pfps are SQUARE
            img.save(target_path)
            return send_file(target_path, max_age=1000)
        elif db.user_exists(username):
            shutil.copyfile(user_default_pfp_paths[0], WEB_ROOT / "img" / ("user." + username + ".100.webp"))
            shutil.copyfile(user_default_pfp_paths[1], WEB_ROOT / "img" / ("user." + username + ".250.webp"))
            shutil.copyfile(user_default_pfp_paths[2], WEB_ROOT / "img" / ("user." + username + ".500.webp"))
            return send_file(target_path, max_age=1000)
    return serve_error(404, "Not Found")

# Routing images
@app.route("/img/<filename>")
def img_serve(filename: str):
    target_path = WEB_ROOT / "img" / filename
    if target_path.is_file():
        return send_file(target_path, max_age=31536000)   # 1 year
    return serve_error(404, "Not Found")

# Error handling
@app.errorhandler(404)
def error_handler_404(e):
    return serve_error(404, "Not Found")