import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, QueryHistory
import ml_model

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = 'mcs_project_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

# Ensure Database is created
with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/')
def home():
    # Pass user info to template if needed, though we will handle via JS mostly
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    
    return render_template('index.html', user=user)

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
            
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400
            
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        
        return jsonify({"message": "Signup successful", "user": {"id": new_user.id, "username": new_user.username}}), 201
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"error": "An error occurred during signup"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({"message": "Login successful", "user": {"id": user.id, "username": user.username}}), 200
            
        return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "An error occurred during login"}), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/status', methods=['GET'])
def status():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "username": session.get('username')}), 200
    return jsonify({"logged_in": False}), 200

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        problem_statement = data.get('statement', '').strip()
        
        if not problem_statement:
            return jsonify({"error": "No problem statement provided."}), 400
            
        # Get prediction from imported ML model
        response_data = ml_model.predict_category(problem_statement)
        
        # If user is logged in, log the query to history
        if 'user_id' in session:
            try:
                history_entry = QueryHistory(
                    user_id=session['user_id'],
                    input_text=problem_statement,
                    category=response_data.get('category', 'unknown'),
                    architecture=response_data.get('architecture_type', 'unknown')
                )
                db.session.add(history_entry)
                db.session.commit()
            except Exception as db_err:
                print(f"Error saving history: {db_err}")
                db.session.rollback()
                
        return jsonify(response_data), 200
    except Exception as e:
        print(f"Predict error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized. Please log in to view history."}), 401
        
    try:
        queries = QueryHistory.query.filter_by(user_id=session['user_id']).order_by(QueryHistory.timestamp.desc()).all()
        history_list = []
        for q in queries:
            history_list.append({
                "id": q.id,
                "input_text": q.input_text,
                "category": q.category,
                "architecture": q.architecture,
                "timestamp": q.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        return jsonify(history_list), 200
    except Exception as e:
        print(f"History error: {e}")
        return jsonify({"error": "Failed to fetch history"}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    try:
        metrics_data = ml_model.get_metrics()
        return jsonify(metrics_data), 200
    except Exception as e:
        print(f"Metrics error: {e}")
        return jsonify({"error": "Failed to fetch metrics"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
