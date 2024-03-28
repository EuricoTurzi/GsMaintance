// Função para filtrar as requisições
function filtrarRequisicoes() {
    var input, filter, cards, card, cardHeader, i, txtValue;
    input = document.getElementById("search-input");
    filter = input.value.toUpperCase();
    cards = document.getElementsByClassName("card");

    // Capturar o valor do filtro de status
    var filtroStatus = document.getElementById('status-filter').value.toUpperCase();

    for (i = 0; i < cards.length; i++) {
        card = cards[i];
        cardHeader = card.getElementsByTagName("h3")[0];
        txtValue = cardHeader.textContent || cardHeader.innerText;

        if (txtValue.toUpperCase().indexOf(filter) > -1 &&
            (filtroStatus === '' || card.innerText.toUpperCase().indexOf(filtroStatus) > -1)) {
            card.style.display = "";
        } else {
            card.style.display = "none";
        }
    }
}

// Event listener para chamar a função de filtrar quando os dropdowns forem alterados
document.getElementById('status-filter').addEventListener('change', filtrarRequisicoes);
