import os
import re

# Fix app.py to pass .env variables to app.config
with open('app.py', 'r', encoding='utf-8') as f:
    app_py_content = f.read()

config_injection = """load_dotenv()

# Inject Firebase configurations into Flask config so templates can access them
app.config['FIREBASE_API_KEY'] = os.environ.get('FIREBASE_API_KEY', '')
app.config['FIREBASE_AUTH_DOMAIN'] = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
app.config['FIREBASE_PROJECT_ID'] = os.environ.get('FIREBASE_PROJECT_ID', '')
app.config['FIREBASE_STORAGE_BUCKET'] = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
app.config['FIREBASE_MESSAGING_SENDER_ID'] = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
app.config['FIREBASE_APP_ID'] = os.environ.get('FIREBASE_APP_ID', '')

app.config['SECRET_KEY']"""

if "app.config['FIREBASE_API_KEY']" not in app_py_content:
    app_py_content = app_py_content.replace("load_dotenv()\n\napp.config['SECRET_KEY']", config_injection)
    app_py_content = app_py_content.replace("load_dotenv()\napp.config['SECRET_KEY']", config_injection)
    app_py_content = app_py_content.replace("load_dotenv()\r\n\r\napp.config['SECRET_KEY']", config_injection)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_py_content)

# Fix HTML files
files_to_fix = [
    'templates/login.html',
    'templates/register.html',
    'templates/admin_dashboard.html',
    'templates/student_portal.html'
]

replacements = [
    (r"bg-slate-900/55", r"bg-\[var\(--card-bg\)]"),
    (r"bg-slate-900/80", r"bg-\[var\(--card-bg\)]"),
    (r"bg-slate-900(?=\s|>|/)", r"bg-\[var(--card-bg)]"),
    (r"bg-slate-800/50", r"bg-\[var\(--body-bg\)]"),
    (r"bg-slate-950/80", r"bg-\[var\(--body-bg\)]"),
    (r"bg-slate-950", r"bg-\[var\(--body-bg\)]"),
    
    (r"border-slate-800", r"border-\[var\(--border\)]"),
    (r"border-slate-700", r"border-\[var\(--border\)]"),
    
    (r"text-slate-400", r"text-\[var\(--text-secondary\)]"),
    (r"text-slate-500", r"text-\[var\(--text-secondary\)]"),
    (r"text-slate-600", r"text-\[var\(--text-secondary\)]"),
    
    (r"placeholder-slate-600", r"placeholder-\[var\(--text-secondary\)]"),
    (r"placeholder-slate-500", r"placeholder-\[var\(--text-secondary\)]"),
    
    # Text primary overrides
    (r'text-white mb-2', r'text-\[var\(--text-primary\)] mb-2'),
    (r'text-white focus:', r'text-\[var\(--text-primary\)] focus:'),
]

for fpath in files_to_fix:
    if not os.path.exists(fpath): continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    # Intercept firebase api key invalid in login
    if 'login.html' in fpath:
        js_hook = """    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const role = "{{ type }}";
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('error-msg');
        const btn = document.getElementById('submit-btn');
        
        if (!firebaseConfig.apiKey || firebaseConfig.apiKey === 'YOUR_API_KEY') {
            errorDiv.innerText = "Firebase Error: API Key is missing. Add FIREBASE_API_KEY to your .env file.";
            errorDiv.classList.remove('hidden');
            return;
        }"""
        content = re.sub(r"    document.getElementById\('login-form'\).addEventListener\('submit', async \(e\) => \{.*?const btn = document.getElementById\('submit-btn'\);", js_hook, content, flags=re.DOTALL)

    if 'register.html' in fpath:
        js_hook_reg = """    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const role = "{{ type }}";
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('error-msg');
        const btn = document.getElementById('submit-btn');

        if (!firebaseConfig.apiKey || firebaseConfig.apiKey === 'YOUR_API_KEY') {
            errorDiv.innerText = "Firebase Error: API Key is missing. Add FIREBASE_API_KEY to your .env file.";
            errorDiv.classList.remove('hidden');
            return;
        }"""
        content = re.sub(r"    document.getElementById\('register-form'\).addEventListener\('submit', async \(e\) => \{.*?const btn = document.getElementById\('submit-btn'\);", js_hook_reg, content, flags=re.DOTALL)

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Themes and config patched successfully.")
