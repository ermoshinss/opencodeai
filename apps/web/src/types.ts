export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  created_by: string;
  created_at: string;
}

export interface ModuleInfo {
  code: string;
  title: string;
  version: string;
  state: string;
}

export interface Grant {
  workspace_id: string;
  module_code: string;
  enabled: boolean;
  config: Record<string, unknown>;
  updated_at: string;
}