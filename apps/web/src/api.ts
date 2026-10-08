import type { Grant, ModuleInfo, Project, User, Workspace } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${body}`);
  }
  return (await response.json()) as T;
}

export const api = {
  users: {
    list: () => request<User[]>("/users"),
    create: (data: { email: string; name: string }) =>
      request<User>("/users", { method: "POST", body: JSON.stringify(data) }),
  },
  workspaces: {
    list: () => request<Workspace[]>("/workspaces"),
    create: (data: { name: string; created_by: string }) =>
      request<Workspace>("/workspaces", { method: "POST", body: JSON.stringify(data) }),
    projects: (workspaceId: string) =>
      request<Project[]>(`/workspaces/${workspaceId}/projects`),
    createProject: (workspaceId: string, data: { name: string; created_by: string }) =>
      request<Project>(`/workspaces/${workspaceId}/projects`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  modules: {
    list: () => request<ModuleInfo[]>("/modules"),
  },
  admin: {
    grants: () => request<Grant[]>("/admin/grants"),
    upsertGrant: (
      workspaceId: string,
      data: { module_code: string; enabled: boolean },
    ) =>
      request<Grant>(`/admin/workspaces/${workspaceId}/modules`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};