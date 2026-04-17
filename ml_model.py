import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
import random

# Global variables to hold the trained pipeline
vectorizer = None
best_model = None
model_metrics = {}

templates_data = {
    "auth": {
        "code_template": """from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    # Add authentication logic here
    if username == "admin" and password == "password":
        return jsonify({"message": "Login successful", "token": "abc.123.xyz"}), 200
    return jsonify({"message": "Invalid credentials"}), 401
""",
        "explanation": "This is a basic Flask authentication blueprint for a login endpoint. It accepts a JSON payload with a username and password, validates them, and returns a mock authentication token upon success. In a real application, you would connect this to a database and securely hash passwords.",
        "diagram": """graph TD;
    User -->|POST /login| API_Gateway;
    API_Gateway --> Auth_Service;
    Auth_Service -->|Validate| Database;
    Database -->|User Info| Auth_Service;
    Auth_Service -->|JWT Token| User;"""
    },
    "crud": {
        "code_template": """from flask import Blueprint, request, jsonify

crud_bp = Blueprint('crud', __name__)
items = []

@crud_bp.route('/items', methods=['GET', 'POST'])
def manage_items():
    if request.method == 'GET':
        return jsonify(items), 200
    if request.method == 'POST':
        item = request.json
        items.append(item)
        return jsonify({"message": "Item added successfully", "item": item}), 201
""",
        "explanation": "This snippet demonstrates Create and Read operations (part of CRUD) in a Flask application using an in-memory list. It allows fetching all items via a GET request and adding new items via a POST request.",
        "diagram": """graph TD;
    Client -->|GET/POST| Web_Server;
    Web_Server --> Router;
    Router -->|GET /items| Read_Logic;
    Router -->|POST /items| Create_Logic;
    Read_Logic --> Database;
    Create_Logic --> Database;"""
    },
    "ml": {
        "code_template": """from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Sample training data
X_train = np.array([[0, 0], [1, 1], [1, 0], [0, 1]])
y_train = np.array([0, 1, 1, 0])

# Initialize and train model
model = RandomForestClassifier(n_estimators=10)
model.fit(X_train, y_train)

# Predict
sample = np.array([[1, 0]])
prediction = model.predict(sample)
print(f"Prediction: {prediction[0]}")
""",
        "explanation": "This code initializes a Random Forest Classifier using scikit-learn, trains it on a synthetic dataset, and makes a simple prediction. This template forms the basis for integrating predictive modeling into an application.",
        "diagram": """graph TD;
    Raw_Data --> Data_Preprocessing;
    Data_Preprocessing --> Features;
    Features --> ML_Model;
    ML_Model -->|Train| Model_Artefact;
    New_Input --> Model_Artefact;
    Model_Artefact --> Prediction;"""
    },
    "chat": {
        "code_template": """from flask import Flask, render_template
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('message')
def handle_message(msg):
    print('Message: ' + msg)
    send(msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
""",
        "explanation": "This implements a real-time bi-directional communication channel using WebSockets (via Flask-SocketIO). When a client sends a message, the server broadcasts it to all connected clients, form the basis of a chat application.",
        "diagram": """graph TD;
    User_A -->|WebSocket Send| Socket_Server;
    Socket_Server -->|Broadcast| User_B;
    Socket_Server -->|Broadcast| User_C;"""
    },
    "ecommerce": {
        "code_template": """from flask import Blueprint, request, jsonify

shop_bp = Blueprint('shop', __name__)
cart = {}

@shop_bp.route('/cart/<user_id>', methods=['POST', 'GET'])
def manage_cart(user_id):
    if request.method == 'POST':
        product_id = request.json.get('product_id')
        quantity = request.json.get('quantity', 1)
        if user_id not in cart:
            cart[user_id] = {}
        cart[user_id][product_id] = cart[user_id].get(product_id, 0) + quantity
        return jsonify({"message": "Added to cart", "cart": cart[user_id]}), 200
    
    return jsonify(cart.get(user_id, {})), 200
""",
        "explanation": "A simple ecommerce cart management blueprint. It endpoints for a user to add items to their shopping cart and retrieve their current cart contents, using an in-memory dictionary for storage.",
        "diagram": """graph TD;
    Customer -->|POST /cart/add| Product_Service;
    Product_Service --> Cart_Database;
    Customer -->|GET /cart| Checkout_Service;
    Checkout_Service --> Cart_Database;"""
    },
    "payment": {
        "code_template": """from flask import Blueprint, request, jsonify
import uuid

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/process', methods=['POST'])
def process_payment():
    data = request.json
    amount = data.get('amount')
    card_number = data.get('card_number')
    
    # Mock payment processing
    if amount and card_number:
        transaction_id = str(uuid.uuid4())
        return jsonify({"status": "Success", "transaction_id": transaction_id}), 200
    return jsonify({"status": "Failed", "message": "Invalid details"}), 400
""",
        "explanation": "This demonstrates a mock payment gateway API. It receives credit card details and an amount, simulates processing, and returns a transaction ID on success.",
        "diagram": """graph TD;
    Order_Service -->|Charge Request| Payment_API;
    Payment_API --> Validations;
    Validations -->|Authorize| Bank_Gateway;
    Bank_Gateway -->|Response| Payment_API;
    Payment_API -->|Status Update| Order_Service;"""
    },
    "notification": {
        "code_template": """from flask import Blueprint, request, jsonify
import smtplib

notify_bp = Blueprint('notify', __name__)

@notify_bp.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    recipient = data.get('to')
    message = data.get('message')
    
    # Mock SMTP logic
    try:
        # server = smtplib.SMTP('smtp.example.com', 587)
        # server.sendmail('sender@example.com', recipient, message)
        print(f"Mock email sent to {recipient}: {message}")
        return jsonify({"message": "Email queued successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
""",
        "explanation": "A background notification service blueprint representing logic to send emails or SMS. It accepts recipient and message details and conceptually interfaces with an SMTP server.",
        "diagram": """graph TD;
    Application_Core -->|Trigger Event| Notification_Queue;
    Notification_Queue --> Email_Worker;
    Notification_Queue --> SMS_Worker;
    Email_Worker --> SMTP_Server;
    SMTP_Server --> User_Inbox;"""
    }
}

