document.addEventListener('DOMContentLoaded', () => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  document.querySelectorAll('form').forEach(form => {
    if ((form.method || '').toLowerCase() === 'post' && !form.querySelector('[name="csrf_token"]')) {
      const input = document.createElement('input'); input.type = 'hidden'; input.name = 'csrf_token'; input.value = token || ''; form.appendChild(input);
    }
  });
  document.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', () => { if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = '/static/meal.svg'; } });
    if (img.complete && !img.naturalWidth) { img.dataset.fallback = '1'; img.src = '/static/meal.svg'; }
  });
});
const nativeFetch = window.fetch;
window.fetch = (input, options = {}) => {
  const url = new URL(typeof input === 'string' ? input : input.url, location.href);
  if (url.origin === location.origin) {
    const headers = new Headers(options.headers || (input instanceof Request ? input.headers : undefined));
    headers.set('X-CSRF-Token', document.querySelector('meta[name="csrf-token"]')?.content || ''); options = {...options, headers};
  }
  return nativeFetch(input, options);
};
