import type {
  Assignment,
  Device,
  HomeRights,
  HomeStatus,
  Me,
  ModuleInfo,
  Reading,
  Resource,
  Role,
  Superadmin,
  User,
} from "./types";

const TOKEN_KEY = "opencodeai_token";

export function authToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string | null): void {
  if (token === null) localStorage.removeItem(TOKEN_KEY);
  else localStorage.setItem(TOKEN_KEY, token);
}

export interface ApiError extends Error {
  status: number;
  code?: string;
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = authToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`/api/v1${path}`, { ...init, headers });
  if (!response.ok) {
    let code: string | undefined;
    try {
      const body = (await response.json()) as { code?: string; message?: string };
      code = body.code;
    } catch {
      /* пустое тело */
    }
    const error = new Error(`${response.status}${code ? ` ${code}` : ""}`) as ApiError;
    error.status = response.status;
    error.code = code;
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const json = (method: string, body: unknown) => ({
  method,
  body: JSON.stringify(body),
});

export const api = {
  auth: {
    register: (data: { email: string; name: string; password: string }) =>
      request<User>("/auth/register", json("POST", data)),
    login: (data: { email: string; password: string }) =>
      request<{ access_token: string }>("/auth/login", json("POST", data)),
    logout: () => request<void>("/auth/logout", { method: "POST" }),
    me: () => request<Me>("/auth/me"),
  },
  homes: {
    list: () => request<Resource[]>("/homes"),
    create: (data: { name: string }) => request<Resource>("/homes", json("POST", data)),
    get: (homeId: string) => request<Resource>(`/homes/${homeId}`),
    modules: (homeId: string) => request<Resource[]>(`/homes/${homeId}/modules`),
    enableModule: (homeId: string, moduleCode: string) =>
      request<Resource>(`/homes/${homeId}/modules`, json("POST", { module_code: moduleCode })),
    roles: (homeId: string) => request<Assignment[]>(`/homes/${homeId}/roles`),
    assignRole: (
      homeId: string,
      data: { email: string; role_code: string; node_id?: string },
    ) => request<Assignment>(`/homes/${homeId}/roles`, json("POST", data)),
    revokeRole: (homeId: string, assignmentId: string) =>
      request<void>(`/homes/${homeId}/roles/${assignmentId}`, { method: "DELETE" }),
  },
  modules: {
    list: () => request<ModuleInfo[]>("/modules"),
  },
  climate: {
    listDevices: (homeId: string) =>
      request<Device[]>(`/homes/${homeId}/climate/devices`),
    createDevice: (homeId: string, data: { name: string; kind: string }) =>
      request<Device>(`/homes/${homeId}/climate/devices`, json("POST", data)),
    readings: (homeId: string, deviceId: string) =>
      request<Reading[]>(`/homes/${homeId}/climate/devices/${deviceId}/readings`),
    command: (
      homeId: string,
      deviceId: string,
      command: string,
      params: Record<string, unknown>,
    ) =>
      request<Device>(
        `/homes/${homeId}/climate/devices/${deviceId}/command`,
        json("POST", { command, params }),
      ),
    status: (homeId: string) => request<HomeStatus>(`/homes/${homeId}/climate/status`),
  },
  admin: {
    users: () => request<User[]>("/admin/users"),
    homes: () => request<Resource[]>("/admin/homes"),
    roles: () => request<Role[]>("/admin/roles"),
    superadmins: () => request<Superadmin[]>("/admin/superadmins"),
    grantSuperadmin: (userId: string) =>
      request<Superadmin>(`/admin/users/${userId}/superadmin`, { method: "POST" }),
    revokeSuperadmin: (userId: string) =>
      request<void>(`/admin/users/${userId}/superadmin`, { method: "DELETE" }),
  },
};

export type { HomeRights };