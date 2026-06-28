Replace your whole app.py with this:

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from datetime import datetime
app = Flask(__name__)
app.config.from_prefixed_env()
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "FLASK_SQLALCHEMY_DATABASE_URI",
    "sqlite:///finance.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
STATIC_DIR = os.path.join(app.root_path, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    transactions = db.relationship("Transaction", backref="owner", lazy=True)
    goals = db.relationship("Goal", backref="owner", lazy=True)
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_name = db.Column(db.String(50), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Sign Up")
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
class TransactionForm(FlaskForm):
    amount = FloatField("Amount", validators=[DataRequired(), NumberRange(min=0)])
    type = SelectField(
        "Type",
        choices=[("income", "Income"), ("expense", "Expense")],
        validators=[DataRequired()]
    )
    category = StringField("Category", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()], default=datetime.today)
    note = StringField("Note")
    submit = SubmitField("Add Transaction")
class GoalForm(FlaskForm):
    goal_name = StringField("Goal Name", validators=[DataRequired()])
    target_amount = FloatField("Target Amount", validators=[DataRequired(), NumberRange(min=0)])
    due_date = DateField("Due Date", validators=[DataRequired()], default=datetime.today)
    submit = SubmitField("Set Goal")
def get_or_create_demo_user():
    demo_email = "demo@financeapp.com"
    demo_password = "demo123"
    demo_user = User.query.filter_by(email=demo_email).first()
    if demo_user:
        return demo_user
    hashed_password = bcrypt.generate_password_hash(demo_password).decode("utf-8")
    demo_user = User(
        username="Demo User",
        email=demo_email,
        password=hashed_password
    )
    db.session.add(demo_user)
    db.session.commit()
    sample_transactions = [
        Transaction(amount=4200, type="income", category="Salary", date=datetime(2026, 1, 15), note="Monthly salary", user_id=demo_user.id),
        Transaction(amount=600, type="income", category="Freelance", date=datetime(2026, 2, 5), note="Web project", user_id=demo_user.id),
        Transaction(amount=850, type="expense", category="Rent", date=datetime(2026, 1, 20), note="Apartment rent", user_id=demo_user.id),
        Transaction(amount=230, type="expense", category="Groceries", date=datetime(2026, 1, 22), note="Weekly groceries", user_id=demo_user.id),
        Transaction(amount=150, type="expense", category="Transport", date=datetime(2026, 1, 25), note="Gas and rideshare", user_id=demo_user.id),
        Transaction(amount=95, type="expense", category="Subscriptions", date=datetime(2026, 2, 10), note="Software tools", user_id=demo_user.id),
        Transaction(amount=120, type="expense", category="Dining", date=datetime(2026, 2, 14), note="Dinner and coffee", user_id=demo_user.id),
        Transaction(amount=300, type="income", category="Tutoring", date=datetime(2026, 3, 1), note="Tutoring income", user_id=demo_user.id),
    ]
    sample_goals = [
        Goal(goal_name="Emergency Fund", target_amount=5000, current_amount=1800, due_date=datetime(2026, 12, 31), user_id=demo_user.id),
        Goal(goal_name="Graduate School Savings", target_amount=12000, current_amount=3500, due_date=datetime(2027, 1, 15), user_id=demo_user.id),
        Goal(goal_name="New Laptop Fund", target_amount=2200, current_amount=750, due_date=datetime(2026, 9, 1), user_id=demo_user.id),
    ]
    db.session.add_all(sample_transactions + sample_goals)
    db.session.commit()
    return demo_user
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()
        if existing_user:
            flash("Username or Email already exists. Please choose a different one.", "danger")
            return render_template("register.html", form=form)
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)
@app.route("/login", methods=["GET", "POST"])
def login():
    demo_user = get_or_create_demo_user()
    session["user_id"] = demo_user.id
    flash("Demo dashboard loaded successfully.", "success")
    return redirect(url_for("dashboard"))
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found. Please log in again.", "danger")
        return redirect(url_for("login"))
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    income_data = [transaction.amount for transaction in transactions if transaction.type == "income"]
    expense_data = [transaction.amount for transaction in transactions if transaction.type == "expense"]
    current_balance = sum(income_data) - sum(expense_data)
    chart_path = os.path.join(STATIC_DIR, "chart.png")
    if transactions:
        labels = ["Income", "Expense"]
        sizes = [sum(income_data), sum(expense_data)]
        colors = ["#4caf50", "#f44336"]
        explode = (0.1, 0)
        plt.figure(figsize=(6, 4))
        plt.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct="%1.1f%%",
            shadow=True,
            startangle=140
        )
        plt.title("Transaction Overview")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
    return render_template(
        "dashboard.html",
        transactions=transactions,
        income_data=income_data,
        expense_data=expense_data,
        current_balance=current_balance
    )
@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))
    form = TransactionForm()
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            type=form.type.data,
            category=form.category.data,
            date=form.date.data,
            note=form.note.data,
            user_id=session["user_id"]
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Transaction added successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_transaction.html", form=form)
@app.route("/set-goal", methods=["GET", "POST"])
def set_goal():
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(
            goal_name=form.goal_name.data,
            target_amount=form.target_amount.data,
            due_date=form.due_date.data,
            user_id=session["user_id"]
        )
        db.session.add(goal)
        db.session.commit()
        flash("Goal set successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("set_goal.html", form=form)
@app.route("/goals_viewer")
def goals_viewer():
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))
    results = db.session.query(
        Goal.id.label("goal_id"),
        Goal.goal_name,
        Goal.target_amount,
        Goal.current_amount,
        Goal.due_date,
        User.username.label("owner_name")
    ).join(
        User,
        Goal.user_id == User.id
    ).filter(
        User.id == session["user_id"]
    ).order_by(
        Goal.due_date.asc()
    ).all()
    goals_data = [
        {
            "goal_id": row.goal_id,
            "goal_name": row.goal_name,
            "target_amount": row.target_amount,
            "current_amount": row.current_amount,
            "due_date": row.due_date.strftime("%Y-%m-%d"),
            "owner_name": row.owner_name
        }
        for row in results
    ]
    return render_template("goals_viewer.html", goals=goals_data)
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))
@app.route("/news")
def news():
    return render_template("news.html")
with app.app_context():
    db.create_all()
if __name__ == "__main__":
    app.run(debug=True)