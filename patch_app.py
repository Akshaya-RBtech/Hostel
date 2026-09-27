import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
content = content.replace(
'''from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")''',
'''from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ADMIN_SETUP_SECRET = os.environ.get("ADMIN_SETUP_SECRET")'''
)

# 2. init_db remove admin
content = content.replace(
'''            # Create admin
            admin = User(username='admin', password='admin123', role='admin')
            db.session.add(admin)
            
            import random''',
'''            # (Admin creation removed - use /admin/setup)
            import random'''
)

# 3. New login logic
login_block_old = '''@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', type='Admin')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            user = User(username=name, student_id=student_id, role='student')
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('student_portal'))
    return render_template('login.html', type='Student')'''

login_block_new = '''@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='admin').first()
        if user and user.password:
            is_valid = False
            if user.password.startswith('scrypt:') or user.password.startswith('pbkdf2:'):
                is_valid = check_password_hash(user.password, password)
            else:
                is_valid = (user.password == password)
                if is_valid:
                    user.password = generate_password_hash(password)
                    db.session.commit()
            if is_valid:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', type='Admin')

@app.route('/admin/setup', methods=['GET', 'POST'])
def admin_setup():
    if request.method == 'POST':
        secret = request.form.get('secret')
        if not ADMIN_SETUP_SECRET or secret != ADMIN_SETUP_SECRET:
            flash('Invalid setup secret.')
            return redirect(url_for('admin_setup'))
            
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if password != confirm:
            flash('Passwords do not match.')
            return redirect(url_for('admin_setup'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('admin_setup'))
            
        user = User(username=username, email=email, full_name=full_name,
                    password=generate_password_hash(password), role='admin')
        db.session.add(user)
        db.session.commit()
        flash('Admin account created successfully. You can now log in.')
        return redirect(url_for('login'))
        
    return render_template('register.html', type='Admin')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('full_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if password != confirm:
            flash('Passwords do not match.')
            return redirect(url_for('student_register'))
            
        # Check if student ID already registered with a password
        existing = User.query.filter_by(student_id=student_id).first()
        if existing:
            if existing.password:
                flash('Account with this Student ID already exists and is registered.')
                return redirect(url_for('student_register'))
            else:
                # Claim existing mock student account
                existing.username = username
                existing.full_name = name
                existing.email = email
                existing.password = generate_password_hash(password)
                db.session.commit()
                flash('Student account claimed successfully! Please sign in.')
                return redirect(url_for('student_login'))
                
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('student_register'))
            
        user = User(username=username, full_name=name, email=email, student_id=student_id,
                    password=generate_password_hash(password), role='student')
        db.session.add(user)
        db.session.commit()
        flash('Student account created successfully! Please sign in.')
        return redirect(url_for('student_login'))
        
    return render_template('register.html', type='Student')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='student').first()
        if user and user.password:
            is_valid = False
            if user.password.startswith('scrypt:') or user.password.startswith('pbkdf2:'):
                is_valid = check_password_hash(user.password, password)
            else:
                is_valid = (user.password == password)
                if is_valid:
                    user.password = generate_password_hash(password)
                    db.session.commit()
            if is_valid:
                login_user(user)
                return redirect(url_for('student_portal'))
                
        flash('Invalid student credentials. Did you register?')
        return redirect(url_for('student_login'))
    return render_template('login.html', type='Student')'''

content = content.replace(login_block_old, login_block_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

