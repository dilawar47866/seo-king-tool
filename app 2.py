# Backup if exists
mv app.py app_backup.py 2>/dev/null || true

# Create new app.py
cat > app.py << 'ENDOFPYTHON'
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, make_response, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from datetime import datetime
import os
from dotenv import load_dotenv
import anthropic

# Load environment
load_dotenv()

# Initialize Flask
app = Flask(__name__)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///seoking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')

# Email config
app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Anthropic
try:
    anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
except:
    anthropic_client = None
    print("⚠️  Warning: Anthropic API key not set")

# ==========================================
# DATABASE MODELS
# ==========================================
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
        limits = {'free': 50, 'pro': 500, 'enterprise': 9999}
        return {'ai_requests_per_month': limits.get(self.tier.lower(), 50)}

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
    return User.query.get(int(user_id))

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def call_claude(prompt, system_prompt="You are a helpful assistant.", temperature=0.6, max_tokens=3000):
    """Call Claude API with error handling"""
    if not anthropic_client:
        raise Exception("Anthropic API not configured")
    
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        raise Exception(f"Claude API Error: {str(e)}")

# ==========================================
# ROUTES: PUBLIC
# ==========================================
@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# ==========================================
# ROUTES: AUTH
# ==========================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            # Check if email exists
            if User.query.filter_by(email=data.get('email').lower()).first():
                return jsonify({'error': 'Email already registered'}), 400
            
            # Create user
            hashed = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
            user = User(
                username=data.get('username'),
                email=data.get('email').lower(),
                password_hash=hashed
            )
            
            # First user is admin
            if User.query.count() == 0:
                user.is_admin = True
            
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
        data = request.get_json() if request.is_json else request.form
        user = User.query.filter_by(email=data.get('email').lower()).first()
        
        if user and user.check_password(data.get('password')):
            if not user.is_active:
                return jsonify({'error': 'Account banned'}), 403
            login_user(user)
            return jsonify({'success': True, 'redirect': '/dashboard'})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ==========================================
# ROUTES: DASHBOARD
# ==========================================
@app.route('/dashboard')
@login_required
def dashboard():
    recent = Content.query.filter_by(user_id=current_user.id)\
        .order_by(Content.updated_at.desc()).limit(5).all()
    
    total = Content.query.filter_by(user_id=current_user.id).count()
    
    words = db.session.query(db.func.sum(Content.word_count))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('dashboard.html',
        recent_content=recent,
        total_content=total,
        total_words=words,
        limits=current_user.get_limits()
    )

@app.route('/editor')
@login_required
def editor():
    content_id = request.args.get('id')
    content = None
    
    if content_id:
        content = Content.query.filter_by(id=content_id, user_id=current_user.id).first()
    
    return render_template('editor.html', content=content)

# ==========================================
# API: CONTENT GENERATION
# ==========================================
@app.route('/api/generate-content', methods=['POST'])
@login_required
def api_generate_content():
    if current_user.ai_requests_this_month >= current_user.get_limits()['ai_requests_per_month']:
        return jsonify({'error': 'Monthly AI limit reached'}), 403
    
    try:
        import markdown
        
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            return jsonify({'error': 'Keyword required'}), 400
        
        prompt = f"""Write a comprehensive SEO-optimized blog post about: "{keyword}"

Requirements:
- Create an engaging H1 title
- Write a compelling introduction
- Use H2 (##) and H3 (###) headings
- Include 4-6 main sections
- Target 800-1200 words
- Be factual and accurate

Format using Markdown."""
        
        content = call_claude(
            prompt=prompt,
            system_prompt="You are an expert SEO content writer.",
            temperature=0.6,
            max_tokens=3500
        )
        
        current_user.ai_requests_this_month += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'content': content,
            'html_content': markdown.markdown(content),
            'word_count': len(content.split())
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# API: CONTENT MANAGEMENT
# ==========================================
@app.route('/api/save-content', methods=['POST'])
@login_required
def api_save_content():
    try:
        data = request.get_json()
        
        # Update existing
        if data.get('id'):
            content = Content.query.get(data.get('id'))
            if content and content.user_id == current_user.id:
                content.title = data.get('title')
                content.content = data.get('content')
                content.keyword = data.get('keyword')
                content.word_count = len(data.get('content', '').split())
                db.session.commit()
                return jsonify({'success': True, 'id': content.id})
        
        # Create new
        new_content = Content(
            user_id=current_user.id,
            title=data.get('title'),
            content=data.get('content'),
            keyword=data.get('keyword'),
            word_count=len(data.get('content', '').split())
        )
        
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

# ==========================================
# TECHNICAL SEO
# ==========================================
@app.route('/robots.txt')
def robots_txt():
    lines = [
        "User-agent: *",
        "Disallow: /dashboard",
        "Disallow: /editor",
        f"Sitemap: {request.url_root}sitemap.xml"
    ]
    return "\n".join(lines), 200, {'Content-Type': 'text/plain'}

# ==========================================
# ADMIN
# ==========================================
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect('/dashboard')
    
    users = User.query.order_by(User.id.desc()).all()
    total_content = Content.query.count()
    
    return render_template('admin.html',
        users=users,
        total_content=total_content
    )

# ==========================================
# ERROR HANDLERS
# ==========================================
@app.errorhandler(404)
def not_found(e):
    return "<h1>404 - Page Not Found</h1>", 404

@app.errorhandler(500)
def server_error(e):
    return "<h1>500 - Server Error</h1>", 500

# ==========================================
# RUN APP
# ==========================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database initialized!")
        print(f"📊 Total users: {User.query.count()}")
        print(f"📝 Total content: {Content.query.count()}")
    
    print("\n🚀 Starting server...")
    print("🌐 Open: http://localhost:5001")
    print("⚠️  Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
ENDOFPYTHON

echo "✅ app.py recreated!"