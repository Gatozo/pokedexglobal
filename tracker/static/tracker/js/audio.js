/**
 * Pokédex Global - Reproductor de Sonidos y Gritos Pokémon (audio.js)
 */

let currentCryAudio = null;
export let activeModalCryUrl = '';

export function setActiveModalCryUrl(url) {
    activeModalCryUrl = url || '';
}

export function playPokemonCry(cryUrl, btnElem) {
    if (!cryUrl) return;
    try {
        if (currentCryAudio) {
            currentCryAudio.pause();
            currentCryAudio.currentTime = 0;
        }
        currentCryAudio = new Audio(cryUrl);
        currentCryAudio.volume = 0.6;
        currentCryAudio.play().catch(err => console.log("Audio play error:", err));

        if (btnElem) {
            btnElem.classList.add('text-amber-400', 'scale-125');
            setTimeout(() => {
                btnElem.classList.remove('text-amber-400', 'scale-125');
            }, 400);
        }
    } catch (err) {
        console.error("Error al reproducir audio:", err);
    }
}

export function playModalCry(btnElem) {
    if (activeModalCryUrl) {
        playPokemonCry(activeModalCryUrl, btnElem);
    }
}
