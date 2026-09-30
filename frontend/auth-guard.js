// Sessions live in DynamoDB (cookie "agri_session"). Any API call that comes back 401
// (no/expired session) sends the user back to the login page.
(function () {
    var nativeFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
        return nativeFetch(input, init).then(function (res) {
            var url = typeof input === 'string' ? input : (input && input.url) || '';
            if (res.status === 401 && url.indexOf('/api/') !== -1 && url.indexOf('/api/login') === -1) {
                localStorage.removeItem('currentUser');
                window.location.href = 'index.html';
            }
            return res;
        });
    };
})();


// Hide sidebar links the signed-in role cannot open (the server enforces it as well)
(function () {
    var PAGES = {
        'data admin': ['/inventory.html'],
        'admin': ['/inventory.html'],
        'executive': ['/dashboard.html', '/agent.html'],
        'data analyst': ['/dashboard.html', '/agent.html']
    };
    function apply() {
        var user = null;
        try { user = JSON.parse(localStorage.getItem('currentUser') || 'null'); } catch (e) { /* ignore */ }
        var roleName = user && String(user.role || '').trim().toLowerCase();
        var allowed = roleName && PAGES[roleName];
        if (!allowed) return;
        document.querySelectorAll('.nav-item a[href]').forEach(function (a) {
            var m = /^\/?(dashboard|inventory|agent)\.html(?:[?#].*)?$/.exec(a.getAttribute('href') || '');
            if (m && allowed.indexOf('/' + m[1] + '.html') === -1) {
                var li = a.closest('li');
                if (li) li.style.display = 'none';
            }
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
    else apply();
})();
