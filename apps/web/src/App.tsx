import { useCallback, useEffect, useState } from "react";

import { api } from "./api";
import type { Grant, ModuleInfo, Project, User, Workspace } from "./types";

type Status = "loading" | "ready" | "error";

export default function App() {
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string>("");
  const [users, setUsers] = useState<User[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [grants, setGrants] = useState<Grant[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const [u, w, m, g] = await Promise.all([
        api.users.list(),
        api.workspaces.list(),
        api.modules.list(),
        api.admin.grants(),
      ]);
      setUsers(u);
      setWorkspaces(w);
      setModules(m);
      setGrants(g);
      if (!selectedWorkspace && w.length > 0) setSelectedWorkspace(w[0].id);
      setStatus("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStatus("error");
    }
  }, [selectedWorkspace]);

  useEffect(() => {
    void load();
  }, [load]);

  const reload = () => void load();

  const createUser = async (email: string, name: string) => {
    await api.users.create({ email, name });
    reload();
  };

  const createWorkspace = async (name: string, createdBy: string) => {
    await api.workspaces.create({ name, created_by: createdBy });
    reload();
  };

  const selectWorkspace = async (id: string) => {
    setSelectedWorkspace(id);
    const p = await api.workspaces.projects(id);
    setProjects(p);
  };

  const createProject = async (name: string, createdBy: string) => {
    if (!selectedWorkspace) return;
    await api.workspaces.createProject(selectedWorkspace, {
      name,
      created_by: createdBy,
    });
    setProjects(await api.workspaces.projects(selectedWorkspace));
  };

  const toggleModule = async (workspaceId: string, code: string, enabled: boolean) => {
    await api.admin.upsertGrant(workspaceId, { module_code: code, enabled });
    reload();
  };

  if (status === "loading") return <div className="page">Загрузка…</div>;
  if (status === "error")
    return (
      <div className="page">
        <div className="error-card">
          <h2>Не удалось получить данные</h2>
          <p>{error}</p>
          <p className="muted">
            Убедитесь, что API запущен на :8000 (см. README → «Проверка работы»).
          </p>
          <button onClick={reload}>Повторить</button>
        </div>
      </div>
    );

  const selected = workspaces.find((w) => w.id === selectedWorkspace);
  const grantMap = new Map(grants.map((g) => [`${g.workspace_id}|${g.module_code}`, g.enabled]));

  return (
    <div className="page">
      <header className="topbar">
        <span className="brand">opencodeai</span>
        <span className="sub">Admin · админка платформы</span>
        <button className="ghost" onClick={reload}>
          Обновить
        </button>
      </header>

      <section className="cards">
        <Card label="Пользователи" value={users.length} />
        <Card label="Workspace" value={workspaces.length} />
        <Card label="Модули в каталоге" value={modules.length} />
        <Card label="Выданные grants" value={grants.length} />
      </section>

      <main className="grid">
        <section className="panel">
          <h2>Пользователи</h2>
          <CreateUserForm onCreate={createUser} />
          <table>
            <thead>
              <tr>
                <th>Имя</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="panel">
          <h2>Workspace → проекты</h2>
          <CreateWorkspaceForm users={users} onCreate={createWorkspace} />
          <select
            className="full"
            value={selectedWorkspace}
            onChange={(e) => void selectWorkspace(e.target.value)}
          >
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          {selected && (
            <>
              <CreateProjectForm
                users={users}
                onCreate={async (name, createdBy) => createProject(name, createdBy)}
              />
              <h3>Проекты «{selected.name}»</h3>
              <table>
                <thead>
                  <tr>
                    <th>Название</th>
                    <th>Создатель</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id}>
                      <td>{p.name}</td>
                      <td>{users.find((u) => u.id === p.created_by)?.name ?? p.created_by}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>

        <section className="panel">
          <h2>Доступ к модулям</h2>
          {selected ? (
            <table>
              <thead>
                <tr>
                  <th>Модуль</th>
                  <th>Версия</th>
                  <th>Включён</th>
                  <th>Переключить</th>
                </tr>
              </thead>
              <tbody>
                {modules.map((m) => {
                  const enabled = grantMap.get(`${selected.id}|${m.code}`) === true;
                  return (
                    <tr key={m.code}>
                      <td>
                        {m.title} <code>{m.code}</code>
                      </td>
                      <td>{m.version}</td>
                      <td>{enabled ? "да" : "нет"}</td>
                      <td>
                        <button onClick={() => void toggleModule(selected.id, m.code, !enabled)}>
                          {enabled ? "Выключить" : "Включить"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <p className="muted">Создайте workspace, чтобы управлять доступом.</p>
          )}
        </section>

        <section className="panel">
          <h2>Выданные grants</h2>
          <table>
            <thead>
              <tr>
                <th>Workspace</th>
                <th>Модуль</th>
                <th>Состояние</th>
              </tr>
            </thead>
            <tbody>
              {grants.map((g) => (
                <tr key={`${g.workspace_id}|${g.module_code}`}>
                  <td>{workspaces.find((w) => w.id === g.workspace_id)?.name ?? g.workspace_id}</td>
                  <td>{g.module_code}</td>
                  <td>{g.enabled ? "включён" : "выключен"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}

function Card({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <div className="card-value">{value}</div>
      <div className="card-label">{label}</div>
    </div>
  );
}

function CreateUserForm({ onCreate }: { onCreate: (email: string, name: string) => void }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  return (
    <form
      className="row"
      onSubmit={(e) => {
        e.preventDefault();
        void onCreate(email, name);
        setEmail("");
        setName("");
      }}
    >
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Имя" required />
      <input
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="email"
        type="email"
        required
      />
      <button type="submit">Создать</button>
    </form>
  );
}

function CreateWorkspaceForm({
  users,
  onCreate,
}: {
  users: User[];
  onCreate: (name: string, createdBy: string) => void;
}) {
  const [name, setName] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  return (
    <form
      className="row"
      onSubmit={(e) => {
        e.preventDefault();
        if (!createdBy) return;
        void onCreate(name, createdBy);
        setName("");
      }}
    >
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название" required />
      <select value={createdBy} onChange={(e) => setCreatedBy(e.target.value)} required>
        <option value="">владелец…</option>
        {users.map((u) => (
          <option key={u.id} value={u.id}>
            {u.name}
          </option>
        ))}
      </select>
      <button type="submit">Создать</button>
    </form>
  );
}

function CreateProjectForm({
  users,
  onCreate,
}: {
  users: User[];
  onCreate: (name: string, createdBy: string) => void;
}) {
  const [name, setName] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  return (
    <form
      className="row"
      onSubmit={(e) => {
        e.preventDefault();
        if (!createdBy) return;
        void onCreate(name, createdBy);
        setName("");
      }}
    >
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Проект" required />
      <select value={createdBy} onChange={(e) => setCreatedBy(e.target.value)} required>
        <option value="">создатель…</option>
        {users.map((u) => (
          <option key={u.id} value={u.id}>
            {u.name}
          </option>
        ))}
      </select>
      <button type="submit">Создать</button>
    </form>
  );
}