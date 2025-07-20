from datetime import datetime
from app import db

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, completed, on_hold, cancelled
    priority = db.Column(db.String(10), nullable=False, default='medium')  # low, medium, high, urgent
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    budget = db.Column(db.Float)
    progress = db.Column(db.Integer, default=0)  # 0-100%
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def get_task_count(self):
        return len(self.tasks)
    
    def get_completed_tasks(self):
        return len([task for task in self.tasks if task.status == 'completed'])
    
    def calculate_progress(self):
        if not self.tasks:
            return 0
        completed = self.get_completed_tasks()
        return round((completed / len(self.tasks)) * 100)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_by': self.created_by,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'budget': self.budget,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'task_count': self.get_task_count(),
            'completed_tasks': self.get_completed_tasks()
        }
    
    def __repr__(self):
        return f'<Project {self.title}>'
