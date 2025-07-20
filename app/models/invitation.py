from datetime import datetime
from app import db

class ProjectInvitation(db.Model):
    __tablename__ = 'project_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, accepted, declined
    role = db.Column(db.String(20), nullable=False, default='member')  # member, viewer
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Relationships
    project = db.relationship('Project', backref='invitations')
    inviter = db.relationship('User', foreign_keys=[inviter_id], backref='sent_invitations')
    invitee = db.relationship('User', foreign_keys=[invitee_id], backref='received_invitations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_title': self.project.title,
            'inviter_id': self.inviter_id,
            'inviter_name': self.inviter.get_full_name(),
            'invitee_id': self.invitee_id,
            'invitee_name': self.invitee.get_full_name(),
            'status': self.status,
            'role': self.role,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }

class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # owner, member, viewer
    permissions = db.Column(db.String(100), default='read,write,create')  # read,write,create,delete
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='members')
    user = db.relationship('User', backref='project_memberships')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='unique_project_member'),)
    
    def has_permission(self, permission):
        return permission in self.permissions.split(',')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'user_name': self.user.get_full_name(),
            'user_email': self.user.email,
            'role': self.role,
            'permissions': self.permissions.split(','),
            'joined_at': self.joined_at.isoformat()
        }
