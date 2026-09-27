import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

eval_pattern = """@app.route('/api/predict/evaluate')
@login_required
def evaluate_model():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(predictor.evaluate())
"""

# Insert it before "/student/portal"
text = text.replace("@app.route('/student/portal')", eval_pattern + "\n@app.route('/student/portal')")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
