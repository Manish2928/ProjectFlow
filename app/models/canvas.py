from datetime import datetime
from app import db
import json

class Canvas(db.Model):
    __tablename__ = 'canvas'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='Untitled Canvas')
    content = db.Column(db.Text)  # JSON content of canvas elements
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_saved = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='canvas_items')
    creator = db.relationship('User', backref='created_canvas')
    elements = db.relationship('CanvasElement', backref='canvas', cascade='all, delete-orphan')
    chat_messages = db.relationship('CanvasChatMessage', backref='canvas', cascade='all, delete-orphan')
    
    def get_content_json(self):
        if self.content:
            return json.loads(self.content)
        return {'elements': [], 'settings': {'theme': 'light'}}
    
    def set_content_json(self, content_dict):
        self.content = json.dumps(content_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'content': self.get_content_json(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_saved': self.last_saved.isoformat()
        }

class CanvasElement(db.Model):
    __tablename__ = 'canvas_elements'
    
    id = db.Column(db.Integer, primary_key=True)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvas.id'), nullable=False)
    element_type = db.Column(db.String(50), nullable=False)  # text, shape, image, document, etc.
    position_x = db.Column(db.Float, default=0)
    position_y = db.Column(db.Float, default=0)
    width = db.Column(db.Float, default=200)
    height = db.Column(db.Float, default=100)
    content = db.Column(db.Text)  # JSON content specific to element type
    style = db.Column(db.Text)  # JSON style properties
    z_index = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_content_json(self):
        if self.content:
            return json.loads(self.content)
        return {}
    
    def set_content_json(self, content_dict):
        self.content = json.dumps(content_dict)
    
    def get_style_json(self):
        if self.style:
            return json.loads(self.style)
        return {}
    
    def set_style_json(self, style_dict):
        self.style = json.dumps(style_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'canvas_id': self.canvas_id,
            'element_type': self.element_type,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width,
            'height': self.height,
            'content': self.get_content_json(),
            'style': self.get_style_json(),
            'z_index': self.z_index,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CanvasChatMessage(db.Model):
    __tablename__ = 'canvas_chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvas.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, file, image
    file_path = db.Column(db.String(500))  # for file attachments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='canvas_messages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'canvas_id': self.canvas_id,
            'user_id': self.user_id,
            'user_name': self.user.get_full_name(),
            'message': self.message,
            'message_type': self.message_type,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat()
        }

class CanvasFile(db.Model):
    __tablename__ = 'canvas_files'
    
    id = db.Column(db.Integer, primary_key=True)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvas.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_canvas_files')
    
    def to_dict(self):
        return {
            'id': self.id,
            'canvas_id': self.canvas_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.get_full_name(),
            'uploaded_at': self.uploaded_at.isoformat()
        }
