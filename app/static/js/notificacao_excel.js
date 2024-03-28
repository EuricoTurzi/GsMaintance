var ultimaVerificacao = localStorage.getItem('ultimaVerificacao') || 0; // Recuperar a última verificação do armazenamento local
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

    // Atualizar o número de notificações e o contador no botão
    numNotificacoes++;
    document.getElementById('badgeNotificacoes').innerText = numNotificacoes;

    // Atualizar o texto do último protocolo no modal
    var protocoloAtualizado = "Último protocolo atualizado: " + message; // Aqui você deve colocar o protocolo real, por exemplo, o valor da coluna do protocolo na linha atualizada
    document.getElementById('ultimoProtocolo').innerText = protocoloAtualizado;
}

function verificarAtualizacaoExcel() {
    // Fazer uma requisição AJAX para a rota de verificação de atualização
    fetch('/verificar_atualizacao_excel')
        .then(response => response.text())
        .then(data => {
            // Exibir a resposta da rota no console (pode remover isso em produção)
            console.log('Resposta da rota:', data);
            
            // Converter a resposta para um número inteiro
            var numLinhas = parseInt(data);
            console.log('Número de linhas:', numLinhas);

            // Verificar se há uma atualização desde a última verificação
            if (numLinhas > ultimaVerificacao) {
                // Se houve atualização, mostrar o toast e atualizar a última verificação
                showToast('Houve atualização no Excel!');
                ultimaVerificacao = numLinhas;
                // Atualizar o valor no armazenamento local
                localStorage.setItem('ultimaVerificacao', ultimaVerificacao);
            }
        })
        .catch(error => console.error('Erro ao verificar atualização do Excel:', error));
}

// Chamar a função de verificação a cada 10 segundos
setInterval(verificarAtualizacaoExcel, 10000); // 10 segundos
