import re

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the broken gemini card tail
bad_tail = """
            
                </div>
                <div class="card-body">
                    <div id="gemini-chat-history" style="max-height:200px;overflow-y:auto;margin-bottom:15px;display:flex;flex-direction:column;gap:10px;font-size:13px;">
                        <!-- Messages will appear here -->
                    </div>
                    <div style="display:flex;gap:8px;">
                        <input type="text" id="gemini-input" placeholder="E.g. How to use leftover rice?" class="form-input" style="flex:1;" onkeypress="if(event.key==='Enter') askGemini()">
                        <button onclick="askGemini()" id="gemini-btn" class="btn-primary" style="background:linear-gradient(135deg,#7c3aed,#4f46e5);border:none;">
                            Ask AI
                        </button>
                    </div>
                </div>
            </div>"""

text = text.replace(bad_tail, "")

eval_card = """
            <!-- Model Evaluation Card -->
            <div class="card" style="margin-top:20px;">
                <div class="card-header" style="justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div class="icon-badge" style="background:rgba(52,211,153,0.1);color:#34d399;">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div>
                            <div class="section-title">Model Diagnostics</div>
                            <div class="section-sub">XGBoost Evaluation Metrics</div>
                        </div>
                    </div>
                    <button onclick="evaluateModel()" class="btn-primary flex items-center justify-center p-2.5 min-w-[120px]">
                        Run Eval
                    </button>
                </div>
                <div class="card-body">
                    <div id="eval-result" style="display:none;" class="grid grid-cols-3 gap-4 text-center mt-2">
                        <div class="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
                            <div class="text-[10px] text-slate-400 font-bold uppercase mb-1">MAE</div>
                            <div id="eval-mae" class="text-xl font-bold text-white">0</div>
                        </div>
                        <div class="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
                            <div class="text-[10px] text-slate-400 font-bold uppercase mb-1">RMSE</div>
                            <div id="eval-rmse" class="text-xl font-bold text-white">0</div>
                        </div>
                        <div class="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
                            <div class="text-[10px] text-slate-400 font-bold uppercase mb-1">Samples</div>
                            <div id="eval-samples" class="text-xl font-bold text-white">0</div>
                        </div>
                    </div>
                </div>
            </div>
"""

# Insert the eval card after the prediction-result card
pred_result_end = """            <!-- Result card -->
            <div id="prediction-result" style="display:none;" class="card">
                <div style="padding:36px;text-align:center;">
                    <div style="font-size:11px;font-weight:700;color:#818cf8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                        Recommended Preparation Quantity
                    </div>
                    <div id="result-val" style="font-size:64px;font-weight:900;color:var(--text-primary);letter-spacing:-3px;line-height:1;">0</div>
                    <div style="font-size:20px;font-weight:500;color:var(--text-secondary);margin-top:2px;">kilograms</div>
                    <p style="font-size:13px;color:var(--text-secondary);opacity:0.7;margin-top:12px;">Based on historical data &amp; real-time student feedback.</p>
                </div>
            </div>"""

text = text.replace(pred_result_end, pred_result_end + "\n" + eval_card)

# Add js for evaluating
js_eval = """
    async function evaluateModel() {
        const resultDiv = document.getElementById('eval-result');
        const maeDiv = document.getElementById('eval-mae');
        const rmseDiv = document.getElementById('eval-rmse');
        const samplesDiv = document.getElementById('eval-samples');
        
        maeDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        rmseDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        resultDiv.style.display = 'grid';
        
        try {
            const res = await fetch('/api/predict/evaluate');
            const data = await res.json();
            if (data.error) {
                alert(data.error);
                resultDiv.style.display = 'none';
                return;
            }
            maeDiv.innerText = data.mae;
            rmseDiv.innerText = data.rmse;
            samplesDiv.innerText = data.samples;
        } catch(e) {
            alert('Failed to evaluate model');
            resultDiv.style.display = 'none';
        }
    }
"""

text = text.replace("async function askGemini()", js_eval + "\n\n    async function askGemini()")

# But I removed askGemini from html! 
# Let's just put it under runPrediction
js_eval_replace_target = "async function runPrediction()"
text = text.replace(js_eval_replace_target, js_eval + "\n\n    " + js_eval_replace_target)

# Clean up any leftover askGemini functions
text = re.sub(r'async function askGemini\(\) \{.*?\n\s+\}', '', text, flags=re.DOTALL)

with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
