const token = sessionStorage.getItem('token');

const listaAgendamentos = document.getElementById('lista-agendamentos');

const filtroStatus = document.getElementById('filtro-status');
const filtroData = document.getElementById('filtro-data');
const botaoLimparFiltros = document.getElementById('btn-limpar-filtros');

const botaoSair = document.getElementById('btn-sair');

let agendamentosCarregados = [];
let servicosPorId = {};


const STATUS = {
    agendado: {
        nome: 'Agendado',
        cor: 'confirmado',
        acoes: [
            { texto: 'Cancelar', novo: 'cancelado', classe: 'btn-cancelar-agendamento' }
        ]
    },
    cancelado: {
        nome: 'Cancelado',
        cor: 'cancelado',
        acoes: []
    }
};

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

// preenche o filtro de status com os status do objeto STATUS
function montarFiltroStatus() {
    // mantem so a opcao "Todos" antes de adicionar as demais
    filtroStatus.length = 1;

    Object.keys(STATUS).forEach(chave => {
        const opcao = document.createElement('option');
        opcao.value = chave;
        opcao.textContent = STATUS[chave].nome;
        filtroStatus.appendChild(opcao);
    });
}

// mostra uma mensagem ocupando a tabela inteira
function mostrarMensagemTabela(texto) {
    listaAgendamentos.textContent = '';

    const linha = document.createElement('tr');
    const celula = document.createElement('td');

    celula.colSpan = 5;
    celula.textContent = texto;

    linha.appendChild(celula);
    listaAgendamentos.appendChild(linha);
}

// converte 2026-11-26 para 26/11/2026
function formatarData(data) {
    if (!data) {
        return '-';
    }

    const [ano, mes, dia] = data.split('-');
    return `${dia}/${mes}/${ano}`;
}

// converte 15:30:00 para 15:30
function formatarHora(hora) {
    return hora ? hora.slice(0, 5) : '-';
}

// busca os servicos para trocar o id pelo nome na tabela
async function carregarServicos() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/servicos`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!resposta.ok) {
            return;
        }

        const dados = await obterDados(resposta);

        if (!Array.isArray(dados)) {
            return;
        }

        servicosPorId = {};

        dados.forEach(servico => {
            servicosPorId[servico.id_servico] = servico.nome;
        });

    } catch (erro) {
        console.error('Erro ao carregar servicos:', erro);
    }
}

// busca os agendamentos cadastrados
async function carregarAgendamentos() {
    try {
        // os servicos sao carregados antes para exibir o nome na tabela
        await carregarServicos();

        const resposta = await fetch(`${API_BASE_URL}/agendamentos`, {
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
            mostrarMensagemTabela('Nao foi possivel carregar os agendamentos.');
            return;
        }

        agendamentosCarregados = dados;
        exibirAgendamentos();

    } catch (erro) {
        mostrarMensagemTabela('Erro ao conectar com o servidor.');
        console.error('Erro ao carregar agendamentos:', erro);
    }
}

// aplica os filtros e exibe os agendamentos na tabela
function exibirAgendamentos() {
    const statusSelecionado = filtroStatus.value;
    const dataSelecionada = filtroData.value;

    const filtrados = agendamentosCarregados.filter(agendamento => {

        if (statusSelecionado && agendamento.status !== statusSelecionado) {
            return false;
        }

        // o input date e a api usam o mesmo formato (yyyy-mm-dd)
        if (dataSelecionada && agendamento.data_agendamento !== dataSelecionada) {
            return false;
        }

        return true;
    });

    // ordena por data e horario
    filtrados.sort((a, b) => {
        const inicioA = `${a.data_agendamento} ${a.horario_inicio}`;
        const inicioB = `${b.data_agendamento} ${b.horario_inicio}`;

        return inicioA.localeCompare(inicioB);
    });

    listaAgendamentos.textContent = '';

    if (filtrados.length === 0) {
        mostrarMensagemTabela('Nenhum agendamento encontrado.');
        return;
    }

    filtrados.forEach(agendamento => {
        const linha = document.createElement('tr');

        const colunaDataHora = document.createElement('td');
        colunaDataHora.textContent =
            `${formatarData(agendamento.data_agendamento)}, ` +
            `${formatarHora(agendamento.horario_inicio)} às ${formatarHora(agendamento.horario_fim)}`;

        const colunaCliente = document.createElement('td');
        colunaCliente.textContent = agendamento.nome_cliente;

        if (agendamento.telefone_cliente) {
            const telefone = document.createElement('span');
            telefone.className = 'telefone-cliente';
            telefone.textContent = agendamento.telefone_cliente;
            colunaCliente.appendChild(telefone);
        }

        const colunaServico = document.createElement('td');
        colunaServico.textContent =
            servicosPorId[agendamento.id_servico] || `Serviço #${agendamento.id_servico}`;

        // se vier um status que nao esta em STATUS, mostra o texto da api sem acoes
        const infoStatus = STATUS[agendamento.status] || {
            nome: agendamento.status,
            cor: '',
            acoes: []
        };

        const colunaStatus = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = `badge-status badge-${infoStatus.cor}`;
        badge.textContent = infoStatus.nome;
        colunaStatus.appendChild(badge);

        const colunaAcoes = document.createElement('td');

        if (infoStatus.acoes.length === 0) {
            colunaAcoes.textContent = '-';
        }

        infoStatus.acoes.forEach(acao => {
            const botao = document.createElement('button');

            botao.type = 'button';
            botao.className = acao.classe;
            botao.textContent = acao.texto;
            botao.dataset.id = agendamento.id_agendamento;
            botao.dataset.status = acao.novo;

            colunaAcoes.appendChild(botao);
        });

        linha.appendChild(colunaDataHora);
        linha.appendChild(colunaCliente);
        linha.appendChild(colunaServico);
        linha.appendChild(colunaStatus);
        linha.appendChild(colunaAcoes);

        listaAgendamentos.appendChild(linha);
    });
}

// monta o filtro e carrega os agendamentos ao abrir a pagina
montarFiltroStatus();

if (token) {
    carregarAgendamentos();
}

// refaz a lista quando o filtro muda
filtroStatus.addEventListener('change', exibirAgendamentos);
filtroData.addEventListener('change', exibirAgendamentos);

botaoLimparFiltros.addEventListener('click', () => {
    filtroStatus.value = '';
    filtroData.value = '';
    exibirAgendamentos();
});

// controla os botoes de concluir, confirmar e cancelar
listaAgendamentos.addEventListener('click', async (event) => {
    const botao = event.target.closest('button[data-id]');

    if (!botao) {
        return;
    }

    const id = Number(botao.dataset.id);
    const novoStatus = botao.dataset.status;

    const confirmar = confirm(
        `Deseja alterar este agendamento para "${STATUS[novoStatus].nome}"?`
    );

    if (!confirmar) {
        return;
    }

    try {
        const resposta = await fetch(`${API_BASE_URL}/agendamentos/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                status: novoStatus
            })
        });

        if (!verificarAutenticacao(resposta)) {
            return;
        }

        const dados = await obterDados(resposta);

        if (!resposta.ok) {
            alert(typeof dados.detail === 'string'
                ? dados.detail
                : 'Nao foi possivel atualizar o agendamento.');
            return;
        }

        await carregarAgendamentos();

        alert('Agendamento atualizado com sucesso!');

    } catch (erro) {
        alert('Erro ao conectar com o servidor.');
        console.error('Erro ao atualizar agendamento:', erro);
    }
});