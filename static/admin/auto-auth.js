(function() {
  // Auto-redirect root to /admin/ (after basic auth is passed)
  if (window.location.pathname === "/" || window.location.pathname === "") {
    window.location.replace("/admin/");
    return;
  }

  // GitHub PAT injected at deploy time by entrypoint script
  var pat = "__GITHUB_PAT_PLACEHOLDER__";
  if (pat && pat.indexOf("__") === -1) {
    var user = {
      name: "Aksa",
      login: "aksatera",
      avatar_url: "",
      html_url: "https://github.com/aksatera",
      token: pat,
      backendName: "github"
    };
    localStorage.setItem("netlify-cms-user", JSON.stringify(user));
  }
})();
