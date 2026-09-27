import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add imports for Firebase and RAG
imports = """
from services.firebase_service import init_firebase, verify_id_token
from services.rag_service import rag_index

init_firebase()
"""

# Insert right after app initialization or before init_db
text = text.replace("app = Flask(__name__)", "app = Flask(__name__)" + imports)

# 2. Replace auth routes block entirely
auth_block_pattern = r"@app\.route\('/login', methods=\['GET', 'POST'\]\).*?def logout\(\):\n    logout_user\(\)\n    return redirect\(url_for\('index'\)\)"

new_auth_block = """@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', type='Admin')

@app.route('/admin/setup', methods=['GET', 'POST'])
def admin_setup():
    if request.method == 'GET':
        return render_template('register.html', type='Admin')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'GET':
        return render_template('register.html', type='Student')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'GET':
        return render_template('login.html', type='Student')

@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    data = request.json
    id_token = data.get('idToken')
    role = data.get('role')
    full_name = data.get('full_name')
    username = data.get('username')
    
    claims = verify_id_token(id_token)
    if not claims:
        return jsonify({'error': 'Invalid Firebase Token'}), 401
        
    email = claims.get('email')
    
    if role == 'admin':
        secret = data.get('admin_secret')
        if not ADMIN_SETUP_SECRET or secret != ADMIN_SETUP_SECRET:
            return jsonify({'error': 'Invalid setup secret.'}), 403
            
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists.'}), 400
            
        user = User(username=username, email=email, full_name=full_name, role='admin')
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('login')})
        
    elif role == 'student':
        student_id = data.get('student_id')
        
        existing = User.query.filter_by(student_id=student_id).first()
        if existing:
            if existing.email:
                return jsonify({'error': 'Student ID already registered.'}), 400
            else:
                existing.username = username
                existing.full_name = full_name
                existing.email = email
                db.session.commit()
                return jsonify({'success': True, 'redirect': url_for('student_login')})
                
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists.'}), 400
            
        user = User(username=username, full_name=full_name, email=email, student_id=student_id, role='student')
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('student_login')})
        
    return jsonify({'error': 'Invalid role'}), 400

@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    data = request.json
    id_token = data.get('idToken')
    role = data.get('role', 'student')
    
    claims = verify_id_token(id_token)
    if not claims:
        return jsonify({'error': 'Invalid Firebase Token. Unauthorized.'}), 401
        
    email = claims.get('email')
    user = User.query.filter_by(email=email, role=role).first()
    
    if not user:
        return jsonify({'error': f'Account not found for this {role} role in database.'}), 404
        
    login_user(user)
    
    if role == 'admin':
        return jsonify({'success': True, 'redirect': url_for('admin_dashboard')})
    else:
        return jsonify({'success': True, 'redirect': url_for('student_portal')})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))"""

text = re.sub(auth_block_pattern, new_auth_block, text, flags=re.DOTALL)

rag_context = """
            # Use RAG to fetch local feedback data context
            if not rag_index.is_built:
                rag_index.build_index(feedbacks)
            
            rag_results = rag_index.retrieve(message, top_k=5)
            if rag_results:
                context += "\\n\\nRelated Historical Semantic Context (RAG):\\n"
                for res in rag_results:
                    context += f"- {res['text']} (Match: {round(res['score'], 2)})\\n"
            
            prompt = f"System Context: {context}\\n\\nUser Question: {message}"
"""

text = text.replace('prompt = f"System Context: {context}\\n\\nUser Question: {message}"', rag_context)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
