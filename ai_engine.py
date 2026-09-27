"""
Agentic AI Engine for Smart Hostel Food Waste Management
=========================================================
Algorithms Used:
  1. XGBoost Regressor — Food quantity prediction (existing)
  2. K-Means Clustering — Meal waste pattern grouping
  3. Exponential Smoothing — Waste trend forecasting
  4. Z-Score Anomaly Detection — Waste spike detection
  5. TF-IDF + Cosine Similarity — Student feedback analysis
  6. Rule-Based Expert System — Actionable recommendations
  7. NLP Pattern Matching — Chatbot query understanding
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import re
import math


class WasteAnalyticsAI:
    """Core Agentic AI class that analyzes food waste data and provides intelligent insights."""

    def __init__(self):
        self.conversation_context = {}

    # ─────────────────────────────────────────────
    # 1. K-MEANS CLUSTERING (from scratch)
    # ─────────────────────────────────────────────
    def _kmeans(self, data, k=3, max_iter=100):
        """Pure numpy K-Means clustering implementation."""
        if len(data) < k:
            return [0] * len(data), data.tolist()

        data = np.array(data, dtype=float)
        n_samples = len(data)

        # Initialize centroids using K-Means++ strategy
        centroids = [data[np.random.randint(n_samples)]]
        for _ in range(1, k):
            distances = np.array([min(np.linalg.norm(x - c) for c in centroids) for x in data])
            probabilities = distances ** 2 / (distances ** 2).sum()
            cumprob = np.cumsum(probabilities)
            r = np.random.random()
            idx = np.searchsorted(cumprob, r)
            idx = min(idx, n_samples - 1)
            centroids.append(data[idx])
        centroids = np.array(centroids)

        labels = np.zeros(n_samples, dtype=int)
        for _ in range(max_iter):
            # Assignment step
            for i in range(n_samples):
                dists = [np.linalg.norm(data[i] - centroids[j]) for j in range(k)]
                labels[i] = np.argmin(dists)

            # Update step
            new_centroids = np.zeros_like(centroids)
            for j in range(k):
                cluster_points = data[labels == j]
                if len(cluster_points) > 0:
                    new_centroids[j] = cluster_points.mean(axis=0)
                else:
                    new_centroids[j] = centroids[j]

            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        return labels.tolist(), centroids.tolist()

    def cluster_meals(self, consumption_logs):
        """Cluster meals by waste patterns to identify high/medium/low waste groups."""
        if len(consumption_logs) < 3:
            return {'clusters': [], 'summary': 'Insufficient data for clustering. Need at least 3 meal records.'}

        features = []
        meal_info = []
        for log in consumption_logs:
            features.append([
                log['prepared_qty'],
                log['consumed_qty'],
                log['wastage_percent'],
                log['total_loss']
            ])
            meal_info.append({
                'date': log['date'],
                'meal_type': log['meal_type'],
                'items': log['items'],
                'wastage_percent': log['wastage_percent']
            })

        data = np.array(features)
        # Normalize
        mins = data.min(axis=0)
        maxs = data.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1
        normalized = (data - mins) / ranges

        labels, centroids = self._kmeans(normalized, k=3)

        # Determine cluster characteristics
        cluster_waste = {}
        for i, label in enumerate(labels):
            if label not in cluster_waste:
                cluster_waste[label] = []
            cluster_waste[label].append(features[i][2])  # wastage_percent

        cluster_avg = {k: np.mean(v) for k, v in cluster_waste.items()}
        sorted_clusters = sorted(cluster_avg.items(), key=lambda x: x[1])

        cluster_names = {}
        severity_labels = ['🟢 Low Waste', '🟡 Moderate Waste', '🔴 High Waste']
        for idx, (cluster_id, avg) in enumerate(sorted_clusters):
            cluster_names[cluster_id] = severity_labels[min(idx, 2)]

        results = []
        for i, label in enumerate(labels):
            results.append({
                **meal_info[i],
                'cluster': cluster_names.get(label, 'Unknown'),
                'cluster_id': label
            })

        summary = f"Analyzed {len(consumption_logs)} meals into 3 clusters. "
        high_waste = [r for r in results if '🔴' in r['cluster']]
        if high_waste:
            summary += f"{len(high_waste)} meals flagged as high-waste patterns."
        else:
            summary += "No critical waste clusters detected."

        return {'clusters': results, 'summary': summary, 'cluster_averages': {cluster_names[k]: round(v, 1) for k, v in cluster_avg.items()}}

    # ─────────────────────────────────────────────
    # 2. EXPONENTIAL SMOOTHING FORECASTING
    # ─────────────────────────────────────────────
    def forecast_waste(self, consumption_logs, periods=7):
        """Simple Exponential Smoothing to forecast waste trends."""
        if len(consumption_logs) < 3:
            return {'forecast': [], 'summary': 'Need at least 3 data points for forecasting.'}

        waste_values = [log['wastage_percent'] for log in consumption_logs]
        loss_values = [log['total_loss'] for log in consumption_logs]

        alpha = 0.3  # Smoothing factor

        # Forecast waste percentage
        smoothed_waste = [waste_values[0]]
        for i in range(1, len(waste_values)):
            smoothed_waste.append(alpha * waste_values[i] + (1 - alpha) * smoothed_waste[-1])

        # Forecast loss
        smoothed_loss = [loss_values[0]]
        for i in range(1, len(loss_values)):
            smoothed_loss.append(alpha * loss_values[i] + (1 - alpha) * smoothed_loss[-1])

        # Project forward
        forecast = []
        last_waste = smoothed_waste[-1]
        last_loss = smoothed_loss[-1]
        trend_waste = (smoothed_waste[-1] - smoothed_waste[0]) / len(smoothed_waste) if len(smoothed_waste) > 1 else 0
        trend_loss = (smoothed_loss[-1] - smoothed_loss[0]) / len(smoothed_loss) if len(smoothed_loss) > 1 else 0

        for i in range(1, periods + 1):
            pred_waste = max(0, last_waste + trend_waste * i + np.random.normal(0, 0.5))
            pred_loss = max(0, last_loss + trend_loss * i + np.random.normal(0, 20))
            forecast.append({
                'day': f'Day +{i}',
                'predicted_waste_pct': round(pred_waste, 1),
                'predicted_loss': round(pred_loss, 2)
            })

        direction = 'increasing ⬆️' if trend_waste > 0.5 else ('decreasing ⬇️' if trend_waste < -0.5 else 'stable ➡️')
        summary = f"Waste trend is {direction}. Current smoothed rate: {round(smoothed_waste[-1], 1)}%. "
        if trend_waste > 0.5:
            summary += "⚠️ Action required: Waste is trending upward."
        elif trend_waste < -0.5:
            summary += "✅ Good progress: Waste is declining."

        return {
            'forecast': forecast,
            'trend_direction': direction,
            'current_smoothed_rate': round(smoothed_waste[-1], 1),
            'summary': summary
        }

    # ─────────────────────────────────────────────
    # 3. Z-SCORE ANOMALY DETECTION
    # ─────────────────────────────────────────────
    def detect_anomalies(self, consumption_logs, threshold=1.5):
        """Detect anomalous waste events using Z-Score method."""
        if len(consumption_logs) < 3:
            return {'anomalies': [], 'summary': 'Need at least 3 records for anomaly detection.'}

        waste_values = [log['wastage_percent'] for log in consumption_logs]
        mean_w = np.mean(waste_values)
        std_w = np.std(waste_values) if np.std(waste_values) > 0 else 1

        anomalies = []
        for i, log in enumerate(consumption_logs):
            z = (log['wastage_percent'] - mean_w) / std_w
            if abs(z) > threshold:
                anomalies.append({
                    'date': log['date'],
                    'meal_type': log['meal_type'],
                    'items': log['items'],
                    'wastage_percent': log['wastage_percent'],
                    'z_score': round(z, 2),
                    'severity': '🔴 Critical' if abs(z) > 2.5 else '🟠 Warning',
                    'direction': 'Unusually HIGH waste' if z > 0 else 'Unusually LOW waste'
                })

        summary = f"Scanned {len(consumption_logs)} records. Found {len(anomalies)} anomalies (Z-score > {threshold}). "
        if anomalies:
            worst = max(anomalies, key=lambda x: abs(x['z_score']))
            summary += f"Most critical: {worst['meal_type']} on {worst['date']} ({worst['wastage_percent']}% waste, Z={worst['z_score']})."
        else:
            summary += "✅ All waste levels are within normal statistical bounds."

        return {'anomalies': anomalies, 'mean': round(mean_w, 1), 'std': round(std_w, 1), 'summary': summary}

    # ─────────────────────────────────────────────
    # 4. TF-IDF FEEDBACK ANALYSIS
    # ─────────────────────────────────────────────
    def _compute_tfidf(self, documents):
        """Compute TF-IDF from scratch without sklearn."""
        # Tokenize
        tokenized = []
        for doc in documents:
            tokens = re.findall(r'\b[a-zA-Z]{3,}\b', doc.lower())
            tokenized.append(tokens)

        # Build vocabulary
        vocab = sorted(set(word for doc in tokenized for word in doc))
        if not vocab:
            return [], {}

        word_to_idx = {w: i for i, w in enumerate(vocab)}
        n_docs = len(tokenized)
        n_words = len(vocab)

        # Compute TF
        tf = np.zeros((n_docs, n_words))
        for i, doc in enumerate(tokenized):
            counter = Counter(doc)
            total = len(doc) if doc else 1
            for word, count in counter.items():
                if word in word_to_idx:
                    tf[i][word_to_idx[word]] = count / total

        # Compute IDF
        idf = np.zeros(n_words)
        for j in range(n_words):
            doc_count = sum(1 for i in range(n_docs) if tf[i][j] > 0)
            idf[j] = math.log((n_docs + 1) / (doc_count + 1)) + 1

        tfidf = tf * idf
        return tfidf, vocab

    def analyze_feedback(self, feedbacks):
        """Analyze student feedback using TF-IDF to find top complaint themes."""
        if not feedbacks:
            return {'top_keywords': [], 'themes': [], 'summary': 'No feedback data available.'}

        reasons = [f['reason'] for f in feedbacks if f.get('reason')]
        if not reasons:
            return {'top_keywords': [], 'themes': [], 'summary': 'No textual feedback found.'}

        tfidf, vocab = self._compute_tfidf(reasons)
        if not vocab:
            return {'top_keywords': [], 'themes': [], 'summary': 'Feedback too short for analysis.'}

        # Get top keywords by total TF-IDF score
        word_scores = tfidf.sum(axis=0)
        top_indices = np.argsort(word_scores)[-10:][::-1]
        top_keywords = [{'word': vocab[i], 'score': round(float(word_scores[i]), 3)} for i in top_indices]

        # Stopwords to filter out
        stopwords = {'the', 'and', 'for', 'was', 'this', 'that', 'with', 'not', 'too', 'are', 'its', 'has', 'had', 'have', 'will', 'but'}
        top_keywords = [kw for kw in top_keywords if kw['word'] not in stopwords][:8]

        # Extract complaint themes
        theme_map = {
            'quality': ['poor', 'bad', 'taste', 'quality', 'stale', 'cold', 'undercooked', 'overcooked', 'bland'],
            'preference': ['like', 'prefer', 'want', 'hate', 'allergic', 'allergies', 'vegetarian', 'vegan'],
            'variety': ['repetitive', 'same', 'boring', 'twice', 'again', 'variety'],
            'quantity': ['less', 'more', 'small', 'insufficient', 'portion'],
            'health': ['oily', 'spicy', 'unhealthy', 'stomach', 'sick', 'health'],
            'external': ['outside', 'friends', 'home', 'going', 'weekend', 'holiday', 'willing']
        }

        theme_counts = {}
        all_text = ' '.join(reasons).lower()
        for theme, keywords in theme_map.items():
            count = sum(1 for kw in keywords if kw in all_text)
            if count > 0:
                theme_counts[theme] = count

        themes = [{'theme': k.title(), 'strength': v} for k, v in sorted(theme_counts.items(), key=lambda x: -x[1])]

        summary = f"Analyzed {len(reasons)} student feedback entries. "
        if themes:
            top_theme = themes[0]['theme']
            summary += f"Top complaint theme: '{top_theme}'. "
        if top_keywords:
            summary += f"Most mentioned keywords: {', '.join([kw['word'] for kw in top_keywords[:5]])}."

        return {'top_keywords': top_keywords, 'themes': themes, 'summary': summary}

    # ─────────────────────────────────────────────
    # 5. SMART RECOMMENDATION ENGINE
    # ─────────────────────────────────────────────
    def generate_smart_recommendations(self, consumption_logs, feedbacks):
        """Generate AI-powered recommendations combining all data signals."""
        recommendations = []

        if not consumption_logs:
            return [{'type': 'info', 'icon': 'ℹ️', 'title': 'No Data', 'text': 'Start recording consumption data to receive AI recommendations.', 'priority': 'low'}]

        # 1. Overall waste analysis
        avg_waste = np.mean([l['wastage_percent'] for l in consumption_logs])
        total_loss = sum(l['total_loss'] for l in consumption_logs)

        if avg_waste > 20:
            recommendations.append({
                'type': 'critical', 'icon': '🚨', 'priority': 'critical',
                'title': 'Critical Waste Alert',
                'text': f'Average waste rate is {round(avg_waste, 1)}%, which is dangerously high. Immediate action required: Reduce all preparation quantities by 15-25% across the board.'
            })
        elif avg_waste > 12:
            recommendations.append({
                'type': 'warning', 'icon': '⚠️', 'priority': 'high',
                'title': 'High Waste Warning',
                'text': f'Average waste rate is {round(avg_waste, 1)}%. Target is below 10%. Focus on the meal types with highest individual waste.'
            })
        else:
            recommendations.append({
                'type': 'success', 'icon': '✅', 'priority': 'low',
                'title': 'Good Performance',
                'text': f'Average waste rate is {round(avg_waste, 1)}%, which is within acceptable limits. Continue current practices.'
            })

        # 2. Meal-type specific analysis
        meal_waste = {}
        for log in consumption_logs:
            mt = log['meal_type']
            if mt not in meal_waste:
                meal_waste[mt] = []
            meal_waste[mt].append(log['wastage_percent'])

        for mt, wastes in meal_waste.items():
            avg_mt = np.mean(wastes)
            if avg_mt > 18:
                recommendations.append({
                    'type': 'warning', 'icon': '🍽️', 'priority': 'high',
                    'title': f'{mt} Optimization Needed',
                    'text': f'{mt} has an average waste of {round(avg_mt, 1)}%. Consider reducing portion sizes or switching to more popular dishes for this meal slot.'
                })

        # 3. Cost saving opportunities
        if total_loss > 5000:
            potential_saving = round(total_loss * 0.3, 0)
            recommendations.append({
                'type': 'insight', 'icon': '💰', 'priority': 'medium',
                'title': 'Cost Saving Opportunity',
                'text': f'Total financial loss: ₹{round(total_loss, 0)}. By implementing AI predictions consistently, estimated savings: ₹{potential_saving}/period.'
            })

        # 4. Feedback-driven recommendations
        if feedbacks:
            feedback_analysis = self.analyze_feedback(feedbacks)
            if feedback_analysis['themes']:
                top = feedback_analysis['themes'][0]
                recommendations.append({
                    'type': 'insight', 'icon': '📊', 'priority': 'medium',
                    'title': f'Student Sentiment: {top["theme"]}',
                    'text': f'Dominant complaint theme from students is "{top["theme"]}". Address this to improve meal acceptance and reduce No-votes.'
                })

        # 5. Forecast-based recommendation
        forecast = self.forecast_waste(consumption_logs, periods=3)
        if forecast.get('forecast'):
            next_waste = forecast['forecast'][0]['predicted_waste_pct']
            if next_waste > 15:
                recommendations.append({
                    'type': 'prediction', 'icon': '🔮', 'priority': 'high',
                    'title': 'Forecast Alert',
                    'text': f'AI predicts next meal waste at ~{next_waste}%. Proactively reduce preparation quantity by {round(next_waste * 0.4, 0)} kg.'
                })

        # 6. Anomaly-based
        anomalies = self.detect_anomalies(consumption_logs)
        if anomalies['anomalies']:
            recommendations.append({
                'type': 'anomaly', 'icon': '🔍', 'priority': 'high',
                'title': f'{len(anomalies["anomalies"])} Anomalies Detected',
                'text': f'Statistical outliers found in waste data. {anomalies["summary"]}'
            })

        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda r: priority_order.get(r['priority'], 4))

        return recommendations

    # ─────────────────────────────────────────────
    # 6. AI CHATBOT (NLP Pattern Matching)
    # ─────────────────────────────────────────────
    def chat(self, message, consumption_logs, feedbacks, menu_data=None, role='admin', student_id=None, vote_stats=None):

        """Process user message and return intelligent response using NLP pattern matching."""
        from datetime import datetime, timedelta
        msg = message.lower().strip()
        response = {'text': '', 'type': 'text', 'data': None}

        today_str = datetime.now().strftime('%Y-%m-%d')
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        today_label = datetime.now().strftime('%A, %B %d')
        tomorrow_label = (datetime.now() + timedelta(days=1)).strftime('%A, %B %d')

        # ════════════════════════════════════════════════
        # STUDENT BRANCH — All student-focused NLP intents
        # ════════════════════════════════════════════════
        if role == 'student':

            # ── Student Greeting
            if any(w in msg for w in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'good afternoon']):
                response['text'] = (
                    "👋 **Hi there! I'm your WasteZero Hostel Assistant.**\n\n"
                    "Here's what I can help you with:\n\n"
                    "🍽️ **Today's Menu** — *\"What's for breakfast today?\"*\n"
                    "📅 **Tomorrow's Menu** — *\"What's on the menu tomorrow?\"*\n"
                    "👥 **Vote Stats** — *\"How many students are eating today?\"*\n"
                    "🗳️ **Voting Help** — *\"How do I skip a meal?\"*\n"
                    "💡 **Diet Tips** — *\"Give me some healthy eating advice\"*\n"
                    "❓ **Project Info** — *\"What is this system?\"*\n\n"
                    "*Ask me anything and I'll help you out!*"
                )
                return response

            # ── STUDENT: Role-guard admin-only questions
            admin_only_keywords = ['report', 'anomal', 'z-score', 'cluster', 'financial loss', 'total loss',
                                   'waste analytics', 'consumption log', 'forecast waste', 'generate report',
                                   'kpi', 'wastage percent', 'admin']
            if any(kw in msg for kw in admin_only_keywords):
                response['text'] = (
                    "🔒 **That's an admin-level feature!**\n\n"
                    "I'm set up to assist **students** like you. "
                    "Waste analytics, reports, and anomaly detection are managed by the hostel admin.\n\n"
                    "Here's what I *can* help you with:\n"
                    "• 🍽️ Today's or tomorrow's menu\n"
                    "• 👥 How many students are voting to eat\n"
                    "• 💡 Healthy eating tips\n"
                    "• 🗳️ How to vote or skip a meal\n\n"
                    "Type **help** to see all my features!"
                )
                return response

            # ── STUDENT: TODAY'S MENU
            if (any(w in msg for w in ['today', 'todays', "today's", 'now', 'current'])
                    and any(w in msg for w in ['menu', 'food', 'meal', 'breakfast', 'lunch', 'dinner', 'snack', 'eating', 'serve', 'dish'])):
                if menu_data:
                    today_menus = [m for m in menu_data if m['date'] == today_str]
                    if today_menus:
                        response['text'] = f"🍽️ **Today's Menu — {today_label}**\n\n"
                        for m in today_menus:
                            icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                            response['text'] += f"{icon} **{m['meal_type']}**\n"
                            response['text'] += f"   📋 {m['items']}\n"
                            if m.get('event_type') and m['event_type'] != 'Normal':
                                response['text'] += f"   🎉 *{m['event_type']} Special*\n"
                            response['text'] += "\n"
                        response['text'] += "💡 *Don't forget to cast your vote to help the kitchen plan better!*"
                    else:
                        response['text'] = (
                            f"📅 **No menu is published for today ({today_label}) yet.**\n\n"
                            "Check back soon — the admin usually publishes menus a day in advance.\n"
                            "You can ask me about **tomorrow's menu** too!"
                        )
                else:
                    response['text'] = "No menu data is available right now. Please check back shortly."
                return response

            # ── STUDENT: TOMORROW'S MENU
            if any(w in msg for w in ['tomorrow', 'tmrw', 'next day', "tomorrow's"]):
                if menu_data:
                    tomorrow_menus = [m for m in menu_data if m['date'] == tomorrow_str]
                    if tomorrow_menus:
                        response['text'] = f"📅 **Tomorrow's Menu — {tomorrow_label}**\n\n"
                        for m in tomorrow_menus:
                            icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                            response['text'] += f"{icon} **{m['meal_type']}**\n"
                            response['text'] += f"   📋 {m['items']}\n"
                            if m.get('event_type') and m['event_type'] != 'Normal':
                                response['text'] += f"   🎉 *{m['event_type']} Special*\n"
                            response['text'] += "\n"
                        response['text'] += "🗳️ *You can vote Yes/No for each meal on this page. Your vote helps the kitchen prepare the right amount!*"
                    else:
                        response['text'] = (
                            f"📅 **No menu has been published for tomorrow ({tomorrow_label}) yet.**\n\n"
                            "The admin will publish it soon. You'll be able to vote once it goes live.\n"
                            "Want to know about **today's menu** instead?"
                        )
                else:
                    response['text'] = "No menu data is available right now. Please check back shortly."
                return response

            # ── STUDENT: GENERAL MENU / SCHEDULE
            if any(w in msg for w in ['menu', 'schedule', 'upcoming', 'what is for', "what's for", 'what are we having']):
                if menu_data:
                    upcoming = [m for m in menu_data if m['date'] >= today_str][:6]
                    past = [m for m in menu_data if m['date'] < today_str][:3]
                    show = upcoming if upcoming else past
                    response['text'] = "📋 **Upcoming Menu Schedule**\n\n"
                    for m in show:
                        if m['date'] == today_str:
                            date_label = "📍 Today"
                        elif m['date'] == tomorrow_str:
                            date_label = "🔜 Tomorrow"
                        else:
                            date_label = f"📅 {m['date']}"
                        icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                        response['text'] += f"{date_label} — {icon} **{m['meal_type']}**: {m['items']}\n"
                    response['text'] += "\n🗳️ *Don't forget to cast your vote on the menu cards above!*"
                else:
                    response['text'] = "No menus have been published yet. Check back soon!"
                return response

            # ── STUDENT: VOTE STATS (who's eating / how many)
            if any(w in msg for w in ['how many', 'who', 'eating', 'others', 'students eating',
                                       'vote count', 'votes', 'yes votes', 'popular', 'majority']):
                if vote_stats:
                    today_stats = [s for s in vote_stats if s.get('date') == today_str]
                    tomorrow_stats = [s for s in vote_stats if s.get('date') == tomorrow_str]
                    show_stats = today_stats if today_stats else tomorrow_stats
                    label = today_label if today_stats else tomorrow_label

                    if show_stats:
                        response['text'] = f"👥 **Student Vote Summary — {label}**\n\n"
                        for s in show_stats:
                            icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(s['meal_type'], '🍽️')
                            total = s['yes'] + s['no']
                            pct = round(s['yes'] / total * 100) if total > 0 else 0
                            response['text'] += (
                                f"{icon} **{s['meal_type']}**\n"
                                f"   ✅ Eating: **{s['yes']}** students ({pct}%)\n"
                                f"   ❌ Skipping: **{s['no']}** students\n\n"
                            )
                        response['text'] += "💡 *Your vote matters — it helps the kitchen prepare just the right amount!*"
                    else:
                        response['text'] = (
                            "👥 **No votes have been cast yet** for today or tomorrow.\n\n"
                            "Be the first to vote on the menu cards above! Your vote helps reduce food waste."
                        )
                else:
                    response['text'] = (
                        "👥 **Vote stats aren't available right now.**\n\n"
                        "Head to the menu cards on this page to see the voting options and cast your own vote!"
                    )
                return response

            # ── STUDENT: SHOULD I EAT / VOTING RECOMMENDATION
            if any(w in msg for w in ['should i', 'worth it', 'worth eating', 'recommend', 'suggestion',
                                       'good meal', 'is it good', 'skip or eat', 'eat or skip']):
                if menu_data:
                    today_menus = [m for m in menu_data if m['date'] == today_str]
                    tomorrow_menus = [m for m in menu_data if m['date'] == tomorrow_str]
                    show = today_menus or tomorrow_menus
                    label = today_label if today_menus else tomorrow_label
                    if show:
                        response['text'] = f"🤔 **Should you eat? Here's my take for {label}:**\n\n"
                        for m in show:
                            event = m.get('event_type', 'Normal')
                            items_lower = m['items'].lower()
                            is_special = event != 'Normal'
                            # Simple heuristic scoring
                            positive_words = ['biryani', 'paneer', 'gulab', 'kheer', 'ice cream',
                                              'naan', 'halwa', 'pulao', 'tikka', 'lassi']
                            score = sum(1 for w in positive_words if w in items_lower)
                            icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                            if is_special:
                                verdict = "⭐ **Highly Recommended** — it's a special occasion meal!"
                            elif score >= 2:
                                verdict = "👍 **Looks great!** Seems like a popular menu choice."
                            elif score == 1:
                                verdict = "😊 **Decent meal.** Worth eating if you're hungry!"
                            else:
                                verdict = "🤷 **Standard meal.** Vote based on your preference."
                            response['text'] += f"{icon} **{m['meal_type']}**: {m['items']}\n   → {verdict}\n\n"
                        response['text'] += "🗳️ *Cast your vote on the menu cards — it only takes a second!*"
                    else:
                        response['text'] = "No menu is published yet for today or tomorrow. Check back soon!"
                else:
                    response['text'] = "No menu data is available to make a recommendation right now."
                return response

            # ── STUDENT: HOW TO VOTE / SKIP
            if any(w in msg for w in ['how to vote', 'how do i vote', 'how to skip', 'voting', 'skip meal',
                                       'cancel meal', 'opt out', 'submit vote', 'what is voting']):
                response['text'] = (
                    "🗳️ **How to Vote / Skip a Meal:**\n\n"
                    "**To confirm you're eating:**\n"
                    "1️⃣ Find the meal card on this page\n"
                    "2️⃣ Click the **✅ Yes, eating** button\n"
                    "3️⃣ Done! The kitchen will count you in.\n\n"
                    "**To skip a meal:**\n"
                    "1️⃣ Click the **👎 Will Skip** button\n"
                    "2️⃣ Enter a reason (e.g. allergies, going out)\n"
                    "3️⃣ Click **Submit Cancellation**\n\n"
                    "💡 *Your reason helps the admin understand why food gets wasted — "
                    "so they can improve the menu for everyone!*\n\n"
                    "⚠️ *Each meal can only be voted on once.*"
                )
                return response

            # ── STUDENT: DIETARY ADVICE / HEALTH TIPS
            if any(w in msg for w in ['diet', 'healthy', 'nutrition', 'health', 'calories', 'protein',
                                       'suggestion', 'advice', 'tip', 'oily', 'spicy', 'avoid',
                                       'vegetarian', 'vegan', 'allergic', 'allergy', 'meal suggestion']):
                response['text'] = (
                    "💡 **Healthy Eating Tips for Hostel Life:**\n\n"
                    "🥗 **Balance your plate** — aim for carbs (rice/roti), protein (dal/eggs/paneer), and veggies every meal\n\n"
                    "💧 **Hydrate well** — drink water before and with your meals, not just cold drinks\n\n"
                    "🌅 **Don't skip breakfast** — it powers your focus for morning classes\n\n"
                    "🍛 **Oily/spicy food?** — have curd or raita alongside to balance it\n\n"
                    "🥛 **Dairy allergies?** — mention it when voting 'Skip' so the admin notes your preference\n\n"
                    "🌙 **Light dinner** — lighter meals at night (dal, sabzi, roti) improve sleep quality\n\n"
                    "♻️ **Reduce waste** — only vote 'Yes' if you plan to eat. It saves food and money!\n\n"
                    "*Have a specific dietary question? Type it out and I'll help!*"
                )
                return response

            # ── STUDENT: WHAT IS THIS SYSTEM / PROJECT INFO
            if any(w in msg for w in ['what is this', 'what is wastezero', 'how does this work',
                                       'about this', 'this system', 'this app', 'purpose', 'why vote',
                                       'what is the point', 'explain']):
                response['text'] = (
                    "🏫 **About WasteZero — Smart Hostel Food Management**\n\n"
                    "WasteZero is an AI-powered system that helps your hostel **reduce food waste** "
                    "by predicting exactly how much food needs to be cooked each day.\n\n"
                    "**🎯 How it works:**\n"
                    "1. Admin publishes the menu in advance\n"
                    "2. **You vote** Yes/No for each meal\n"
                    "3. The AI uses your votes + historical data to predict the right quantity\n"
                    "4. Kitchen prepares just the right amount — less waste, fresher food!\n\n"
                    "**📊 Behind the scenes:**\n"
                    "• **XGBoost** — predicts optimal food quantity\n"
                    "• **K-Means Clustering** — groups meal waste patterns\n"
                    "• **Exponential Smoothing** — forecasts waste trends\n"
                    "• **Z-Score Detection** — spots unusual waste spikes\n"
                    "• **TF-IDF Analysis** — analyses your feedback for themes\n\n"
                    "**Your vote directly reduces food waste. Every click counts! 🌱**"
                )
                return response

            # ── STUDENT: CAPABILITIES / HELP
            if any(w in msg for w in ['what can you', 'help', 'capabilities', 'features',
                                       'what do you', 'commands', 'options']):
                response['text'] = (
                    "🤖 **WasteZero Student Assistant — What I can do:**\n\n"
                    "1️⃣ **Today's Menu** — *\"What's for breakfast today?\"*\n"
                    "2️⃣ **Tomorrow's Menu** — *\"What's on the menu tomorrow?\"*\n"
                    "3️⃣ **Vote Stats** — *\"How many students are eating today?\"*\n"
                    "4️⃣ **Meal Recommendation** — *\"Should I eat today?\"*, *\"Worth eating?\"*\n"
                    "5️⃣ **Voting Help** — *\"How do I skip a meal?\"*\n"
                    "6️⃣ **Diet Tips** — *\"Give me healthy eating advice\"*\n"
                    "7️⃣ **About the System** — *\"How does WasteZero work?\"*\n\n"
                    "*Try the quick-action buttons above or just type your question!*"
                )
                return response

            # ── STUDENT: DEFAULT / UNKNOWN
            response['text'] = (
                "🤔 **I didn't quite get that!** Here are things you can ask me:\n\n"
                "• *\"What's for lunch today?\"*\n"
                "• *\"Tomorrow's menu\"*\n"
                "• *\"How many students are eating?\"*\n"
                "• *\"Should I eat lunch?\"*\n"
                "• *\"How do I skip a meal?\"*\n"
                "• *\"Give me diet tips\"*\n"
                "• *\"What is WasteZero?\"*\n\n"
                "Type **help** to see all my features!"
            )
            return response

        # ════════════════════════════════════════════════
        # ADMIN BRANCH — All original admin NLP intents
        # ════════════════════════════════════════════════

        # ── Greetings
        if any(w in msg for w in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'good afternoon']):
            response['text'] = (
                "👋 **Hello, Admin! Welcome to WasteZero AI.**\n\n"
                "Here's what I can help you with:\n\n"
                "🍽️ **Today's / Tomorrow's Menu** — *\"What's for lunch tomorrow?\"*\n"
                "📊 **Waste Analysis** — *\"What's the average waste this week?\"*\n"
                "🔮 **Forecast** — *\"Predict next week's waste trend\"*\n"
                "🔍 **Anomalies** — *\"Show me any unusual waste spikes\"*\n"
                "💡 **Recommendations** — *\"How can we reduce waste?\"*\n"
                "📝 **Student Feedback** — *\"Top student complaints\"*\n"
                "📋 **Reports** — *\"Generate weekly report\"*\n\n"
                "*Type your question below and I'll answer instantly.*"
            )
            return response

        # ── TODAY'S MENU
        if any(w in msg for w in ['today', 'todays', "today's"]) and any(w in msg for w in ['menu', 'food', 'meal', 'breakfast', 'lunch', 'dinner', 'snack', 'eating', 'scheduled', 'serve', 'dish']):
            if menu_data:
                today_menus = [m for m in menu_data if m['date'] == today_str]
                if today_menus:
                    response['text'] = f"🍽️ **Today's Menu — {today_label}**\n\n"
                    for m in today_menus:
                        icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                        response['text'] += f"{icon} **{m['meal_type']}**\n"
                        response['text'] += f"   📋 {m['items']}\n"
                        if m.get('event_type') and m['event_type'] != 'Normal':
                            response['text'] += f"   🎉 *{m['event_type']} Special*\n"
                        response['text'] += "\n"
                else:
                    response['text'] = f"📅 No menus are currently published for today ({today_label}). Please publish a menu from the Menu Planning tab."
            else:
                response['text'] = "No menu data is available at the moment."
            return response

        # ── TOMORROW'S MENU
        if any(w in msg for w in ['tomorrow', 'tmrw', 'next day', "tomorrow's"]):
            if menu_data:
                tomorrow_menus = [m for m in menu_data if m['date'] == tomorrow_str]
                if tomorrow_menus:
                    response['text'] = f"🍽️ **Tomorrow's Menu — {tomorrow_label}**\n\n"
                    for m in tomorrow_menus:
                        icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                        response['text'] += f"{icon} **{m['meal_type']}**\n"
                        response['text'] += f"   📋 {m['items']}\n"
                        if m.get('event_type') and m['event_type'] != 'Normal':
                            response['text'] += f"   🎉 *{m['event_type']} Special*\n"
                        response['text'] += "\n"
                    response['text'] += "💡 *Use the AI Prediction tab to estimate the optimal preparation quantity for each meal.*"
                else:
                    response['text'] = (
                        f"📅 **No menu has been published for tomorrow ({tomorrow_label}) yet.**\n\n"
                        "You can publish tomorrow's menu from the **Menu Planning** tab.\n"
                        "Students will be able to vote once the menu is live."
                    )
            else:
                response['text'] = "No menu data is available at the moment."
            return response

        # ── MENU / UPCOMING SCHEDULE (general)
        if any(w in msg for w in ['menu', 'upcoming', 'scheduled', 'schedule', 'what is for', 'what\'s for']):
            if menu_data:
                # Show most recent / upcoming menus
                upcoming = [m for m in menu_data if m['date'] >= today_str][:6]
                past = [m for m in menu_data if m['date'] < today_str][:4]
                show = upcoming if upcoming else past
                response['text'] = "📅 **Published Menu Schedule**\n\n"
                for m in show:
                    date_label = "📍 Today" if m['date'] == today_str else ("🔜 Tomorrow" if m['date'] == tomorrow_str else f"📅 {m['date']}")
                    icon = {'Breakfast': '🌅', 'Lunch': '☀️', 'Dinner': '🌙', 'Snacks': '🍪'}.get(m['meal_type'], '🍽️')
                    response['text'] += f"{date_label} — {icon} **{m['meal_type']}**: {m['items']}\n"
            else:
                response['text'] = "No menus have been published yet."
            return response

        # ── WASTE STATISTICS
        if any(w in msg for w in ['waste', 'wastage', 'wasted', 'total waste']):
            if any(w in msg for w in ['today', 'current', 'now', 'latest']):
                if consumption_logs:
                    latest = consumption_logs[-1]
                    response['text'] = (
                        f"📊 **Latest Consumption Record**\n\n"
                        f"• **Date:** {latest['date']} — {latest['meal_type']}\n"
                        f"• **Dishes:** {latest['items']}\n"
                        f"• **Prepared:** {latest['prepared_qty']} kg\n"
                        f"• **Consumed:** {latest['consumed_qty']} kg\n"
                        f"• **Wasted:** {latest['wastage_qty']} kg ({latest['wastage_percent']}%)\n"
                        f"• **Financial Loss:** ₹{latest['total_loss']}\n\n"
                    )
                    if latest['wastage_percent'] > 15:
                        response['text'] += "⚠️ This is above optimal levels. I recommend reducing preparation quantity."
                    else:
                        response['text'] += "✅ Waste is within acceptable range."
                else:
                    response['text'] = "No consumption data recorded yet. Start logging meals to get insights."
                return response

            if any(w in msg for w in ['average', 'avg', 'mean']):
                if consumption_logs:
                    avg_waste = np.mean([l['wastage_percent'] for l in consumption_logs])
                    avg_loss = np.mean([l['total_loss'] for l in consumption_logs])
                    response['text'] = (
                        f"📊 **Average Waste Statistics**\n\n"
                        f"• **Average Waste Rate:** {round(avg_waste, 1)}%\n"
                        f"• **Average Loss per Meal:** ₹{round(avg_loss, 2)}\n"
                        f"• **Total Records Analyzed:** {len(consumption_logs)}\n\n"
                    )
                    if avg_waste > 15:
                        response['text'] += "🚨 Your average waste is significantly high. Review your meal portion strategies."
                    elif avg_waste > 10:
                        response['text'] += "⚠️ There's room for improvement. Use the Demand Predictor to optimize quantities."
                    else:
                        response['text'] += "✅ Excellent! Waste levels are well-managed."
                else:
                    response['text'] = "No data available yet for analysis."
                return response

            if any(w in msg for w in ['highest', 'worst', 'maximum', 'max', 'most']):
                if consumption_logs:
                    worst = max(consumption_logs, key=lambda x: x['wastage_percent'])
                    response['text'] = (
                        f"🔴 **Highest Waste Record**\n\n"
                        f"• **Date:** {worst['date']} — {worst['meal_type']}\n"
                        f"• **Dishes:** {worst['items']}\n"
                        f"• **Waste:** {worst['wastage_percent']}% ({worst['wastage_qty']} kg)\n"
                        f"• **Loss:** ₹{worst['total_loss']}\n\n"
                        f"💡 **Recommendation:** Reduce preparation of similar dishes by 20-30% or revise the menu."
                    )
                else:
                    response['text'] = "No consumption data available."
                return response

            # General waste summary
            if consumption_logs:
                total_waste = sum(l['wastage_qty'] for l in consumption_logs)
                total_loss = sum(l['total_loss'] for l in consumption_logs)
                avg_pct = np.mean([l['wastage_percent'] for l in consumption_logs])
                response['text'] = (
                    f"📊 **Overall Waste Summary**\n\n"
                    f"• **Total Waste:** {round(total_waste, 1)} kg\n"
                    f"• **Average Rate:** {round(avg_pct, 1)}%\n"
                    f"• **Total Financial Loss:** ₹{round(total_loss, 2)}\n"
                    f"• **Records Analyzed:** {len(consumption_logs)}"
                )
            else:
                response['text'] = "No waste data available. Record consumption to start getting insights."
            return response

        # ── FORECAST / PREDICTION
        if any(w in msg for w in ['predict', 'forecast', 'future', 'next week', 'trend']):
            forecast = self.forecast_waste(consumption_logs)
            if forecast['forecast']:
                fc = forecast['forecast'][:5]
                response['text'] = f"🔮 **Waste Forecast (Next {len(fc)} Periods)**\n\n"
                response['text'] += f"📈 **Trend:** {forecast['trend_direction']}\n"
                response['text'] += f"📊 **Current Rate:** {forecast['current_smoothed_rate']}%\n\n"
                for f in fc:
                    emoji = '🔴' if f['predicted_waste_pct'] > 15 else ('🟡' if f['predicted_waste_pct'] > 10 else '🟢')
                    response['text'] += f"{emoji} **{f['day']}:** ~{f['predicted_waste_pct']}% waste (est. loss ₹{f['predicted_loss']})\n"
                response['text'] += f"\n💡 *Based on historical data trends from {len(consumption_logs)} meal records.*"
            else:
                response['text'] = forecast['summary']
            response['type'] = 'forecast'
            response['data'] = forecast
            return response

        # ── ANOMALY DETECTION
        if any(w in msg for w in ['anomal', 'unusual', 'strange', 'spike', 'outlier', 'abnormal']):
            anomalies = self.detect_anomalies(consumption_logs)
            if anomalies['anomalies']:
                response['text'] = f"🔍 **Waste Anomaly Report**\n\n"
                response['text'] += f"📊 Baseline: {anomalies['mean']}% avg waste (σ = {anomalies['std']}%)\n\n"
                for a in anomalies['anomalies']:
                    response['text'] += f"{a['severity']} **{a['date']}** ({a['meal_type']}) — {a['wastage_percent']}% waste\n"
                    response['text'] += f"   → {a['direction']}\n\n"
                response['text'] += "*Based on statistical deviation analysis of your waste data.*"
            else:
                response['text'] = f"✅ **No Anomalies Detected**\n\nAll {len(consumption_logs)} records are within normal statistical bounds (Mean: {anomalies['mean']}%, σ: {anomalies['std']}%)."
            return response

        # ── STUDENT FEEDBACK / COMPLAINTS
        if any(w in msg for w in ['feedback', 'complaint', 'student', 'reason', 'why', 'skip', 'cancel']):
            analysis = self.analyze_feedback(feedbacks)
            response['text'] = f"📝 **Student Feedback Analysis**\n\n"
            if analysis['themes']:
                response['text'] += "**Top Complaint Categories:**\n"
                for t in analysis['themes']:
                    bar = '█' * min(t['strength'], 10)
                    response['text'] += f"• {t['theme']}: {bar} ({t['strength']} signals)\n"
                response['text'] += "\n"
            if analysis['top_keywords']:
                response['text'] += "**Most Mentioned Words in Feedback:**\n"
                for kw in analysis['top_keywords'][:6]:
                    response['text'] += f"• `{kw['word']}` (relevance: {kw['score']})\n"
            response['text'] += f"\n{analysis['summary']}"
            return response

        # ── RECOMMENDATIONS
        if any(w in msg for w in ['recommend', 'suggestion', 'advice', 'improve', 'reduce', 'how to', 'tips', 'optimize']):
            recs = self.generate_smart_recommendations(consumption_logs, feedbacks)
            response['text'] = "💡 **AI-Powered Recommendations**\n\n"
            for rec in recs[:6]:
                response['text'] += f"{rec['icon']} **{rec['title']}** `[{rec['priority'].upper()}]`\n"
                response['text'] += f"   {rec['text']}\n\n"
            response['text'] += "*Generated by the WasteZero AI recommendation engine.*"
            return response

        # ── REPORT GENERATION
        if any(w in msg for w in ['report', 'summary', 'generate report', 'weekly', 'monthly', 'daily']):
            period = 'weekly'
            if 'daily' in msg or 'today' in msg:
                period = 'daily'
            elif 'monthly' in msg or 'month' in msg:
                period = 'monthly'
            report = self.generate_report(consumption_logs, feedbacks, period)
            response['text'] = report['content']
            response['type'] = 'report'
            response['data'] = report
            return response

        # ── CLUSTERING / PATTERNS
        if any(w in msg for w in ['cluster', 'group', 'pattern', 'categor', 'profile']):
            clusters = self.cluster_meals(consumption_logs)
            response['text'] = f"📊 **Meal Consumption Patterns**\n\n{clusters['summary']}\n\n"
            if clusters.get('cluster_averages'):
                response['text'] += "**Pattern Groups:**\n"
                for name, avg in clusters['cluster_averages'].items():
                    response['text'] += f"• {name}: avg waste {avg}%\n"
            if clusters.get('clusters'):
                response['text'] += f"\n**Sample Classifications:**\n"
                for c in clusters['clusters'][:6]:
                    response['text'] += f"• {c['date']} {c['meal_type']}: {c['cluster']} ({c['wastage_percent']}%)\n"
            response['text'] += "\n*Generated by the WasteZero Consumption Pattern Profiler.*"
            return response

        # ── CAPABILITIES / HELP
        if any(w in msg for w in ['what can you', 'help', 'capabilities', 'features', 'what do you', 'commands']):
            response['text'] = (
                "🤖 **WasteZero AI — What I can do:**\n\n"
                "1️⃣ **Today's or Tomorrow's Menu** — *\"What's for breakfast tomorrow?\"*\n"
                "2️⃣ **Waste Analysis** — *\"What's the average waste?\", \"Show me the worst meal\"*\n"
                "3️⃣ **Forecasting** — *\"Predict next week's waste\", \"Show the trend\"*\n"
                "4️⃣ **Anomaly Detection** — *\"Any unusual spikes?\", \"Detect anomalies\"*\n"
                "5️⃣ **Feedback Analysis** — *\"What are top complaints?\", \"Why are students skipping?\"*\n"
                "6️⃣ **Recommendations** — *\"How to reduce waste?\", \"Give me suggestions\"*\n"
                "7️⃣ **Reports** — *\"Generate weekly report\", \"Show daily summary\"*\n"
                "8️⃣ **Patterns** — *\"Group meals by waste pattern\"*\n\n"
                "*Try any of the above or use the quick-prompt chips above!*"
            )
            return response

        # ── DEFAULT / UNKNOWN
        response['text'] = (
            "🤔 I didn't quite catch that. Here are some things you can ask me:\n\n"
            "• *\"What's on the menu for tomorrow?\"*\n"
            "• *\"Today's menu\"*\n"
            "• *\"What is the average waste percentage?\"*\n"
            "• *\"Predict future waste\"*\n"
            "• *\"Show anomalies\"*\n"
            "• *\"Top student complaints\"*\n"
            "• *\"How to reduce waste?\"*\n"
            "• *\"Generate weekly report\"*\n\n"
            "Type **help** to see all my capabilities!"
        )
        return response




    # ─────────────────────────────────────────────
    # 7. AUTOMATED REPORT GENERATION
    # ─────────────────────────────────────────────
    def generate_report(self, consumption_logs, feedbacks, period='weekly'):
        """Generate comprehensive AI-powered report."""
        now = datetime.now()

        if period == 'daily':
            title = f"Daily Report — {now.strftime('%B %d, %Y')}"
            scope = consumption_logs[-3:] if consumption_logs else []
        elif period == 'monthly':
            title = f"Monthly Report — {now.strftime('%B %Y')}"
            scope = consumption_logs
        else:
            title = f"Weekly Report — Week of {now.strftime('%B %d, %Y')}"
            scope = consumption_logs[-21:] if consumption_logs else []

        if not scope:
            return {
                'title': title,
                'period': period,
                'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                'content': f"# {title}\n\nNo data available for this period.",
                'summary': 'Insufficient data.'
            }

        # Compute metrics
        total_prepared = sum(l['prepared_qty'] for l in scope)
        total_consumed = sum(l['consumed_qty'] for l in scope)
        total_wastage = sum(l['wastage_qty'] for l in scope)
        total_loss = sum(l['total_loss'] for l in scope)
        avg_waste = np.mean([l['wastage_percent'] for l in scope])
        utilization = (total_consumed / total_prepared * 100) if total_prepared > 0 else 0
        num_meals = len(scope)

        # Best and worst
        best = min(scope, key=lambda x: x['wastage_percent'])
        worst = max(scope, key=lambda x: x['wastage_percent'])

        # Meal type breakdown
        mt_stats = {}
        for l in scope:
            mt = l['meal_type']
            if mt not in mt_stats:
                mt_stats[mt] = {'waste': [], 'loss': []}
            mt_stats[mt]['waste'].append(l['wastage_percent'])
            mt_stats[mt]['loss'].append(l['total_loss'])

        # Forecast
        forecast = self.forecast_waste(scope, periods=3)

        # Anomalies
        anomalies = self.detect_anomalies(scope)

        # Recommendations
        recs = self.generate_smart_recommendations(scope, feedbacks)

        # Build report content
        content = f"""# 📋 {title}
