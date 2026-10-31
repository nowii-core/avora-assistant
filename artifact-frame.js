/* Loader of the sandboxed preview frame. The page is served with a strict CSP: inline scripts,
   network access and forms are blocked, so previews are static renderings only. */
window.addEventListener('message', event => {
  if (event.source !== window.parent) return;
  const html = String((event.data && event.data.html) || '');
  document.open(); document.write(html); document.close();
});
if (window.parent !== window) window.parent.postMessage({ ready: true }, '*');
