from datetime import date
from tempfile import mkdtemp
from werkzeug.security import check_password_hash

from flask import Flask, redirect, url_for, request, render_template, jsonify, session
from flask_session import Session
from sqlalchemy import create_engine, MetaData, Table, select, update

from helper import login_required, filter_none

app = Flask(__name__)

# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["filter_none"] = filter_none

# Create db engine
engine = create_engine('mysql+pymysql://b784cf9ee454b3:19d7c9c4@us-cdbr-iron-east-05.cleardb.net/heroku_5c5c458993391ff', pool_recycle=3600)

# Connect
conn = engine.connect()

# Get metadata of db
metadata = MetaData()

# Get table `orders_test`
table_orders = Table('orders_test', metadata, autoload=True, autoload_with=engine)
table_users = Table('users', metadata, autoload=True, autoload_with=engine)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    return redirect(url_for("order"))


@app.route("/longxing/order", methods=["GET", "POST"])
@login_required
def order():

    session.pop('order', None)

    # POST method
    if request.method == "POST":
        # Message passing to user
        message = {}

        name = request.form.get('name')

        phone = request.form.get('phone')

        # Ensure the data is not before today
        datepicker = request.form.get('datepicker')
        today = date.today()
        y, m, d = [int(x) for x in datepicker.split('/')]
        reserved_date = date(y, m, d)
        if reserved_date < today:
            message['datepicker'] = f'預定日期小於今天日期{today}'

        section = request.form.get('section')


        # Ensure at least order 1 table
        tables = request.form.get('tables')
        if tables and int(tables) < 1:
            message['tables'] = '桌數不足一桌'

        # Ensure at least 1 person
        people = request.form.get('people')
        if people and int(people) < 1:
            message['people'] = '至少一人用餐'

        dishes = request.form.get('dishes')

        remark = request.form.get('remark')

        # if input value doesn't validate
        if message:
            return render_template("error.html", message=message)

        # Write order in db
        else:
            query = table_orders.insert().values(
                date=today,
                name=name,
                phone=phone,
                reserved_date=reserved_date,
                section=section,
                tables=int(tables),
                people=int(people) if people else None,
                dishes=dishes,
                remark=remark
            )
            proxy = conn.execute(query)

            session['order'] = f"新增： {reserved_date}  {name}  {tables}桌"

            return render_template("order.html")

    # GET method
    else:
        return render_template("order.html")


@app.route("/longxing/sheet")
@login_required
def sheet():
    '''List the orders in db'''

    # Get today date
    today = date.today().strftime('%Y/%m/%d')

    # Columns to show on sheet
    columns_selected = [table_orders.c.id, table_orders.c.section, table_orders.c.name, table_orders.c.tables, table_orders.c.dishes, table_orders.c.phone, table_orders.c.remark]

    header = ['時段', '名字', '桌數', '金額', '電話', '備註']

    # Get orders from db
    query = select(columns_selected)\
        .where(table_orders.c.toshow==1)\
        .where(table_orders.c.reserved_date==date.today())
    proxy = conn.execute(query)
    orders = proxy.fetchall()

    return render_template("sheet.html", today=today, header=header, orders=orders)

@app.route('/longxing/statistic')
@login_required
def statistic():
    return render_template('statistic.html')

# Hide the order by set toshow = 0
@app.route('/longxing/deleteorder/<int:id_number>')
@login_required
def delete_order(id_number):

    # Hide the deleted order
    query = table_orders.update().where(table_orders.c.id == id_number).values(toshow = 0)
    conn.execute(query)

    # Get selected date
    query = select([table_orders.c.reserved_date]).where(table_orders.c.id == id_number)
    proxy = conn.execute(query)
    date = proxy.fetchone()[0]

    # Columns to show on sheet
    columns_selected = [table_orders.c.id, table_orders.c.section, table_orders.c.name, table_orders.c.tables, table_orders.c.dishes, table_orders.c.phone, table_orders.c.remark]

    # Get orders from db
    query = select(columns_selected)\
        .where(table_orders.c.toshow==1)\
        .where(table_orders.c.reserved_date==date)
    proxy = conn.execute(query)
    orders = proxy.fetchall()

    return render_template("order_list.html", orders=orders)

