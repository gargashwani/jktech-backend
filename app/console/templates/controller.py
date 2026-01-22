"""Controller templates for CLI commands"""

BASIC_CONTROLLER_TEMPLATE = """from fastapi import APIRouter, Depends
from typing import List
from app.schemas.{model_name} import {model_class}Create, {model_class}Response
from app.services.{model_name} import {model_class}Service

router = APIRouter(prefix="/{model_name}s", tags=["{model_name}s"])

@router.get("/", response_model=List[{model_class}Response])
async def get_{model_name}s(service: {model_class}Service = Depends()):
    return await service.get_all()

@router.post("/", response_model={model_class}Response)
async def create_{model_name}({model_name}: {model_class}Create, service: {model_class}Service = Depends()):
    return await service.create({model_name})
"""

RESOURCE_CONTROLLER_TEMPLATE = """from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.{model_name} import {model_class}Create, {model_class}Update, {model_class}Response
from app.services.{model_name} import {model_class}Service

router = APIRouter(prefix="/{model_name}s", tags=["{model_name}s"])

@router.get("/", response_model=List[{model_class}Response])
async def get_{model_name}s(service: {model_class}Service = Depends()):
    return await service.get_all()

@router.post("/", response_model={model_class}Response, status_code=status.HTTP_201_CREATED)
async def create_{model_name}({model_name}: {model_class}Create, service: {model_class}Service = Depends()):
    return await service.create({model_name})

@router.get("/{{id}}", response_model={model_class}Response)
async def get_{model_name}(id: int, service: {model_class}Service = Depends()):
    {model_name} = await service.get_by_id(id)
    if not {model_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_class} not found")
    return {model_name}

@router.put("/{{id}}", response_model={model_class}Response)
async def update_{model_name}(id: int, {model_name}: {model_class}Update, service: {model_class}Service = Depends()):
    updated_{model_name} = await service.update(id, {model_name})
    if not updated_{model_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_class} not found")
    return updated_{model_name}

@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{model_name}(id: int, service: {model_class}Service = Depends()):
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_class} not found")
    return None
"""

API_CONTROLLER_TEMPLATE = """from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from app.schemas.{model_name} import {model_class}Create, {model_class}Update, {model_class}Response
from app.services.{model_name} import {model_class}Service
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/{model_name}s", tags=["{model_name}s"])

@router.get("/", response_model=List[{model_class}Response])
async def list_{model_name}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: {model_class}Service = Depends(),
    current_user = Depends(get_current_user)
):
    return await service.get_all(skip=skip, limit=limit)

@router.post("/", response_model={model_class}Response, status_code=status.HTTP_201_CREATED)
async def create_{model_name}(
    {model_name}: {model_class}Create,
    service: {model_class}Service = Depends(),
    current_user = Depends(get_current_user)
):
    return await service.create({model_name})

@router.get("/{{id}}", response_model={model_class}Response)
async def get_{model_name}(
    id: int = Path(..., ge=1),
    service: {model_class}Service = Depends(),
    current_user = Depends(get_current_user)
):
    {model_name} = await service.get_by_id(id)
    if not {model_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_class} not found")
    return {model_name}

@router.put("/{{id}}", response_model={model_class}Response)
async def update_{model_name}(
    id: int = Path(..., ge=1),
    {model_name}: {model_class}Update = Depends(),
    service: {model_class}Service = Depends(),
    current_user = Depends(get_current_user)
):
    updated_{model_name} = await service.update(id, {model_name})
    if not updated_{model_name}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_class} not found")
    return updated_{model_name}

@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{model_name}(
    id: int = Path(..., ge=1),
    service: {model_class}Service = Depends(),
    current_user = Depends(get_current_user)
):
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{model_class} not found")
    return None
"""
