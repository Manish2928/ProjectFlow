"""
SQLite to PostgreSQL Migration Script
This script handles the complete migration from SQLite to PostgreSQL
"""

import sqlite3
import psycopg2
import psycopg2.extras
import os
import sys
from datetime import datetime
import json
from urllib.parse import urlparse

class SQLiteToPostgreSQLMigrator:
    def __init__(self, sqlite_path, postgresql_url):
        self.sqlite_path = sqlite_path
        self.postgresql_url = postgresql_url
        self.sqlite_conn = None
        self.pg_conn = None
        
    def connect_databases(self):
        """Connect to both SQLite and PostgreSQL databases"""
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            print("✓ Connected to SQLite database")
            
            # Connect to PostgreSQL
            self.pg_conn = psycopg2.connect(self.postgresql_url)
            self.pg_conn.autocommit = False
            print("✓ Connected to PostgreSQL database")
            
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            sys.exit(1)
    
    def create_postgresql_schema(self):
        """Create PostgreSQL schema based on SQLite structure"""
        
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            profile_picture VARCHAR(200) DEFAULT 'default-avatar.png',
            bio TEXT,
            phone VARCHAR(20),
            department VARCHAR(100),
            job_title VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );

        -- Projects table
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            priority VARCHAR(10) NOT NULL DEFAULT 'medium',
            created_by INTEGER NOT NULL REFERENCES users(id),
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            deadline TIMESTAMP,
            budget DECIMAL(10,2),
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tasks table
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            priority VARCHAR(10) NOT NULL DEFAULT 'medium',
            project_id INTEGER NOT NULL REFERENCES projects(id),
            assigned_to INTEGER REFERENCES users(id),
            created_by INTEGER NOT NULL REFERENCES users(id),
            due_date TIMESTAMP,
            completed_date TIMESTAMP,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Canvas table
        CREATE TABLE IF NOT EXISTS canvas (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            title VARCHAR(200) NOT NULL DEFAULT 'Untitled Canvas',
            content TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Canvas Elements table
        CREATE TABLE IF NOT EXISTS canvas_elements (
            id SERIAL PRIMARY KEY,
            canvas_id INTEGER NOT NULL REFERENCES canvas(id),
            element_type VARCHAR(50) NOT NULL,
            position_x DECIMAL(10,2) DEFAULT 0,
            position_y DECIMAL(10,2) DEFAULT 0,
            width DECIMAL(10,2) DEFAULT 200,
            height DECIMAL(10,2) DEFAULT 100,
            content TEXT,
            style TEXT,
            z_index INTEGER DEFAULT 1,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Canvas Chat Messages table
        CREATE TABLE IF NOT EXISTS canvas_chat_messages (
            id SERIAL PRIMARY KEY,
            canvas_id INTEGER NOT NULL REFERENCES canvas(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            message_type VARCHAR(20) DEFAULT 'text',
            file_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Canvas Files table
        CREATE TABLE IF NOT EXISTS canvas_files (
            id SERIAL PRIMARY KEY,
            canvas_id INTEGER NOT NULL REFERENCES canvas(id),
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_by INTEGER NOT NULL REFERENCES users(id),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Project Invitations table
        CREATE TABLE IF NOT EXISTS project_invitations (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            inviter_id INTEGER NOT NULL REFERENCES users(id),
            invitee_id INTEGER NOT NULL REFERENCES users(id),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP
        );

        -- Project Members table
        CREATE TABLE IF NOT EXISTS project_members (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            permissions VARCHAR(100) DEFAULT 'read,write,create',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);
        CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
        CREATE INDEX IF NOT EXISTS idx_canvas_project_id ON canvas(project_id);
        CREATE INDEX IF NOT EXISTS idx_canvas_elements_canvas_id ON canvas_elements(canvas_id);
        CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
        CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);
        """
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(schema_sql)
            self.pg_conn.commit()
            print("✓ PostgreSQL schema created successfully")
        except Exception as e:
            print(f"✗ Error creating PostgreSQL schema: {e}")
            self.pg_conn.rollback()
            raise

    def migrate_table_data(self, table_name, id_mapping=None):
        """Migrate data from SQLite table to PostgreSQL table"""
        try:
            # Get SQLite data
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  No data found in {table_name}")
                return {}
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare PostgreSQL insert
            pg_cursor = self.pg_conn.cursor()
            
            # Handle different table structures
            new_id_mapping = {}
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                old_id = row_dict['id']
                
                # Update foreign key references if needed
                if id_mapping:
                    for fk_column, fk_table in self.get_foreign_keys(table_name).items():
                        if fk_column in row_dict and row_dict[fk_column] is not None:
                            if fk_table in id_mapping and row_dict[fk_column] in id_mapping[fk_table]:
                                row_dict[fk_column] = id_mapping[fk_table][row_dict[fk_column]]
                
                # Remove the old ID to let PostgreSQL generate a new one
                del row_dict['id']
                
                # Prepare insert statement
                placeholders = ', '.join(['%s'] * len(row_dict))
                columns_str = ', '.join(row_dict.keys())
                
                insert_sql = f"""
                INSERT INTO {table_name} ({columns_str}) 
                VALUES ({placeholders}) 
                RETURNING id
                """
                
                pg_cursor.execute(insert_sql, list(row_dict.values()))
                new_id = pg_cursor.fetchone()[0]
                new_id_mapping[old_id] = new_id
            
            self.pg_conn.commit()
            print(f"✓ Migrated {len(rows)} rows from {table_name}")
            return new_id_mapping
            
        except Exception as e:
            print(f"✗ Error migrating {table_name}: {e}")
            self.pg_conn.rollback()
            raise

    def get_foreign_keys(self, table_name):
        """Get foreign key relationships for a table"""
        fk_mapping = {
            'projects': {'created_by': 'users'},
            'tasks': {'project_id': 'projects', 'assigned_to': 'users', 'created_by': 'users'},
            'canvas': {'project_id': 'projects', 'created_by': 'users'},
            'canvas_elements': {'canvas_id': 'canvas', 'created_by': 'users'},
            'canvas_chat_messages': {'canvas_id': 'canvas', 'user_id': 'users'},
            'canvas_files': {'canvas_id': 'canvas', 'uploaded_by': 'users'},
            'project_invitations': {'project_id': 'projects', 'inviter_id': 'users', 'invitee_id': 'users'},
            'project_members': {'project_id': 'projects', 'user_id': 'users'}
        }
        return fk_mapping.get(table_name, {})

    def migrate_all_data(self):
        """Migrate all data in the correct order to handle foreign key constraints"""
        migration_order = [
            'users',
            'projects', 
            'tasks',
            'canvas',
            'canvas_elements',
            'canvas_chat_messages',
            'canvas_files',
            'project_invitations',
            'project_members'
        ]
        
        id_mappings = {}
        
        for table in migration_order:
            print(f"Migrating {table}...")
            try:
                id_mappings[table] = self.migrate_table_data(table, id_mappings)
            except Exception as e:
                print(f"Failed to migrate {table}: {e}")
                continue
        
        return id_mappings

    def verify_migration(self):
        """Verify that migration was successful"""
        print("\n=== Migration Verification ===")
        
        tables = [
            'users', 'projects', 'tasks', 'canvas', 
            'canvas_elements', 'canvas_chat_messages', 
            'canvas_files', 'project_invitations', 'project_members'
        ]
        
        for table in tables:
            try:
                # Count SQLite records
                sqlite_cursor = self.sqlite_conn.cursor()
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Count PostgreSQL records
                pg_cursor = self.pg_conn.cursor()
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cursor.fetchone()[0]
                
                status = "✓" if sqlite_count == pg_count else "✗"
                print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                
            except Exception as e:
                print(f"✗ Error verifying {table}: {e}")

    def close_connections(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()

    def run_migration(self):
        """Run the complete migration process"""
        print("=== SQLite to PostgreSQL Migration ===")
        print(f"Source: {self.sqlite_path}")
        print(f"Target: {self.postgresql_url.split('@')[1] if '@' in self.postgresql_url else 'PostgreSQL'}")
        print()
        
        try:
            self.connect_databases()
            self.create_postgresql_schema()
            self.migrate_all_data()
            self.verify_migration()
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            raise
        finally:
            self.close_connections()

def main():
    # Configuration
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'project_management.db')
    
    # Get PostgreSQL URL from environment or prompt user
    postgresql_url = os.environ.get('DATABASE_URL')
    if not postgresql_url:
        print("Please set the DATABASE_URL environment variable with your PostgreSQL connection string")
        print("Example: postgresql://username:password@host:port/database")
        postgresql_url = input("Enter PostgreSQL URL: ")
    
    if not os.path.exists(sqlite_path):
        print(f"SQLite database not found at: {sqlite_path}")
        return
    
    # Run migration
    migrator = SQLiteToPostgreSQLMigrator(sqlite_path, postgresql_url)
    migrator.run_migration()

if __name__ == "__main__":
    main()
