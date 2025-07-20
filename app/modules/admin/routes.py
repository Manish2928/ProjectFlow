from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.canvas import CanvasChatMessage, Canvas
from app.utils.forms import CreateUserForm, EditUserForm
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='completed').count()

    # Calculate task completion rate
    if total_tasks > 0:
        task_completion_rate = round((completed_tasks / total_tasks) * 100)
    else:
        task_completion_rate = 0

    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()

    # User activity in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_logins = User.query.filter(User.last_login >= thirty_days_ago).count()

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'task_completion_rate': task_completion_rate,
    }

    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_projects=recent_projects,
                         recent_logins=recent_logins)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, 
                         role_filter=role_filter, status_filter=status_filter)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return render_template('admin/create_user.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return render_template('admin/create_user.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            department=form.department.data,
            job_title=form.job_title.data,
            phone=form.phone.data,
            bio=form.bio.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', form=form)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    if form.validate_on_submit():
        # Check if username or email already exists (excluding current user)
        if form.username.data != user.username and User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return render_template('admin/edit_user.html', form=form, user=user)
        
        if form.email.data != user.email and User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return render_template('admin/edit_user.html', form=form, user=user)
        
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role = form.role.data
        user.department = form.department.data
        user.job_title = form.job_title.data
        user.phone = form.phone.data
        user.bio = form.bio.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot modify your own status'}), 400
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'User {status} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Project.query
    
    if search:
        query = query.filter(
            (Project.title.contains(search)) |
            (Project.description.contains(search))
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    projects = query.order_by(Project.created_at.desc()).all()
    
    return render_template('admin/projects.html', projects=projects, search=search, status_filter=status_filter)

@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Admin Chat endpoints
@admin_bp.route('/chat/messages', methods=['GET'])
@login_required
@admin_required
def get_admin_chat_messages():
    # Create a special admin canvas for admin chat
    admin_canvas = Canvas.query.filter_by(title='Admin Chat').first()
    if not admin_canvas:
        admin_canvas = Canvas(
            title='Admin Chat',
            created_by=current_user.id,
            content='{"elements": [], "settings": {"theme": "light"}}'
        )
        db.session.add(admin_canvas)
        db.session.commit()
    
    messages = CanvasChatMessage.query.filter_by(canvas_id=admin_canvas.id)\
                                    .order_by(CanvasChatMessage.created_at.asc()).all()
    
    return jsonify({
        'success': True,
        'messages': [message.to_dict() for message in messages]
    })

@admin_bp.route('/chat/messages', methods=['POST'])
@login_required
@admin_required
def send_admin_chat_message():
    try:
        # Create a special admin canvas for admin chat
        admin_canvas = Canvas.query.filter_by(title='Admin Chat').first()
        if not admin_canvas:
            admin_canvas = Canvas(
                title='Admin Chat',
                created_by=current_user.id,
                content='{"elements": [], "settings": {"theme": "light"}}'
            )
            db.session.add(admin_canvas)
            db.session.commit()
        
        data = request.get_json()
        
        message = CanvasChatMessage(
            canvas_id=admin_canvas.id,
            user_id=current_user.id,
            message=data.get('message', ''),
            message_type=data.get('message_type', 'text')
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
