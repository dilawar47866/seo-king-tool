from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from datetime import datetime
import os, markdown, requests, json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seoking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Use Claude 3 Opus (most widely available model)
CLAUDE_MODEL = "claude-3-haiku-20240307"

def call_claude_api(prompt, max_tokens=3000):
    """Direct API call using requests"""
    print(f"🌐 Calling {CLAUDE_MODEL}...")
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()['content'][0]['text']
    except Exception as e:
        raise Exception(f"API error: {str(e)}")

print("\n" + "="*60)
print("🧪 TESTING API")
print("="*60)
try:
    test_result = call_claude_api("Say 'Ready!'", max_tokens=10)
    print(f"✅ SUCCESS: {test_result}")
    print(f"✅ Using model: {CLAUDE_MODEL}")
    print("="*60 + "\n")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print("="*60 + "\n")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    tier = db.Column(db.String(20), default='free')
    ai_requests_this_month = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contents = db.relationship('Content', backref='author', lazy=True, cascade="all, delete-orphan")
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    def get_limits(self):
        return {'ai_requests_per_month': {'free': 50, 'pro': 500, 'enterprise': 9999}.get(self.tier.lower(), 50)}

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    keyword = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def landing():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else render_template('landing.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    if request.method == 'POST':
        try:
            data = request.get_json() or request.form
            if User.query.filter_by(email=data.get('email').lower()).first():
                return jsonify({'error': 'Email exists'}), 400
            user = User(username=data.get('username'), email=data.get('email').lower(), password_hash=bcrypt.generate_password_hash(data.get('password')).decode('utf-8'))
            if User.query.count() == 0: user.is_admin = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return jsonify({'success': True, 'redirect': '/dashboard'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        user = User.query.filter_by(email=data.get('email').lower()).first()
        if user and user.check_password(data.get('password')):
            login_user(user)
            return jsonify({'success': True, 'redirect': '/dashboard'})
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    recent = Content.query.filter_by(user_id=current_user.id).order_by(Content.updated_at.desc()).limit(5).all()
    return render_template('dashboard.html', recent_content=recent, total_content=Content.query.filter_by(user_id=current_user.id).count(), total_words=db.session.query(db.func.sum(Content.word_count)).filter_by(user_id=current_user.id).scalar() or 0, limits=current_user.get_limits())

@app.route('/editor')
@login_required
def editor():
    content = Content.query.filter_by(id=request.args.get('id'), user_id=current_user.id).first() if request.args.get('id') else None
    return render_template('editor.html', content=content)

@app.route('/api/generate-content', methods=['POST'])
@login_required
def api_generate_content():
    if current_user.ai_requests_this_month >= current_user.get_limits()['ai_requests_per_month']:
        return jsonify({'error': 'Limit reached'}), 403
    try:
        keyword = request.get_json().get('keyword', '').strip()
        if not keyword:
            return jsonify({'error': 'Keyword required'}), 400
        print(f"\n📝 Generating: {keyword}")
        content = call_claude_api(f'Write a comprehensive SEO blog post about "{keyword}". Use H1/H2/H3 headings, 800-1200 words, Markdown format.', 3500)
        word_count = len(content.split())
        print(f"✅ Generated {word_count} words\n")
        current_user.ai_requests_this_month += 1
        db.session.commit()
        return jsonify({'success': True, 'content': content, 'html_content': markdown.markdown(content), 'word_count': word_count})
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-content', methods=['POST'])
@login_required
def api_save_content():
    try:
        data = request.get_json()
        if data.get('id'):
            content = Content.query.get(data.get('id'))
            if content and content.user_id == current_user.id:
                content.title = data.get('title')
                content.content = data.get('content')
                content.keyword = data.get('keyword')
                content.word_count = len(data.get('content', '').split())
                db.session.commit()
                return jsonify({'success': True, 'id': content.id})
        new_content = Content(user_id=current_user.id, title=data.get('title'), content=data.get('content'), keyword=data.get('keyword'), word_count=len(data.get('content', '').split()))
        db.session.add(new_content)
        db.session.commit()
        return jsonify({'success': True, 'id': new_content.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-content/<int:id>', methods=['POST'])
@login_required
def api_delete_content(id):
    try:
        content = Content.query.get_or_404(id)
        if content.user_id == current_user.id:
            db.session.delete(content)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/robots.txt')
def robots_txt():
    return "User-agent: *\nDisallow: /dashboard\nDisallow: /editor", 200, {'Content-Type': 'text/plain'}

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect('/dashboard')
    return render_template('admin.html', users=User.query.order_by(User.id.desc()).all(), total_content=Content.query.count())

@app.errorhandler(404)
def not_found(e): return "<h1>404</h1>", 404
@app.errorhandler(500)
def server_error(e): return "<h1>500</h1>", 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🚀 http://localhost:5001\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
