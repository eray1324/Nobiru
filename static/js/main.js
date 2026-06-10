// Esperar a que toda la página web esté cargada
document.addEventListener('DOMContentLoaded', () => {
    console.log("Nobiru Engine Activo 🚀");

    // 1. Lógica para la sección de Reels (Grabar / Reproducir)
    const btnGrabar = document.getElementById('btn-grabar');
    const videoPreview = document.getElementById('video-preview');

    if (btnGrabar && videoPreview) {
        btnGrabar.addEventListener('click', async () => {
            try {
                // Solicita permiso para usar la cámara del celular o computadora
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                videoPreview.srcObject = stream;
                videoPreview.play();
                alert("¡Cámara activada! En una versión avanzada, aquí conectarías un MediaRecorder para guardar el archivo.");
            } catch (err) {
                alert("No se pudo acceder a la cámara: " + err.message);
            }
        });
    }

    // 2. Sistema de Favoritos (Guardar localmente)
    const botonesFavoritos = document.querySelectorAll('.btn-favorito');
    botonesFavoritos.forEach(boton => {
        boton.addEventListener('click', (e) => {
            const elementoId = e.target.dataset.id;
            const tipo = e.target.dataset.tipo; // 'pdf', 'video', 'quiz'
            
            // Obtener lo que ya estaba guardado o crear una lista vacía
            let favoritos = JSON.parse(localStorage.getItem('nobiru_favoritos')) || [];
            
            const item = { id: elementoId, tipo: tipo, fecha: new Date().toLocaleDateString() };
            
            // Evitar duplicados
            if (!favoritos.some(f => f.id === elementoId && f.tipo === tipo)) {
                favoritos.push(item);
                localStorage.setItem('nobiru_favoritos', JSON.stringify(favoritos));
                e.target.innerText = "⭐ Guardado en Favoritos";
                e.target.style.backgroundColor = "#ff8906";
            } else {
                alert("Este elemento ya está en tus favoritos.");
            }
        });
    });
});
