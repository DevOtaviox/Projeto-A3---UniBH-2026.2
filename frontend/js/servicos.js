
const token = sessionStorage.getItem('token');

const listaServicos = document.getElementById('lista-servicos');
const modalServico = document.getElementById('modal-servico');
const formServico = document.getElementById('form-servico');
const mensagemServico = document.getElementById('mensagem-servico');

const botaoSair = document.getElementById('btn-sair');
const botaoNovoServico = document.getElementById('btn-novo-servico');
const botaoFecharModal = document.getElementById('btn-fechar-modal');
const botaoCancelar = document.getElementById('btn-cancelar');

const tituloModal = modalServico.querySelector('.modal-header h2');
const botaoSalvar = formServico.querySelector('button[type="submit"]');

let servicosCarregados = [];
let idServicoEdicao = null;

// verifica se existe um token de autenticacao
if (!token) {
    window.location.href = 'index.html';
}

// realiza o logout
botaoSair.addEventListener('click', () => {
    sessionStorage.removeItem('token');
    window.location.href = 'index.html';
});

// trata respostas que podem nao estar em json
async function obterDados(resposta) {
    try {
        return await resposta.json();
    } catch {
        return {};
    }
}

// verifica se a sessao ainda e valida
function verificarAutenticacao(resposta) {
    if (resposta.status === 401) {
        sessionStorage.removeItem('token');
        window.location.href = 'index.html';
        return false;
    }

    return true;
}

// busca os servicos cadastrados
async function carregarServicos() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/servicos`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!verificarAutenticacao(resposta)) {
            return;
        }

        const dados = await obterDados(resposta);

        if (!resposta.ok || !Array.isArray(dados)) {
            listaServicos.textContent = '';

            const linha = document.createElement('tr');
            const celula = document.createElement('td');

            celula.colSpan = 5;
            celula.textContent = 'Nao foi possivel carregar os servicos.';

            linha.appendChild(celula);
            listaServicos.appendChild(linha);
            return;
        }

        servicosCarregados = dados;
        listaServicos.textContent = '';

        if (dados.length === 0) {
            const linha = document.createElement('tr');
            const celula = document.createElement('td');

            celula.colSpan = 5;
            celula.textContent = 'Nenhum servico cadastrado.';

            linha.appendChild(celula);
            listaServicos.appendChild(linha);
            return;
        }

        // exibe os servicos na tabela
        dados.forEach(servico => {
            const linha = document.createElement('tr');

            const colunaNome = document.createElement('td');
            colunaNome.textContent = servico.nome;

            const colunaPreco = document.createElement('td');
            colunaPreco.textContent = Number(servico.preco).toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });

            const colunaDuracao = document.createElement('td');
            colunaDuracao.textContent = `${servico.duracao_minutos} min`;

            const colunaStatus = document.createElement('td');
            colunaStatus.textContent = servico.ativo ? 'Ativo' : 'Inativo';

            const colunaAcoes = document.createElement('td');

            const botaoEditar = document.createElement('button');
            botaoEditar.className = 'btn-editar';
            botaoEditar.dataset.id = servico.id_servico;
            botaoEditar.textContent = 'Editar';

            const botaoStatus = document.createElement('button');
            botaoStatus.className = 'btn-status';
            botaoStatus.dataset.id = servico.id_servico;
            botaoStatus.dataset.ativo = servico.ativo;
            botaoStatus.textContent = servico.ativo ? 'Desativar' : 'Ativar';

            colunaAcoes.appendChild(botaoEditar);
            colunaAcoes.appendChild(botaoStatus);

            linha.appendChild(colunaNome);
            linha.appendChild(colunaPreco);
            linha.appendChild(colunaDuracao);
            linha.appendChild(colunaStatus);
            linha.appendChild(colunaAcoes);

            listaServicos.appendChild(linha);
        });

    } catch (erro) {
        listaServicos.textContent = '';

        const linha = document.createElement('tr');
        const celula = document.createElement('td');

        celula.colSpan = 5;
        celula.textContent = 'Erro ao conectar com o servidor.';

        linha.appendChild(celula);
        listaServicos.appendChild(linha);

        console.error('Erro ao carregar servicos:', erro);
    }
}

// carrega os servicos ao abrir a pagina
if (token) {
    carregarServicos();
}

// abre o formulario para novo servico
botaoNovoServico.addEventListener('click', () => {
    idServicoEdicao = null;

    formServico.reset();
    mensagemServico.textContent = '';

    tituloModal.textContent = 'Novo serviço';
    botaoSalvar.textContent = 'Salvar serviço';

    modalServico.classList.add('aberto');
});

// fecha o formulario
function fecharModal() {
    modalServico.classList.remove('aberto');
    formServico.reset();
    mensagemServico.textContent = '';
    idServicoEdicao = null;
}

botaoFecharModal.addEventListener('click', fecharModal);
botaoCancelar.addEventListener('click', fecharModal);

// fecha ao clicar fora do formulario
modalServico.addEventListener('click', (event) => {
    if (event.target === modalServico) {
        fecharModal();
    }
});

// controla os botoes de editar e alterar status
listaServicos.addEventListener('click', async (event) => {
    const botaoEditar = event.target.closest('.btn-editar');
    const botaoStatus = event.target.closest('.btn-status');

    // abre o formulario com os dados do servico
    if (botaoEditar) {
        const id = Number(botaoEditar.dataset.id);

        const servico = servicosCarregados.find(item =>
            item.id_servico === id
        );

        if (!servico) {
            return;
        }

        idServicoEdicao = id;

        document.getElementById('nome-servico').value = servico.nome;
        document.getElementById('descricao-servico').value = servico.descricao || '';
        document.getElementById('preco-servico').value = servico.preco;
        document.getElementById('duracao-servico').value = servico.duracao_minutos;

        tituloModal.textContent = 'Editar serviço';
        botaoSalvar.textContent = 'Salvar alterações';
        mensagemServico.textContent = '';

        modalServico.classList.add('aberto');
        return;
    }

    // ativa ou desativa um servico
    if (botaoStatus) {
        const id = Number(botaoStatus.dataset.id);
        const ativoAtual = botaoStatus.dataset.ativo === 'true';

        const confirmar = confirm(
            `Deseja ${ativoAtual ? 'desativar' : 'ativar'} este servico?`
        );

        if (!confirmar) {
            return;
        }

        try {
            const resposta = await fetch(`${API_BASE_URL}/servicos/${id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    ativo: !ativoAtual
                })
            });

            if (!verificarAutenticacao(resposta)) {
                return;
            }

            if (!resposta.ok) {
                alert('Nao foi possivel alterar o status do servico.');
                return;
            }

            await carregarServicos();

            alert('Status do servico atualizado com sucesso!');

        } catch (erro) {
            alert('Erro ao conectar com o servidor.');
            console.error('Erro ao alterar status:', erro);
        }
    }
});

