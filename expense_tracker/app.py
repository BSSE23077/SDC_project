from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy import extract, func
from datetime import datetime
# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    merchant = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    receipt_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_budget = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), default=datetime.utcnow().strftime('%Y-%m'))

# ==================== LOGIN MANAGER ====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== ROUTES ====================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            # IMPORTANT: no redirect here, just flash + render on same request
            flash('Invalid email or password', 'error')

    # for both GET and failed POST, render login.html
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    now = datetime.utcnow()

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    base_filter = [Expense.user_id == current_user.id]

    # build date conditions once
    if start_date_str and end_date_str:
        s = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        e = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        date_filter = [Expense.date.between(s, e)]
    else:
        date_filter = [
            extract('year', Expense.date) == now.year,
            extract('month', Expense.date) == now.month,
        ]

    # expenses list
    month_expenses = Expense.query.filter(*base_filter, *date_filter).all()
    total_spent = sum(e.amount for e in month_expenses)

    # category totals using same filters
    category_rows = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter(*base_filter, *date_filter)
        .group_by(Expense.category)
        .all()
    )

    labels = [row[0] for row in category_rows]
    values = [float(row[1]) for row in category_rows]

    budget = Budget.query.filter_by(user_id=current_user.id).first()
    budget_amount = budget.total_budget if budget else 0
    remaining = budget_amount - total_spent

    return render_template(
        "dashboard.html",
        total_spent=total_spent,
        budget_amount=budget_amount,
        remaining=remaining,
        expenses=month_expenses,
        labels=labels,
        values=values,
    )




@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        category = request.form.get('category')
        merchant = request.form.get('merchant')
        description = request.form.get('description')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        
        expense = Expense(
            user_id=current_user.id,
            amount=amount,
            category=category,
            merchant=merchant,
            description=description,
            date=date
        )
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_expense.html')

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    user_budget = Budget.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        total_budget = float(request.form.get('total_budget'))
        
        if user_budget:
            user_budget.total_budget = total_budget
        else:
            user_budget = Budget(user_id=current_user.id, total_budget=total_budget)
            db.session.add(user_budget)
        
        db.session.commit()
        flash('Budget updated!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('budget.html', budget=user_budget)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name')
    email = request.form.get('email')
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Email already taken by another user', 'error')
        return redirect(url_for('profile'))
    
    current_user.name = name
    current_user.email = email
    db.session.commit()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))
    
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    # Security: only owner can edit
    if expense.user_id != current_user.id:
        flash('You are not allowed to edit this expense.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        expense.amount = float(request.form.get('amount'))
        expense.category = request.form.get('category')
        expense.merchant = request.form.get('merchant')
        expense.description = request.form.get('description')
        expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        db.session.commit()

        flash('Expense updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # For GET request, show form with existing data
    return render_template('edit_expense.html', expense=expense)


@app.route('/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    # Security: only owner can delete
    if expense.user_id != current_user.id:
        flash('You are not allowed to delete this expense.', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route("/expenses")
@login_required
def view_expenses():
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    start_date = request.args.get("start_date")  # 'YYYY-MM-DD'
    end_date = request.args.get("end_date")      # 'YYYY-MM-DD'

    q = Expense.query.filter_by(user_id=current_user.id)

    # exact range has priority if both dates given
    if start_date and end_date:
        from datetime import datetime
        s = datetime.strptime(start_date, "%Y-%m-%d").date()
        e = datetime.strptime(end_date, "%Y-%m-%d").date()
        q = q.filter(Expense.date.between(s, e))
    else:
        if year:
            q = q.filter(extract("year", Expense.date) == year)
        if month:
            q = q.filter(extract("month", Expense.date) == month)

    expenses = q.order_by(Expense.date.desc()).all()

    years = db.session.query(extract("year", Expense.date)) \
        .filter(Expense.user_id == current_user.id).distinct().all()
    years = [int(y[0]) for y in years]

    return render_template(
        "view_expenses.html",
        expenses=expenses,
        years=years,
    )

@app.route('/scan-receipt', methods=['GET', 'POST'])
@login_required
def scan_receipt():
    extracted = None
    suggested = {}

    if request.method == 'POST':
        file = request.files.get('receipt')
        if not file or file.filename == '':
            flash('Please select a receipt image.', 'error')
            return redirect(url_for('scan_receipt'))

        # save locally for now
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        # TODO: replace this with real AWS Textract later
        # For now, just pretend or use local OCR if installed
        extracted = "Sample OCR text for demo only."
        suggested = {
            "amount": 0.0,
            "date": datetime.utcnow().date().strftime('%Y-%m-%d'),
            "merchant": "Unknown"
        }

    return render_template(
        'scan_receipt.html',
        extracted=extracted,
        suggested=suggested
    )

# ==================== RUN APP ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
