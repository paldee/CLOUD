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
