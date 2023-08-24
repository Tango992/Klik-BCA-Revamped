import os
import pathlib
import requests
import pyotp
import urllib.parse

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Google OAuth
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from helpers import apology, date_convert, generate_cardless_pin, generate_id, login_required, no_google_login, otp_required, rp, timestamp_convert, verify_otp


app = Flask(__name__)
app.secret_key = "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"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # to allow Http traffic for local dev

GOOGLE_CLIENT_ID = "48988692443-al9efmrmd415o6kn6tc68an6ecmlrmft.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://localhost:5000/callback"
)

app.jinja_env.filters["rp"] = rp
app.jinja_env.filters["timestamp_convert"] = timestamp_convert

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
@otp_required
def index():
    name = db.execute("SELECT fullname FROM users WHERE id = ?", session["user_id"])
    name = name[0]["fullname"]
    return render_template("index.html", name=name)


@app.route("/glogin")
def glogin():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            flash("Provide a username", "warning")
            return render_template("login.html"), 400

        elif not request.form.get("password"):
            flash("Provide a password", "warning")
            return render_template("login.html"), 400

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username/password", "danger")
            return render_template("login.html"), 403

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        fullname = request.form.get("fullname").title()
        username = request.form.get("username")
        password = request.form.get("password")
        hashed = generate_password_hash(password, method="scrypt")

        # Ensure username was submitted
        if not fullname:
            flash("Provide a first name", "warning")
            return render_template("register.html"), 400

        # Ensure username was submitted
        if not username:
            flash("Provide a username", "warning")
            return render_template("register.html"), 400

        # Ensure password was submitted
        elif not password:
            flash("Provide a password", "warning")
            return render_template("register.html"), 400

        # Ensure re-password was submitted
        elif not request.form.get("confirmation"):
            flash("Please re-enter password", "warning")
            return render_template("register.html"), 400

        # Query database for username
        unamecheck = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username already exists
        if len(unamecheck) != 0:
            flash("Username is already taken", "warning")
            return render_template("register.html"), 400

        # if password and re-password match
        if request.form.get("password") == request.form.get("confirmation"):
            db.execute("INSERT INTO users (id, username, hash, fullname) VALUES (?,?,?,?)", generate_id(), username, hashed, fullname)
            return render_template("login.html")
        else:
            flash("Password does not match", "danger")
            return render_template("register.html"), 400

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    currentid = db.execute("SELECT * FROM users WHERE username = ?", id_info.get("sub"))

    if len(currentid) < 1:
        db.execute("INSERT INTO users (id, username, hash, fullname) VALUES (?,?,?,?)", generate_id(), id_info.get("sub"), "", id_info.get("name"))

    currentid = db.execute("SELECT id FROM users WHERE username = ?", id_info.get("sub"))
    currentid = currentid[0]["id"]
    session["user_id"] = currentid
    return redirect("/")


@app.route("/login/tfa", methods=["GET", "POST"])
@login_required
def tfa():
    otpdb = db.execute("SELECT otp FROM users WHERE id = ?", session["user_id"])
    otpdb = otpdb[0]["otp"]

    fullname = db.execute("SELECT fullname FROM users WHERE id = ?", session["user_id"])
    fullname = urllib.parse.quote(fullname[0]["fullname"])

    if otpdb is None:
        db.execute("UPDATE users SET otp = ? WHERE id = ?", pyotp.random_base32(), session["user_id"])

        otpdb = db.execute("SELECT otp FROM users WHERE id = ?", session["user_id"])
        otpdb = otpdb[0]["otp"]

        session["firstotp"] = True

        return render_template("tfaregister.html", otpdb=otpdb, fullname=fullname)

    if request.method == "POST":
        otp_verified = verify_otp(request.form.get("otpinput"))

        if otp_verified:
            session["otp"] = True
            session.pop("firstotp", None)
            return redirect("/")

        elif not otp_verified:
            if session.get("firstotp") is True:
                flash("Invalid OTP!", "danger")
                return render_template("tfaregister.html", otpdb=otpdb, fullname=fullname), 400
            else:
                flash("Invalid OTP!", "danger")
                return render_template("tfalogin.html"), 400

    return render_template("tfalogin.html")


@app.route("/info/account")
@login_required
@otp_required
def account():
    account_info = db.execute("SELECT fullname, id, date FROM users WHERE id = ?", session.get("user_id"))
    account_info = account_info[0]
    return render_template("account.html", fullname=account_info["fullname"], id=account_info["id"], date=date_convert(account_info["date"]))

