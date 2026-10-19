/**
 * Pokédex Global - Calculadora y Configuración de Partida (game_config.js)
 * Módulo para gestionar configuraciones por partida, como la calculadora de árboles de Munchlax en Gen 4.
 */

// Lista canónica de los 21 árboles de miel de Sinnoh (índices internos 0 a 20 de la ROM de DPPt/BDSP)
export const SINNOH_HONEY_TREES = {
    0: "Ruta 205 (Norte)",
    1: "Ruta 205 (Sur)",
    2: "Ruta 206 (Camino de Bicis)",
    3: "Ruta 207",
    4: "Ruta 208",
    5: "Ruta 209",
    6: "Ruta 210 (Norte)",
    7: "Ruta 210 (Sur)",
    8: "Ruta 211 (Este)",
    9: "Ruta 212 (Norte)",
    10: "Ruta 212 (Sur)",
    11: "Ruta 213",
    12: "Ruta 214",
    13: "Ruta 215",
    14: "Ruta 218",
    15: "Ruta 221",
    16: "Ruta 222",
    17: "Valle Eólico",
    18: "Bosque Vetusto",
    19: "Forja Fuego",
    20: "Prado Aromaflor"
};

/**
 * Calcula los índices de los árboles de Munchlax en Sinnoh según el algoritmo canónico.
 * @param {number} tid - Trainer ID (0 - 65535)
 * @param {number|null} sid - Secret ID (0 - 65535, opcional)
 * @returns {Array<number>} Índices (0-20) de los árboles calculados. 2 si solo hay TID, 4 si hay TID y SID.
 */
export function calculateMunchlaxTrees(tid, sid = null) {
    if (typeof tid !== 'number' || isNaN(tid) || tid < 0 || tid > 65535) {
        return [];
    }

    const tid1 = tid % 256;
    const tid2 = Math.floor(tid / 256);

    let c = tid1 % 21;
    let d = tid2 % 21;

    const hasSid = (typeof sid === 'number' && !isNaN(sid) && sid >= 0 && sid <= 65535);

    if (!hasSid) {
        // Solo TID conocido: calcula los dos árboles garantizados de TID
        if (c === d) {
            d = (d + 1) % 21;
        }
        return [c, d];
    }

    const sid1 = sid % 256;
    const sid2 = Math.floor(sid / 256);

    let a = sid1 % 21;
    let b = sid2 % 21;

    // Resolución canónica de colisiones de Gen 4
    if (a === b) b = (b + 1) % 21;
    if (a === c) c = (c + 1) % 21;
    if (b === c) c = (c + 1) % 21;
    if (a === d) d = (d + 1) % 21;
    if (b === d) d = (d + 1) % 21;
    if (c === d) d = (d + 1) % 21;

    return [a, b, c, d];
}

/**
 * Obtiene los nombres de los árboles calculados.
 */
export function getMunchlaxTreeNames(tid, sid = null) {
    const indices = calculateMunchlaxTrees(tid, sid);
    return indices.map(idx => SINNOH_HONEY_TREES[idx]).filter(Boolean);
}

/**
 * Clave de almacenamiento local por juego.
 */
function getStorageKey(gameSlug) {
    return `pokedex_game_config_${gameSlug || (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || 'default'}`;
}

/**
 * Carga la configuración guardada del juego actual.
 */
export function loadGameConfig(gameSlug) {
    const key = getStorageKey(gameSlug);
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return null;
        return JSON.parse(raw);
    } catch (e) {
        console.warn('Error al leer configuración de partida:', e);
        return null;
    }
}

/**
 * Guarda la configuración del juego actual en localStorage.
 */
export function saveGameConfigData(configData, gameSlug) {
    const key = getStorageKey(gameSlug);
    try {
        if (!configData) {
            localStorage.removeItem(key);
        } else {
            localStorage.setItem(key, JSON.stringify(configData));
        }
        updateConfigDotIndicator();
    } catch (e) {
        console.warn('Error al guardar configuración de partida:', e);
    }
}

/**
 * Actualiza el indicador visual (punto verde) en el botón de la tuerca si hay configuración activa.
 */
export function updateConfigDotIndicator() {
    const dot = document.getElementById('cfg-active-dot');
    if (!dot) return;
    const cfg = loadGameConfig();
    if (cfg && (cfg.tid !== null && cfg.tid !== undefined)) {
        dot.classList.remove('hidden');
    } else {
        dot.classList.add('hidden');
    }
}

/**
 * Abre el modal de configuración de partida.
 */
export function openGameConfigModal() {
    const modal = document.getElementById('game-config-modal');
    const cardPanel = document.getElementById('game-config-modal-card');
    if (!modal) return;

    // Cargar datos previos si existen
    const cfg = loadGameConfig();
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');

    if (tidInput) {
        tidInput.value = (cfg && cfg.tid !== undefined && cfg.tid !== null) ? cfg.tid : '';
    }
    if (sidInput) {
        sidInput.value = (cfg && cfg.sid !== undefined && cfg.sid !== null) ? cfg.sid : '';
    }

    renderConfigPreview();

    modal.style.display = 'flex';
    modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100', 'pointer-events-auto');

    if (cardPanel) {
        cardPanel.classList.remove('scale-95');
        cardPanel.classList.add('scale-100');
    }

    document.documentElement.classList.add('overflow-hidden');
    document.body.classList.add('overflow-hidden');
}

