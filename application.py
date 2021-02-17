import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""

    username = session["username"]

    if request.method == "POST":
        # Add funds
        funds = request.form.get("funds")
        funds = float(funds)

        if not funds or funds < 0:
            return apology("must transfer greater than 0 funds", 403)

        cash = db.execute("SELECT cash from users WHERE username = :username", username=username)
        cash = cash[0]["cash"]

        cash += funds
        db.execute("UPDATE users SET cash=:cash WHERE username=:username", cash=cash, username=username)

        flash("Successfully added funds!")
        return redirect("/")

    else:
        # Display portfolio
        rows = db.execute("SELECT symbol, name, SUM(shares) AS totalshares from holdings WHERE username = :username GROUP BY name HAVING totalshares > 0", username=username)
        cash = db.execute("SELECT cash from users WHERE username = :username", username=username)
        cash = cash[0]["cash"]
        balance = cash

        for row in rows:
            symbol = row["symbol"]
            temp = lookup(symbol)
            row["price"] = temp["price"]
            row["total"] = row["price"]*row["totalshares"]
            balance += row["total"]

        return render_template("index.html", rows=rows, cash=cash, balance=balance)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        username = session["username"]
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol or not shares:
            return apology("must fill in all fields to purchase", 403)

        shares = float(shares)
        if shares < 0:
            return apology("number of shares must be more than 0", 403)

        quote = lookup(symbol)
        if quote == None:
            return apology("stock not found")

        total = quote["price"] * shares
        rows = db.execute("SELECT cash from users WHERE username = :username", username=username)
        currentfunds = rows[0]["cash"]

        if total > currentfunds:
            return apology("insufficient funds")

        # Logs the transaction and updates cash balance
        db.execute("INSERT INTO holdings (username, symbol, name, shares, price) VALUES(?,?,?,?,?)", username, quote["symbol"], quote["name"], shares, quote["price"])
        db.execute("UPDATE users SET cash=:balance WHERE username=:username", balance=currentfunds-total, username=username)
        flash("Bought!")
        return redirect("/")

    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    username = session["username"]
    rows = db.execute("SELECT symbol, shares, price, transacted from holdings WHERE username = :username", username=username)

    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username=request.form.get("username")

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = username

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        symbol = request.form.get("symbol")

        #Ensure symbol was entered
        if not symbol:
            return apology("must input stock symbol", 403)

        quote = lookup(symbol)
        if(quote == None):
            return apology("stock not found", 403)

        return render_template("quoted.html", quote=quote)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure firstname was submitted
        if not firstname or not lastname or not username or not password or not confirmation:
            return apology("must fill in all fields", 403)

        # Query database for username to ensure it does not exist
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) == 1:
            return apology("Username already exists!", 403)

        # Max username & password check
        if len(username) > 10:
            return apology("Username must be less than 10 characters", 403)

        if confirmation != password:
            return apology("Passwords do not match", 403)

        if len(password) < 6:
            return apology("Passwords must be greater than 6 characters long", 403)

        if password.isalpha() == True:
            return apology("Password must contain at least one number", 403)

        if password.isalnum() == True:
            return apology("Password must contain at last one special character", 403)

        # Add user to database if all else checks out
        pwhash = generate_password_hash(password, 'pbkdf2:sha256', 8)
        rows = db.execute("INSERT INTO users (firstname, lastname, username, hash) VALUES(?,?,?,?)", firstname, lastname, username, pwhash)
        flash("Account created!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        username = session["username"]
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol or not shares:
            return apology("must fill in all fields to sell", 403)

        shares = float(shares)
        if shares < 0:
            return apology("number of shares must be greater than 0", 403)

        quote = lookup(symbol)
        if quote == None:
            return apology("stock not found", 403)

        total = quote["price"] * shares
        cash = db.execute("SELECT cash from users WHERE username = :username", username=username)
        cash = cash[0]["cash"]
        currentshares = db.execute("SELECT SUM(shares) AS totalshares from holdings WHERE symbol = :symbol AND username = :username GROUP BY name", symbol=symbol, username=username)
        currentshares = currentshares[0]["totalshares"]

        if currentshares < shares:
            return apology("insufficient shares", 403)

        # Logs the transaction and updates cash balance
        db.execute("INSERT INTO holdings (username, symbol, name, shares, price) VALUES(?,?,?,?,?)", username, quote["symbol"], quote["name"], -1*shares, quote["price"])
        db.execute("UPDATE users SET cash=:balance WHERE username=:username", balance=cash+total, username=username)
        flash("Sold!")
        return redirect("/")

    else:
        return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
