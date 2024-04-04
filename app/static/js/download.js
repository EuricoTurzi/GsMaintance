document.addEventListener('DOMContentLoaded', function() {
    const downloadButtons = document.querySelectorAll('.download-button');
    downloadButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = this.closest('.download-form');
            const protocolo = form.querySelector('input[name="protocolo"]').value;
            const cliente = form.querySelector('input[name="cliente"]').value;
            const url = "/download_protocolo"; // Modificado para adicionar uma barra

            console.log("Enviando protocolo e cliente:", protocolo, cliente);

            fetch(url, {
                method: 'POST',
                body: JSON.stringify({ protocolo, cliente }),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                throw new Error('Erro ao gerar o protocolo.');
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${protocolo} - ${cliente}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Erro:', error);
            });
        });
    });
});
