"""
Update Flask application configuration for PostgreSQL
This script updates the Flask app configuration to use PostgreSQL instead of SQLite
"""

import os
import re
import shutil
from datetime import datetime

def backup_original_config():
    """Create a backup of the original __init__.py"""
    original_file = os.path.join(os.path.dirname(__file__), '..', 'app', '__init__.py')
    backup_file = f"{original_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(original_file):
        shutil.copy2(original_file, backup_file)
        print(f"✓ Backup created: {backup_file}")

def update_flask_config():
    """Update Flask configuration to use PostgreSQL"""
    
    # Path to the Flask app initialization file
    app_init_path = os.path.join(os.path.dirname(__file__), '..', 'app', '__init__.py')
    
    # Read the current configuration
    with open(app_init_path, 'r', encoding='utf-8') as file:

        content = file.read()
    
    # Replace SQLite configuration with PostgreSQL
    old_db_config = r"db_path = os\.path\.join$$app\.root_path, '\.\.', 'instance', 'project_management\.db'$$\s*app\.config\['SQLALCHEMY_DATABASE_URI'\] = f\"sqlite:///\{os\.path\.abspath$$db_path$$\}\""
    
    new_db_config = """# PostgreSQL Configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        # Fix for Heroku postgres:// URLs
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'postgresql://localhost/project_management'"""
    
    # Perform the replacement
    updated_content = re.sub(old_db_config, new_db_config, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the updated configuration
    with open(app_init_path, 'w', encoding='utf-8') as file:

        file.write(updated_content)
    
    print("✅ Flask configuration updated for PostgreSQL")
    print("📝 Make sure to set the DATABASE_URL environment variable")

def create_env_template():
    """Create a .env template file"""
    env_template = """# Environment Variables Template
# Copy this to .env and fill in your values

# PostgreSQL Database URL
# Format: postgresql://username:password@host:port/database
DATABASE_URL=postgresql://username:password@localhost:5432/project_management

# Flask Secret Key (generate a secure random key for production)
SECRET_KEY=your-secret-key-here

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True

# Upload Configuration
MAX_CONTENT_LENGTH=16777216

# Example URLs for different providers:
# Supabase: postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
# Neon: postgresql://username:password@ep-xxx.us-east-1.aws.neon.tech/neondb
# Render: postgresql://username:password@dpg-xxx-a.oregon-postgres.render.com/database_name
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.template')
    with open(env_path, 'w') as file:
        file.write(env_template)
    
    print("✅ Created .env.template file")
    print("📝 Copy .env.template to .env and update with your database credentials")

def update_requirements():
    """Update requirements.txt to include PostgreSQL dependencies"""
    requirements_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    
    # Read current requirements
    with open(requirements_path, 'r') as file:
        requirements = file.read()
    
    # Add PostgreSQL dependencies if not present
    new_deps = [
        'psycopg2-binary>=2.9.0',
        'python-dotenv>=0.19.0'
    ]
    
    for dep in new_deps:
        package_name = dep.split('>=')[0].split('==')[0]
        if package_name not in requirements:
            requirements += f"\n{dep}"
    
    # Write updated requirements
    with open(requirements_path, 'w') as file:
        file.write(requirements)
    
    print("✓ Updated requirements.txt with PostgreSQL dependencies")

def main():
    print("=== Updating Flask Configuration for PostgreSQL ===")
    backup_original_config()
    update_flask_config()
    create_env_template()
    update_requirements()
    print("✓ Configuration update complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env")
    print("2. Update .env with your PostgreSQL credentials")
    print("3. Install new requirements: pip install -r requirements.txt")
    print("4. Run your Flask application")

if __name__ == "__main__":
    main()
