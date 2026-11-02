"""Environment configuration and an isolated, disposable portfolio demo."""
import copy
import os
import secrets
import threading
import uuid
from pathlib import Path
from flask import session, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash


def verify_password(stored, supplied):
    if not stored or not stored.startswith(('scrypt:', 'pbkdf2:')):
        return False  # Legacy plaintext accounts must reset their password.
    try:
        return check_password_hash(stored, supplied)
    except (ValueError, TypeError):
        return False


class MemoryDB:
    """Firebase-shaped adapter. Data never leaves the process and resets on restart."""
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()

    def reference(self, path='/'):
        return MemoryRef(self, path)


class MemoryRef:
    def __init__(self, db, path):
        self.db, self.parts = db, [p for p in path.split('/') if p]
        self.key = self.parts[-1] if self.parts else None

    def get(self):
        with self.db.lock:
            data = self.db.data
            for part in self.parts:
                if not isinstance(data, dict):
                    return None
                data = data.get(part)
            return copy.deepcopy(data)

    def set(self, value):
        with self.db.lock:
            if not self.parts:
                self.db.data = copy.deepcopy(value)
                return
            data = self.db.data
            for part in self.parts[:-1]:
                data = data.setdefault(part, {})
            if value is None:
                data.pop(self.key, None)
            else:
                data[self.key] = copy.deepcopy(value)

    def update(self, updates):
        with self.db.lock:
            for key, value in updates.items():
                self.db.reference('/'.join(self.parts + [key])).set(value)

    def delete(self):
        self.set(None)

    def push(self, value=None):
        ref = self.db.reference('/'.join(self.parts + [uuid.uuid4().hex]))
        if value is not None:
            ref.set(value)
        return ref

    def transaction(self, callback):
        with self.db.lock:
            result = callback(self.get())
            self.set(result)
            return copy.deepcopy(result)


def configure(app):
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(app.root_path) / '.env')
    except ImportError:
        pass
    demo = os.getenv('APP_MODE', 'demo') == 'demo'
    secret = os.getenv('SECRET_KEY')
    if not demo and (not secret or len(secret) < 32):
        raise RuntimeError('Set a random SECRET_KEY of at least 32 characters.')
    app.config.update(SECRET_KEY=secret or secrets.token_hex(32), DEMO_MODE=demo,
                      MAX_CONTENT_LENGTH=8 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE') == 'true')
    if demo:
        db = MemoryDB()
        db.data = demo_data()
    else:
        import firebase_admin
        from firebase_admin import credentials, db
        cert = os.getenv('FIREBASE_CREDENTIALS')
        url = os.getenv('FIREBASE_DATABASE_URL')
        if not cert or not url:
            raise RuntimeError('Set FIREBASE_CREDENTIALS and FIREBASE_DATABASE_URL.')
        firebase_admin.initialize_app(credentials.Certificate(cert), {'databaseURL': url})

    def csrf_token():
        if '_csrf' not in session:
            session['_csrf'] = secrets.token_urlsafe(32)
        return session['_csrf']

    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.context_processor
    def runtime_context():
        return {'demo_mode': demo}

    @app.before_request
    def protect_mutations():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
            expected = session.get('_csrf', '')
            if not expected or not secrets.compare_digest(expected, token):
                return jsonify(success=False, message='Your session expired. Reload the page and try again.'), 400

    @app.after_request
    def response_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.route('/demo', methods=['GET', 'POST'])
    def demo_entry():
        if not demo:
            return 'Demo is disabled', 404
        if request.method == 'POST':
            from flask import redirect, url_for
            session.clear()
            session.update(user_id='demo-user', user_email='demo@example.invalid', user_name='Demo Guest')
            return redirect(url_for('user_dashboard'))
        return render_template('demo.html')

    @app.errorhandler(413)
    def too_large(error):
        return render_template('error.html', title='This file is too large', message='Choose an image smaller than 8 MB.'), 413

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', title='Page not found', message='This page may have moved. Let’s get you back to the menu.'), 404

    return db


def demo_data():
    return {
        'users': {'demo-user': {'name': 'Demo Guest', 'email': 'demo@example.invalid', 'status': True,
            'age': '25', 'sex': 'Other', 'city': 'Lahore', 'phone': '', 'address': 'Demo address',
            'diabetes': 'No', 'bp': 'No', 'spice': 'Mild', 'dishes': ['Grilled'], 'father_name': '',
            'password': generate_password_hash(secrets.token_urlsafe(24))}},
        'restaurants': {'demo-kitchen': {'restaurant_name': 'The Green Table', 'owner_name': 'Demo Kitchen',
            'email': 'kitchen@example.invalid', 'status': 'approved', 'city': 'Lahore',
            'address': 'Sample location', 'category': 'Healthy', 'cuisine_type': 'Healthy',
            'description': 'A fictional kitchen for exploring Health Tailor.', 'images': [],
            'phone': '', 'opening_time': '09:00', 'closing_time': '22:00'}},
        'menu': {'demo-kitchen': {
            'bowl': {'name': 'Garden grain bowl', 'description': 'Chickpeas, seasonal vegetables and grains.', 'price': 650,
                'category': 'Main Course', 'spice_level': 'Mild', 'is_available': True, 'image_url': '/static/meal.svg', 'preparation_time': '20 mins'},
            'salad': {'name': 'Citrus chicken salad', 'description': 'Grilled chicken, leafy greens and citrus dressing.', 'price': 750,
                'category': 'Salad', 'spice_level': 'Mild', 'is_available': True, 'image_url': '/static/meal.svg', 'preparation_time': '15 mins'}}},
        'wallets': {'demo-user': {'balance': 5000}},
    }


def get_model():
    # Demo never calls a paid service, even if credentials exist in the environment.
    if os.getenv('APP_MODE', 'demo') == 'demo' or not os.getenv('GEMINI_API_KEY'):
        return None
    from google import genai
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    class Model:
        def generate_content(self, contents):
            return client.models.generate_content(model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'), contents=contents)
    return Model()


def mail_client(*args, **kwargs):
    if os.getenv('APP_MODE', 'demo') == 'demo':
        class DemoMail:
            def send(self, *args, **kwargs):
                return None
        return DemoMail()
    import yagmail
    if not os.getenv('SMTP_USER') or not os.getenv('SMTP_PASSWORD'):
        raise RuntimeError('Email is not configured.')
    return yagmail.SMTP(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
