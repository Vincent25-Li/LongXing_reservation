from datetime import date

from flask import Flask, redirect, url_for, request, render_template, jsonify
from sqlalchemy import create_engine, MetaData, Table, select, update

from helper import login_required, filter_none

app = Flask(__name__)

# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["filter_none"] = filter_none

# Create db engine
engine = create_engine('mysql+pymysql://root:root@localhost:3306/orders_management')

# Connect
conn = engine.connect()

# Get metadata of db
metadata = MetaData()

# Get table `orders_test`
table_orders = Table('orders_test', metadata, autoload=True, autoload_with=engine)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return redirect(url_for("form"))

@app.route("/longxing/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # Message passing to user
        message = {}

        name = request.form.get('name')

        phone = request.form.get('phone')

        # Ensure the data is not before today
        datepicker = request.form.get('datepicker')
        today = date.today()
        m, d, y = [int(x) for x in datepicker.split('/')]
        reserved_date = date(y, m, d)
        if reserved_date < today:
            message['datepicker'] = f'預定日期小於今天日期{today}'

        section = request.form.get('section')

        time = request.form.get('time')

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
                time=time,
                tables=int(tables),
                people=int(people) if people else None,
                dishes=dishes,
                remark=remark
            )
            proxy = conn.execute(query)
            return redirect(url_for("sheet"))

    else:
        return render_template("form.html")


@app.route("/longxing/sheet")
def sheet():
    '''List the orders in db'''

    # Columns to show on sheet
    columns_selected = [table_orders.c.id, table_orders.c.reserved_date, table_orders.c.section, table_orders.c.name, table_orders.c.tables, table_orders.c.dishes, table_orders.c.phone, table_orders.c.remark]

    header = ['訂位日期', '時段', '名字', '桌數', '金額', '電話', '備註']

    # Get orders from db
    query = select(columns_selected).where(table_orders.c.toshow==1)
    proxy = conn.execute(query)
    orders = proxy.fetchall()

    return render_template("sheet.html", header=header, orders=orders)

@app.route('/longxing/statistic')
def statistic():
    return render_template('statistic.html')

# Hide the order by set toshow = 0
@app.route('/longxing/deleteorder/<int:id_number>')
def delete_order(id_number):

    # delete order
    query = table_orders.update().where(table_orders.c.id == id_number).values(toshow = 0)
    conn.execute(query)


    # Columns to show on sheet
    columns_selected = [table_orders.c.id, table_orders.c.reserved_date, table_orders.c.section, table_orders.c.name, table_orders.c.tables, table_orders.c.dishes, table_orders.c.phone, table_orders.c.remark]

    # Get orders from db
    query = select(columns_selected).where(table_orders.c.toshow==1)
    proxy = conn.execute(query)
    orders = proxy.fetchall()

    return render_template("order_list.html", orders=orders)

# render edit from template
@app.route("/longxing/editorder/<int:id_number>")
def edit_order(id_number):

    query = select([table_orders]).where(table_orders.c.id==id_number)
    proxy = conn.execute(query)
    edit_order = proxy.fetchone()
    reserved_date = edit_order["reserved_date"].strftime("%m/%d/%Y")
    time = edit_order["time"].strftime("%H:%M") if edit_order["time"] is not None else "None"

    return render_template("edit_form.html", edit_order=edit_order, reserved_date=reserved_date, time=time)

@app.route("/longxing/edit_form/<int:id_number>", methods=["POST"])
def edit_form(id_number):
    if request.method == "POST":
        # Message passing to user
        message = {}

        name = request.form.get('name')

        phone = request.form.get('phone')

        # Ensure the data is not before today
        datepicker = request.form.get('datepicker')
        today = date.today()
        m, d, y = [int(x) for x in datepicker.split('/')]
        reserved_date = date(y, m, d)

        if reserved_date < today:
            message['datepicker'] = f'預定日期小於今天日期{today}'

        section = request.form.get('section')

        time = request.form.get('time')

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
                time=time,
                tables=int(tables),
                people=int(people) if people else None,
                dishes=dishes,
                remark=remark
            )
            proxy = conn.execute(query)
            return redirect(url_for("sheet"))

# Ensure date is valid
@app.route("/checkdatepicker")
def check_datepicler():
    datepicker = request.args.get("datepicker")
    today = date.today()
    m, d, y = [int(x) for x in datepicker.split('/')]
    customer_date = date(y, m, d)
    validation = False if customer_date < today else True

    return jsonify(validation)

