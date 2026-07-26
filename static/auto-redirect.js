// Author root redirect: if on author subdomain at root, redirect to /admin/
(function() {
  if (window.location.hostname === "author.meterai.digital"
      && (window.location.pathname === "/" || window.location.pathname === "")) {
    window.location.replace("/admin/");
  }
})();
