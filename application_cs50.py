import os
from datetime import datetime

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


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get user cash
    cash = db.execute("SELECT cash FROM users WHERE id = :id",
                      id=session["user_id"])[0].get("cash")
    total = cash

    # Get user stocks value
    stocks = db.execute("SELECT symbol, sum(shares) FROM transactions WHERE user_id = :user_id \
                        GROUP BY symbol HAVING sum(shares) > 0",
                        user_id=session["user_id"])

    # Lookup the current price for possessed stock
    for i, stock in enumerate(stocks):
        price = lookup(stock["symbol"])["price"]
        stocks[i]["price"] = usd(price)
        stocks[i]["value"] = usd(stock["sum(shares)"] * price)
        total += stock["sum(shares)"] * price

    return render_template("index.html", stocks=stocks, cash=usd(cash), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        # Ensure symbol exists
        elif not lookup(request.form.get("symbol")):
            return apology("symbol not found", 400)

        # Ensure share is valid
        shares = request.form.get("shares")
        if not shares.isdigit() or int(shares) < 0:
            return apology("share must be a positive integer", 400)

        # Ensure user is affordable
        cash = db.execute("SELECT cash FROM users WHERE id = :id",
                          id=session["user_id"])[0].get('cash')
        symbol = request.form.get("symbol")
        price = lookup(symbol).get("price")
        if cash < price*int(shares):
            return apology("You are not affordable", 400)

        # Update user cash
        cash -= price * int(shares)
        rows_u = db.execute("UPDATE users SET cash = :cash WHERE id = :id",
                            cash=cash, id=session["user_id"])

        # Insert transaction into table
        rows_ti = db.execute("INSERT INTO transactions (user_id, date, symbol, price, shares) \
                            VALUES (:user_id, :date, :symbol, :price, :shares)",
                             user_id=session["user_id"],
                             date=datetime.now(),
                             symbol=symbol,
                             price=price,
                             shares=int(shares))

        return redirect('/')

    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # Ensure username not in database
    usernames = db.execute("SELECT username FROM users")
    usernames = [username["username"] for username in usernames]
    username = request.args.get("username")
    valid = True if username not in usernames else False
    return jsonify(valid)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT date, symbol, price, shares FROM transactions WHERE user_id = :user_id",
                         user_id=session["user_id"])

    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        quote = lookup(request.form.get("symbol"))

        # Ensure symbol found
        if quote == None:
            return apology("can not find the stock", 400)

        quote["price"] = usd(quote["price"])

        return render_template('quote.html', quote=quote)

    # When method is GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Query database for username
        rows_s = db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get("username"))

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure username is not duplicate
        elif len(rows_s) == 1:
            return apology("username already exists", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 400)

        # Ensure password is the same as confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Hash the passowrd
        hash_password = generate_password_hash(request.form.get("password"))

        # Write in the registered user information and return id value
        rows_w = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"),
                            hash=hash_password)

        # Log in the registered user automatically
        # Forget any user_id
        session.clear()

        # Remember which user has logged in
        session["user_id"] = rows_w

        return redirect("/")

    # When method is GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must select symbol", 400)

        # Ensure shares is valid
        shares = request.form.get("shares")
        user_shares = db.execute("SELECT sum(shares) FROM transactions WHERE user_id = :user_id \
                                AND symbol = :symbol GROUP BY symbol",
                                 user_id=session["user_id"],
                                 symbol=request.form.get("symbol"))[0]["sum(shares)"]
        if not shares.isdigit() or int(shares) < 0:
            return apology("share must be a positive integer", 400)

        if int(shares) > user_shares:
            return apology("Shares insufficient", 400)

        # Update user cash
        cash = db.execute("SELECT cash FROM users WHERE id = :id",
                          id=session["user_id"])[0]["cash"]
        price = lookup(request.form.get("symbol"))["price"]
        cash += price * int(shares)
        rows_u = db.execute("UPDATE users SET cash = :cash WHERE id = :id",
                            cash=cash,
                            id=session["user_id"])

        # Insert sell request into transaction
        rows_i = db.execute("INSERT INTO transactions (user_id, date, symbol, price, shares) \
                            VALUES (:user_id, :date, :symbol, :price, :shares)",
                            user_id=session["user_id"],
                            date=datetime.now(),
                            symbol=request.form.get("symbol"),
                            price=price,
                            shares=int(shares)*(-1))

        return redirect('/')

    # When method is GET
    else:
        stocks = db.execute("SELECT symbol FROM transactions WHERE user_id = :user_id \
                            GROUP BY symbol HAVING sum(shares) > 0",
                            user_id=session["user_id"])

        return render_template("sell.html", stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
