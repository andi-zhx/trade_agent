(() => {
  const csrf = () => document.querySelector('meta[name="csrf-token"]').content;
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    const method = (init.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    if (url.origin === location.origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
      headers.set('X-CSRFToken', csrf()); init = {...init, headers};
    }
    return originalFetch(input, init);
  };
  window.getPrivilegedDeletePassword = (message) => {
    if (!window.APP_IS_ADMIN) { alert('仅管理员可以移除资料。'); return null; }
    if (message && !confirm(message)) return null;
    return prompt('请输入你当前的管理员密码确认操作：');
  };
  window.confirmPrivilegedDelete = (formOrButton, message) => {
    const password = window.getPrivilegedDeletePassword(message);
    if (password === null) return false;
    const form = formOrButton.tagName === 'FORM' ? formOrButton : formOrButton.form;
    if (!form) return false;
    let field = form.querySelector('[name="admin_password"]');
    if (!field) { field = document.createElement('input'); field.type = 'hidden'; field.name = 'admin_password'; form.appendChild(field); }
    field.value = password; return true;
  };
  document.querySelectorAll('form[data-guard-unsaved]').forEach(form => {
    let dirty = false, submitting = false;
    const status = form.querySelector('[data-save-status]');
    form.addEventListener('input', () => { dirty = true; if (status) status.textContent = '有修改尚未保存'; });
    form.addEventListener('change', () => { dirty = true; });
    window.addEventListener('beforeunload', event => { if (dirty && !submitting) { event.preventDefault(); event.returnValue = ''; } });
    form.addEventListener('submit', event => {
      if (submitting) { event.preventDefault(); return; }
      submitting = true;
      if (status) status.textContent = '正在保存，请稍候…';
      setTimeout(() => form.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = true; }), 0);
    });
    window.addEventListener('pageshow', event => {
      if (event.persisted) { submitting = false; form.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = false; }); if (status) status.textContent = '请确认内容后保存。'; }
    });
  });
})();
