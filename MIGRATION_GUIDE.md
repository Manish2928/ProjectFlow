# Complete SQLite to PostgreSQL Migration Guide

## 🚨 Fix Current Error

The error shows that database "demo1" doesn't exist. Here's how to fix it:

### Step 1: Get Correct Supabase Connection String

1. **Go to your Supabase Dashboard**
   - Visit [https://supabase.com/dashboard](https://supabase.com/dashboard)
   - Select your project

2. **Get the correct connection string**
   - Go to **Settings** → **Database**
   - Look for **Connection string** section
   - Copy the **URI** format (not the individual parameters)
   - It should look like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`

3. **Important**: The database name should be `postgres`, not `demo1`

### Step 2: Set Up Environment

1. **Create .env file**:
   \`\`\`bash
   cp .env.template .env
   \`\`\`

2. **Edit .env file** with your correct Supabase URL:
   \`\`\`
   DATABASE_URL=postgresql://postgres:your_actual_password@db.your_project_ref.supabase.co:5432/postgres
   SECRET_KEY=your-secret-key-here
   \`\`\`

## 🚀 Complete Migration Steps

### Step 1: Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Step 2: Set Up Migration Environment
\`\`\`bash
# Make setup script executable (Linux/Mac)
chmod +x migration/setup_migration.sh
./migration/setup_migration.sh

# Or run directly with bash
bash migration/setup_migration.sh
\`\`\`

### Step 3: Configure Database Connection

1. **For Supabase** (Recommended):
   \`\`\`bash
   # Get your connection string from Supabase Dashboard
   # Settings > Database > Connection string > URI
   export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"
   \`\`\`

2. **For Neon**:
   \`\`\`bash
   export DATABASE_URL=""
   export DATABASE_URL=""
   \`\`\`

3. **For local PostgreSQL**:
   \`\`\`bash
   export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"
   \`\`\`

### Step 4: Run Migration
\`\`\`bash
python migration/migrate_to_postgresql.py
\`\`\`

### Step 5: Verify Migration
\`\`\`bash
python migration/verify_migration.py
\`\`\`

### Step 6: Update Flask Configuration
\`\`\`bash
python migration/update_flask_config.py
\`\`\`

### Step 7: Test Your Application
\`\`\`bash
python run.py
\`\`\`

## 🔧 Troubleshooting

### Common Issues:

1. **Database doesn't exist error**:
   - Check your DATABASE_URL
   - Ensure database name is correct (usually 'postgres' for Supabase)

2. **Connection refused**:
   - Verify your credentials
   - Check if your IP is whitelisted (Supabase allows all by default)

3. **Permission denied**:
   - Ensure your database user has CREATE privileges
   - For Supabase, use the 'postgres' user

4. **SSL connection error**:
   - Add `?sslmode=require` to your connection string if needed

## 📊 PostgreSQL Provider Comparison

| Provider | Free Tier | Pros | Cons |
|----------|-----------|------|------|
| **Supabase** | 500MB | Easy setup, built-in auth, real-time | Smaller free tier |
| **Neon** | 3GB | Larger free tier, serverless | Newer service |
| **Render** | 1GB | Good performance | Limited features |
| **ElephantSQL** | 20MB | Reliable | Very small free tier |

## 🎯 Recommended: Supabase Setup

1. **Create Account**: Go to [supabase.com](https://supabase.com)
2. **New Project**: Click "New Project"
3. **Get Connection String**: 
   - Settings → Database → Connection string
   - Use the URI format
   - Replace `[YOUR-PASSWORD]` with your actual password

## ✅ Post-Migration Checklist

- [ ] All tables created successfully
- [ ] Data counts match between SQLite and PostgreSQL
- [ ] Foreign key relationships intact
- [ ] Application starts without errors
- [ ] Login functionality works
- [ ] Can create/edit projects and tasks
- [ ] File uploads work correctly

## 🔄 Rollback Plan

If migration fails, you can rollback:

1. **Restore original configuration**:
   \`\`\`bash
   # Your original __init__.py is backed up automatically
   cp app/__init__.py.backup_* app/__init__.py
   \`\`\`

2. **Use SQLite again**:
   - Remove DATABASE_URL from environment
   - Application will fall back to SQLite

## 📞 Support

If you encounter issues:
1. Check the error logs carefully
2. Verify your connection string format
3. Ensure your PostgreSQL service is running
4. Check firewall/network settings
\`\`\`

```python file="app/__init__.py"
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database Configuration
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL Configuration
        if database_url.startswith('postgres://'):
            # Fix for Heroku postgres:// URLs
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"✓ Using PostgreSQL database")
    else:
        # Fallback to SQLite for development
        db_path = os.path.join(app.root_path, '..', 'instance', 'project_management.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(db_path)}"
        print(f"⚠️  Using SQLite database (set DATABASE_URL for PostgreSQL)")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directories exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'canvas'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register template filter
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ""
        return value.strftime(format)
    
    # Register blueprints
    from app.modules.auth.routes import auth_bp
    from app.modules.dashboard.routes import dashboard_bp
    from app.modules.projects.routes import projects_bp
    from app.modules.users.routes import users_bp
    from app.modules.admin.routes import admin_bp
    from app.modules.invitations.routes import invitations_bp
    from app.modules.canvas.routes import canvas_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(invitations_bp, url_prefix='/invitations')
    app.register_blueprint(canvas_bp, url_prefix='/canvas')
    
    # Root route
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Create tables and default admin user
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Create default admin user if it doesn't exist
            from app.models.user import User
            admin_user = User.query.filter_by(email='admin@example.com').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Default admin user created: admin@example.com / admin123")
        except Exception as e:
            print(f"✗ Database initialization error: {e}")
            print("Please check your DATABASE_URL and ensure the database exists")
            raise
    
    return app
