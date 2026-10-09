import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api, authToken, setAuthToken } from "./api";
import type {
  Assignment,
  Device,
  Me,
  ModuleInfo,
  Reading,
  Resource,
  Role,
  Superadmin,
  User,
} from "./types";

type View = { kind: "home"; homeId: string } | { kind: "admin" } | null;

export default function App() {
  const [token, setToken] = useState<string | null>(authToken());
  const [me, setMe] = useState<Me | null>(null);
  const [homes, setHomes] = useState<Resource[]>([]);
  const [view, setView] = useState<View>(null);

  const refreshAuth = useCallback(async () => {
    const body = await api.auth.me();
    setMe(body);
  }, []);

  const loadHomes = useCallback(async () => {
    setHomes(await api.homes.list());
  }, []);

  useEffect(() => {
    if (!token) return;
    Promise.all([refreshAuth(), loadHomes()]).catch((e) => {
      if (e instanceof Error && e.message.startsWith("401")) setToken(null);
    });
  }, [token, refreshAuth, loadHomes]);

  if (!token)
    return <AuthScreen onAuthed={(t) => setToken(t)} />;
  if (!me) return <div className="page">Загрузка…</div>;

  return (
    <div className="page">
      <header className="topbar">
        <span className="brand">Умный дом</span>
        <span className="sub">{me.user.email}</span>
        <button
          className={view?.kind === "admin" ? "ghost-on" : "ghost"}
          onClick={() => setView({ kind: "admin" })}
        >
          Платформа
        </button>
        <button
          className="ghost"
          onClick={() => {
            setView(null);
            void api.auth.logout().catch(() => undefined);
            setAuthToken(null);
            setToken(null);
          }}
        >
          Выйти
        </button>
      </header>

      {view?.kind === "admin" ? (
        <AdminPanel homes={homes} />
      ) : view?.kind === "home" ? (
        <HomePanel
          key={view.homeId}
          homeId={view.homeId}
          rights={me.homes.find((h) => h.id === view.homeId)?.rights ?? []}
          onBack={() => setView(null)}
        />
      ) : (
        <HomeList
          homes={homes}
          rights={new Map(me.homes.map((h) => [h.id, h.rights]))}
          onCreate={async (name) => {
            await api.homes.create({ name });
            await loadHomes();
          }}
          onOpen={(id) => setView({ kind: "home", homeId: id })}
        />
      )}
    </div>
  );
}