@app.route("/info/balance")
@login_required
@otp_required
def balance():
    balance = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
    balance = balance[0]["cash"]

    date = datetime.now()
    date_format = date.strftime("%d/%m/%Y %H:%M:%S")
    return render_template("balance.html", balance=balance, date_format=date_format)


@app.route("/info/mutation")
@login_required
@otp_required
def mutation():
    rows = db.execute("SELECT * FROM mutations WHERE mutation_id = ? ORDER BY date DESC", session.get("user_id"))
    return render_template("mutation.html", rows=rows)


@app.route("/transfer/input", methods=["GET", "POST"])
@login_required
@otp_required
def trfinput():
    bank_symbol = request.form.get("bank_symbol")
    recipient_id = request.form.get("recipient_id")

    banks = db.execute("SELECT name, symbol FROM bank_lists LIMIT 1")
    greyed_banks = db.execute("SELECT * FROM bank_lists WHERE bank_id NOT LIKE('1')")

    if request.method == "POST":
        if bank_symbol == None:
            flash("Select a bank", "danger")

        elif bank_symbol != "bbca":
            flash("For the moment we only accept transfer between BCA accounts", "danger")

        else:
            check_recipient_id = db.execute("SELECT * FROM users WHERE id = ?", recipient_id)
            check_duplicate = db.execute("SELECT * FROM transfer_lists WHERE sender_id = ? AND recipient_id = ?", session.get("user_id"), recipient_id)

            if len(check_duplicate) != 0:
                flash("Account number already on your list", "warning")
                return render_template("trf_input.html", banks=banks, greyed_banks=greyed_banks), 400

            elif len(check_recipient_id) < 1 or check_recipient_id[0]["id"] == session.get("user_id"):
                flash("Account number invalid", "danger")
                return render_template("trf_input.html", banks=banks, greyed_banks=greyed_banks), 400

            db.execute("INSERT INTO transfer_lists (sender_id, symbol, recipient_id) VALUES (?,?,?)", session.get("user_id"), bank_symbol, recipient_id)

            success_flash = check_recipient_id[0]["fullname"] + " - " + str(check_recipient_id[0]["id"]) + " have been successfuly added to your transfer list"
            flash(success_flash, "success")
            return render_template("trf_input.html", banks=banks, greyed_banks=greyed_banks)

    flash("As of this final project, you can only transfer between BCA accounts registered in this project database. Try using this dummy account number: 7285000001", "info")
    return render_template("trf_input.html", banks=banks, greyed_banks=greyed_banks)


@app.route("/transfer/list", methods=["GET", "POST"])
@login_required
@otp_required
def trflist():
    recipients = db.execute("SELECT symbol, recipient_id, fullname  FROM transfer_lists JOIN users ON transfer_lists.recipient_id = users.id WHERE sender_id = ?", session.get("user_id"))
    current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
    current_cash = current_cash[0]["cash"]

    recipient_id = request.form.get("recipient_id")
    amount = request.form.get("amount")
    note = request.form.get("note")
    otpinput = request.form.get("otpinput")

    if request.method == "POST":
        try:
            if current_cash < int(amount):
                flash("Cash insufficient", "danger")
                return render_template("trf_list.html", recipients=recipients), 400
        except ValueError:
                flash("Amount must not contain text", "danger")
                return render_template("trf_list.html", recipients=recipients), 400

        if not recipient_id:
            flash("Select a recipient", "danger")
            return render_template("trf_list.html", recipients=recipients), 400

        elif not verify_otp(otpinput):
            flash("Invalid OTP!", "danger")
            return render_template("trf_list.html", recipients=recipients), 400

        recipient_name = db.execute("SELECT fullname FROM users WHERE id = ?", recipient_id)
        recipient_name = recipient_name[0]["fullname"]
        sender_name = db.execute("SELECT fullname FROM users WHERE id = ?", session.get("user_id"))
        sender_name = sender_name[0]["fullname"]

        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", amount, session.get("user_id"))
        db.execute("INSERT INTO mutations (mutation_id, note, in_out, amount, type) VALUES (?,?,?,?,?)", session.get("user_id"), note, "-", amount, "Bank transfer to " + recipient_name)

        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", amount, recipient_id)
        db.execute("INSERT INTO mutations (mutation_id, note, in_out, amount, type) VALUES (?,?,?,?,?)", recipient_id, note, "+", amount, "Bank transfer from " + sender_name)

        flash("Transaction successful", "success")
        return render_template("trf_list.html", recipients=recipients)

    return render_template("trf_list.html", recipients=recipients)


