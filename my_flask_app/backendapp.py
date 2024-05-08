from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    
    def __repr__(self):
        return '<User %r>' % self.username

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return '<Expense %r>' % self.name

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return 'Username already exists!'
        
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('user_login'))
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/login', methods=["GET", "POST"])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["logged_in"] = True
            session["username"] = username  # Store the username in the session
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Credentials!"
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        notes = request.form['notes']
        user_id = User.query.filter_by(username=session['username']).first().id
        new_expense = Expense(name=name, amount=amount, notes=notes, user_id=user_id)
        db.session.add(new_expense)
        db.session.commit()

        # Redirect to prevent form resubmission on refresh
        return redirect(url_for('dashboard'))

    user_id = User.query.filter_by(username=session['username']).first().id
    expenses = Expense.query.filter_by(user_id=user_id).all()

    # Calculate total monthly and overall expenses
    total_monthly_expenses = sum(expense.amount for expense in expenses)
    total_expenses = total_monthly_expenses * 12

    return render_template('dashboard.html', expenses=expenses, total_monthly_expenses=total_monthly_expenses, total_expenses=total_expenses)

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if request.method == 'POST':
        expense.name = request.form['name']
        expense.amount = float(request.form['amount'])
        expense.notes = request.form['notes']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_expense.html', expense=expense)

@app.route('/remove_expense/<int:expense_id>', methods=['POST'])
def remove_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Flask route for calculating total expenses
def calculate_total_expenses(expenses):
    total = sum(expense.amount for expense in expenses)
    return total

if __name__ == '__main__':
    app.run(debug=True)
