from flask import Flask, request, render_template, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager , login_user, current_user, UserMixin, logout_user
from datetime import datetime as dt
import csv
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask_login import login_required
import os
from dotenv import load_dotenv

load_dotenv()

day:list[str] = [
    'Monday', 'Tuesday',
    'Wednesday', 'Thursday',
    'Friday', 'Saturday', 'Sunday'
]
monthStr:list[str] = [
    "January", "February", "March",
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December"
]

def actual_month(fig:int) -> str:
    num:int = fig - 1
    # noinspection PyTypeHints
    month_string:str = monthStr[num]
    return month_string

def month_year(year_, month_):
    years: int = year_
    months: str = actual_month(month_)
    return f"{months}, {date} {years}"

def date_month(date_, month_):
    dates:int  = date_
    months: str = actual_month(month_)
    return f"{months} {dates}"


#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance-tracker.db'
database_url = os.getenv('POSTGRES_URL', os.getenv('DATABASE_URL', 'sqlite:///finance-tracker.db'))

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash
#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(120), nullable=False)
    transaction_type = db.Column(db.String(120), nullable=False)
    month = db.Column(db.String(120), nullable=False)
    year = db.Column(db.String(120), nullable=False)
    dateMonth = db.Column(db.String(120) ,nullable=False)
    note = db.Column(db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

with app.app_context():
    db.create_all()
#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

@app.route("/", methods=['GET', 'POST'])
@login_required
def home():
    now = dt.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day

    today = month_year(current_year, current_month)

    expenses = Transaction.query.filter_by(user_id=current_user.id, transaction_type='expenses').all()
    income = Transaction.query.filter_by(user_id=current_user.id, transaction_type='income').all()

    #  !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    this_month_income = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='income',
        month=f'{actual_month(current_month)}',
        year=str(current_year)
    ).all()
    tmi = sum(t.amount for t in this_month_income)

    #  !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    this_month_expense = Transaction.query.filter_by(
        transaction_type='expenses',
        month=f'{actual_month(current_month)}',
        year=str(current_year),
        user_id=current_user.id
    ).all()
    tme = sum(t.amount for t in this_month_expense)

    #  !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    total_expense = sum(t.amount for t in expenses) if expenses else 0
    total_income = sum(t.amount for t in income) if income else 0
    net_total = total_income - total_expense

    #  !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    last_income = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='income',
        month=f'{actual_month(current_month - 1)}',
        year=str(current_year)
    ).all()
    lmi = sum(t.amount for t in last_income) if last_income else 0

    #  !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    percentage = (net_total/total_income)*100 if total_income>0 else 0

    #  !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    last_expense = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='expense',
        month=f'{actual_month(current_month - 1)}',
        year=str(current_year)
    ).all()
    lme = sum(t.amount for t in last_expense) if last_expense else 0

    if request.method == 'POST':
        # Get the real-time date right when they click submit
        current_time = dt.now()
        
        trans_type = request.form.get('transaction_type')
        amount = request.form.get('amount')
        category = request.form.get('category')
        note = request.form.get('note') if request.form.get('note') else '—'

        new_transaction = Transaction(
            amount=amount,
            category=category,
            transaction_type=trans_type,
            month=f'{actual_month(current_time.month)}',
            user_id=current_user.id,
            note=note,
            dateMonth=f'{date_month(date_=current_time.day, month_=current_time.month)}',
            year=current_time.year,
        )
        db.session.add(new_transaction)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template(
        "index.html",
        logged_in=True,
        day=today,
        total=net_total,
        this_income=tmi,
        this_expense=tme,
        last_income=lmi,
        per=percentage,
        last_expense=lme,
    )
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("The email doesn't exist!")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password_hash, password):
            flash("The password doesn't match!")
            return redirect(url_for('login'))
        else:
            login_user(user)
            print(user.id)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=False)
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if User.query.filter_by(email=email).first():
            flash("The email already exists!")
            return redirect(url_for('signup'))

        if password == confirm_password:
            new_user = User(
                username=name,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('home'))
        else:
            flash("The password doesn't match!")
            return redirect(url_for('signup'))

    return render_template("signup.html", logged_in=False)
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/transaction-history")
@login_required
def transaction_history():
    
    filter_type = request.args.get('filter', 'all')

    now = dt.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day

    # Calculate current and last month safely
    current_month_str = actual_month(current_month)
    current_year_str = str(current_year)

    last_month_num = 12 if now.month == 1 else now.month - 1
    last_month_year_str = str(now.year - 1) if now.month == 1 else str(now.year)
    last_month_str = actual_month(last_month_num)

    # Base query for the logged-in user
    base_query = Transaction.query.filter_by(user_id=current_user.id)

    if filter_type == 'income':
        transactions = base_query.filter_by(transaction_type='income', month=current_month_str,
                                            year=current_year_str).all()
        page_title = "Income"
    elif filter_type == 'expenses':
        transactions = base_query.filter_by(transaction_type='expenses', month=current_month_str,
                                            year=current_year_str).all()
        page_title = "Expenses"
    elif filter_type == 'last_month_income':
        transactions = base_query.filter_by(transaction_type='income', month=last_month_str,
                                            year=last_month_year_str).all()
        page_title = "Last Month Income"
    elif filter_type == 'last_month_expenses':
        transactions = base_query.filter_by(transaction_type='expenses', month=last_month_str,
                                            year=last_month_year_str).all()
        page_title = "Last Month Expenses"
    else:  # 'net' or 'all'
        transactions = base_query.all()
        page_title = "Net Total"

    # Sort descending by ID so newest is on top
    transactions.sort(key=lambda x: x.id, reverse=True)

    return render_template("transaction-history.html", transactions=transactions, page_title=page_title,
                           filter_type=filter_type)
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    name = current_user.username
    email = current_user.email
    action = request.form.get("action")

    if request.method == "POST":
        if action == "change_password":
            old_password = request.form.get("oldPassword")
            new_password = request.form.get("newPassword")
            new_password_confirm = request.form.get("newPasswordConfirm")

            if check_password_hash(current_user.password_hash, old_password):
                print(f"Hi {check_password_hash(current_user.password_hash, old_password)}")
                if new_password == new_password_confirm:
                    new_password_hash = generate_password_hash(new_password)
                    current_user.password_hash = new_password_hash
                    db.session.commit()
                    return redirect(url_for('login'))
                else:
                    flash("The password doesn't match!")
                    return redirect(url_for('settings'))
            else:
                flash("The password incorrect!")
                return redirect(url_for('settings'))
        elif action == "update_profile":
            new_name = request.form.get("name")
            new_email = request.form.get("email")

            # Making sure they don't submit blank fields
            if new_name and new_email:
                current_user.username = new_name
                current_user.email = new_email
                db.session.commit()
                flash("Profile updated successfully!")

            return redirect(url_for('settings'))
        elif action == "delete_all":
            Transaction.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            return redirect(url_for('settings'))
        elif action == "delete_account":
            Transaction.query.filter_by(user_id=current_user.id).delete()
            User.query.filter_by(id=current_user.id).delete()
            db.session.commit()
            logout_user()
            return redirect(url_for('login'))

    return render_template(
        "settings.html",
        logged_in=True,
        name=name,
        email=email
    )
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/export")
@login_required
def export():
    # 1. Grab the filter (defaults to 'all' for the Settings page)
    filter_type = request.args.get('filter', 'all')
    base_query = Transaction.query.filter_by(user_id=current_user.id)

    # 2. Filter the database query based on the button clicked
    if filter_type == 'income':
        transactions = base_query.filter_by(transaction_type='income').all()
        file_label = "Income"
    elif filter_type == 'expenses':
        transactions = base_query.filter_by(transaction_type='expenses').all()
        file_label = "Expenses"
    else:
        transactions = base_query.all()
        file_label = "All Transactions"

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Date', 'Category', 'Type', 'Amount', 'Note', 'Month', 'Year'])

    for t in transactions:
        writer.writerow([t.dateMonth, t.category, t.transaction_type,
                         f"{t.amount:.2f}", t.note, t.month, t.year])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        # dynamically names the file!
        headers={"Content-Disposition": f"attachment; filename={current_user.username} {file_label}.csv"}
    )
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/export-pdf")
@login_required
def export_pdf():
    filter_type = request.args.get('filter', 'all')
    base_query = Transaction.query.filter_by(user_id=current_user.id)

    if filter_type == 'income':
        transactions = base_query.filter_by(transaction_type='income').all()
        file_label = "Income"
    elif filter_type == 'expenses':
        transactions = base_query.filter_by(transaction_type='expenses').all()
        file_label = "Expenses"
    else:
        transactions = base_query.all()
        file_label = "All Transactions"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title updates dynamically based on the filter
    elements.append(Paragraph(f"{file_label} History — {current_user.username}", styles['Title']))
    elements.append(Spacer(1, 20))

    data = [['Date', 'Category', 'Type', 'Amount', 'Note']]
    for t in transactions:
        data.append([t.dateMonth, t.category, t.transaction_type,
                     f"GH₵ {t.amount:.2f}", t.note or '—'])

    table = Table(data, colWidths=[80, 100, 80, 80, 180])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2dcc8f')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#13141a'), colors.HexColor('#1d1f28')]),
        ('TEXTCOLOR',  (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME',   (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 1), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#333')),
        ('PADDING',    (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={"Content-Disposition": f"attachment; filename={current_user.username}_{file_label}.pdf"}
    )
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/edit-transaction/<int:tx_id>", methods=["POST"])
@login_required
def edit_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)

    # Security check: only allow editing if they own it
    if tx.user_id == current_user.id:
        try:
            # Safely grab and convert the amount
            amount_str = request.form.get('amount')
            tx.amount = float(amount_str)
        except ValueError:
            flash("Error: Invalid amount entered.")
            return redirect(request.referrer or url_for('transaction_history'))

        # Grab the rest of the fields (these won't change unless the user actually changed them now!)
        tx.category = request.form.get('category')
        tx.transaction_type = request.form.get('transaction_type')

        note = request.form.get('note')
        tx.note = note if note else '—'

        db.session.commit()

    return redirect(request.referrer or url_for('transaction_history'))
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

@app.route("/delete-transaction/<int:tx_id>", methods=["POST"])
@login_required
def delete_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    # Security check: only allow deleting if they own it
    if tx.user_id == current_user.id:
        db.session.delete(tx)
        db.session.commit()
    return redirect(request.referrer or url_for('transaction_history'))
#=>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>  =>> =>> =>>

# if __name__ == '__main__':
#     app.run(debug=True)
