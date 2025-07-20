from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.utils.forms import ProjectForm, TaskForm
from app.models.invitation import ProjectMember

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    # Fix: Show projects for both admin and project members
    if current_user.is_admin():
        query = Project.query
    else:
        # Show projects created by user OR projects where user is a member
        member_project_ids = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id).subquery()
        query = Project.query.filter(
            db.or_(
                Project.created_by == current_user.id,
                Project.id.in_(member_project_ids)
            )
        )
    
    if search:
        query = query.filter(Project.title.contains(search))
    
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    projects = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('projects/index.html', projects=projects, search=search, status_filter=status_filter)

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            start_date=form.start_date.data,
            deadline=form.deadline.data,
            budget=form.budget.data,
            created_by=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects.view', project_id=project.id))
    
    return render_template('projects/create.html', form=form)

@projects_bp.route('/<int:project_id>')
@login_required
def view(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user can view this project
    if not (
        current_user.is_admin() or
        project.created_by == current_user.id or
        ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first()
    ):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    
    # Update project progress
    project.progress = project.calculate_progress()
    db.session.commit()
    
    tasks = Task.query.filter_by(project_id=project.id).order_by(Task.created_at.desc()).all()
    
    return render_template('projects/view.html', project=project, tasks=tasks)

@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user can edit this project
    if not current_user.is_admin() and project.created_by != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.status = form.status.data
        project.priority = form.priority.data
        project.start_date = form.start_date.data
        project.deadline = form.deadline.data
        project.budget = form.budget.data
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects.view', project_id=project.id))
    
    return render_template('projects/edit.html', form=form, project=project)

@projects_bp.route('/<int:project_id>/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user can create tasks for this project
    if not (
        current_user.is_admin() or 
        project.created_by == current_user.id or
        ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first()
    ):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.view', project_id=project_id))
    
    form = TaskForm()
    # Get all users for assignment
    form.assigned_to.choices = [(0, 'Unassigned')] + [(u.id, u.get_full_name()) for u in User.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            project_id=project_id,
            assigned_to=form.assigned_to.data if form.assigned_to.data != 0 else None,
            created_by=current_user.id,
            due_date=form.due_date.data,
            estimated_hours=form.estimated_hours.data
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('projects.view', project_id=project_id))
    
    return render_template('projects/create_task.html', form=form, project=project)

@projects_bp.route('/tasks/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if user can update this task
    if not current_user.is_admin() and task.assigned_to != current_user.id and task.created_by != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    status = request.json.get('status')
    if status not in ['pending', 'in_progress', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    task.status = status
    if status == 'completed':
        task.completed_date = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Task status updated successfully'})
