"""Service templates for CLI commands"""

SERVICE_TEMPLATE = """from typing import List, Optional
from fastapi import Depends
from app.models.{model_name} import {model_class}
from app.schemas.{model_name} import {model_class}Create, {model_class}Response
from app.core.database import get_db
from sqlalchemy.orm import Session

class {service_class}:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def get_all(self) -> List[{model_class}Response]:
        return self.db.query({model_class}).all()

    async def get_by_id(self, id: int) -> Optional[{model_class}Response]:
        return self.db.query({model_class}).filter({model_class}.id == id).first()

    async def create(self, data: {model_class}Create) -> {model_class}Response:
        db_obj = {model_class}(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: int, data: {model_class}Create) -> {model_class}Response:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise Exception("Object not found")
        
        for key, value in data.dict().items():
            setattr(db_obj, key, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise Exception("Object not found")
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
"""

SERVICE_WITH_INTERFACE_TEMPLATE = """from abc import ABC, abstractmethod
from typing import List, Optional
from fastapi import Depends
from app.models.{model_name} import {model_class}
from app.schemas.{model_name} import {model_class}Create, {model_class}Response
from app.core.database import get_db
from sqlalchemy.orm import Session

class I{service_class}(ABC):
    @abstractmethod
    async def get_all(self) -> List[{model_class}Response]:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[{model_class}Response]:
        pass

    @abstractmethod
    async def create(self, data: {model_class}Create) -> {model_class}Response:
        pass

    @abstractmethod
    async def update(self, id: int, data: {model_class}Create) -> {model_class}Response:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass

class {service_class}(I{service_class}):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def get_all(self) -> List[{model_class}Response]:
        return self.db.query({model_class}).all()

    async def get_by_id(self, id: int) -> Optional[{model_class}Response]:
        return self.db.query({model_class}).filter({model_class}.id == id).first()

    async def create(self, data: {model_class}Create) -> {model_class}Response:
        db_obj = {model_class}(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: int, data: {model_class}Create) -> {model_class}Response:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise Exception("Object not found")
        
        for key, value in data.dict().items():
            setattr(db_obj, key, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise Exception("Object not found")
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
"""
