import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

IEX_API_KEY = "pk_e7260e58ccd74cb092488737c7102848"


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
