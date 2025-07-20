from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import db
from app.models.user import User
from app.models.canvas import CanvasChatMessage, Canvas
from app.utils.forms import ProfileForm, ChangePasswordForm

users_bp = Blueprint('users', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_avatar_folder():
    avatar_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
    if not os.path.exists(avatar_folder):
        os.makedirs(avatar_folder)
    return avatar_folder

@users_bp.route('/profile')
@login_required
def profile():
    return render_template('users/profile.html', user=current_user)

@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if email already exists (excluding current user)
        if form.email.data != current_user.email and User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return render_template('users/edit_profile.html', form=form)
        
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.department = form.department.data
        current_user.job_title = form.job_title.data
        current_user.bio = form.bio.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('users.profile'))
    
    return render_template('users/edit_profile.html', form=form)

@users_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('users/change_password.html', form=form)
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('users.profile'))
    
    return render_template('users/change_password.html', form=form)

@users_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            avatar_folder = ensure_avatar_folder()
            
            # Delete old profile picture if it's not the default
            if current_user.profile_picture and current_user.profile_picture != 'default-avatar.png':
                old_file_path = os.path.join(avatar_folder, current_user.profile_picture)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            filename = secure_filename(file.filename)
            # Add user ID and timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = f"user_{current_user.id}_{timestamp}{filename}"
            
            file_path = os.path.join(avatar_folder, filename)
            file.save(file_path)
            
            # Update user's profile picture
            current_user.profile_picture = filename
            db.session.commit()
            
            return jsonify({
                'success': True,
                'url': f'/static/uploads/avatars/{filename}',
                'filename': filename
            })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile picture upload error: {str(e)}")
            return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500
    
    return jsonify({'success': False, 'message': 'File type not allowed. Please use PNG, JPG, JPEG, GIF, or WEBP.'}), 400

# Global Chat endpoints
@users_bp.route('/global-chat/messages', methods=['GET'])
@login_required
def get_global_chat_messages():
    # Create a special global canvas for global chat
    global_canvas = Canvas.query.filter_by(title='Global Chat').first()
    if not global_canvas:
        global_canvas = Canvas(
            title='Global Chat',
            created_by=current_user.id,
            content='{"elements": [], "settings": {"theme": "light"}}'
        )
        db.session.add(global_canvas)
        db.session.commit()
    
    messages = CanvasChatMessage.query.filter_by(canvas_id=global_canvas.id)\
                                    .order_by(CanvasChatMessage.created_at.asc()).all()
    
    return jsonify({
        'success': True,
        'messages': [message.to_dict() for message in messages]
    })

@users_bp.route('/global-chat/messages', methods=['POST'])
@login_required
def send_global_chat_message():
    try:
        # Create a special global canvas for global chat
        global_canvas = Canvas.query.filter_by(title='Global Chat').first()
        if not global_canvas:
            global_canvas = Canvas(
                title='Global Chat',
                created_by=current_user.id,
                content='{"elements": [], "settings": {"theme": "light"}}'
            )
            db.session.add(global_canvas)
            db.session.commit()
        
        data = request.get_json()
        
        message = CanvasChatMessage(
            canvas_id=global_canvas.id,
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
