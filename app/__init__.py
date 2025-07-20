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
