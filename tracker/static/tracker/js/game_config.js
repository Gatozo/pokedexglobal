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
import { calculateFeebasFishingSpots, calculateGen4FeebasSpots } from './feebas_calculator.js';
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
    const hasTid = cfg && (cfg.tid !== null && cfg.tid !== undefined);
    const hasGen3Feebas = cfg && (Boolean(cfg.phrase1) && Boolean(cfg.phrase2));
    const hasGen4Feebas = cfg && (cfg.lottoToday !== null && cfg.lottoToday !== undefined);
    if (hasTid || hasGen3Feebas || hasGen4Feebas) {
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
    const todayInput = document.getElementById('cfg-feebas-gen4-today');
    const yestInput = document.getElementById('cfg-feebas-gen4-yesterday');

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
    if (todayInput) {
        todayInput.value = (cfg && cfg.lottoToday !== undefined && cfg.lottoToday !== null) ? cfg.lottoToday : '';
    }
    if (yestInput) {
        yestInput.value = (cfg && cfg.lottoYesterday !== undefined && cfg.lottoYesterday !== null) ? cfg.lottoYesterday : '';
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

        // Restablecer acordeón de Feebas Gen 3 para próxima apertura
        const phraseContent = document.getElementById('feebas-phrase-accordion-content');
        const phraseIcon = document.getElementById('feebas-phrase-accordion-icon');
        const phraseLabel = document.getElementById('feebas-phrase-accordion-label');
        const phraseBtn = document.getElementById('feebas-phrase-accordion-btn');
        if (phraseContent) {
            if (phraseContent._animCleanup) phraseContent._animCleanup();
            phraseContent.classList.add('hidden');
            phraseContent.style.maxHeight = '';
            phraseContent.style.overflow = '';
            phraseContent.style.opacity = '';
            phraseContent.style.transition = '';
        }
        if (phraseIcon) phraseIcon.classList.remove('rotate-180');
        if (phraseLabel) phraseLabel.textContent = 'Ver nota';
        if (phraseBtn) phraseBtn.setAttribute('aria-expanded', 'false');

        // Restablecer acordeón de Feebas Gen 4 para próxima apertura
        const gen4Content = document.getElementById('feebas-gen4-accordion-content');
        const gen4Icon = document.getElementById('feebas-gen4-accordion-icon');
        const gen4Label = document.getElementById('feebas-gen4-accordion-label');
        const gen4Btn = document.getElementById('feebas-gen4-accordion-btn');
        if (gen4Content) {
            if (gen4Content._animCleanup) gen4Content._animCleanup();
            gen4Content.classList.add('hidden');
            gen4Content.style.maxHeight = '';
            gen4Content.style.overflow = '';
            gen4Content.style.opacity = '';
            gen4Content.style.transition = '';
        }
        if (gen4Icon) gen4Icon.classList.remove('rotate-180');
        if (gen4Label) gen4Label.textContent = 'Ver nota';
        if (gen4Btn) gen4Btn.setAttribute('aria-expanded', 'false');
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
    const tidVal = tidInput ? parseInt(tidInput.value, 10) : NaN;
    const hasValidTid = !isNaN(tidVal) && tidVal >= 0 && tidVal <= 65535;

    // 1. Previsualización para Gen 4 (Munchlax y Feebas en Sinnoh)
    if (!isGen3Hoenn) {
        const sidInput = document.getElementById('cfg-secret-id');
        const previewContainer = document.getElementById('cfg-calculated-preview');
        const treesList = document.getElementById('cfg-trees-list');
        const countBadge = document.getElementById('cfg-trees-count-badge');

        if (previewContainer && treesList) {
            if (!hasValidTid) {
                previewContainer.classList.add('hidden');
                treesList.innerHTML = '';
            } else {
                const sidVal = sidInput ? parseInt(sidInput.value, 10) : null;
                const hasValidSid = !isNaN(sidVal) && sidVal >= 0 && sidVal <= 65535;
                const names = getMunchlaxTreeNames(tidVal, hasValidSid ? sidVal : null);

                if (names.length === 0) {
                    previewContainer.classList.add('hidden');
                } else {
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
            }
        }

        // Feebas Gen 4 (Lotería Jubilife TV -> Casillas Monte Corona B1F)
        const lottoTodayInput = document.getElementById('cfg-feebas-gen4-today');
        const lottoYestInput = document.getElementById('cfg-feebas-gen4-yesterday');
        const gen4Preview = document.getElementById('cfg-feebas-gen4-preview');
        const gen4CountBadge = document.getElementById('cfg-feebas-gen4-count-badge');
        const gen4Summary = document.getElementById('cfg-feebas-gen4-spots-summary');

        if (gen4Preview && gen4Summary && lottoTodayInput) {
            const todayRaw = lottoTodayInput.value.trim();
            const yestRaw = lottoYestInput ? lottoYestInput.value.trim() : '';

            const todayVal = todayRaw !== '' ? parseInt(todayRaw, 10) : NaN;
            const hasValidToday = !isNaN(todayVal) && todayVal >= 0 && todayVal <= 65535;

            if (!hasValidToday) {
                gen4Preview.classList.add('hidden');
                gen4Summary.innerHTML = '';
            } else {
                const yestVal = yestRaw !== '' ? parseInt(yestRaw, 10) : null;
                const hasValidYest = (yestVal !== null && !isNaN(yestVal) && yestVal >= 0 && yestVal <= 65535);

                const spots = calculateGen4FeebasSpots(todayVal, hasValidYest ? yestVal : null);

                if (!spots || spots.length === 0) {
                    gen4Preview.classList.add('hidden');
                    gen4Summary.innerHTML = '';
                } else {
                    gen4Preview.classList.remove('hidden');
                    const isGuaranteed = spots.some(s => s.certainty === 100);

                    if (gen4CountBadge) {
                        gen4CountBadge.textContent = isGuaranteed ? `${spots.length} Casillas (100% Certeza)` : `${spots.length} Casillas (50% Prob.)`;
                        gen4CountBadge.className = isGuaranteed
                            ? 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-emerald-300 text-slate-950'
                            : 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-sky-200 text-slate-900';
                    }

                    gen4Summary.innerHTML = spots.map((s, idx) => {
                        const badgeBg = isGuaranteed
                            ? 'bg-emerald-50 border-emerald-400 text-emerald-950'
                            : (s.group === 'Grupo A' ? 'bg-sky-50 border-sky-400 text-sky-950' : 'bg-purple-50 border-purple-400 text-purple-950');
                        return `
                            <span class="px-2 py-1 rounded-md ${badgeBg} border text-[11px] font-black shadow-xs">
                                #${idx + 1}: Casilla ${s.tileId} (${s.rawX}, ${s.rawY})
                            </span>
                        `;
                    }).join('');
                }
            }
        }
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
    const isGen4Sinnoh = ['diamond', 'pearl', 'platinum'].includes(gameSlug);

    if (isGen3Hoenn) {
        const tidInput = document.getElementById('cfg-trainer-id');
        const tidRaw = tidInput ? tidInput.value.trim() : '';
        const w1Input = document.getElementById('cfg-feebas-word1');
        const w2Input = document.getElementById('cfg-feebas-word2');

        const w1 = w1Input ? w1Input.value.trim().toUpperCase() : '';
        const w2 = w2Input ? w2Input.value.trim().toUpperCase() : '';

        // Si todos los campos están vacíos, se limpia la configuración
        if (!tidRaw && !w1 && !w2) {
            saveGameConfigData(null);
            closeGameConfigModal();
            refreshOpenModals();
            return;
        }

        const tidVal = parseInt(tidRaw, 10);
        if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
            alert('Por favor introduce un ID de Entrenador (TID) válido entre 0 y 65535.');
            if (tidInput) tidInput.focus();
            return;
        }

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

    // Gen 4 Sinnoh (Munchlax y Feebas son configuraciones independientes)
    if (isGen4Sinnoh) {
        const tidInput = document.getElementById('cfg-trainer-id');
        const sidInput = document.getElementById('cfg-secret-id');
        const lottoTodayInput = document.getElementById('cfg-feebas-gen4-today');
        const lottoYestInput = document.getElementById('cfg-feebas-gen4-yesterday');

        const tidRaw = tidInput ? tidInput.value.trim() : '';
        const sidRaw = sidInput ? sidInput.value.trim() : '';
        const todayRaw = lottoTodayInput ? lottoTodayInput.value.trim() : '';
        const yestRaw = lottoYestInput ? lottoYestInput.value.trim() : '';

        // Si todos los campos están vacíos, se limpia la configuración
        if (!tidRaw && !sidRaw && !todayRaw && !yestRaw) {
            saveGameConfigData(null);
            closeGameConfigModal();
            refreshOpenModals();
            return;
        }

        // 1. Validación de Árboles de Munchlax
        let tidVal = null;
        let sidVal = null;

        if (sidRaw !== '' && tidRaw === '') {
            alert('Para configurar los Árboles de Munchlax, el ID de Entrenador (TID) es obligatorio.');
            if (tidInput) tidInput.focus();
            return;
        }

        if (tidRaw !== '') {
            tidVal = parseInt(tidRaw, 10);
            if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
                alert('El ID de Entrenador (TID) para los árboles de Munchlax debe ser un número entre 0 y 65535.');
                if (tidInput) tidInput.focus();
                return;
            }

            if (sidRaw !== '') {
                sidVal = parseInt(sidRaw, 10);
                if (isNaN(sidVal) || sidVal < 0 || sidVal > 65535) {
                    alert('El ID Secreto (SID) debe ser un número válido entre 0 y 65535 o dejarse en blanco.');
                    if (sidInput) sidInput.focus();
                    return;
                }
            }
        }

        // 2. Validación de Casillas de Feebas
        let lottoTodayVal = null;
        let lottoYestVal = null;
        let feebasSpots = null;

        if (yestRaw !== '' && todayRaw === '') {
            alert('Para configurar las Casillas de Feebas, el número de la Lotería de Hoy es obligatorio.');
            if (lottoTodayInput) lottoTodayInput.focus();
            return;
        }

        if (todayRaw !== '') {
            lottoTodayVal = parseInt(todayRaw, 10);
            if (isNaN(lottoTodayVal) || lottoTodayVal < 0 || lottoTodayVal > 65535) {
                alert('El número de Lotería de Hoy (Jubilife TV) debe ser un número entre 00000 y 65535.');
                if (lottoTodayInput) lottoTodayInput.focus();
                return;
            }

            if (yestRaw !== '') {
                lottoYestVal = parseInt(yestRaw, 10);
                if (isNaN(lottoYestVal) || lottoYestVal < 0 || lottoYestVal > 65535) {
                    alert('El número de Lotería de Ayer debe ser un número entre 00000 y 65535 o dejarse en blanco.');
                    if (lottoYestInput) lottoYestInput.focus();
                    return;
                }
            }

            feebasSpots = calculateGen4FeebasSpots(lottoTodayVal, lottoYestVal);
        }

        const configData = {
            tid: tidVal,
            sid: sidVal,
            lottoToday: lottoTodayVal,
            lottoYesterday: lottoYestVal,
            feebasSpots: feebasSpots,
            spots: feebasSpots, // Alias para compatibilidad con el modal del mapa
            updatedAt: new Date().toISOString()
        };

        saveGameConfigData(configData);
        closeGameConfigModal();
        refreshOpenModals();
        return;
    }

    // Otros juegos / Fallback
    const tidInput = document.getElementById('cfg-trainer-id');
    const tidRaw = tidInput ? tidInput.value.trim() : '';
    if (tidRaw !== '') {
        const tidVal = parseInt(tidRaw, 10);
        if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
            alert('Por favor introduce un ID de Entrenador (TID) válido entre 0 y 65535.');
            if (tidInput) tidInput.focus();
            return;
        }
        saveGameConfigData({
            tid: tidVal,
            updatedAt: new Date().toISOString()
        });
    } else {
        saveGameConfigData(null);
    }
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
    const todayInput = document.getElementById('cfg-feebas-gen4-today');
    const yestInput = document.getElementById('cfg-feebas-gen4-yesterday');

    if (tidInput) tidInput.value = '';
    if (sidInput) sidInput.value = '';
    if (w1Input) w1Input.value = '';
    if (w2Input) w2Input.value = '';
    if (todayInput) todayInput.value = '';
    if (yestInput) yestInput.value = '';

    renderConfigPreview();
    closeGameConfigModal();
    refreshOpenModals();
}

/**
 * Anima la apertura y cierre de un acordeón de forma fluida.
 */
function animateAccordionToggle(element, isOpen) {
    if (!element) return;
    if (element._animCleanup) {
        element._animCleanup();
    }

    if (isOpen) {
        element.classList.remove('hidden');
        element.style.overflow = 'hidden';
        element.style.transition = 'max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease-out';
        element.style.maxHeight = '0px';
        element.style.opacity = '0';

        requestAnimationFrame(() => {
            const targetHeight = element.scrollHeight;
            element.style.maxHeight = targetHeight + 'px';
            element.style.opacity = '1';
        });

        const onEnd = (e) => {
            if (e && e.target !== element) return;
            element.style.maxHeight = 'none';
            element.style.overflow = '';
            element.style.opacity = '';
            element.style.transition = '';
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
        element.addEventListener('transitionend', onEnd);
        element._animCleanup = () => {
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
    } else {
        element.style.overflow = 'hidden';
        element.style.transition = 'max-height 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease-in';
        element.style.maxHeight = element.scrollHeight + 'px';
        element.style.opacity = '1';

        requestAnimationFrame(() => {
            element.style.maxHeight = '0px';
            element.style.opacity = '0';
        });

        const onEnd = (e) => {
            if (e && e.target !== element) return;
            element.classList.add('hidden');
            element.style.maxHeight = '';
            element.style.overflow = '';
            element.style.opacity = '';
            element.style.transition = '';
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
        element.addEventListener('transitionend', onEnd);
        element._animCleanup = () => {
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
    }
}

/**
 * Alterna el acordeón de advertencia de la frase de Feebas con transición fluida.
 */
export function toggleFeebasPhraseAccordion() {
    const content = document.getElementById('feebas-phrase-accordion-content');
    const icon = document.getElementById('feebas-phrase-accordion-icon');
    const label = document.getElementById('feebas-phrase-accordion-label');
    const btn = document.getElementById('feebas-phrase-accordion-btn');
    if (!content) return;

    const isCollapsed = content.classList.contains('hidden') || content.style.maxHeight === '0px';
    if (isCollapsed) {
        animateAccordionToggle(content, true);
        if (icon) icon.classList.add('rotate-180');
        if (label) label.textContent = 'Ocultar nota';
        if (btn) btn.setAttribute('aria-expanded', 'true');
    } else {
        animateAccordionToggle(content, false);
        if (icon) icon.classList.remove('rotate-180');
        if (label) label.textContent = 'Ver nota';
        if (btn) btn.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Alterna el acordeón de advertencia de la lotería de Feebas en Gen 4 con transición fluida.
 */
export function toggleFeebasGen4LottoAccordion() {
    const content = document.getElementById('feebas-gen4-accordion-content');
    const icon = document.getElementById('feebas-gen4-accordion-icon');
    const label = document.getElementById('feebas-gen4-accordion-label');
    const btn = document.getElementById('feebas-gen4-accordion-btn');
    if (!content) return;

    const isCollapsed = content.classList.contains('hidden') || content.style.maxHeight === '0px';
    if (isCollapsed) {
        animateAccordionToggle(content, true);
        if (icon) icon.classList.add('rotate-180');
        if (label) label.textContent = 'Ocultar nota';
        if (btn) btn.setAttribute('aria-expanded', 'true');
    } else {
        animateAccordionToggle(content, false);
        if (icon) icon.classList.remove('rotate-180');
        if (label) label.textContent = 'Ver nota';
        if (btn) btn.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Abre el modal del mapa de pesca de Feebas (Ruta 119 en Hoenn o Monte Corona B1F en Sinnoh).
 */
export function openFeebasMapModal() {
    const modal = document.getElementById('feebas-map-modal');
    const cardPanel = document.getElementById('feebas-map-modal-card');
    if (!modal) return;

    const gameSlug = (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || 'emerald';
    const isGen4Sinnoh = ['diamond', 'pearl', 'platinum'].includes(gameSlug);
    let cfg = loadGameConfig(gameSlug);

    let spots = [];
    if (isGen4Sinnoh) {
        if (cfg && cfg.lottoToday !== undefined && cfg.lottoToday !== null) {
            spots = calculateGen4FeebasSpots(cfg.lottoToday, cfg.lottoYesterday);
            cfg.feebasSpots = spots;
            cfg.spots = spots;
            saveGameConfigData(cfg, gameSlug);
        } else if (cfg && (cfg.feebasSpots || cfg.spots)) {
            spots = cfg.feebasSpots || cfg.spots;
        }
    } else {
        // Gen 3 Hoenn
        if (cfg && cfg.tid !== undefined && cfg.phrase1 && cfg.phrase2) {
            const isEmerald = (gameSlug === 'emerald');
            const updatedSpots = calculateFeebasFishingSpots(cfg.tid, cfg.phrase1, cfg.phrase2, isEmerald);
            if (updatedSpots && updatedSpots.length > 0) {
                cfg.spots = updatedSpots;
                saveGameConfigData(cfg, gameSlug);
            }
        }
        spots = (cfg && cfg.spots) ? cfg.spots : [];
    }

    const markersLayer = document.getElementById('feebas-map-markers-layer');
    const jumpNav = document.getElementById('feebas-spots-jump-nav');

    if (markersLayer) {
        markersLayer.innerHTML = spots.map((spot, idx) => {
            let bgClass = 'bg-rose-600';
            let pingClass = 'bg-rose-400';
            let badgeText = `${idx + 1}`;
            let tooltipText = `Casilla #${spot.tileId}`;

            if (spot.group) {
                if (spot.group === 'Garantizada') {
                    bgClass = 'bg-emerald-600';
                    pingClass = 'bg-emerald-400';
                    tooltipText = `Casilla #${spot.tileId} (100% Certeza)`;
                } else if (spot.group === 'Grupo A') {
                    bgClass = 'bg-sky-600';
                    pingClass = 'bg-sky-400';
                    badgeText = `A${(idx % 2) + 1}`;
                    tooltipText = `Casilla #${spot.tileId} (Grupo A • 50%)`;
                } else if (spot.group === 'Grupo B') {
                    bgClass = 'bg-purple-600';
                    pingClass = 'bg-purple-400';
                    badgeText = `B${(idx % 2) + 1}`;
                    tooltipText = `Casilla #${spot.tileId} (Grupo B • 50%)`;
                }
            }

            if (isGen4Sinnoh) {
                return `
                    <div 
                        id="feebas-marker-${idx}"
                        class="absolute cursor-pointer group z-20 flex items-center justify-center pointer-events-auto"
                        style="left: ${spot.x}px; top: ${spot.y}px; width: 32px; height: 32px; transform: translate(-50%, -50%);"
                        onclick="highlightFeebasSpot(${idx})"
                        title="${tooltipText} (${spot.rawX || spot.x}, ${spot.rawY || spot.y})"
                    >
                        <span class="animate-ping absolute w-5 h-5 rounded-full ${pingClass} opacity-60 pointer-events-none"></span>
                        <div class="relative w-[22px] h-[22px] rounded-full ${bgClass} border-[1.5px] border-white text-[10px] font-black text-white flex items-center justify-center shadow-md group-hover:scale-125 transition-transform select-none">
                            ${badgeText}
                        </div>
                        <div class="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-0.5 bg-slate-950 text-amber-300 border border-slate-700 rounded text-[10px] font-black whitespace-nowrap shadow-lg pointer-events-none z-30">
                            ${tooltipText}
                        </div>
                    </div>
                `;
            }

            return `
                <div 
                    id="feebas-marker-${idx}"
                    class="absolute cursor-pointer group z-20 flex items-center justify-center pointer-events-auto"
                    style="left: ${spot.x}px; top: ${spot.y}px; width: 16px; height: 16px; transform: translate(-50%, -50%);"
                    onclick="highlightFeebasSpot(${idx})"
                    title="${tooltipText} (${spot.x}, ${spot.y})"
                >
                    <span class="animate-ping absolute w-3 h-3 rounded-full ${pingClass} opacity-60 pointer-events-none"></span>
                    <div class="relative w-[12px] h-[12px] rounded-full ${bgClass} border border-white text-[8px] font-black text-white flex items-center justify-center shadow-sm group-hover:scale-150 transition-transform select-none">
                        ${badgeText}
                    </div>
                    <div class="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-0.5 bg-slate-950 text-amber-300 border border-slate-700 rounded text-[10px] font-black whitespace-nowrap shadow-lg pointer-events-none z-30">
                        ${tooltipText}
                    </div>
                </div>
            `;
        }).join('');
    }

    if (jumpNav) {
        jumpNav.innerHTML = spots.map((spot, idx) => {
            let btnBg = 'bg-rose-500 hover:bg-rose-400';
            let label = `#${idx + 1} (${spot.tileId})`;

            if (spot.group) {
                if (spot.group === 'Garantizada') {
                    btnBg = 'bg-emerald-600 hover:bg-emerald-500';
                    label = `#${idx + 1} (${spot.tileId})`;
                } else if (spot.group === 'Grupo A') {
                    btnBg = 'bg-sky-600 hover:bg-sky-500';
                    label = `A${(idx % 2) + 1} (${spot.tileId})`;
                } else if (spot.group === 'Grupo B') {
                    btnBg = 'bg-purple-600 hover:bg-purple-500';
                    label = `B${(idx % 2) + 1} (${spot.tileId})`;
                }
            }

            return `
                <button 
                    type="button" 
                    onclick="highlightFeebasSpot(${idx})"
                    class="px-2 py-0.5 text-[10px] font-black uppercase rounded border border-slate-950 ${btnBg} text-white shadow-[1px_1px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                    title="Ir a Casilla #${spot.tileId}"
                >
                    ${label}
                </button>
            `;
        }).join('');
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
 * Alterna la visibilidad de la cuadrícula suave en el mapa de Feebas.
 */
export function toggleFeebasMapGrid() {
    const grid = document.getElementById('feebas-map-grid');
    const btn = document.getElementById('feebas-grid-toggle-btn');
    if (!grid) return;

    const isHidden = grid.classList.contains('hidden') || grid.style.display === 'none';
    if (isHidden) {
        grid.classList.remove('hidden');
        grid.style.display = 'block';
        if (btn) {
            btn.classList.remove('bg-white', 'text-slate-600');
            btn.classList.add('bg-amber-200', 'text-slate-900');
            btn.setAttribute('aria-pressed', 'true');
        }
    } else {
        grid.classList.add('hidden');
        grid.style.display = 'none';
        if (btn) {
            btn.classList.remove('bg-amber-200', 'text-slate-900');
            btn.classList.add('bg-white', 'text-slate-600');
            btn.setAttribute('aria-pressed', 'false');
        }
    }
}

/**
 * Desplaza la vista del mapa de Feebas hacia una zona de la ruta o monte.
 */
export function scrollFeebasMapTo(section) {
    const viewport = document.getElementById('feebas-map-viewport');
    if (!viewport) return;

    const gameSlug = (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || '';
    const isGen4Sinnoh = ['diamond', 'pearl', 'platinum'].includes(gameSlug);

    let targetY = 0;
    if (isGen4Sinnoh) {
        if (section === 'north') targetY = 50;
        else if (section === 'center') targetY = 500;
        else if (section === 'south') targetY = 950;
    } else {
        if (section === 'north') targetY = 50;
        else if (section === 'center') targetY = 900;
        else if (section === 'south') targetY = 1750;
    }

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
    const isGen4Sinnoh = ['diamond', 'pearl', 'platinum'].includes(gameSlug);
    const cfg = loadGameConfig(gameSlug);
    const spots = isGen4Sinnoh
        ? ((cfg && (cfg.feebasSpots || cfg.spots)) || [])
        : ((cfg && cfg.spots) || []);
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
    const todayInput = document.getElementById('cfg-feebas-gen4-today');
    const yestInput = document.getElementById('cfg-feebas-gen4-yesterday');

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
    if (todayInput) {
        todayInput.addEventListener('input', () => {
            sanitizeDigits(todayInput);
            renderConfigPreview();
        });
    }
    if (yestInput) {
        yestInput.addEventListener('input', () => {
            sanitizeDigits(yestInput);
            renderConfigPreview();
        });
    }

    updateConfigDotIndicator();
}
