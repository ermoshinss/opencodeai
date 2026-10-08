"""Эндпоинты модуля tenancy."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.tenancy import service
from app.modules.tenancy.models import Project, Workspace, WorkspaceMember
from app.modules.tenancy.schemas import (
    MemberRead,
    ProjectCreate,
    ProjectRead,
    WorkspaceCreate,
    WorkspaceRead,
)

router = APIRouter(prefix="/workspaces", tags=["tenancy"])


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(data: WorkspaceCreate, db: Session = Depends(get_db)) -> Workspace:
    return service.create_workspace(db, data)


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)) -> list[Workspace]:
    return service.list_workspaces(db)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(workspace_id: uuid.UUID, db: Session = Depends(get_db)) -> Workspace:
    return service.get_workspace(db, workspace_id)


@router.post(
    "/{workspace_id}/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
def create_project(
    workspace_id: uuid.UUID, data: ProjectCreate, db: Session = Depends(get_db)
) -> Project:
    return service.create_project(db, workspace_id, data)


@router.get("/{workspace_id}/projects", response_model=list[ProjectRead])
def list_projects(workspace_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Project]:
    return service.list_projects(db, workspace_id)


@router.get("/{workspace_id}/members", response_model=list[MemberRead])
def list_members(workspace_id: uuid.UUID, db: Session = Depends(get_db)) -> list[WorkspaceMember]:
    return service.list_members(db, workspace_id)
