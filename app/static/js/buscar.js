// Função para filtrar as requisições
function filtrarRequisicoes() {
    var input, filter, cards, card, cardHeader, i, txtValue;
    input = document.getElementById("search-input");
    filter = input.value.toUpperCase();
    cards = document.getElementsByClassName("card");

    for (i = 0; i < cards.length; i++) {
        card = cards[i];
        cardHeader = card.getElementsByTagName("h3")[0];
        txtValue = cardHeader.textContent || cardHeader.innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            card.style.display = "";
        } else {
            card.style.display = "none";
        }
    }
}