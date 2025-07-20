from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio
import json

@socketio.on('join_canvas')
def handle_join_canvas(data):
    canvas_id = data.get('canvas_id')
    if canvas_id:
        room = f"canvas_{canvas_id}"
        join_room(room)
        
        # Notify others that user joined
        emit('user_joined', {
            'user_id': current_user.id,
            'user_name': current_user.get_full_name(),
            'canvas_id': canvas_id
        }, room=room, include_self=False)
        
        print(f"User {current_user.get_full_name()} joined canvas {canvas_id}")

@socketio.on('leave_canvas')
def handle_leave_canvas(data):
    canvas_id = data.get('canvas_id')
    if canvas_id:
        room = f"canvas_{canvas_id}"
        leave_room(room)
        
        # Notify others that user left
        emit('user_left', {
            'user_id': current_user.id,
            'user_name': current_user.get_full_name(),
            'canvas_id': canvas_id
        }, room=room, include_self=False)
        
        print(f"User {current_user.get_full_name()} left canvas {canvas_id}")

@socketio.on('canvas_update')
def handle_canvas_update(data):
    canvas_id = data.get('canvas_id')
    if canvas_id:
        room = f"canvas_{canvas_id}"
        
        # Add user info to the update
        data['user_id'] = current_user.id
        data['user_name'] = current_user.get_full_name()
        
        # Broadcast to all other users in the room
        emit('canvas_update', data, room=room, include_self=False)
        
        print(f"Canvas update from {current_user.get_full_name()} in canvas {canvas_id}: {data.get('action')}")

@socketio.on('cursor_move')
def handle_cursor_move(data):
    canvas_id = data.get('canvas_id')
    if canvas_id:
        room = f"canvas_{canvas_id}"
        
        # Add user info
        data['user_id'] = current_user.id
        data['user_name'] = current_user.get_full_name()
        
        # Broadcast cursor position to others
        emit('cursor_update', data, room=room, include_self=False)

@socketio.on('element_select')
def handle_element_select(data):
    canvas_id = data.get('canvas_id')
    if canvas_id:
        room = f"canvas_{canvas_id}"
        
        # Add user info
        data['user_id'] = current_user.id
        data['user_name'] = current_user.get_full_name()
        
        # Broadcast selection to others
        emit('element_selected', data, room=room, include_self=False)

@socketio.on('chat_message')
def handle_chat_message(data):
    canvas_id = data.get('canvas_id')
    if canvas_id:
        room = f"canvas_{canvas_id}"
        
        # Add user info and timestamp
        data['user_id'] = current_user.id
        data['user_name'] = current_user.get_full_name()
        data['timestamp'] = data.get('timestamp')
        
        # Broadcast message to all users in the room
        emit('new_chat_message', data, room=room)
        
        print(f"Chat message from {current_user.get_full_name()} in canvas {canvas_id}")
