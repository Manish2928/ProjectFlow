"""
Comprehensive migration verification script
"""
import sqlite3
import psycopg2
import psycopg2.extras
import os
from urllib.parse import urlparse

class MigrationVerifier:
    def __init__(self, sqlite_path, postgresql_url):
        self.sqlite_path = sqlite_path
        self.postgresql_url = postgresql_url
        self.sqlite_conn = None
        self.pg_conn = None
        
    def connect_databases(self):
        """Connect to both databases"""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            
            self.pg_conn = psycopg2.connect(self.postgresql_url)
            print("✓ Connected to both databases")
        except Exception as e:
            print(f"✗ Connection error: {e}")
            raise

    def verify_table_counts(self):
        """Verify record counts match between databases"""
        print("\n=== Table Record Count Verification ===")
        
        tables = [
            'users', 'projects', 'tasks', 'canvas', 
            'canvas_elements', 'canvas_chat_messages', 
            'canvas_files', 'project_invitations', 'project_members'
        ]
        
        all_match = True
        
        for table in tables:
            try:
                # SQLite count
                sqlite_cursor = self.sqlite_conn.cursor()
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # PostgreSQL count
                pg_cursor = self.pg_conn.cursor()
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cursor.fetchone()[0]
                
                match = sqlite_count == pg_count
                status = "✓" if match else "✗"
                print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                
                if not match:
                    all_match = False
                    
            except Exception as e:
                print(f"✗ Error checking {table}: {e}")
                all_match = False
        
        return all_match

    def verify_data_integrity(self):
        """Verify data integrity with sample checks"""
        print("\n=== Data Integrity Verification ===")
        
        try:
            # Check user data
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT username, email FROM users ORDER BY id LIMIT 5")
            sqlite_users = sqlite_cursor.fetchall()
            
            pg_cursor = self.pg_conn.cursor()
            pg_cursor.execute("SELECT username, email FROM users ORDER BY id LIMIT 5")
            pg_users = pg_cursor.fetchall()
            
            users_match = len(sqlite_users) == len(pg_users)
            if users_match:
                for i, (sqlite_user, pg_user) in enumerate(zip(sqlite_users, pg_users)):
                    if sqlite_user[0] != pg_user[0] or sqlite_user[1] != pg_user[1]:
                        users_match = False
                        break
            
            print(f"{'✓' if users_match else '✗'} User data integrity check")
            
            # Check project data
            sqlite_cursor.execute("SELECT title, status FROM projects ORDER BY id LIMIT 5")
            sqlite_projects = sqlite_cursor.fetchall()
            
            pg_cursor.execute("SELECT title, status FROM projects ORDER BY id LIMIT 5")
            pg_projects = pg_cursor.fetchall()
            
            projects_match = len(sqlite_projects) == len(pg_projects)
            if projects_match:
                for sqlite_proj, pg_proj in zip(sqlite_projects, pg_projects):
                    if sqlite_proj[0] != pg_proj[0] or sqlite_proj[1] != pg_proj[1]:
                        projects_match = False
                        break
            
            print(f"{'✓' if projects_match else '✗'} Project data integrity check")
            
            return users_match and projects_match
            
        except Exception as e:
            print(f"✗ Data integrity check failed: {e}")
            return False

    def verify_foreign_keys(self):
        """Verify foreign key relationships"""
        print("\n=== Foreign Key Relationship Verification ===")
        
        try:
            pg_cursor = self.pg_conn.cursor()
            
            # Check if all projects have valid created_by references
            pg_cursor.execute("""
                SELECT COUNT(*) FROM projects p 
                LEFT JOIN users u ON p.created_by = u.id 
                WHERE u.id IS NULL
            """)
            orphaned_projects = pg_cursor.fetchone()[0]
            
            # Check if all tasks have valid project_id references
            pg_cursor.execute("""
                SELECT COUNT(*) FROM tasks t 
                LEFT JOIN projects p ON t.project_id = p.id 
                WHERE p.id IS NULL
            """)
            orphaned_tasks = pg_cursor.fetchone()[0]
            
            print(f"{'✓' if orphaned_projects == 0 else '✗'} Projects with valid creators: {orphaned_projects} orphaned")
            print(f"{'✓' if orphaned_tasks == 0 else '✗'} Tasks with valid projects: {orphaned_tasks} orphaned")
            
            return orphaned_projects == 0 and orphaned_tasks == 0
            
        except Exception as e:
            print(f"✗ Foreign key verification failed: {e}")
            return False

    def run_verification(self):
        """Run complete verification"""
        print("=== Migration Verification Report ===")
        
        try:
            self.connect_databases()
            
            counts_match = self.verify_table_counts()
            data_integrity = self.verify_data_integrity()
            fk_integrity = self.verify_foreign_keys()
            
            print(f"\n=== Summary ===")
            print(f"Record counts match: {'✓' if counts_match else '✗'}")
            print(f"Data integrity: {'✓' if data_integrity else '✗'}")
            print(f"Foreign key integrity: {'✓' if fk_integrity else '✗'}")
            
            if counts_match and data_integrity and fk_integrity:
                print("\n🎉 Migration verification PASSED! Your data has been successfully migrated.")
            else:
                print("\n⚠️  Migration verification FAILED. Please check the issues above.")
                
        except Exception as e:
            print(f"✗ Verification failed: {e}")
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.pg_conn:
                self.pg_conn.close()

def main():
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'project_management.db')
    postgresql_url = os.environ.get('DATABASE_URL')
    
    if not postgresql_url:
        print("Please set DATABASE_URL environment variable")
        return
    
    if not os.path.exists(sqlite_path):
        print(f"SQLite database not found at: {sqlite_path}")
        return
    
    verifier = MigrationVerifier(sqlite_path, postgresql_url)
    verifier.run_verification()

if __name__ == "__main__":
    main()