/**
 * Cierra el modal de configuración de partida.
 */
export function closeGameConfigModal() {
    const modal = document.getElementById('game-config-modal');
    const cardPanel = document.getElementById('game-config-modal-card');
    if (!modal) return;

    modal.classList.remove('opacity-100', 'pointer-events-auto');
    modal.classList.add('opacity-0', 'pointer-events-none');

    if (cardPanel) {
        cardPanel.classList.remove('scale-100');
        cardPanel.classList.add('scale-95');
    }

    setTimeout(() => {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        // Liberar scroll si ningún otro modal está abierto
        const comicModal = document.getElementById('comic-modal');
        const isComicOpen = comicModal && !comicModal.classList.contains('opacity-0');
        if (!isComicOpen) {
            document.documentElement.classList.remove('overflow-hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }, 150);
}

/**
 * Maneja el clic en el backdrop para cerrar.
 */
export function handleGameConfigBackdropClick(e) {
    if (e && e.target && e.target.id === 'game-config-modal') {
        closeGameConfigModal();
    }
}

/**
 * Renderiza la previsualización de árboles en tiempo real mientras el usuario escribe.
 */
export function renderConfigPreview() {
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');
    const previewContainer = document.getElementById('cfg-calculated-preview');
    const treesList = document.getElementById('cfg-trees-list');
    const countBadge = document.getElementById('cfg-trees-count-badge');

    if (!tidInput || !previewContainer || !treesList) return;

    const tidVal = parseInt(tidInput.value, 10);
    const sidVal = sidInput ? parseInt(sidInput.value, 10) : null;

    if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
        previewContainer.classList.add('hidden');
        treesList.innerHTML = '';
        return;
    }

    const hasValidSid = !isNaN(sidVal) && sidVal >= 0 && sidVal <= 65535;
    const names = getMunchlaxTreeNames(tidVal, hasValidSid ? sidVal : null);

    if (names.length === 0) {
        previewContainer.classList.add('hidden');
        return;
    }

    previewContainer.classList.remove('hidden');
    if (countBadge) {
        countBadge.textContent = `${names.length} Árboles`;
        countBadge.className = names.length === 4 
            ? 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-emerald-300 text-slate-950'
            : 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-amber-200 text-slate-900';
    }

    treesList.innerHTML = names.map(name => `
        <li class="flex items-center gap-1.5 py-0.5">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></span>
            <span class="font-black text-slate-900">${name}</span>
        </li>
    `).join('');
}

/**
 * Guarda los valores configurados y refresca el modal abierto (si corresponde).
 */
export function saveGameConfig() {
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');

    if (!tidInput) return;

    const tidVal = parseInt(tidInput.value, 10);
    const sidVal = sidInput && sidInput.value.trim() !== '' ? parseInt(sidInput.value, 10) : null;

    if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
        alert('Por favor introduce un ID de Entrenador (TID) válido entre 0 y 65535.');
        tidInput.focus();
        return;
    }

    if (sidVal !== null && (isNaN(sidVal) || sidVal < 0 || sidVal > 65535)) {
        alert('El ID Secreto (SID) debe ser un número válido entre 0 y 65535 o dejarse en blanco.');
        sidInput.focus();
        return;
    }

    const configData = {
        tid: tidVal,
        sid: sidVal,
        updatedAt: new Date().toISOString()
    };

    saveGameConfigData(configData);
    closeGameConfigModal();

    // Si el modal de cómic está abierto para Munchlax, refrescar inmediatamente sus ubicaciones
    refreshMunchlaxModalIfOpen();
}

/**
 * Restablece la configuración del juego a los valores por defecto (sin filtrar).
 */
export function resetGameConfig() {
    saveGameConfigData(null);
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');
    if (tidInput) tidInput.value = '';
    if (sidInput) sidInput.value = '';
    renderConfigPreview();
    closeGameConfigModal();
    refreshMunchlaxModalIfOpen();
}

/**
 * Refresca la información de Munchlax si el modal cómic está activo.
 */
function refreshMunchlaxModalIfOpen() {
    const comicModal = document.getElementById('comic-modal');
    if (!comicModal || comicModal.classList.contains('hidden') || comicModal.classList.contains('opacity-0')) {
        return;
    }
    // Si la función openPokemonModalDirect o openPokemonModal existe en window
    if (typeof window.openPokemonModalDirect === 'function' && window.__activeModalEntryId) {
        window.openPokemonModalDirect(window.__activeModalEntryId, false);
    }
}

/**
 * Inicializador del módulo: escuchar inputs y configurar estado inicial.
 */
export function initGameConfig() {
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');

    const sanitizeDigits = (input) => {
        if (!input) return;
        input.value = input.value.replace(/[^0-9]/g, '').slice(0, 5);
    };

    if (tidInput) {
        tidInput.addEventListener('input', () => {
            sanitizeDigits(tidInput);
            renderConfigPreview();
        });
    }
    if (sidInput) {
        sidInput.addEventListener('input', () => {
            sanitizeDigits(sidInput);
            renderConfigPreview();
        });
    }

    updateConfigDotIndicator();
}
