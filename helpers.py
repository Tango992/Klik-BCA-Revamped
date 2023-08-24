import pyotp
import random

from datetime import datetime
from cs50 import SQL
from flask import flash, redirect, render_template, session
from functools import wraps

db = SQL("sqlite:///project.db")


def apology(message, code=400):
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def otp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("otp") is None:
            return redirect("/login/tfa")
        return f(*args, **kwargs)

    return decorated_function


def no_google_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("state") is not None:
            flash("Forbidden", "danger")
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_function


def generate_id():
    while True:
        try:
            fixed_value = "7285"
            random_value = str(random.randint(100000, 999999))
            id_value = int(fixed_value + random_value)

            checkid = db.execute("SELECT id FROM users WHERE id = ?", id_value)

            if len(checkid) != 0:
                raise ValueError
            else:
                return id_value

        except ValueError:
            pass


def generate_cardless_pin(s):
    fixed_value = None

    if s == "withdraw":
        fixed_value = "1"
    elif s == "deposit":
        fixed_value = "2"
    else:
        return None

    while True:
        try:
            random_value = str(random.randint(10000, 99999))
            pin = int(fixed_value + random_value)

            checkpin = db.execute("SELECT pin FROM cardless WHERE pin = ?", pin)

            if len(checkpin) != 0:
                raise ValueError
            else:
                return pin

        except ValueError:
            pass


def verify_otp(input):
    otpsecret = db.execute("SELECT otp FROM users WHERE id = ?", session["user_id"])
    otpsecret = otpsecret[0]["otp"]

    secret = pyotp.TOTP(otpsecret)

    return secret.verify(input)


def date_convert(string):
    outdate = string.split("-")
    outdate[0] = str(outdate[0]).zfill(2)
    outdate[1] = str(outdate[1]).zfill(2)

    year = outdate[0]
    month = outdate[1]
    date = outdate[2]

    return date + "/" + month + "/" + year


def timestamp_convert(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")


def rp(value):
    return f"Rp. {value:,.2f}"
