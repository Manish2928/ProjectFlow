from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.invitation import ProjectMember
from sqlalchemy import select

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Get user's statistics
    if current_user.is_admin():
        # Admin dashboard
        total_users = User.query.count()
        total_projects = Project.query.count()
        total_tasks = Task.query.count()
        my_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
        my_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    else:
        # Regular user dashboard - include projects where user is member
        total_users = None
        
        # Count projects created by user OR where user is a member
        member_project_ids = select(ProjectMember.project_id).filter_by(user_id=current_user.id)
        total_projects = Project.query.filter(
            db.or_(
                Project.created_by == current_user.id,
                Project.id.in_(member_project_ids)
            )
        ).count()
        
        total_tasks = Task.query.filter_by(assigned_to=current_user.id).count()
        
        # Get recent projects (created by user OR where user is member)
        my_projects = Project.query.filter(
            db.or_(
                Project.created_by == current_user.id,
                Project.id.in_(member_project_ids)
            )
        ).order_by(Project.created_at.desc()).limit(5).all()
        
        my_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).limit(5).all()
    
    # Recent activities
    recent_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.updated_at.desc()).limit(5).all()
    
    # Tasks due soon (next 7 days)
    seven_days_later = datetime.utcnow() + timedelta(days=7)
    upcoming_tasks = Task.query.filter(
        Task.assigned_to == current_user.id,
        Task.due_date <= seven_days_later,
        Task.status != 'completed'
    ).order_by(Task.due_date.asc()).limit(5).all()
    
    # Overdue tasks
    overdue_tasks = Task.query.filter(
        Task.assigned_to == current_user.id,
        Task.due_date < datetime.utcnow(),
        Task.status != 'completed'
    ).count()
    
    stats = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_tasks': Task.query.filter_by(assigned_to=current_user.id, status='completed').count()
    }
    
    return render_template('dashboard/index.html', 
                         stats=stats,
                         my_projects=my_projects,
                         my_tasks=my_tasks,
                         recent_tasks=recent_tasks,
                         upcoming_tasks=upcoming_tasks)

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    # Get user's notifications (tasks due soon, overdue, etc.)
    seven_days_later = datetime.utcnow() + timedelta(days=7)
    
    upcoming_tasks = Task.query.filter(
        Task.assigned_to == current_user.id,
        Task.due_date <= seven_days_later,
        Task.status != 'completed'
    ).order_by(Task.due_date.asc()).all()
    
    overdue_tasks = Task.query.filter(
        Task.assigned_to == current_user.id,
        Task.due_date < datetime.utcnow(),
        Task.status != 'completed'
    ).order_by(Task.due_date.asc()).all()
    
    return render_template('dashboard/notifications.html', 
                         upcoming_tasks=upcoming_tasks,
                         overdue_tasks=overdue_tasks)
