const loginForm = document.getElementById('form-login');

const emailInput = document.getElementById('email');

const passwordInput = document.getElementById('password');


loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = emailInput.value;
    const password = passwordInput.value;

    fetch("http://127.0.0.1:8000/auth/login", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        email: email,
        senha: password
    })
});
    
    // consultar no console do navegador os valores digitados nos campos de email e senha
    console.log('Email:', email);
    console.log('Password:', password);    
});
