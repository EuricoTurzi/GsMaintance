    function handleAprovacaoChange(select) {
        const protocolo = select.closest('form').getAttribute('id').replace('aprovarForm', '');
        const dataAprovacaoInput = document.getElementById(`data_aprovacao_${protocolo}`);

        if (select.value === 'aprovar') {
            const now = new Date();
            const formattedDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
            dataAprovacaoInput.value = formattedDate;
        } else {
            dataAprovacaoInput.value = '';
        }
    }