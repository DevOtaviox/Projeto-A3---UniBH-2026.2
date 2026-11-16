
const token = sessionStorage.getItem('token');

// verifica se existe um token de autenticacao
if (!token) {
    window.location.href = 'index.html';
}

// realiza o logout
const botaoSair = document.getElementById('btn-sair');

botaoSair.addEventListener('click', () => {
    sessionStorage.removeItem('token');
    window.location.href = 'index.html';
});
