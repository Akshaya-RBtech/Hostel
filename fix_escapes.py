import os

files_to_fix = [
    'templates/login.html',
    'templates/register.html',
    'templates/admin_dashboard.html',
    'templates/student_portal.html'
]

for fpath in files_to_fix:
    if not os.path.exists(fpath): continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove all incorrect python-escaped slashes from inside Tailwind classes
    content = content.replace(r'bg-\[var\(--card-bg\)]', 'bg-[var(--card-bg)]')
    content = content.replace(r'bg-\[var\(--body-bg\)]', 'bg-[var(--body-bg)]')
    content = content.replace(r'border-\[var\(--border\)]', 'border-[var(--border)]')
    content = content.replace(r'text-\[var\(--text-secondary\)]', 'text-[var(--text-secondary)]')
    content = content.replace(r'placeholder-\[var\(--text-secondary\)]', 'placeholder-[var(--text-secondary)]')
    content = content.replace(r'text-\[var\(--text-primary\)]', 'text-[var(--text-primary)]')

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Double slash CSS escapes completely fixed.")
