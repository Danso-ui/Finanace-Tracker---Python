from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager , login_user, current_user, UserMixin, logout_user
from datetime import datetime as dt

day:list[str] = [
    'Monday', 'Tuesday',
    'Wednesday', 'Thursday',
    'Friday', 'Saturday', 'Sunday'
]
monthStr:list[str] = [
    "January", "Febuary", "March",
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December"
]
now = dt.now()

# TODO: DATE, MONTH, YEAR
date:int = now.day
month:int = now.month
year:int = now.year

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
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance-tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

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

    secure_password = generate_password_hash('dummy1!')

    if not User.query.first():
        # firstUser = User(
        #     id =1000,
        #     username="dummy",
        #     email="dummy@gmail.com",
        #     password_hash=secure_password
        # )
        # db.session.add(firstUser)
        #
        # first_transaction = Transaction(
        #     id=5000,
        #     amount=0.00,
        #     category="System Setup",
        #     transaction_type="income",
        #     month=actual_month(month),
        #     year=now.year,
        #     dateMonth=date_month(date, month),
        #     note="Some light setup",
        #     user_id=firstUser.id,
        # )
        # db.session.add(first_transaction)

        db.session.commit()
        print("Set starting ID to 1001!")
#=== === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

@app.route("/")
def home():
    today = month_year(year, month)
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    expenses = Transaction.query.filter_by(user_id=current_user.id, transaction_type='expense').all()
    income = Transaction.query.filter_by(user_id=current_user.id, transaction_type='income').all()

    # TODO !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    this_month_income = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='income',
        month=f'{actual_month(month)}'
    ).all()
    tmi = sum(t.amount for t in this_month_income)

    # TODO !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    this_month_expense = Transaction.query.filter_by(
        transaction_type='expense',
        month=f'{actual_month(month)}',
        user_id=current_user.id
    ).all()
    tme = sum(t.amount for t in this_month_expense)

    # TODO !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    total_expense = sum(t.amount for t in expenses) if expenses else 0
    total_income = sum(t.amount for t in income) if income else 0
    net_total = total_income - total_expense

    # TODO !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    last_income = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='income',
        month=f'{actual_month(month)}'
    ).all()
    lmi = sum(t.amount for t in last_income) if last_income else 0

    # TODO !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    percentage = (net_total/total_income)*100 if total_income>0 else 0

    # TODO !==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==!==
    last_expense = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='expense',
        month=f'{actual_month(month)}'
    ).order_by()
    lme = sum(t.amount for t in last_expense) if last_expense else 0

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

            initial_transaction = Transaction(
                amount=0.00,
                category="Beginning",
                transaction_type="income",
                month=actual_month(month),
                year=now.year,
                dateMonth=date_month(date, month),
                note="The starting point",
                user_id=new_user.id
            )
            db.session.add(initial_transaction)
            db.session.commit()
            print(f"PASSWORD MATCH: {password}")
            print(f"PASSWORD MATCH: {confirm_password}")
            login_user(new_user)
            return redirect(url_for('home'))
        else:
            flash("The password doesn't match!")
            return redirect(url_for('signup'))

    return render_template("signup.html", logged_in=False)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    name = current_user.username
    email = current_user.email
    return render_template(
        "settings.html",
        logged_in=True,
        name=name,
        email=email
    )

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)