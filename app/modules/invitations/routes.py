from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.user import User
from app.models.project import Project
from app.models.invitation import ProjectInvitation, ProjectMember

invitations_bp = Blueprint('invitations', __name__)

@invitations_bp.route('/search-users')
@login_required
def search_users():
    query = request.args.get('q', '').strip()
    project_id = request.args.get('project_id', type=int)
    
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    # Get users who are not already members or invited to this project
    existing_member_ids = db.session.query(ProjectMember.user_id).filter_by(project_id=project_id).subquery()
    pending_invitation_ids = db.session.query(ProjectInvitation.invitee_id).filter_by(
        project_id=project_id, status='pending'
    ).subquery()
    
    users = User.query.filter(
        db.and_(
            User.is_active == True,
            User.id != current_user.id,
            ~User.id.in_(existing_member_ids),
            ~User.id.in_(pending_invitation_ids),
            db.or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()
    
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'department': user.department,
            'job_title': user.job_title
        } for user in users]
    })

@invitations_bp.route('/invite', methods=['POST'])
@login_required
def send_invitation():
    data = request.get_json()
    project_id = data.get('project_id')
    user_id = data.get('user_id')
    message = data.get('message', '')
    role = data.get('role', 'member')
    
    # Verify project exists and user has permission to invite
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_admin() or project.created_by == current_user.id):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Verify invitee exists
    invitee = User.query.get_or_404(user_id)
    
    # Check if already a member
    existing_member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if existing_member:
        return jsonify({'success': False, 'message': 'User is already a member of this project'}), 400
    
    # Check if invitation already exists
    existing_invitation = ProjectInvitation.query.filter_by(
        project_id=project_id, invitee_id=user_id, status='pending'
    ).first()
    if existing_invitation:
        return jsonify({'success': False, 'message': 'Invitation already sent to this user'}), 400
    
    # Create invitation
    invitation = ProjectInvitation(
        project_id=project_id,
        inviter_id=current_user.id,
        invitee_id=user_id,
        role=role,
        message=message
    )
    
    db.session.add(invitation)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Invitation sent to {invitee.get_full_name()}',
        'invitation': invitation.to_dict()
    })

@invitations_bp.route('/respond/<int:invitation_id>', methods=['POST'])
@login_required
def respond_to_invitation(invitation_id):
    invitation = ProjectInvitation.query.get_or_404(invitation_id)
    
    # Verify user is the invitee
    if invitation.invitee_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Verify invitation is still pending
    if invitation.status != 'pending':
        return jsonify({'success': False, 'message': 'Invitation has already been responded to'}), 400
    
    response = request.json.get('response')  # 'accept' or 'decline'
    
    if response == 'accept':
        # Create project membership
        permissions = 'read,write,create'  # Default permissions for members
        if invitation.role == 'viewer':
            permissions = 'read'
        
        member = ProjectMember(
            project_id=invitation.project_id,
            user_id=current_user.id,
            role=invitation.role,
            permissions=permissions
        )
        
        db.session.add(member)
        invitation.status = 'accepted'
        flash(f'You have joined the project "{invitation.project.title}"!', 'success')
        
    elif response == 'decline':
        invitation.status = 'declined'
        flash('Invitation declined.', 'info')
    else:
        return jsonify({'success': False, 'message': 'Invalid response'}), 400
    
    invitation.responded_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Invitation {response}ed successfully',
        'redirect': url_for('projects.view', project_id=invitation.project_id) if response == 'accept' else url_for('dashboard.index')
    })

@invitations_bp.route('/my-invitations')
@login_required
def my_invitations():
    pending_invitations = ProjectInvitation.query.filter_by(
        invitee_id=current_user.id, status='pending'
    ).order_by(ProjectInvitation.created_at.desc()).all()
    
    return render_template('invitations/my_invitations.html', invitations=pending_invitations)

@invitations_bp.route('/project/<int:project_id>/members')
@login_required
def project_members(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user has access to view members
    if not (current_user.is_admin() or project.created_by == current_user.id or 
            ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    pending_invitations = ProjectInvitation.query.filter_by(project_id=project_id, status='pending').all()
    
    return render_template('invitations/project_members.html', 
                         project=project, 
                         members=members, 
                         pending_invitations=pending_invitations)

@invitations_bp.route('/remove-member/<int:member_id>', methods=['POST'])
@login_required
def remove_member(member_id):
    member = ProjectMember.query.get_or_404(member_id)
    project = member.project
    
    # Only project owner or admin can remove members
    if not (current_user.is_admin() or project.created_by == current_user.id):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Cannot remove project owner
    if member.user_id == project.created_by:
        return jsonify({'success': False, 'message': 'Cannot remove project owner'}), 400
    
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{member.user.get_full_name()} removed from project'
    })