// cadastra ou atualiza um servico
formServico.addEventListener('submit', async (event) => {
    event.preventDefault();

    mensagemServico.textContent = '';

    const nome = document.getElementById('nome-servico').value.trim();
    const descricao = document.getElementById('descricao-servico').value.trim();
    const preco = Number(document.getElementById('preco-servico').value);
    const duracao = Number(document.getElementById('duracao-servico').value);

    const servico = {
        nome: nome,
        descricao: descricao || null,
        preco: preco,
        duracao_minutos: duracao
    };

    // define se sera cadastro ou atualizacao
    const editando = idServicoEdicao !== null;

    const url = editando
        ? `${API_BASE_URL}/servicos/${idServicoEdicao}`
        : `${API_BASE_URL}/servicos`;

    const metodo = editando ? 'PATCH' : 'POST';

    botaoSalvar.disabled = true;

    try {
        const resposta = await fetch(url, {
            method: metodo,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(servico)
        });

        if (!verificarAutenticacao(resposta)) {
            return;
        }

        const dados = await obterDados(resposta);

        if (!resposta.ok) {
            mensagemServico.textContent = typeof dados.detail === 'string'
                ? dados.detail
                : 'Nao foi possivel salvar o servico.';
            return;
        }

        fecharModal();

        await carregarServicos();

        alert(editando
            ? 'Servico atualizado com sucesso!'
            : 'Servico cadastrado com sucesso!');

    } catch (erro) {
        mensagemServico.textContent = 'Erro ao conectar com o servidor.';
        console.error('Erro ao salvar servico:', erro);

    } finally {
        botaoSalvar.disabled = false;
    }
});
