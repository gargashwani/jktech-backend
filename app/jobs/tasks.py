from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.user import User


@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_id: int):
    """
    Send welcome email to new user
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Implement email sending logic here
            print(f"Sending welcome email to {user.email}")
    finally:
        db.close()


@celery_app.task(name="process_user_data")
def process_user_data(user_id: int):
    """
    Process user data asynchronously
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Implement data processing logic here
            print(f"Processing data for user {user.email}")
    finally:
        db.close()
