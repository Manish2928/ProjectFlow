from app import create_app, db, socketio
from app.models import User, Project, Task
from sqlalchemy import select
import os

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
