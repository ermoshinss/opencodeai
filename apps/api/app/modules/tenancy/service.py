"""Сервис модуля tenancy."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.tenancy.models import Project, Workspace, WorkspaceMember
from app.modules.tenancy.schemas import ProjectCreate, WorkspaceCreate

OWNER_ROLE = "owner"


def create_workspace(db: Session, data: WorkspaceCreate) -> Workspace:
    workspace = Workspace(name=data.name, created_by=data.created_by)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=data.created_by, role=OWNER_ROLE))
    db.commit()
    db.refresh(workspace)
    return workspace


def list_workspaces(db: Session) -> list[Workspace]:
    return list(db.scalars(select(Workspace).order_by(Workspace.created_at)))


def get_workspace(db: Session, workspace_id: uuid.UUID) -> Workspace:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise ApiError("workspace_not_found", "Workspace не найден", status_code=404)
    return workspace


def create_project(db: Session, workspace_id: uuid.UUID, data: ProjectCreate) -> Project:
    get_workspace(db, workspace_id)
    project = Project(workspace_id=workspace_id, name=data.name, created_by=data.created_by)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, workspace_id: uuid.UUID) -> list[Project]:
    get_workspace(db, workspace_id)
    return list(
        db.scalars(
            select(Project).where(Project.workspace_id == workspace_id).order_by(Project.created_at)
        )
    )


def list_members(db: Session, workspace_id: uuid.UUID) -> list[WorkspaceMember]:
    get_workspace(db, workspace_id)
    return list(
        db.scalars(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.joined_at)
        )
    )
