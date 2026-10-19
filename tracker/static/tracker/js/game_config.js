/**
 * Pokédex Global - Calculadora y Configuración de Partida (game_config.js)
 * Módulo para gestionar configuraciones por partida:
 * - Calculadora de árboles de Munchlax en Gen 4 (Sinnoh).
 * - Calculadora de casillas de Feebas en Gen 3 (Rubí, Zafiro y Esmeralda).
 */

import { 
    FEEBAS_CONDITIONS_ES, 
    FEEBAS_LIFESTYLE_ES, 
    FEEBAS_HOBBIES_ES 
} from './feebas_data.js';
import { calculateFeebasFishingSpots } from './feebas_calculator.js';
import { bringModalToFront, registerModalClose } from './url_sync.js';

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
 * Popula las listas de autocompletado datalist para las palabras de la frase de Feebas.
 */
function populateFeebasDatalists() {
    const list1 = document.getElementById('cfg-feebas-word1-list');
    const list2 = document.getElementById('cfg-feebas-word2-list');
    if (!list1 || !list2) return;

    if (list1.children.length === 0) {
        const sortedConditions = [...FEEBAS_CONDITIONS_ES].sort((a, b) => a.localeCompare('es'));
        list1.innerHTML = sortedConditions.map(w => `<option value="${w}">${w}</option>`).join('');
    }

    if (list2.children.length === 0) {
        const combined = Array.from(new Set([...FEEBAS_LIFESTYLE_ES, ...FEEBAS_HOBBIES_ES])).sort((a, b) => a.localeCompare('es'));
        list2.innerHTML = combined.map(w => `<option value="${w}">${w}</option>`).join('');
    }
}

/**
 * Abre el modal de configuración de partida.
 */
