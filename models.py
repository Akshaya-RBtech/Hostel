import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import joblib

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(120), nullable=True)  # Password for admin, None for students initially
    role = db.Column(db.String(20), nullable=False, default='student')  # 'admin' or 'student'
    student_id = db.Column(db.String(50), unique=True, nullable=True)

class MenuEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # Breakfast, Lunch, Snacks, Dinner
    items = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(20), default='Normal')  # Normal, Festival, Holiday
    published = db.Column(db.Boolean, default=True)
    kitchen_status = db.Column(db.String(50), default='Planned') # Planned, Prep Started, Cooking, Ready, Served

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu_entry.id'), nullable=False)
    choice = db.Column(db.String(10), nullable=False)  # 'Yes' or 'No'
    reason = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

class FoodConsumption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu_entry.id'), unique=True, nullable=False)
    prepared_qty = db.Column(db.Float, nullable=False)
    consumed_qty = db.Column(db.Float, nullable=False)
    wastage_qty = db.Column(db.Float, nullable=False)
    wastage_percent = db.Column(db.Float, nullable=False)
    cost_per_unit = db.Column(db.Float, default=80.0)
    total_loss = db.Column(db.Float, nullable=False)
    recommendations = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    menu = db.relationship('MenuEntry', backref=db.backref('consumption', uselist=False, cascade="all, delete-orphan"))

    def __init__(self, menu_id, prepared_qty, consumed_qty, wastage_qty, wastage_percent, total_loss, recommendations, cost_per_unit=80.0):
        self.menu_id = menu_id
        self.prepared_qty = prepared_qty
        self.consumed_qty = consumed_qty
        self.wastage_qty = wastage_qty
        self.wastage_percent = wastage_percent
        self.cost_per_unit = cost_per_unit
        self.total_loss = total_loss
        self.recommendations = recommendations


# ── AI Report Model ──
class AIReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    period = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    metrics_json = db.Column(db.Text, nullable=True)  # JSON string of KPIs
    generated_at = db.Column(db.DateTime, server_default=db.func.now())


# ── Chat Message Model ──
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(20), default='text')  # 'text', 'report', 'forecast'
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# ── Notifications and Announcements (New Features) ──
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')  # General, Menu, Urgent
    target_audience = db.Column(db.String(50), default='all') # all, specific
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    created_by = db.Column(db.String(80), nullable=True) # admin username

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

# ── Complaints and Leave (New Operations) ──
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Food Quality, Cleanliness, Timing, etc
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open') # Open, In Progress, Resolved, Rejected
    admin_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# ── Inventory & Feedback ──
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False) # kg, L, etc
    min_stock = db.Column(db.Float, default=10.0)
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu_entry.id'), nullable=False)
    rating = db.Column(db.String(20), nullable=False) # Like, Neutral, Dislike
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())


class FoodPredictor:
    def __init__(self, data_path='hostel_food_data.csv', model_path='xgboost_model.joblib'):
        self.data_path = data_path
        self.model_path = model_path
        self.model = None
        self.le_day = LabelEncoder()
        self.le_meal = LabelEncoder()
        self.le_event = LabelEncoder()
        
        # Fit encoders with all possible values to ensure consistency
        self.le_day.fit(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        self.le_meal.fit(['Breakfast', 'Lunch', 'Snacks', 'Dinner'])
        self.le_event.fit(['Normal', 'Festival', 'Holiday'])

    def train(self):
        if not os.path.exists(self.data_path):
            print(f"Data file {self.data_path} not found. Skipping training.")
            return False
        
        df = pd.read_csv(self.data_path)
        
        # Preprocessing
        X = df[['day_of_week', 'meal_type', 'event_type', 'student_yes_count', 'guest_count']]
        y = df['actual_quantity']
        
        X = X.copy()
        X['day_of_week'] = self.le_day.transform(X['day_of_week'])
        X['meal_type'] = self.le_meal.transform(X['meal_type'])
        X['event_type'] = self.le_event.transform(X['event_type'])
        
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        self.model.fit(X, y)
        
        joblib.dump(self.model, self.model_path)
        print("Model trained and saved.")
        return True

    def predict(self, day, meal, event, yes_count, guest_count):
        if self.model is None:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            else:
                self.train()
        
        # In case training failed
        if self.model is None:
            return float(yes_count + guest_count)  # Fallback prediction

        # Encode inputs
        try:
            day_enc = self.le_day.transform([day])[0]
            meal_enc = self.le_meal.transform([meal])[0]
            event_enc = self.le_event.transform([event])[0]
        except ValueError:
            # Handle unknown labels
            return float(yes_count + guest_count)

        features = pd.DataFrame([[day_enc, meal_enc, event_enc, yes_count, guest_count]], 
                                columns=['day_of_week', 'meal_type', 'event_type', 'student_yes_count', 'guest_count'])
        
        prediction = self.model.predict(features)[0]
        return float(prediction)

    def evaluate(self):
        """Evaluate the model using the training data with a simple holdout."""
        if not os.path.exists(self.data_path):
            return {'error': 'No data file found for evaluation.'}
        
        df = pd.read_csv(self.data_path)
        
        if len(df) < 5:
            return {'error': 'Insufficient data for evaluation. Need at least 5 records.'}
        
        X = df[['day_of_week', 'meal_type', 'event_type', 'student_yes_count', 'guest_count']].copy()
        y = df['actual_quantity']
        
        X['day_of_week'] = self.le_day.transform(X['day_of_week'])
        X['meal_type'] = self.le_meal.transform(X['meal_type'])
        X['event_type'] = self.le_event.transform(X['event_type'])
        
        if self.model is None:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            else:
                return {'error': 'No trained model available.'}
        
        y_pred = self.model.predict(X)
        
        mae = round(float(mean_absolute_error(y, y_pred)), 2)
        rmse = round(float(np.sqrt(mean_squared_error(y, y_pred))), 2)
        r2 = round(float(r2_score(y, y_pred)), 4)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'samples': len(df),
            'note': 'Evaluated on training data (small dataset). For production, use time-based train/test split.'
        }
