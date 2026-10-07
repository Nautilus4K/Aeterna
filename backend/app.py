from flask import Flask, Response, request, redirect, render_template_string, send_file, abort
from utils import *
from consts import WEB_ROOT
import os
import pathlib

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

# Routing images
@app.route("/img/<filename>")
def img_serve(filename: str):
    target_path = WEB_ROOT / "img" / filename
    if target_path.exists() and target_path.is_file():
        return send_file(target_path), 200
    else:
        return serve_error(404, "Not Found")

# Error handling
@app.errorhandler(404)
def error_handler_404(e):
    return serve_error(404, "Not Found")