def generate_dataset():
    data = []
    
    base_auth = ["login system", "authentication api", "user login", "signup page", "auth module", "register user", "password reset", "oauth setup", "jwt token authentication", "user registration"]
    base_crud = ["todo app", "crud operations", "task manager", "create read update delete", "manage records", "database entry app", "item catalog", "inventory management", "post articles", "address book app"]
    base_ml = ["predict marks", "machine learning model", "classification model", "regression analysis", "ai predictor", "image recognition", "sentiment analysis", "data prediction", "neural network training", "nlp pipeline"]
    base_chat = ["chat application", "messaging app", "real-time communication", "websocket server", "group chat", "instant messenger", "live support chat", "video call signaling", "chat room", "message broadcast"]
    base_ecommerce = ["ecommerce store", "shopping cart", "online shop", "product catalog", "add to cart", "purchase items", "retail website", "order management", "product checkout", "digital storefront"]
    base_payment = ["payment gateway", "process credit card", "stripe integration", "paypal checkout", "billing system", "subscription processing", "transaction handler", "invoice generator", "mock payment api", "secure checkout"]
    base_notification = ["email sender", "push notifications", "sms alert system", "notification worker", "sendgrid integration", "alert mechanism", "reminders app", "trigger emails", "background job notifications", "broadcast alerts"]

    # We augment these to reach ~250+ rows by generating variations
    categories = {
        "auth": base_auth,
        "crud": base_crud,
        "ml": base_ml,
        "chat": base_chat,
        "ecommerce": base_ecommerce,
        "payment": base_payment,
        "notification": base_notification
    }
    
    # Generate variations
    prefixes = ["build a", "create", "i need a", "develop an", "setup", "implement", "make a simple", "design a"]
    suffixes = ["using python", "in flask", "for my project", "with rest api", "backend", "module", "service architecture"]

    for category, base_phrases in categories.items():
        for phrase in base_phrases:
            data.append({"text": phrase, "label": category})
            for _ in range(3): # Create 3 variations per base phrase
                pref = random.choice(prefixes)
                suff = random.choice(suffixes)
                variation = f"{pref} {phrase} {suff}"
                data.append({"text": variation, "label": category})

    df = pd.DataFrame(data)
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df['text'].tolist(), df['label'].tolist()

def init_models():
    global vectorizer, best_model, model_metrics
    
    print("Initializing Machine Learning Models...")
    texts, labels = generate_dataset()
    print(f"Generated dataset with {len(texts)} samples.")

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)
    y = np.array(labels)

    # Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Define models
    models = {
        "MultinomialNB": MultinomialNB(),
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "SVM": SVC(kernel='linear')
    }

    best_acc = 0
    best_model_name = ""

    print("--- Model Evaluation ---")
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred).tolist() # Convert to list for JSON serialization
        
        model_metrics[name] = {
            "accuracy": round(acc, 4),
            "confusion_matrix": cm
        }
        
        print(f"{name} Accuracy: {acc:.4f}")
        
        if acc > best_acc:
            best_acc = acc
            best_model_name = name
            best_model = model

    print(f"Selected Best Model: {best_model_name} with Accuracy >= {best_acc:.4f}")
    model_metrics["best_model"] = best_model_name

def predict_category(text):
    if not best_model or not vectorizer:
        init_models()
        
    vectorized_input = vectorizer.transform([text])
    prediction = best_model.predict(vectorized_input)[0]
    
    response_data = dict(templates_data.get(prediction, {}))
    response_data['category'] = prediction
    
    # Adaptive Architecture Recommendation
    word_count = len(text.split())
    if word_count < 3:
        response_data['architecture_type'] = 'Monolithic Architecture'
    else:
        response_data['architecture_type'] = 'Microservices Architecture'
        
    return response_data

def get_metrics():
    if not model_metrics:
        init_models()
    return model_metrics

# Initialize on import for standard operation, but we will let app manage it if needed
init_models()
