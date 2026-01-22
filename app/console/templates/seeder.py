"""Seeder templates for CLI commands"""

SEEDER_TEMPLATE = '''from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.{model_name} import {model_class}
from app.schemas.{model_name} import {model_class}Create

class {seeder_class}:
    def __init__(self, db: Session = next(get_db())):
        self.db = db
        self.model = {model_class}
        self.data = [
            {model_class}Create(
                email="user1@example.com",
                name="User One"
            ),
            {model_class}Create(
                email="user2@example.com",
                name="User Two"
            ),
            # Add more seed data here
        ]

    def run(self):
        """Run the seeder"""
        for item in self.data:
            # Check if item already exists
            existing = self.db.query(self.model).filter(
                self.model.email == item.email
            ).first()
            
            if not existing:
                db_item = self.model(**item.dict())
                self.db.add(db_item)
        
        self.db.commit()
        return len(self.data)

    def clear(self):
        """Clear seeded data"""
        self.db.query(self.model).delete()
        self.db.commit()
'''
