export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface HomeRights {
  id: string;
  name: string;
  rights: string[];
}

export interface Me {
  user: User;
  homes: HomeRights[];
}

export interface Resource {
  id: string;
  home_id: string;
  parent_id: string | null;
  node_type: string;
  module_code: string | null;
  name: string;
  config: Record<string, unknown>;
}

export interface ModuleInfo {
  code: string;
  title: string;
  version: string;
  state: string;
}

export interface Role {
  id: string;
  code: string;
  name: string;
  scope: string;
  can_view: boolean;
  can_edit: boolean;
}

export interface Superadmin {
  user_id: string;
  granted_by: string | null;
  created_at: string;
}

export interface Assignment {
  id: string;
  user_id: string;
  email: string;
  role_code: string;
  role_name: string;
  node_id: string;
  node_name: string;
  created_at: string;
}

export interface Device {
  id: string;
  name: string;
  kind: string;
  state: Record<string, number | string>;
  created_at: string;
}

export interface Reading {
  id: string;
  metric: string;
  value: number;
  created_at: string;
}

export interface HomeStatus {
  enabled: boolean;
  device_count: number;
  devices: { id: string; name: string; state: Record<string, number | string> }[];
}