(() => {
  const STORAGE_KEY = "eduMasProfile";
  const currentScript = document.currentScript;
  const requiredRole = currentScript?.dataset.requiredRole || "";
  const roleTextMap = {
    student: "\u5b66\u751f",
    teacher: "\u6559\u5e08",
  };

  function getProfile() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
    } catch (error) {
      return null;
    }
  }

  function buildLoginUrl() {
    return new URL("/login.html", window.location.href).toString();
  }

  function redirectToLogin() {
    window.location.replace(buildLoginUrl());
  }

  const profile = getProfile();
  if (!profile || (requiredRole && profile.role !== requiredRole)) {
    redirectToLogin();
  }

  function wireFastBackLinks() {
    document.querySelectorAll("[data-nav-back]").forEach((node) => {
      if (node.dataset.eduNavBound === "true") {
        return;
      }
      node.dataset.eduNavBound = "true";
      node.addEventListener("click", (event) => {
        const href = node.getAttribute("href");
        const referrer = document.referrer ? new URL(document.referrer, window.location.href) : null;
        const sameOriginReferrer = referrer && referrer.origin === window.location.origin;
        if (sameOriginReferrer && window.history.length > 1) {
          event.preventDefault();
          window.history.back();
          return;
        }
        if (!href) {
          event.preventDefault();
        }
      });
    });
  }

  function injectIdentityBadge() {
    const shellBar = document.querySelector(".menu-bar, .topbar");
    if (!shellBar || document.getElementById("eduMasIdentityBadge")) {
      return;
    }

    const style = document.createElement("style");
    style.textContent = `
      .edu-auth-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 9px 14px;
        border-radius: 999px;
        border: 1px solid #dbe3ee;
        background: #ffffff;
        color: #243447;
        font-weight: 700;
        box-shadow: 0 8px 20px rgba(36, 52, 71, 0.08);
      }
      .edu-auth-badge span:last-child {
        color: #6b7c93;
        font-weight: 600;
      }
    `;
    document.head.appendChild(style);

    const badge = document.createElement("div");
    badge.id = "eduMasIdentityBadge";
    badge.className = "edu-auth-badge";
    const roleLabel = roleTextMap[profile.role] || "\u7528\u6237";
    const displayName = profile.displayName || "\u672a\u547d\u540d";
    badge.innerHTML = `<span>${roleLabel}</span><span>${displayName}</span>`;
    shellBar.appendChild(badge);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      () => {
        injectIdentityBadge();
        wireFastBackLinks();
      },
      { once: true }
    );
  } else {
    injectIdentityBadge();
    wireFastBackLinks();
  }
})();
