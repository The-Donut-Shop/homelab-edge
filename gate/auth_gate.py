"""Tiny shared-password gate used by Caddy's forward_auth.

GET  /__gate_check   200 if the session cookie is valid, else 302 to the login page
GET  /__gate_login   login form
POST /__gate_login   checks GATE_USER / GATE_PASS, sets a signed cookie (30 days)
"""
import hashlib
import hmac
import html
import os
import time
from urllib.parse import quote

from flask import Flask, Response, make_response, redirect, request

app = Flask(__name__)
SECRET = os.environ["COOKIE_SECRET"]
GATE_USER = os.environ["GATE_USER"]
GATE_PASS = os.environ["GATE_PASS"]
TITLE = os.environ.get("GATE_TITLE", "Sign in")
COOKIE_NAME = os.environ.get("GATE_COOKIE_NAME", "homelab_gate")
MAX_AGE = 30 * 24 * 3600


def make_token():
    ts = str(int(time.time()) + MAX_AGE)
    sig = hmac.new(SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def valid_token(tok):
    try:
        ts, sig = tok.split(".", 1)
        expected = hmac.new(SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        return int(ts) > time.time()
    except Exception:
        return False


def safe_redirect(target):
    # only same-site paths: "/x" is fine, "//evil.com" and "/\\evil.com" are not
    if not target.startswith("/") or target.startswith("//") or target.startswith("/\\"):
        return "/"
    return target


LOGIN_FORM = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="font-family:sans-serif;max-width:380px;margin:100px auto;padding:0 16px;">
<h2>{title}</h2>
{error}
<form method="POST">
<input type="hidden" name="redirect" value="{redirect}">
<input type="text" name="username" placeholder="username" autocomplete="username" style="width:100%;padding:10px;margin-bottom:8px;box-sizing:border-box;" autofocus>
<input type="password" name="password" placeholder="password" autocomplete="current-password" style="width:100%;padding:10px;margin-bottom:8px;box-sizing:border-box;">
<button type="submit" style="width:100%;padding:10px;">Enter</button>
</form>
</body></html>"""


@app.route("/__gate_login", methods=["GET", "POST"])
def login():
    error = ""
    redirect_to = safe_redirect(request.values.get("redirect", "/"))
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if hmac.compare_digest(u, GATE_USER) and hmac.compare_digest(p, GATE_PASS):
            resp = make_response(redirect(redirect_to))
            resp.set_cookie(
                COOKIE_NAME,
                make_token(),
                max_age=MAX_AGE,
                httponly=True,
                secure=request.headers.get("X-Forwarded-Proto", "https") == "https",
                samesite="Lax",
            )
            return resp
        time.sleep(1)  # slow down password guessing
        error = "<p style='color:red'>Wrong username or password.</p>"
    return LOGIN_FORM.format(
        title=html.escape(TITLE), error=error, redirect=html.escape(redirect_to, quote=True)
    )


@app.route("/__gate_check")
def check():
    tok = request.cookies.get(COOKIE_NAME, "")
    if valid_token(tok):
        return Response(status=200)
    orig_uri = request.headers.get("X-Forwarded-Uri", "/")
    resp = Response(status=302)
    resp.headers["Location"] = f"/__gate_login?redirect={quote(safe_redirect(orig_uri), safe='')}"
    return resp


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9091)
