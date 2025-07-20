from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import requests
import urllib.parse
from datetime import datetime
from app import db, socketio
from app.models.canvas import Canvas, CanvasElement, CanvasChatMessage, CanvasFile
from app.models.project import Project
from app.models.user import User
from app.models.invitation import ProjectMember

canvas_bp = Blueprint('canvas', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'svg', 'webp', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'canvas')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

def has_canvas_write_permission(project, user):
    if user.is_admin() or project.created_by == user.id:
        return True
    member = ProjectMember.query.filter_by(project_id=project.id, user_id=user.id).first()
    return member and ('write' in member.permissions or 'create' in member.permissions)

def has_canvas_read_permission(project, user):
    if user.is_admin() or project.created_by == user.id:
        return True
    member = ProjectMember.query.filter_by(project_id=project.id, user_id=user.id).first()
    return member is not None

@canvas_bp.route('/project/<int:project_id>')
@login_required
def project_canvas(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user has access to this project
    if not has_canvas_read_permission(project, current_user):
        flash('Access denied.', 'error')
        return redirect(url_for('projects.index'))
    
    
    
    # Get or create canvas for this project
    canvas = Canvas.query.filter_by(project_id=project_id).first()
    if not canvas:
        canvas = Canvas(
            project_id=project_id,
            title=f"{project.title} - Canvas",
            created_by=current_user.id,
            content=json.dumps({'elements': [], 'settings': {'theme': 'light'}})
        )
        db.session.add(canvas)
        db.session.commit()
    
    # Get all project team members for chat
    team_members_query = User.query.join(ProjectMember, User.id == ProjectMember.user_id)\
                                  .filter(ProjectMember.project_id == project.id)\
                                  .filter(User.is_active == True)
    
    # Add project owner if not already included
    project_owner = User.query.get(project.created_by)
    team_members = list(team_members_query.all())
    if project_owner and project_owner not in team_members:
        team_members.append(project_owner)

    # Convert each User to dict
    team_members_serialized = [user.to_dict() for user in team_members]

    # Get current user's role and permissions for this project
    member = ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first()
    user_role = 'admin' if current_user.is_admin() else (
        'owner' if project.created_by == current_user.id else (member.role if member else 'member')
    )
    
    # Fix permissions - ensure project members have proper access
    if current_user.is_admin() or project.created_by == current_user.id:
        user_permissions = ['read', 'write', 'create', 'delete']
    elif member:
        user_permissions = member.permissions.split(',') if member.permissions else ['read', 'write']
    else:
        user_permissions = ['read']

    return render_template('canvas/canvas.html', 
        canvas=canvas, 
        project=project,
        team_members=team_members_serialized,
        user_role=user_role,
        user_permissions=user_permissions
    )

@canvas_bp.route('/api/canvas/<int:canvas_id>/save', methods=['POST'])
@login_required
def save_canvas(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    # Fix permission check - allow project members to save
    if not has_canvas_write_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Access denied - you do not have write permission'}), 403
    
    try:
        data = request.get_json()
        canvas.set_content_json(data.get('content', {}))
        canvas.last_saved = datetime.utcnow()
        canvas.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Canvas saved successfully',
            'last_saved': canvas.last_saved.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@canvas_bp.route('/api/canvas/<int:canvas_id>/load', methods=['GET'])
@login_required
def load_canvas(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    # Check access
    if not has_canvas_read_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'content': canvas.get_content_json(),
        'title': canvas.title,
        'last_saved': canvas.last_saved.isoformat() if canvas.last_saved else None
    })

@canvas_bp.route('/api/canvas/<int:canvas_id>/elements', methods=['GET'])
@login_required
def get_canvas_elements(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    # Check access
    if not has_canvas_read_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    elements = CanvasElement.query.filter_by(canvas_id=canvas_id).all()
    return jsonify({
        'success': True,
        'elements': [element.to_dict() for element in elements]
    })

@canvas_bp.route('/api/canvas/<int:canvas_id>/elements', methods=['POST'])
@login_required
def create_canvas_element(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    if not has_canvas_write_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        data = request.get_json()
        
        element = CanvasElement(
            canvas_id=canvas_id,
            element_type=data.get('element_type', 'text'),
            position_x=data.get('position_x', 0),
            position_y=data.get('position_y', 0),
            width=data.get('width', 200),
            height=data.get('height', 100),
            z_index=data.get('z_index', 1),
            created_by=current_user.id
        )
        
        element.set_content_json(data.get('content', {}))
        element.set_style_json(data.get('style', {}))
        
        db.session.add(element)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'element': element.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@canvas_bp.route('/api/canvas/elements/<int:element_id>', methods=['PUT'])
@login_required
def update_canvas_element(element_id):
    element = CanvasElement.query.get_or_404(element_id)
    
    if not has_canvas_write_permission(element.canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        data = request.get_json()
        
        element.position_x = data.get('position_x', element.position_x)
        element.position_y = data.get('position_y', element.position_y)
        element.width = data.get('width', element.width)
        element.height = data.get('height', element.height)
        element.z_index = data.get('z_index', element.z_index)
        element.updated_at = datetime.utcnow()
        
        if 'content' in data:
            element.set_content_json(data['content'])
        if 'style' in data:
            element.set_style_json(data['style'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'element': element.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@canvas_bp.route('/api/canvas/elements/<int:element_id>', methods=['DELETE'])
@login_required
def delete_canvas_element(element_id):
    element = CanvasElement.query.get_or_404(element_id)
    
    if not has_canvas_write_permission(element.canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        db.session.delete(element)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Element deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@canvas_bp.route('/api/canvas/<int:canvas_id>/chat/messages', methods=['GET'])
@login_required
def get_chat_messages(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    # Check access
    if not has_canvas_read_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    messages = CanvasChatMessage.query.filter_by(canvas_id=canvas_id)\
                                    .order_by(CanvasChatMessage.created_at.asc()).all()
    
    return jsonify({
        'success': True,
        'messages': [message.to_dict() for message in messages]
    })

@canvas_bp.route('/api/canvas/<int:canvas_id>/chat/messages', methods=['POST'])
@login_required
def send_chat_message(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    if not has_canvas_read_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        data = request.get_json()
        
        message = CanvasChatMessage(
            canvas_id=canvas_id,
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

# Project Chat endpoints (for project-wide chat)
@canvas_bp.route('/api/project/<int:project_id>/chat/messages', methods=['GET'])
@login_required
def get_project_chat_messages(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check access
    if not has_canvas_read_permission(project, current_user):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Get or create canvas for project chat
    canvas = Canvas.query.filter_by(project_id=project_id).first()
    if not canvas:
        canvas = Canvas(
            project_id=project_id,
            title=f"{project.title} - Canvas",
            created_by=current_user.id,
            content=json.dumps({'elements': [], 'settings': {'theme': 'light'}})
        )
        db.session.add(canvas)
        db.session.commit()
    
    messages = CanvasChatMessage.query.filter_by(canvas_id=canvas.id)\
                                    .order_by(CanvasChatMessage.created_at.asc()).all()
    
    return jsonify({
        'success': True,
        'messages': [message.to_dict() for message in messages]
    })

@canvas_bp.route('/api/project/<int:project_id>/chat/messages', methods=['POST'])
@login_required
def send_project_chat_message(project_id):
    project = Project.query.get_or_404(project_id)
    
    if not has_canvas_read_permission(project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        # Get or create canvas for project chat
        canvas = Canvas.query.filter_by(project_id=project_id).first()
        if not canvas:
            canvas = Canvas(
                project_id=project_id,
                title=f"{project.title} - Canvas",
                created_by=current_user.id,
                content=json.dumps({'elements': [], 'settings': {'theme': 'light'}})
            )
            db.session.add(canvas)
            db.session.commit()
        
        data = request.get_json()
        
        message = CanvasChatMessage(
            canvas_id=canvas.id,
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

@canvas_bp.route('/api/canvas/<int:canvas_id>/upload', methods=['POST'])
@login_required
def upload_file(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    if not has_canvas_write_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            upload_folder = ensure_upload_folder()
            
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Save file info to database
            canvas_file = CanvasFile(
                canvas_id=canvas_id,
                filename=filename,
                original_filename=file.filename,
                file_path=f'/static/uploads/canvas/{filename}',
                file_type=file.filename.rsplit('.', 1)[1].lower(),
                file_size=os.path.getsize(file_path),
                uploaded_by=current_user.id
            )
            
            db.session.add(canvas_file)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'file': canvas_file.to_dict(),
                'url': f'/static/uploads/canvas/{filename}',
                'filename': filename,
                'original_filename': file.filename,
                'file_type': canvas_file.file_type,
                'file_size': canvas_file.file_size
            })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"File upload error: {str(e)}")
            return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500
    
    return jsonify({'success': False, 'message': 'File type not allowed'}), 400

@canvas_bp.route('/api/canvas/<int:canvas_id>/files', methods=['GET'])
@login_required
def get_canvas_files(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    # Check access
    if not has_canvas_read_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    files = CanvasFile.query.filter_by(canvas_id=canvas_id)\
                           .order_by(CanvasFile.uploaded_at.desc()).all()
    
    return jsonify({
        'success': True,
        'files': [file.to_dict() for file in files]
    })

# Image Generation endpoint
@canvas_bp.route('/api/canvas/<int:canvas_id>/generate_image', methods=['POST'])
@login_required
def generate_image(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    # Check if user has write permission to add images to canvas
    if not has_canvas_write_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Permission denied - you need write access to generate images'}), 403
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'success': False, 'message': 'Prompt is required'}), 400
        
        # Optional parameters with defaults
        width = data.get('width', 512)
        height = data.get('height', 512)
        model = data.get('model', 'flux')
        
        # Validate dimensions
        if width not in [256, 512, 768, 1024] or height not in [256, 512, 768, 1024]:
            return jsonify({'success': False, 'message': 'Invalid dimensions. Supported sizes: 256, 512, 768, 1024'}), 400
        
        # URL encode the prompt for safe API usage
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Generate image URL using Pollinations AI
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={model}&width={width}&height={height}"
        
        # Test if the image URL is accessible
        try:
            response = requests.head(image_url, timeout=10)
            if response.status_code != 200:
                return jsonify({'success': False, 'message': 'Image generation service is currently unavailable'}), 503
        except requests.RequestException:
            return jsonify({'success': False, 'message': 'Unable to connect to image generation service'}), 503
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'prompt': prompt,
            'width': width,
            'height': height,
            'model': model,
            'generated_at': datetime.utcnow().isoformat(),
            'generated_by': current_user.get_full_name()
        })
        
    except Exception as e:
        current_app.logger.error(f"Image generation error: {str(e)}")
        return jsonify({'success': False, 'message': f'Image generation failed: {str(e)}'}), 500

# Real-time collaboration endpoint
@canvas_bp.route('/api/canvas/<int:canvas_id>/broadcast', methods=['POST'])
@login_required
def broadcast_canvas_update(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    
    if not has_canvas_read_permission(canvas.project, current_user):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        
        # Broadcast to all users in this canvas room
        socketio.emit('canvas_update', {
            'canvas_id': canvas_id,
            'user_id': current_user.id,
            'user_name': current_user.get_full_name(),
            'action': data.get('action'),
            'element_data': data.get('element_data'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'canvas_{canvas_id}')
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
