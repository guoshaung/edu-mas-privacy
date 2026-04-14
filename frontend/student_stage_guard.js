(() => {
  const currentScript = document.currentScript;
  const requiresDiagnosis = currentScript?.dataset.requiresDiagnosis === "true";
  const requiresPlanning = currentScript?.dataset.requiresPlanning === "true";

  function readJson(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      return null;
    }
  }

  const diagnosisResult = readJson("eduMasDiagnosisResult");
  const planningResult = readJson("eduMasPlanningResult");

  let notice = "";

  if (requiresDiagnosis && !diagnosisResult) {
    notice = "请先完成个性化诊断，再进入后续阶段。";
  } else if (requiresPlanning && !diagnosisResult) {
    notice = "请先完成个性化诊断，再进入辅导与知识检验阶段。";
  } else if (requiresPlanning && !planningResult) {
    notice = "请先生成学习规划，再进入辅导与知识检验阶段。";
  }

  if (!notice) return;

  sessionStorage.setItem("eduMasHubNotice", notice);
  window.location.replace("./student_hub.html");
})();