function AuthScreen({ onAuthed }: { onAuthed: (token: string) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("ermoshinss");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (mode === "register") {
        await api.auth.register({ email, name, password });
      }
      const res = await api.auth.login({ email, password });
      setAuthToken(res.access_token);
      onAuthed(res.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="page auth">
      <form className="auth-card" onSubmit={submit}>
        <h1>Умный дом</h1>
        <p className="muted">Вход в платформу управления домом</p>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" type="email" required />
        {mode === "register" && (
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Имя" required />
        )}
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" type="password" required />
        {error && <div className="error-card">{error}</div>}
        <button type="submit">{mode === "login" ? "Войти" : "Зарегистрироваться"}</button>
        <button
          type="button"
          className="ghost"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Нет аккаунта? Регистрация" : "Уже есть аккаунт? Вход"}
        </button>
      </form>
    </div>
  );
}

function HomeList({
  homes,
  rights,
  onCreate,
  onOpen,
}: {
  homes: Resource[];
  rights: Map<string, string[]>;
  onCreate: (name: string) => void;
  onOpen: (id: string) => void;
}) {
  const [name, setName] = useState("");
  return (
    <main className="grid">
      <section className="panel">
        <h2>Мои дома</h2>
        <form
          className="row"
          onSubmit={(e) => {
            e.preventDefault();
            void onCreate(name);
            setName("");
          }}
        >
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название дома" required />
          <button type="submit">Создать дом</button>
        </form>
        {homes.length === 0 ? (
          <p className="muted">Домов пока нет.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Права</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {homes.map((h) => (
                <tr key={h.id}>
                  <td>{h.name}</td>
                  <td><span className="muted">{rights.get(h.id)?.join(", ") || "нет"}</span></td>
                  <td><button onClick={() => onOpen(h.id)}>Открыть</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}

function HomePanel({
  homeId,
  rights,
  onBack,
}: {
  homeId: string;
  rights: string[];
  onBack: () => void;
}) {
  const [home, setHome] = useState<Resource | null>(null);
  const [modules, setModules] = useState<Resource[]>([]);
  const [catalog, setCatalog] = useState<ModuleInfo[]>([]);
  const [roles, setRoles] = useState<Assignment[]>([]);
  const [canManageRoles, setCanManageRoles] = useState(false);
  const [alert, setAlert] = useState("");
  const canEdit = rights.includes("edit");

  const load = useCallback(async () => {
    const [h, ms, cat] = await Promise.all([
      api.homes.get(homeId),
      api.homes.modules(homeId),
      api.modules.list(),
    ]);
    setHome(h);
    setModules(ms);
    setCatalog(cat);
    try {
      setRoles(await api.homes.roles(homeId));
      setCanManageRoles(true);
    } catch {
      setCanManageRoles(false);
    }
  }, [homeId]);

  useEffect(() => {
    void load();
  }, [load]);

  const fail = (e: unknown) => setAlert(e instanceof Error ? e.message : String(e));

  return (
    <main className="grid">
      <section className="panel">
        <div className="row">
          <button className="ghost" onClick={onBack}>← К домам</button>
          <h2>{home?.name ?? "…"}</h2>
          <span className="muted">права: {rights.join(", ") || "нет"}</span>
          <button className="ghost" onClick={() => void load()}>Обновить</button>
        </div>
        {alert && <div className="error-card">{alert}</div>}

        <h3>Модули</h3>
        {modules.length === 0 && <p className="muted">Модули не включены.</p>}
        <table>
          <thead>
            <tr><th>Модуль</th><th>Действия</th></tr>
          </thead>
          <tbody>
            {modules.map((m) => (
              <tr key={m.id}>
                <td>{m.name} <code>{m.module_code}</code></td>
                <td>
                  {m.module_code === "climate" && <ClimateBlock homeId={homeId} canEdit={canEdit} onError={fail} key={m.id} />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {canEdit && (
          <EnableModule
            catalog={catalog.filter((c) => !modules.some((m) => m.module_code === c.code))}
            onEnable={async (code) => {
              await api.homes.enableModule(homeId, code).catch(fail);
              await load();
            }}
          />
        )}

        {canManageRoles && (
          <RolesPanel
            homeId={homeId}
            roles={roles}
            onChanged={load}
            onError={fail}
          />
        )}
      </section>
    </main>
  );
}

function EnableModule({
  catalog,
  onEnable,
}: {
  catalog: ModuleInfo[];
  onEnable: (code: string) => void;
}) {
  const [code, setCode] = useState(catalog[0]?.code ?? "");
  if (catalog.length === 0) return null;
  return (
    <form
      className="row"
      onSubmit={(e) => {
        e.preventDefault();
        void onEnable(code);
      }}
    >
      <select value={code} onChange={(e) => setCode(e.target.value)}>
        {catalog.map((c) => (
          <option key={c.code} value={c.code}>
            {c.title} ({c.code})
          </option>
        ))}
      </select>
      <button type="submit">Включить модуль</button>
    </form>
  );
}

function ClimateBlock({
  homeId,
  canEdit,
  onError,
}: {
  homeId: string;
  canEdit: boolean;
  onError: (e: unknown) => void;
}) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selected, setSelected] = useState<Device | null>(null);
  const [readings, setReadings] = useState<Reading[]>([]);

  const load = useCallback(async () => {
    const devices = await api.climate.listDevices(homeId).catch(() => null);
    if (devices) setDevices(devices);
  }, [homeId]);

  useEffect(() => {
    void load();
  }, [load]);

  const refreshSelected = (device: Device) => {
    setSelected(device);
    void api.climate
      .readings(homeId, device.id)
      .then(setReadings)
      .catch(onError);
  };

  return (
    <div>
      {canEdit && (
        <CreateDevice
          onCreate={async (name, kind) => {
            await api.climate.createDevice(homeId, { name, kind }).catch(onError);
            await load();
          }}
        />
      )}
      {devices.length === 0 ? (
        <p className="muted">Устройств нет.</p>
      ) : (
        <table>
          <thead>
            <tr><th>Устройство</th><th>Тип</th><th></th></tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id}>
                <td>{d.name}</td>
                <td>{d.kind}</td>
                <td><button onClick={() => refreshSelected(d)}>Показания</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {selected && (
        <div className="subpanel">
          <h4>{selected.name} · {selected.kind}</h4>
          <p className="muted">{JSON.stringify(selected.state)}</p>
          {canEdit && (
            <DeviceCommands
              onCommand={async (command, params) => {
                const updated = await api.climate.command(homeId, selected.id, command, params).catch(onError);
                if (updated) refreshSelected(updated);
              }}
            />
          )}
          <h4>Показания</h4>
          <table>
            <thead>
              <tr><th>Метрика</th><th>Значение</th></tr>
            </thead>
            <tbody>
              {readings.map((r) => (
                <tr key={r.id}>
                  <td>{r.metric}</td>
                  <td>{r.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function CreateDevice({
  onCreate,
}: {
  onCreate: (name: string, kind: string) => void;
}) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("sensor");
  return (
    <form
      className="row"
      onSubmit={(e) => {
        e.preventDefault();
        void onCreate(name, kind);
        setName("");
      }}
    >
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название" required />
      <select value={kind} onChange={(e) => setKind(e.target.value)}>
        <option value="sensor">датчик</option>
        <option value="controller">контроллер</option>
      </select>
      <button type="submit">Добавить устройство</button>
    </form>
  );
}

function DeviceCommands({
  onCommand,
}: {
  onCommand: (command: string, params: Record<string, unknown>) => void;
}) {
  const [temp, setTemp] = useState("22");
  return (
    <div className="row">
      <button onClick={() => void onCommand("power", { on: true })}>Вкл</button>
      <button onClick={() => void onCommand("power", { on: false })}>Выкл</button>
      <input value={temp} onChange={(e) => setTemp(e.target.value)} type="number" step="0.5" style={{ width: 70 }} />
      <button onClick={() => void onCommand("set_target", { target_temp: Number(temp) })}>
        Цель
      </button>
    </div>
  );
}

function RolesPanel({
  homeId,
  roles,
  onChanged,
  onError,
}: {
  homeId: string;
  roles: Assignment[];
  onChanged: () => void;
  onError: (e: unknown) => void;
}) {
  const [email, setEmail] = useState("");
  const [roleCode, setRoleCode] = useState("user");
  return (
    <div className="subpanel">
      <h3>Участники дома</h3>
      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          void api.homes
            .assignRole(homeId, { email, role_code: roleCode })
            .then(onChanged)
            .catch(onError);
          setEmail("");
        }}
      >
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email участника" type="email" required />
        <select value={roleCode} onChange={(e) => setRoleCode(e.target.value)}>
          <option value="user">user · просмотр</option>
          <option value="admin">admin · управление</option>
          <option value="owner">owner · владелец</option>
        </select>
        <button type="submit">Назначить роль</button>
      </form>
      {roles.map((r) => (
        <div className="row members" key={r.id}>
          <span>{r.email}</span>
          <code>{r.role_code}</code>
          <span className="muted">· {r.node_name}</span>
          <button
            className="ghost"
            onClick={() => void api.homes.revokeRole(homeId, r.id).then(onChanged).catch(onError)}
          >
            Убрать
          </button>
        </div>
      ))}
    </div>
  );
}

function AdminPanel({ homes }: { homes: Resource[] }) {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [superadmins, setSuperadmins] = useState<Superadmin[]>([]);
  const [adminHomes, setAdminHomes] = useState<Resource[]>([]);
  const [alert, setAlert] = useState("");

  const load = useCallback(async () => {
    try {
      setUsers(await api.admin.users());
      setRoles(await api.admin.roles());
      setSuperadmins(await api.admin.superadmins());
      setAdminHomes(await api.admin.homes());
    } catch (e) {
      setAlert(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main className="grid">
      {alert && <div className="error-card">{alert}</div>}
      <section className="panel">
        <h2>Пользователи</h2>
        <table>
          <thead>
            <tr><th>Имя</th><th>Email</th><th>Суперадмин</th></tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSa = superadmins.some((s) => s.user_id === u.id);
              return (
                <tr key={u.id}>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td>
                    {isSa ? (
                      <button
                        className="ghost"
                        onClick={() => void api.admin.revokeSuperadmin(u.id).then(load)}
                      >
                        Снять
                      </button>
                    ) : (
                      <button onClick={() => void api.admin.grantSuperadmin(u.id).then(load)}>
                        Дать
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <h2>Роли</h2>
        <table>
          <thead>
            <tr><th>Код</th><th>Имя</th><th>Область</th><th>view</th><th>edit</th></tr>
          </thead>
          <tbody>
            {roles.map((r) => (
              <tr key={r.id}>
                <td><code>{r.code}</code></td>
                <td>{r.name}</td>
                <td>{r.scope}</td>
                <td>{r.can_view ? "да" : "—"}</td>
                <td>{r.can_edit ? "да" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <h2>Все дома</h2>
        <table>
          <thead>
            <tr><th>Название</th><th>Тип</th><th>Модуль</th></tr>
          </thead>
          <tbody>
            {adminHomes.map((h) => (
              <tr key={h.id}>
                <td>{h.name}</td>
                <td>{h.node_type}</td>
                <td>{h.module_code ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">Всего домов: {homes.length}</p>
      </section>
    </main>
  );
}