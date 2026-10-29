// Names the portfolio account this browser is logged in to on the login button, when the portfolio says who that is.
(() => {
  const button = document.getElementById("portfolio-button");
  fetch(`${button.dataset.portfolioUrl}/sso/me`, { credentials: "include", signal: AbortSignal.timeout(5000) })
    .then((response) => (response.ok ? response.json() : {}))
    .then((data) => {
      if (data.username) button.textContent = `Log In as ${data.username}`;
    })
    .catch(() => {});
})();
