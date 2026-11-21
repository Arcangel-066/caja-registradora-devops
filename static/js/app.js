function agregarFila() {
    const plantilla = document.getElementById("fila-plantilla");
    const tbody = document.querySelector("#tabla-venta tbody");
    if (plantilla && tbody) {
        const clone = plantilla.content.cloneNode(true);
        tbody.appendChild(clone);
    }
}

function eliminarFila(boton) {
    const fila = boton.closest("tr");
    const tbody = fila.parentElement;
    if (tbody.querySelectorAll("tr").length > 1) {
        fila.remove();
    }
}

function confirmarEliminacion() {
    return confirm("¿Seguro que deseas eliminar este producto?");
}