*Generated by WasteZero AI on {now.strftime('%B %d, %Y at %I:%M %p')}*

---

## 📊 Key Performance Indicators

| Metric | Value |
|--------|-------|
| Total Meals Analyzed | {num_meals} |
| Total Food Prepared | {round(total_prepared, 1)} kg |
| Total Food Consumed | {round(total_consumed, 1)} kg |
| Total Food Wasted | {round(total_wastage, 1)} kg |
| Average Waste Rate | {round(avg_waste, 1)}% |
| Food Utilization Rate | {round(utilization, 1)}% |
| Total Financial Loss | ₹{round(total_loss, 2)} |

---

## 🏆 Best & Worst Performing Meals

**🟢 Best Meal:** {best['date']} — {best['meal_type']}
- Dishes: {best['items']}
- Waste: {best['wastage_percent']}% ({best['wastage_qty']} kg)

**🔴 Worst Meal:** {worst['date']} — {worst['meal_type']}
- Dishes: {worst['items']}
- Waste: {worst['wastage_percent']}% ({worst['wastage_qty']} kg)
- Loss: ₹{worst['total_loss']}

---

## 🍽️ Meal-Type Breakdown

"""
        for mt, stats in mt_stats.items():
            avg_mt = round(np.mean(stats['waste']), 1)
            total_mt_loss = round(sum(stats['loss']), 2)
            status = '🔴' if avg_mt > 18 else ('🟡' if avg_mt > 10 else '🟢')
            content += f"- {status} **{mt}**: Avg waste {avg_mt}%, Total loss ₹{total_mt_loss}\n"

        content += f"""
