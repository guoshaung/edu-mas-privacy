const { chromium } = require("playwright");

const BASE_URL = "http://127.0.0.1:8000";

async function clickIfVisible(page, selector) {
  const locator = page.locator(selector);
  if (await locator.count()) {
    const first = locator.first();
    if (await first.isVisible()) {
      await first.click();
      return true;
    }
  }
  return false;
}

async function textIfAny(page, selector) {
  const locator = page.locator(selector);
  if (await locator.count()) {
    return (await locator.first().innerText()).trim();
  }
  return "";
}

async function bodyText(page) {
  return (await page.locator("body").innerText()).trim();
}

async function waitForSettledStatus(page, selector, timeout = 15000) {
  await page.waitForFunction(
    (sel) => {
      const node = document.querySelector(sel);
      if (!node) {
        return false;
      }
      const text = (node.textContent || "").trim();
      return text.length > 0 && !text.includes("正在");
    },
    selector,
    { timeout }
  );
}

async function main() {
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 1200 },
  });

  const page = await context.newPage();
  const consoleMessages = [];
  const requestFailures = [];

  page.on("console", (msg) => {
    if (["error", "warning"].includes(msg.type())) {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    }
  });

  page.on("requestfailed", (request) => {
    requestFailures.push(`${request.method()} ${request.url()} :: ${request.failure()?.errorText || "failed"}`);
  });

  const findings = [];

  await page.goto(`${BASE_URL}/login.html`, { waitUntil: "networkidle" });
  findings.push({
    area: "login",
    title: await page.title(),
    hasPasswordInput: (await page.locator('input[type="password"]').count()) > 0,
    primaryAction: await textIfAny(page, ".primary-button"),
  });

  await page.locator(".role-card").first().click();
  await page.locator('input[placeholder="张三"]').fill("张三");
  await page.locator('input[type="password"]').fill("123");
  await page.locator(".primary-button").click();
  await page.waitForURL("**/frontend/student_hub.html");
  findings.push({
    area: "student_hub",
    title: await page.title(),
    menuCount: await page.locator(".menu-link").count(),
    hasPlanningBridge: (await page.locator("#planningSummary").count()) > 0,
  });

  await page.goto(`${BASE_URL}/frontend/student_planning.html`, { waitUntil: "networkidle" });
  await page.locator("#generatePlanBtn").click();
  await waitForSettledStatus(page, "#requestStatus");
  findings.push({
    area: "student_planning",
    status: await textIfAny(page, "#requestStatus"),
    currentAgent: await textIfAny(page, "#currentAgent"),
    riskScore: await textIfAny(page, "#riskScore"),
  });

  await page.goto(`${BASE_URL}/frontend/student_tutoring.html`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);
  const tutoringText = await bodyText(page);
  await clickIfVisible(page, "#showCompanionBtn");
  await page.locator("#initBtn").click();
  await waitForSettledStatus(page, "#statusText");
  findings.push({
    area: "student_tutoring",
    title: await page.title(),
    mojibakeDetected: /姣|鏃|闄|杩|姝|榄|锟|�/.test(tutoringText),
    status: await textIfAny(page, "#statusText"),
    chatBubbleCount: await page.locator(".bubble").count(),
    hasVoiceMenuTrigger: (await page.locator("#showCompanionBtn").count()) > 0,
  });

  await page.goto(`${BASE_URL}/frontend/student_assessment.html`, { waitUntil: "networkidle" });
  await page.locator("#generateBtn").click();
  await waitForSettledStatus(page, "#statusText");
  findings.push({
    area: "student_assessment",
    status: await textIfAny(page, "#statusText"),
    questionCount: await page.locator(".question").count(),
  });

  await page.goto(`${BASE_URL}/frontend/privacy_lab.html`, { waitUntil: "networkidle" });
  await page.locator("#runAttackBtn").click();
  await waitForSettledStatus(page, "#statusText");
  findings.push({
    area: "privacy_lab",
    status: await textIfAny(page, "#statusText"),
    timelineCount: await page.locator(".timeline-item").count(),
    compareCardCount: await page.locator(".compare-card").count(),
  });

  await page.goto(`${BASE_URL}/frontend/teacher_question_bank.html`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  findings.push({
    area: "teacher_question_bank",
    title: await page.title(),
    resourceCount: await page.locator(".resource-item").count(),
    hasCopyrightLevel: (await page.locator("#copyrightLevelInput").count()) > 0,
    hasAccessScope: (await page.locator("#accessScopeInput").count()) > 0,
  });

  console.log(JSON.stringify({ findings, consoleMessages, requestFailures }, null, 2));
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
