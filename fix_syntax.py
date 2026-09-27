import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

broken_ai_chat_pattern = r"@app\.route\('/api/ai/chat'.*?def ai_chat\(\):.*?return jsonify.*?\n\s+\}\)\n"

ai_chat_fixed = """@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    \"\"\"AI Chatbot endpoint — processes natural language queries.
    Uses Gemini LLM if API key is configured, with fallback to rule-based engine.
    \"\"\"
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))

    if not message.strip():
        return jsonify({'error': 'Empty message'}), 400

    consumption_logs = get_consumption_dicts()
    feedbacks = get_feedback_dicts()
    menu_data = get_menu_dicts()

    user_role = getattr(current_user, 'role', 'student')
    student_id = getattr(current_user, 'student_id', None)
    vote_stats = get_vote_stats() if user_role == 'student' else None
    
    # Save user message
    user_msg = ChatMessage(session_id=session_id, role='user', content=message)
    db.session.add(user_msg)

    response_text = ""
    msg_type = "text"
    
    # Try Gemini LLM first if available
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            
            context = "You are WasteZero AI, a specialized assistant for a hostel food-waste management app.\\n"
            context += "You must use the following ACTUAL real-time data to answer data-related questions.\\n"
            
            if user_role == 'admin':
                logs_summary = [f"{l['date']}: {l['meal_type']} wasted {l['wastage_percent']}% (Cost loss: {l['total_loss']})" for l in consumption_logs[-10:]]
                context += f"Last 10 Consumption Logs: {logs_summary}\\n"
                context += f"Menus: {menu_data[:5]}\\n"
                context += f"Feedback Summary: {[f['reason'] for f in feedbacks[:10]]}\\n"
            else:
                context += f"Upcoming Menus: {menu_data[:5]}\\n"
                context += "You are talking to a student. Focus on giving them diet tips, menu info, and instructing them to vote."
                if vote_stats:
                    context += f"Current Vote Stats: {vote_stats[:3]}\\n"
                    
            context += "\\nDo not invent statistics or attendance numbers. If you don't know, say so based on the data provided."
            
            # Use RAG to fetch local feedback data context
            if not rag_index.is_built:
                rag_index.build_index(feedbacks)
            
            rag_results = rag_index.retrieve(message, top_k=5)
            if rag_results:
                context += "\\n\\nRelated Historical Semantic Context (RAG):\\n"
                for res in rag_results:
                    context += f"- {res['text']} (Match: {round(res['score'], 2)})\\n"
            
            prompt = f"System Context: {context}\\n\\nUser Question: {message}"
            gemini_resp = gemini_model.generate_content(prompt)
            response_text = gemini_resp.text
        except Exception as e:
            print(f"Gemini error: {e}")
            fallback = ai_engine.chat(message, consumption_logs, feedbacks, menu_data, user_role, student_id, vote_stats)
            response_text = fallback['text']
            msg_type = fallback.get('type', 'text')
    else:
        fallback = ai_engine.chat(message, consumption_logs, feedbacks, menu_data, user_role, student_id, vote_stats)
        response_text = fallback['text']
        msg_type = fallback.get('type', 'text')

    # Save assistant response
    assistant_msg = ChatMessage(
        session_id=session_id,
        role='assistant',
        content=response_text,
        msg_type=msg_type
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        'response': response_text,
        'type': msg_type,
        'session_id': session_id,
        'timestamp': datetime.now().strftime('%I:%M %p')
    })
"""

text = re.sub(broken_ai_chat_pattern, ai_chat_fixed, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
