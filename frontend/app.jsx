const { useState } = React;

const roleOptions = [
  {
    id: "student",
    title: "学生入口",
    subtitle: "进入个性化学习、隐私保护问答与学习支持界面。",
    target: "./student_cn.html",
    metrics: ["提问与对话", "学习规划", "知识检测", "隐私网关"],
  },
  {
    id: "teacher",
    title: "教师入口",
    subtitle: "进入教学分析、资源调度与课堂管理界面。",
    target: "./teacher_cn.html",
    metrics: ["班级画像", "资源编排", "学习监测", "策略反馈"],
  },
];

function App() {
  const [selectedRole, setSelectedRole] = useState("student");
  const [displayName, setDisplayName] = useState("");

  const activeRole = roleOptions.find((role) => role.id === selectedRole);

  const handleEnter = () => {
    const profile = {
      role: activeRole.id,
      displayName: displayName.trim(),
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
            保留现有教师端与学生端页面，在统一入口完成身份选择后再进入对应工作台。
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
            <p>先确认你的身份，再进入现有的教师端或学生端页面。</p>
          </div>

          <div className="role-grid">
            {roleOptions.map((role) => (
              <button
                key={role.id}
                type="button"
                className={`role-card ${selectedRole === role.id ? "active" : ""}`}
                onClick={() => setSelectedRole(role.id)}
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
              placeholder="请输入姓名或账号"
            />
          </label>

          <button type="button" className="primary-button" onClick={handleEnter}>
            进入 {activeRole.title}
          </button>

          <p className="tip-text">
            登录信息会暂存到当前浏览器会话，后续可以继续接教师端与学生端的真实鉴权接口。
          </p>
        </section>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
