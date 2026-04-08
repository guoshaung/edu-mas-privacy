const { useState } = React;

const roleOptions = [
  {
    id: "student",
    title: "学生入口",
    subtitle: "进入个性诊断、学习规划、自适应辅导与本地画像工作台。",
    target: "/frontend/student_hub.html",
    metrics: ["个性诊断", "学习规划", "知识检验", "本地画像"],
    username: "张三",
    password: "123",
  },
  {
    id: "teacher",
    title: "教师入口",
    subtitle: "进入教学观察、任务配置与班级概览工作台。",
    target: "/frontend/teacher_cn.html",
    metrics: ["班级概览", "任务配置", "学习追踪", "课堂反馈"],
    username: "李四",
    password: "123",
  },
];

function App() {
  const [selectedRole, setSelectedRole] = useState("student");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [errorText, setErrorText] = useState("");

  const activeRole = roleOptions.find((role) => role.id === selectedRole);

  const handleRoleChange = (roleId) => {
    setSelectedRole(roleId);
    setDisplayName("");
    setPassword("");
    setErrorText("");
  };

  const handleEnter = () => {
    const username = displayName.trim();

    if (!username || !password) {
      setErrorText("请输入用户名和密码。");
      return;
    }

    if (username !== activeRole.username || password !== activeRole.password) {
      setErrorText(
        `账号或密码错误。${activeRole.title}账号为“${activeRole.username}”，密码为“${activeRole.password}”。`
      );
      return;
    }

    const profile = {
      role: activeRole.id,
      displayName: username,
      updatedAt: new Date().toISOString(),
    };

    sessionStorage.setItem("eduMasProfile", JSON.stringify(profile));
    window.location.href = activeRole.target;
  };

  return (
    <div className="page-shell">
      <div className="orb orb-left"></div>
      <div className="orb orb-right"></div>

      <main className="portal-card">
        <section className="portal-copy">
          <span className="eyebrow">Multi-Agent Privacy Learning</span>
          <h1>统一登录门户</h1>
          <p>
            通过一个统一入口进入教师端或学生端。当前演示环境使用固定测试账号，后续可以继续接入真实鉴权接口。
          </p>
          <div className="pill-row">
            <span>React 入口</span>
            <span>角色分流</span>
            <span>隐私优先</span>
          </div>
          <div className="preview-panel">
            {activeRole.metrics.map((item) => (
              <article key={item} className="preview-tile">
                <strong>{item}</strong>
                <span>{activeRole.title}</span>
              </article>
            ))}
          </div>
        </section>

        <section className="login-panel">
          <div className="panel-header">
            <h2>选择角色</h2>
            <p>先确认你的身份，再进入对应工作台。</p>
          </div>

          <div className="role-grid">
            {roleOptions.map((role) => (
              <button
                key={role.id}
                type="button"
                className={`role-card ${selectedRole === role.id ? "active" : ""}`}
                onClick={() => handleRoleChange(role.id)}
              >
                <strong>{role.title}</strong>
                <span>{role.subtitle}</span>
              </button>
            ))}
          </div>

          <label className="input-group">
            <span>用户名</span>
            <input
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder={activeRole.username}
            />
          </label>

          <label className="input-group">
            <span>密码</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="请输入密码"
            />
          </label>

          {errorText ? <p className="tip-text" style={{ color: "#b42318" }}>{errorText}</p> : null}

          <button type="button" className="primary-button" onClick={handleEnter}>
            进入 {activeRole.title}
          </button>

          <p className="tip-text">测试账号：学生为“张三 / 123”，教师为“李四 / 123”。</p>
        </section>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