@app.route("/cardless/withdraw", methods=["GET", "POST"])
@login_required
@otp_required
def cardless_withdraw():
    current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
    current_cash = current_cash[0]["cash"]

    amount = request.form.get("amount")
    otpinput = request.form.get("otpinput")

    if request.method == "POST":
        try:
            if int(amount) % 50000 != 0:
                flash("The amount entered is not a multiple of Rp. 50,000", "warning")
                return render_template("cardless_withdraw.html"), 400

            elif not verify_otp(otpinput):
                flash("Invalid OTP!", "danger")
                return render_template("cardless_withdraw.html"), 400

            elif current_cash < int(amount):
                flash("Insufficient fund", "danger")
                return render_template("cardless_withdraw.html"), 400

        except ValueError:
            flash("Input must not contain text", "danger")
            return render_template("cardless_withdraw.html"), 400

        pin = generate_cardless_pin("withdraw")
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", amount, session.get("user_id"))
        db.execute("INSERT INTO cardless (cardless_id, pin, cardless_type, amount) VALUES (?,?,?,?)", session.get("user_id"), pin, "withdraw", amount)
        db.execute("INSERT INTO mutations (mutation_id, in_out, amount, type, note) VALUES (?,?,?,?,?)", session.get("user_id"), "-", amount, "Cardless withdrawal", "")

        flash("Use the PIN on your nearest ATM to withdraw the money. You could also see the PIN on Cardless -> Transactions", "info")
        return render_template("cardless_success.html", pin=pin)

    flash("Make sure the amount of money must be a multiple of Rp. 50,000", "info")
    return render_template("cardless_withdraw.html")


@app.route("/cardless/deposit", methods=["GET", "POST"])
@login_required
@otp_required
def cardless_deposit():
    amount = request.form.get("amount")
    otpinput = request.form.get("otpinput")

    if request.method == "POST":
        try:
            if not verify_otp(otpinput):
                flash("Invalid OTP!", "danger")
                return render_template("cardless_withdraw.html"), 400

        except ValueError:
            flash("Input must not contain text", "danger")
            return render_template("cardless_withdraw.html"), 400

        pin = generate_cardless_pin("deposit")
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", amount, session.get("user_id"))
        db.execute("INSERT INTO cardless (cardless_id, pin, cardless_type, amount) VALUES (?,?,?,?)", session.get("user_id"), pin, "deposit", amount)
        db.execute("INSERT INTO mutations (mutation_id, in_out, amount, type, note) VALUES (?,?,?,?,?)", session.get("user_id"), "+", amount, "Cardless deposit", "")

        flash("Use the PIN on your nearest ATM to deposit the money. You could also see the PIN on Cardless -> Transactions", "info")
        return render_template("cardless_success.html", pin=pin)

    return render_template("cardless_deposit.html")

@app.route("/cardless/transactions")
@login_required
@otp_required
def cardless_transactions():
    rows = db.execute("SELECT * FROM cardless WHERE cardless_id = ? ORDER BY date DESC", session.get("user_id"))
    return render_template("cardless_transactions.html", rows=rows)


@app.route("/admin/password", methods=["GET", "POST"])
@login_required
@otp_required
@no_google_login
def password():
    old_pass = request.form.get("old_pass")
    new_pass = request.form.get("new_pass")
    confirmation = request.form.get("confirmation")
    otpinput = request.form.get("otpinput")

    otpsecret = db.execute("SELECT otp FROM users WHERE id = ?", session.get("user_id"))
    otpsecret = otpsecret[0]["otp"]

    hashed = db.execute("SELECT hash FROM users WHERE id = ?", session.get("user_id"))
    hashed = hashed[0]["hash"]

    if request.method == "POST":
        if not check_password_hash(hashed, old_pass):
            flash("Wrong old password", "danger")

        elif new_pass != confirmation:
            flash("New password does not match", "danger")

        else:
            if old_pass == new_pass:
                flash("New password must be different than the old password", "danger")

            elif not verify_otp(otpinput):
                flash("Invalid OTP!", "danger")

            else:
                db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_pass, method='scrypt'), session["user_id"])
                flash("Password changed", "success")
                return render_template("password.html")

        return render_template("password.html"), 400

    return render_template("password.html")


@app.errorhandler(404)
def page_not_found(e):
    print(e)
    return apology("page not found", 404)


@app.errorhandler(500)
def internal_server_error(e):
    print(e)
    return apology("internal server error", 500)
