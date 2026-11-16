
const loginForm = document.getElementById('form-login');

const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');

const erroMensagem = document.getElementById('erro');
const botaoLogin = loginForm.querySelector('button[type="submit"]');

// controla o envio do formulario
loginForm.addEventListener('submit', async (event) => {

    event.preventDefault();

    // limpa mensagens anteriores
    erroMensagem.textContent = '';

    // captura os dados digitados
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // evita varios envios simultaneos
    botaoLogin.disabled = true;
    botaoLogin.textContent = 'Entrando...';

    try {

        // envia as credenciais para o backend
        const resposta = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                senha: password
            })
        });

        // converte a resposta da api
        let dados = {};

        try {
            dados = await resposta.json();
        } catch {
            dados = {};
        }

        // verifica se o login foi recusado
        if (!resposta.ok) {

            if (resposta.status === 401) {
                erroMensagem.textContent = 'E-mail ou senha incorretos.';
            } else {
                erroMensagem.textContent = typeof dados.detail === 'string'
                    ? dados.detail
                    : 'Nao foi possivel realizar o login.';
            }

            return;
        }

        // verifica se o backend retornou o token
        if (!dados.access_token) {
            erroMensagem.textContent = 'Nao foi possivel obter o token de acesso.';
            return;
        }

        // armazena o token durante a sessao do navegador
        sessionStorage.setItem('token', dados.access_token);

        // redireciona para o dashboard
        window.location.href = 'inicio.html';

    } catch (erro) {

        // trata problemas de comunicacao com o backend
        erroMensagem.textContent = 'Nao foi possivel conectar ao servidor. Tente novamente.';

        console.error('Erro na autenticacao:', erro);

    } finally {

        // restaura o botao
        botaoLogin.disabled = false;
        botaoLogin.textContent = 'Login';
    }
});