# Edit order
@app.route("/longxing/editorder/<int:id_number>", methods=["GET", "POST"])
@login_required
def edit_order(id_number):

    # POST method
    if request.method == "POST":
        # Message passing to user
        message = {}

        name = request.form.get('name')

        phone = request.form.get('phone')

        # Ensure the data is not before today
        datepicker = request.form.get('datepicker')
        today = date.today()
        y, m, d = [int(x) for x in datepicker.split('/')]
        reserved_date = date(y, m, d)

        if reserved_date < today:
            message['datepicker'] = f'預定日期小於今天日期{today}'

        section = request.form.get('section')

        # Ensure at least order 1 table
        tables = request.form.get('tables')
        if tables and int(tables) < 1:
            message['tables'] = '桌數不足一桌'

        # Ensure at least 1 person
        people = request.form.get('people')
        if people and int(people) < 1:
            message['people'] = '至少一人用餐'

        dishes = request.form.get('dishes')

        remark = request.form.get('remark')

        # if input value doesn't validate
        if message:
            return render_template("error.html", message=message)

        # Write order in db
        else:
            query = table_orders.update().where(table_orders.c.id==id_number).values(
                date=today,
                name=name,
                phone=phone,
                reserved_date=reserved_date,
                section=section,
                tables=int(tables),
                people=int(people) if people else None,
                dishes=dishes,
                remark=remark
            )
            proxy = conn.execute(query)
            return redirect(url_for("sheet"))

    # GET method
    else:
        query = select([table_orders]).where(table_orders.c.id==id_number)
        proxy = conn.execute(query)
        edit_order = proxy.fetchone()
        reserved_date = edit_order["reserved_date"].strftime("%Y/%m/%d")

        return render_template("edit_order.html", edit_order=edit_order, reserved_date=reserved_date)

'''Update order lists by selected date and section'''
@app.route("/longxing/sheetselected")
@login_required
def sheet_selected():
    select_date = request.args.get('date')
    y, m, d = [int(x) for x in select_date.split('/')]
    select_date = date(y, m, d)
    select_section = request.args.get('section')

    # Columns to show on sheet
    columns_selected = [table_orders.c.id, table_orders.c.section, table_orders.c.name, table_orders.c.tables, table_orders.c.dishes, table_orders.c.phone, table_orders.c.remark]

    # Get orders from db
    if (select_section == '整天'):
        query = select(columns_selected)\
            .where(table_orders.c.toshow==1)\
            .where(table_orders.c.reserved_date==select_date)
    else:
        query = select(columns_selected)\
            .where(table_orders.c.toshow==1)\
            .where(table_orders.c.reserved_date==select_date)\
            .where(table_orders.c.section==select_section)
    proxy = conn.execute(query)
    orders = proxy.fetchall()

    return render_template("order_list.html", orders=orders)


@app.route("/longxing/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for account
        query = select([table_users])\
            .where(table_users.c.account==request.form.get("account"))
        proxy = conn.execute(query)
        account = proxy.fetchall()

        # Ensure account exists and password is correct
        if len(account) != 1 or not check_password_hash(account[0]["password"], request.form.get("password")):
            return render_template("error.html", message={"error": "帳號不存在或密碼錯誤"})

        # Remember which user has logged in
        session["user_id"] = account[0]["id"]

        # Redirect account to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/longxing/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Ensure date is valid (not functional currently)
@app.route("/checkdatepicker")
def check_datepicler():
    datepicker = request.args.get("datepicker")
    today = date.today()
    m, d, y = [int(x) for x in datepicker.split('/')]
    customer_date = date(y, m, d)
    validation = False if customer_date < today else True

    return jsonify(validation)