---

## 🔮 AI Forecast

{forecast['summary']}

| Upcoming | Predicted Waste | Est. Loss |
|----------|----------------|-----------|
"""
        for f in forecast.get('forecast', [])[:5]:
            content += f"| {f['day']} | {f['predicted_waste_pct']}% | ₹{f['predicted_loss']} |\n"

        content += f"""
---

## 🔍 Anomaly Detection

{anomalies['summary']}

"""
        if anomalies['anomalies']:
            for a in anomalies['anomalies']:
                content += f"- {a['severity']} **{a['date']}** ({a['meal_type']}): {a['wastage_percent']}% waste (Z-score: {a['z_score']})\n"
        else:
            content += "✅ No anomalies detected.\n"

        content += f"""
---

## 💡 AI Recommendations

"""
        for rec in recs[:5]:
            content += f"### {rec['icon']} {rec['title']}\n{rec['text']}\n\n"

        content += f"""---

*This report was automatically generated by WasteZero Agentic AI. For questions, use the AI Chat Assistant.*
"""

        summary_text = f"{period.title()} report: {num_meals} meals analyzed, {round(avg_waste, 1)}% avg waste, ₹{round(total_loss, 2)} total loss."

        return {
            'title': title,
            'period': period,
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'content': content,
            'summary': summary_text,
            'metrics': {
                'total_prepared': round(total_prepared, 1),
                'total_consumed': round(total_consumed, 1),
                'total_wastage': round(total_wastage, 1),
                'total_loss': round(total_loss, 2),
                'avg_waste': round(avg_waste, 1),
                'utilization': round(utilization, 1),
                'num_meals': num_meals
            }
        }
