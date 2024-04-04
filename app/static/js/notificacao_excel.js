var ultimaVerificacao = localStorage.getItem('ultimaVerificacao') || ''; // Recuperar a última verificação do armazenamento local
var numNotificacoes = 0; // Inicializar o número de notificações

function showToast(message) {
    console.log('Exibindo toast:', message); // Adicionando log para debug
    var toastEl = document.getElementById('liveToast');
    console.log('Elemento toast:', toastEl); // Novo log para verificar o elemento
    var toast = new bootstrap.Toast(toastEl);
    toast.show();
    // Atualizar o conteúdo do toast com a mensagem
    document.querySelector('.toast-body').innerText = message;

    // Reproduzir o alerta sonoro
    const alertaSonoro = document.getElementById('alertaSonoro');
    alertaSonoro.play();

    // Atualizar a variável ultimaMensagem com a mensagem atual
    ultimaMensagem = message;

    // Atualizar o número de notificações e o contador no botão
    numNotificacoes++;
    document.getElementById('badgeNotificacoes').innerText = numNotificacoes;

    // Atualizar o texto do último protocolo no modal
    document.getElementById('ultimoProtocolo').innerText = ultimaMensagem;
}

function verificarAtualizacaoExcel() {
    // Fazer uma requisição AJAX para a rota de verificação de atualização
    fetch('/verificar_atualizacao_excel')
        .then(response => response.text())
        .then(data => {
            // Exibir a resposta da rota no console (pode remover isso em produção)
            console.log('Resposta da rota:', data);

            // Verificar se há uma atualização desde a última verificação
            if (data !== ultimaVerificacao) {
                // Se houve atualização, buscar a última manutenção
                fetch('/ultima_manutencao')
                    .then(response => response.json())
                    .then(manutencao => {
                        // Formatar a mensagem do toast com o protocolo e cliente da última manutenção
                        var mensagem = `Nova manutenção em sistema! \nProtocolo:${manutencao['Protocolo']} \nCliente: ${manutencao['Nome do Cliente']}`;
                        // Mostrar o toast com a mensagem
                        showToast(mensagem);
                    })
                    .catch(error => console.error('Erro ao obter última manutenção:', error));

                ultimaVerificacao = data;
                // Atualizar o valor no armazenamento local
                localStorage.setItem('ultimaVerificacao', ultimaVerificacao);
            }
        })
        .catch(error => console.error('Erro ao verificar atualização do Excel:', error));
}

// Chamar a função de verificação a cada 5 minutos
setInterval(verificarAtualizacaoExcel, 300000); // 5 minutos