export function openGameConfigModal() {
    const modal = document.getElementById('game-config-modal');
    const cardPanel = document.getElementById('game-config-modal-card');
    if (!modal) return;

    populateFeebasDatalists();

    // Cargar datos previos si existen
    const cfg = loadGameConfig();
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');
    const w1Input = document.getElementById('cfg-feebas-word1');
    const w2Input = document.getElementById('cfg-feebas-word2');

    if (tidInput) {
        tidInput.value = (cfg && cfg.tid !== undefined && cfg.tid !== null) ? cfg.tid : '';
    }
    if (sidInput) {
        sidInput.value = (cfg && cfg.sid !== undefined && cfg.sid !== null) ? cfg.sid : '';
    }
    if (w1Input) {
        w1Input.value = (cfg && cfg.phrase1) ? cfg.phrase1 : '';
    }
    if (w2Input) {
        w2Input.value = (cfg && cfg.phrase2) ? cfg.phrase2 : '';
    }

    renderConfigPreview();

    modal.style.display = 'flex';
    modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100', 'pointer-events-auto');

    if (cardPanel) {
        cardPanel.classList.remove('scale-95');
        cardPanel.classList.add('scale-100');
    }

    bringModalToFront(modal);
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
        registerModalClose(modal);
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
 * Renderiza la previsualización en tiempo real mientras el usuario escribe.
 */
export function renderConfigPreview() {
    const gameSlug = (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || '';
    const isGen3Hoenn = ['ruby', 'sapphire', 'emerald'].includes(gameSlug);

    const tidInput = document.getElementById('cfg-trainer-id');
    if (!tidInput) return;

    const tidVal = parseInt(tidInput.value, 10);
    const hasValidTid = !isNaN(tidVal) && tidVal >= 0 && tidVal <= 65535;

    // 1. Previsualización de Munchlax (Gen 4)
    if (!isGen3Hoenn) {
        const sidInput = document.getElementById('cfg-secret-id');
        const previewContainer = document.getElementById('cfg-calculated-preview');
        const treesList = document.getElementById('cfg-trees-list');
        const countBadge = document.getElementById('cfg-trees-count-badge');

        if (!previewContainer || !treesList) return;

        if (!hasValidTid) {
            previewContainer.classList.add('hidden');
            treesList.innerHTML = '';
            return;
        }

        const sidVal = sidInput ? parseInt(sidInput.value, 10) : null;
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
        return;
    }

    // 2. Previsualización de Feebas (Gen 3 Hoenn)
    const w1Input = document.getElementById('cfg-feebas-word1');
    const w2Input = document.getElementById('cfg-feebas-word2');
    const previewContainer = document.getElementById('cfg-feebas-preview');
    const spotsSummary = document.getElementById('cfg-feebas-spots-summary');
    const countBadge = document.getElementById('cfg-feebas-count-badge');

    if (!previewContainer || !spotsSummary) return;

    const w1 = w1Input ? w1Input.value.trim() : '';
    const w2 = w2Input ? w2Input.value.trim() : '';

    if (!hasValidTid || !w1 || !w2) {
        previewContainer.classList.add('hidden');
        spotsSummary.innerHTML = '';
        return;
    }

    const isEmerald = (gameSlug === 'emerald');
    const spots = calculateFeebasFishingSpots(tidVal, w1, w2, isEmerald);

    if (!spots || spots.length === 0) {
        previewContainer.classList.add('hidden');
        spotsSummary.innerHTML = '';
        return;
    }

    previewContainer.classList.remove('hidden');
    if (countBadge) {
        countBadge.textContent = `${spots.length} Casillas`;
        countBadge.className = 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-sky-200 text-slate-900';
    }

    spotsSummary.innerHTML = spots.map((s, idx) => `
        <span class="px-2 py-1 rounded-md bg-sky-50 border border-sky-400 text-sky-950 text-[11px] font-black shadow-xs">
            #${idx + 1}: Casilla ${s.tileId}
        </span>
    `).join('');
}

/**
 * Guarda los valores configurados y refresca el modal abierto (si corresponde).
 */
export function saveGameConfig() {
    const gameSlug = (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || '';
    const isGen3Hoenn = ['ruby', 'sapphire', 'emerald'].includes(gameSlug);
    const tidInput = document.getElementById('cfg-trainer-id');

    if (!tidInput) return;

    const tidVal = parseInt(tidInput.value, 10);
    if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
        alert('Por favor introduce un ID de Entrenador (TID) válido entre 0 y 65535.');
        tidInput.focus();
        return;
    }

    if (isGen3Hoenn) {
        const w1Input = document.getElementById('cfg-feebas-word1');
        const w2Input = document.getElementById('cfg-feebas-word2');

        const w1 = w1Input ? w1Input.value.trim().toUpperCase() : '';
        const w2 = w2Input ? w2Input.value.trim().toUpperCase() : '';

        if (!w1 || !w2) {
            alert('Por favor ingresa las dos palabras de la Frase de Moda de Pueblo Azuliza.');
            if (!w1 && w1Input) w1Input.focus();
            else if (w2Input) w2Input.focus();
            return;
        }

        const isEmerald = (gameSlug === 'emerald');
        const spots = calculateFeebasFishingSpots(tidVal, w1, w2, isEmerald);

        if (!spots || spots.length === 0) {
            alert('No se encontraron casillas válidas con esa frase. Por favor verifica que las palabras correspondan al vocabulario de Pueblo Azuliza.');
            return;
        }

        const configData = {
            tid: tidVal,
            phrase1: w1,
            phrase2: w2,
            spots: spots,
            updatedAt: new Date().toISOString()
        };

        saveGameConfigData(configData);
        closeGameConfigModal();
        refreshOpenModals();
        return;
    }

    // Gen 4 Munchlax
    const sidInput = document.getElementById('cfg-secret-id');
    const sidVal = sidInput && sidInput.value.trim() !== '' ? parseInt(sidInput.value, 10) : null;

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
    refreshOpenModals();
}

/**
 * Restablece la configuración del juego a los valores por defecto (sin filtrar).
 */
export function resetGameConfig() {
    saveGameConfigData(null);
    const tidInput = document.getElementById('cfg-trainer-id');
    const sidInput = document.getElementById('cfg-secret-id');
    const w1Input = document.getElementById('cfg-feebas-word1');
    const w2Input = document.getElementById('cfg-feebas-word2');

    if (tidInput) tidInput.value = '';
    if (sidInput) sidInput.value = '';
    if (w1Input) w1Input.value = '';
    if (w2Input) w2Input.value = '';

    renderConfigPreview();
    closeGameConfigModal();
    refreshOpenModals();
}

/**
 * Alterna el acordeón de advertencia de la frase de Feebas.
 */
export function toggleFeebasPhraseAccordion() {
    const content = document.getElementById('feebas-phrase-accordion-content');
    const icon = document.getElementById('feebas-phrase-accordion-icon');
    const label = document.getElementById('feebas-phrase-accordion-label');
    const btn = document.getElementById('feebas-phrase-accordion-btn');
    if (!content) return;

    const isCollapsed = content.classList.contains('hidden');
    if (isCollapsed) {
        content.classList.remove('hidden');
        if (icon) icon.classList.add('rotate-180');
        if (label) label.textContent = 'Ocultar nota';
        if (btn) btn.setAttribute('aria-expanded', 'true');
    } else {
        content.classList.add('hidden');
        if (icon) icon.classList.remove('rotate-180');
        if (label) label.textContent = 'Ver nota';
        if (btn) btn.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Abre el modal del mapa de pesca de Feebas en Ruta 119.
 */
export function openFeebasMapModal() {
    const modal = document.getElementById('feebas-map-modal');
    const cardPanel = document.getElementById('feebas-map-modal-card');
    if (!modal) return;

    const gameSlug = (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || 'emerald';
    let cfg = loadGameConfig(gameSlug);

    // Recalcular dinámicamente si los spots provienen de una sesión previa para garantizar coordenadas canónicas 1:1
    if (cfg && cfg.tid !== undefined && cfg.phrase1 && cfg.phrase2) {
        const isEmerald = (gameSlug === 'emerald');
        const updatedSpots = calculateFeebasFishingSpots(cfg.tid, cfg.phrase1, cfg.phrase2, isEmerald);
        if (updatedSpots && updatedSpots.length > 0) {
            cfg.spots = updatedSpots;
            saveGameConfigData(cfg, gameSlug);
        }
    }
    const spots = (cfg && cfg.spots) ? cfg.spots : [];

    const markersLayer = document.getElementById('feebas-map-markers-layer');
    const jumpNav = document.getElementById('feebas-spots-jump-nav');

    if (markersLayer) {
        markersLayer.innerHTML = spots.map((spot, idx) => `
            <div 
                id="feebas-marker-${idx}"
                class="absolute cursor-pointer group z-20"
                style="left: ${spot.x}px; top: ${spot.y}px; transform: translate(-50%, -50%);"
                onclick="highlightFeebasSpot(${idx})"
                title="Casilla #${spot.tileId} (${spot.x}, ${spot.y})"
            >
                <span class="animate-ping absolute inline-flex h-7 w-7 rounded-full bg-rose-400 opacity-75"></span>
                <div class="relative w-7 h-7 rounded-full bg-rose-600 border-2 border-white text-xs font-black text-white flex items-center justify-center shadow-lg group-hover:scale-125 transition-transform">
                    ${idx + 1}
                </div>
                <div class="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-0.5 bg-slate-950 text-amber-300 border border-slate-700 rounded text-[10px] font-black whitespace-nowrap shadow-lg pointer-events-none">
                    Casilla #${spot.tileId}
                </div>
            </div>
        `).join('');
    }

    if (jumpNav) {
        jumpNav.innerHTML = spots.map((spot, idx) => `
            <button 
                type="button" 
                onclick="highlightFeebasSpot(${idx})"
                class="px-2 py-0.5 text-[10px] font-black uppercase rounded border border-slate-950 bg-rose-500 hover:bg-rose-400 text-white shadow-[1px_1px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                title="Ir a Casilla #${spot.tileId}"
            >
                #${idx + 1} (${spot.tileId})
            </button>
        `).join('');
    }

    modal.style.display = 'flex';
    modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100', 'pointer-events-auto');

    if (cardPanel) {
        cardPanel.classList.remove('scale-95');
        cardPanel.classList.add('scale-100');
    }

    bringModalToFront(modal);

    // Centrar automáticamente en la primera casilla encontrada tras renderizar
    if (spots.length > 0) {
        setTimeout(() => {
            highlightFeebasSpot(0, false);
        }, 120);
    }
}

/**
 * Cierra el modal del mapa de pesca de Feebas.
 */
export function closeFeebasMapModal() {
    const modal = document.getElementById('feebas-map-modal');
    const cardPanel = document.getElementById('feebas-map-modal-card');
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
        registerModalClose(modal);
    }, 150);
}

/**
 * Maneja el clic en el fondo del modal del mapa de Feebas.
 */
export function handleFeebasMapBackdropClick(e) {
    if (e && e.target && e.target.id === 'feebas-map-modal') {
        closeFeebasMapModal();
    }
}

/**
 * Desplaza la vista del mapa de Feebas hacia una zona de la Ruta 119.
 */
export function scrollFeebasMapTo(section) {
    const viewport = document.getElementById('feebas-map-viewport');
    if (!viewport) return;

    let targetY = 0;
    if (section === 'north') targetY = 50;
    else if (section === 'center') targetY = 900;
    else if (section === 'south') targetY = 1750;

    viewport.scrollTo({
        top: targetY,
        behavior: 'smooth'
    });
}

/**
 * Centra y resalta visualmente una casilla calculada en el mapa.
 */
export function highlightFeebasSpot(index, smooth = true) {
    const gameSlug = (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || 'emerald';
    const cfg = loadGameConfig(gameSlug);
    const spots = (cfg && cfg.spots) ? cfg.spots : [];
    const spot = spots[index];
    if (!spot) return;

    const viewport = document.getElementById('feebas-map-viewport');
    if (viewport) {
        const targetTop = Math.max(0, spot.y - (viewport.clientHeight / 2));
        const targetLeft = Math.max(0, spot.x - (viewport.clientWidth / 2));
        viewport.scrollTo({
            top: targetTop,
            left: targetLeft,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }

    const marker = document.getElementById(`feebas-marker-${index}`);
    if (marker) {
        marker.classList.add('scale-150');
        setTimeout(() => {
            marker.classList.remove('scale-150');
        }, 600);
    }
}

/**
 * Refresca la información si el modal cómic está activo.
 */
function refreshOpenModals() {
    const comicModal = document.getElementById('comic-modal');
    if (!comicModal || comicModal.classList.contains('hidden') || comicModal.classList.contains('opacity-0')) {
        return;
    }
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
    const w1Input = document.getElementById('cfg-feebas-word1');
    const w2Input = document.getElementById('cfg-feebas-word2');

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
    if (w1Input) {
        w1Input.addEventListener('input', () => {
            renderConfigPreview();
        });
    }
    if (w2Input) {
        w2Input.addEventListener('input', () => {
            renderConfigPreview();
        });
    }

    updateConfigDotIndicator();
}
