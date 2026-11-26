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
import { calculateFeebasFishingSpots, calculateGen4FeebasSpots, calculateGen4FeebasFromSeed } from './feebas_calculator.js';
import { getAllPrimoRewards, calculatePrimoWords, PRIMO_WALLPAPERS, PRIMO_EGGS } from './primo_calculator.js';
import {
    WHITE_FOREST_RESIDENTS,
    WHITE_FOREST_RESIDENTS_BY_ID,
    WHITE_FOREST_MAX_RESIDENTS,
    calculateWhiteForestResults
} from './white_forest_data.js';
import { bringModalToFront, registerModalClose, lockModalScroll, releaseScrollIfNoModalOpen } from './url_sync.js';

// Estado temporal del modal del Bosque Blanco (Pokémon Blanco)
let wfDraftSelection = [];
let wfSearchQuery = '';

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
    const rawSlug = gameSlug || (window.POKEDEX_CONFIG && window.POKEDEX_CONFIG.gameSlug) || 'default';
    const normalizedSlug = rawSlug.startsWith('heartgold')
        ? 'heartgold'
        : (rawSlug.startsWith('soulsilver')
            ? 'soulsilver'
            : (rawSlug === 'white' ? 'white' : rawSlug));
    return `pokedex_game_config_${normalizedSlug}`;
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
    const hasGen4Feebas = cfg && (Boolean(cfg.groupSeed) || (cfg.lottoToday !== null && cfg.lottoToday !== undefined) || (cfg.feebasSpots && cfg.feebasSpots.length > 0));
    const hasWhiteForest = cfg && Array.isArray(cfg.whiteForestResidents) && cfg.whiteForestResidents.length > 0;
    if (hasTid || hasGen3Feebas || hasGen4Feebas || hasWhiteForest) {
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
    const seedInput = document.getElementById('cfg-feebas-gen4-seed');

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
    if (seedInput) {
        seedInput.value = (cfg && cfg.groupSeed) ? cfg.groupSeed : '';
    }

    const hgssTidInput = document.getElementById('cfg-hgss-trainer-id');
    const hgssLangSelect = document.getElementById('cfg-hgss-lang');
    if (hgssTidInput) {
        hgssTidInput.value = (cfg && cfg.tid !== undefined && cfg.tid !== null) ? cfg.tid : '';
    }
    if (hgssLangSelect) {
        hgssLangSelect.value = (cfg && cfg.primoLang) ? cfg.primoLang : 'es';
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

        // Restablecer acordeón de Cástor para próxima apertura
        const primoContent = document.getElementById('primo-accordion-content');
        const primoIcon = document.getElementById('primo-accordion-icon');
        const primoLabel = document.getElementById('primo-accordion-label');
        const primoBtn = document.getElementById('primo-accordion-btn');
        if (primoContent) {
            if (primoContent._animCleanup) primoContent._animCleanup();
            primoContent.classList.add('hidden');
            primoContent.style.maxHeight = '';
            primoContent.style.overflow = '';
            primoContent.style.opacity = '';
            primoContent.style.transition = '';
        }
        if (primoIcon) primoIcon.classList.remove('rotate-180');
        if (primoLabel) primoLabel.textContent = 'Ver nota';
        if (primoBtn) primoBtn.setAttribute('aria-expanded', 'false');
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
    const isGen4Sinnoh = ['diamond', 'pearl', 'platinum'].includes(gameSlug);
    const isGen4HGSS = gameSlug.startsWith('heartgold') || gameSlug.startsWith('soulsilver');
    const isWhite = gameSlug === 'white';

    if (isWhite) {
        renderWhiteForestConfigSummary();
        return;
    }

    // 0. Previsualización para Gen 4 HeartGold / SoulSilver (Cástor: Huevos y Fondos del PC)
    if (isGen4HGSS) {
        const hgssTidInput = document.getElementById('cfg-hgss-trainer-id');
        const hgssLangSelect = document.getElementById('cfg-hgss-lang');
        const primoPreview = document.getElementById('cfg-primo-preview');
        const eggsList = document.getElementById('cfg-primo-eggs-list');
        const wallpapersList = document.getElementById('cfg-primo-wallpapers-list');

        const tidRaw = hgssTidInput ? hgssTidInput.value.trim() : '';
        const tidVal = parseInt(tidRaw, 10);
        const hasValidTid = !isNaN(tidVal) && tidVal >= 0 && tidVal <= 65535;
        const lang = hgssLangSelect ? hgssLangSelect.value : 'es';

        if (!hasValidTid || !primoPreview) {
            if (primoPreview) primoPreview.classList.add('hidden');
            if (eggsList) eggsList.innerHTML = '';
            if (wallpapersList) wallpapersList.innerHTML = '';
            return;
        }

        const rewards = getAllPrimoRewards(tidVal, lang);
        if (!rewards) {
            primoPreview.classList.add('hidden');
            return;
        }

        primoPreview.classList.remove('hidden');

        if (eggsList) {
            eggsList.innerHTML = rewards.eggs.map(egg => `
                <div class="p-2.5 rounded-xl border-2 border-slate-950 bg-pink-50 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div class="flex items-center gap-2 min-w-0">
                        <img src="/media/items/mystery-egg.png" alt="" class="w-6 h-6 object-contain pixel-art shrink-0">
                        <div class="min-w-0">
                            <span class="font-black text-xs text-slate-950 block truncate">Huevo de ${egg.name}</span>
                            <span class="text-[9px] font-bold text-pink-900 block">Ciudad Malva • Centro Pokémon</span>
                        </div>
                    </div>
                    <div class="flex flex-col gap-1 sm:text-right shrink-0">
                        <div class="text-[10px] font-black uppercase text-pink-950 bg-white border border-pink-300 rounded px-2 py-0.5 tracking-tight shadow-xs flex items-center justify-between sm:justify-end gap-1.5">
                            <span class="text-[8px] text-slate-400 font-bold uppercase sm:hidden">Frase 1:</span>
                            <span>${egg.calc.line1[0]} • ${egg.calc.line1[1]}</span>
                        </div>
                        <div class="text-[10px] font-black uppercase text-pink-950 bg-white border border-pink-300 rounded px-2 py-0.5 tracking-tight shadow-xs flex items-center justify-between sm:justify-end gap-1.5">
                            <span class="text-[8px] text-slate-400 font-bold uppercase sm:hidden">Frase 2:</span>
                            <span>${egg.calc.line2[0]} • ${egg.calc.line2[1]}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        if (wallpapersList) {
            wallpapersList.innerHTML = rewards.wallpapers.map(wp => `
                <div class="p-2 rounded-lg border-2 border-slate-950/20 bg-slate-50 flex flex-col justify-between gap-1 shadow-xs hover:border-slate-950 transition-colors">
                    <div class="font-black text-[11px] text-slate-900 uppercase tracking-tight flex items-center justify-between">
                        <span>${wp.name}</span>
                        <span class="text-[9px] font-black px-1 rounded bg-amber-100 text-amber-900 border border-amber-300">Fondo</span>
                    </div>
                    <div class="text-[9px] font-black uppercase text-slate-800 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-center leading-snug">
                        <span>${wp.calc.line1[0]} ${wp.calc.line1[1]}</span>
                        <span class="text-slate-400 font-bold mx-1">/</span>
                        <span>${wp.calc.line2[0]} ${wp.calc.line2[1]}</span>
                    </div>
                </div>
            `).join('');
        }
        return;
    }

    const tidInput = document.getElementById('cfg-trainer-id');
    const tidVal = tidInput ? parseInt(tidInput.value, 10) : NaN;
    const hasValidTid = !isNaN(tidVal) && tidVal >= 0 && tidVal <= 65535;

    // 1. Previsualización para Gen 4 (Munchlax y Feebas en Sinnoh)
    if (isGen4Sinnoh) {
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

        // Feebas Gen 4 (Semilla Hexadecimal Directa o Lotería Jubileo TV -> Casillas Monte Corona Sótano)
        const lottoTodayInput = document.getElementById('cfg-feebas-gen4-today');
        const lottoYestInput = document.getElementById('cfg-feebas-gen4-yesterday');
        const seedInput = document.getElementById('cfg-feebas-gen4-seed');
        const gen4Preview = document.getElementById('cfg-feebas-gen4-preview');
        const gen4CountBadge = document.getElementById('cfg-feebas-gen4-count-badge');
        const gen4Summary = document.getElementById('cfg-feebas-gen4-spots-summary');

        if (gen4Preview && gen4Summary) {
            const seedRaw = seedInput ? seedInput.value.trim() : '';
            const todayRaw = lottoTodayInput ? lottoTodayInput.value.trim() : '';
            const yestRaw = lottoYestInput ? lottoYestInput.value.trim() : '';

            let spots = [];
            let badgeText = '';
            let isGuaranteed = false;

            // Prioridad 1: Semilla Hexadecimal directa
            if (seedRaw !== '') {
                let cleanHex = seedRaw.toLowerCase().startsWith('0x') ? seedRaw.substring(2) : seedRaw;
                if (/^[0-9a-fA-F]{1,8}$/.test(cleanHex)) {
                    spots = calculateGen4FeebasFromSeed(cleanHex);
                    isGuaranteed = true;
                    badgeText = `${spots.length} Casillas (100% Certeza • Semilla Hex)`;
                }
            } 
            // Prioridad 2: Números de Lotería
            else if (todayRaw !== '') {
                const todayVal = parseInt(todayRaw, 10);
                const hasValidToday = !isNaN(todayVal) && todayVal >= 0 && todayVal <= 65535;

                if (hasValidToday) {
                    const yestVal = yestRaw !== '' ? parseInt(yestRaw, 10) : null;
                    const hasValidYest = (yestVal !== null && !isNaN(yestVal) && yestVal >= 0 && yestVal <= 65535);

                    if (hasValidYest) {
                        spots = calculateGen4FeebasSpots(todayVal, yestVal);
                        isGuaranteed = spots.some(s => s.certainty === 100);
                        if (isGuaranteed) {
                            badgeText = `${spots.length} Casillas (100% Certeza • Lotería)`;
                        } else if (spots.length === 8) {
                            badgeText = `8 Casillas (2 Grupos de 4 • 50% Prob.)`;
                        } else {
                            badgeText = `${spots.length} Casillas`;
                        }
                    }
                }
            }

            if (!spots || spots.length === 0) {
                gen4Preview.classList.add('hidden');
                gen4Summary.innerHTML = '';
            } else {
                gen4Preview.classList.remove('hidden');

                if (gen4CountBadge) {
                    gen4CountBadge.textContent = badgeText;
                    gen4CountBadge.className = isGuaranteed
                        ? 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-emerald-300 text-slate-950'
                        : 'text-[9px] font-black px-1.5 py-0.5 rounded border border-slate-950 bg-purple-200 text-purple-950';
                }

                gen4Summary.innerHTML = spots.map((s, idx) => {
                    let badgeBg = 'bg-emerald-50 border-emerald-400 text-emerald-950';
                    let groupPrefix = `#${idx + 1}`;
                    if (s.group && (s.group.includes('Morada') || s.group === 'Grupo 1')) {
                        badgeBg = 'bg-purple-50 border-purple-400 text-purple-950';
                        groupPrefix = `Morada #${(idx % 4) + 1}`;
                    } else if (s.group && (s.group.includes('Verde') || s.group === 'Grupo 2')) {
                        badgeBg = 'bg-emerald-50 border-emerald-400 text-emerald-950';
                        groupPrefix = `Verde #${(idx % 4) + 1}`;
                    }
                    return `
                        <span class="px-2 py-1 rounded-md ${badgeBg} border text-[11px] font-black shadow-xs">
                            ${groupPrefix}: Casilla ${s.tileId} (${s.rawX}, ${s.rawY})
                        </span>
                    `;
                }).join('');
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
    const isGen4HGSS = gameSlug.startsWith('heartgold') || gameSlug.startsWith('soulsilver');

    // Gen 4 HGSS (Cástor: Huevos y Fondos del PC)
    if (isGen4HGSS) {
        const hgssTidInput = document.getElementById('cfg-hgss-trainer-id');
        const hgssLangSelect = document.getElementById('cfg-hgss-lang');
        const tidRaw = hgssTidInput ? hgssTidInput.value.trim() : '';
        const lang = hgssLangSelect ? hgssLangSelect.value : 'es';

        if (tidRaw === '') {
            saveGameConfigData(null);
            closeGameConfigModal();
            refreshOpenModals();
            return;
        }

        const tidVal = parseInt(tidRaw, 10);
        if (isNaN(tidVal) || tidVal < 0 || tidVal > 65535) {
            alert('Por favor introduce un ID de Entrenador (TID) válido entre 0 y 65535.');
            if (hgssTidInput) hgssTidInput.focus();
            return;
        }

        const configData = {
            tid: tidVal,
            primoLang: lang,
            updatedAt: new Date().toISOString()
        };

        saveGameConfigData(configData);
        closeGameConfigModal();
        refreshOpenModals();
        return;
    }

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
        const seedInput = document.getElementById('cfg-feebas-gen4-seed');

        const tidRaw = tidInput ? tidInput.value.trim() : '';
        const sidRaw = sidInput ? sidInput.value.trim() : '';
        const todayRaw = lottoTodayInput ? lottoTodayInput.value.trim() : '';
        const yestRaw = lottoYestInput ? lottoYestInput.value.trim() : '';
        const seedRaw = seedInput ? seedInput.value.trim() : '';

        // Si todos los campos están vacíos, se limpia la configuración
        if (!tidRaw && !sidRaw && !todayRaw && !yestRaw && !seedRaw) {
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
        let groupSeedVal = null;
        let lottoTodayVal = null;
        let lottoYestVal = null;
        let feebasSpots = null;

        // Caso A: Se ingresó la Semilla Hexadecimal directa (Método 100% exacto e instantáneo)
        if (seedRaw !== '') {
            let cleanHex = seedRaw.toLowerCase().startsWith('0x') ? seedRaw.substring(2) : seedRaw;
            if (!/^[0-9a-fA-F]{1,8}$/.test(cleanHex)) {
                alert('La Semilla Hexadecimal (Group Seed) debe ser un valor hexadecimal válido de 1 a 8 caracteres (ej. 4A2F8B1C o 0x4A2F8B1C).');
                if (seedInput) seedInput.focus();
                return;
            }
            groupSeedVal = cleanHex.toUpperCase();
            feebasSpots = calculateGen4FeebasFromSeed(cleanHex);

            // Si además ingresó boletos de lotería válidos, se registran opcionalmente
            if (todayRaw !== '') {
                const tv = parseInt(todayRaw, 10);
                if (!isNaN(tv) && tv >= 0 && tv <= 99999) lottoTodayVal = tv;
            }
            if (yestRaw !== '') {
                const yv = parseInt(yestRaw, 10);
                if (!isNaN(yv) && yv >= 0 && yv <= 99999) lottoYestVal = yv;
            }
        }
        // Caso B: No hay semilla hexadecimal, se evalúa el método por Lotería
        else if (todayRaw !== '' || yestRaw !== '') {
            if (todayRaw === '' || yestRaw === '') {
                alert('Para calcular las casillas de Feebas por lotería se requieren los 2 números (ayer y hoy). Alternativamente, puedes ingresar directamente la Semilla Hexadecimal (Group Seed).');
                if (todayRaw === '' && lottoTodayInput) lottoTodayInput.focus();
                else if (yestRaw === '' && lottoYestInput) lottoYestInput.focus();
                return;
            }

            lottoTodayVal = parseInt(todayRaw, 10);
            lottoYestVal = parseInt(yestRaw, 10);

            if (isNaN(lottoTodayVal) || lottoTodayVal < 0 || lottoTodayVal > 99999) {
                alert('El número de Lotería de Hoy (Jubileo TV) debe ser un número entre 00000 y 99999.');
                if (lottoTodayInput) lottoTodayInput.focus();
                return;
            }

            if (isNaN(lottoYestVal) || lottoYestVal < 0 || lottoYestVal > 99999) {
                alert('El número de Lotería de Ayer debe ser un número entre 00000 y 99999.');
                if (lottoYestInput) lottoYestInput.focus();
                return;
            }

            feebasSpots = calculateGen4FeebasSpots(lottoTodayVal, lottoYestVal);
            if (!feebasSpots || feebasSpots.length === 0) {
                alert('No se pudo encontrar una semilla coincidente con esos números de lotería. Asegúrate de ingresar boletos de dos días consecutivos.');
                return;
            }
        }

        const configData = {
            tid: tidVal,
            sid: sidVal,
            groupSeed: groupSeedVal,
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

    // Caso Pokémon Blanco (Bosque Blanco: la configuración se gestiona desde su modal dedicado)
    if (gameSlug === 'white') {
        closeGameConfigModal();
        refreshOpenModals();
        if (typeof window.filterCards === 'function') {
            window.filterCards();
        }
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
    const seedInput = document.getElementById('cfg-feebas-gen4-seed');

    if (tidInput) tidInput.value = '';
    if (sidInput) sidInput.value = '';
    if (w1Input) w1Input.value = '';
    if (w2Input) w2Input.value = '';
    if (todayInput) todayInput.value = '';
    if (yestInput) yestInput.value = '';
    if (seedInput) seedInput.value = '';

    const hgssTidInput = document.getElementById('cfg-hgss-trainer-id');
    const hgssLangSelect = document.getElementById('cfg-hgss-lang');
    if (hgssTidInput) hgssTidInput.value = '';
    if (hgssLangSelect) hgssLangSelect.value = 'es';

    wfDraftSelection = [];
    renderConfigPreview();
    closeGameConfigModal();
    refreshOpenModals();
    if (typeof window.filterCards === 'function') {
        window.filterCards();
    }
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
 * Alterna el acordeón de instrucciones de Cástor en Gen 4 (HGSS) con transición fluida.
 */
export function togglePrimoAccordion() {
    const content = document.getElementById('primo-accordion-content');
    const icon = document.getElementById('primo-accordion-icon');
    const label = document.getElementById('primo-accordion-label');
    const btn = document.getElementById('primo-accordion-btn');
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
        if (cfg && (cfg.groupSeed || (cfg.lottoToday !== undefined && cfg.lottoToday !== null))) {
            if (cfg.groupSeed) {
                spots = calculateGen4FeebasFromSeed(cfg.groupSeed);
            } else {
                spots = calculateGen4FeebasSpots(cfg.lottoToday, cfg.lottoYesterday);
            }
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
                } else if (spot.group.includes('Morada') || spot.group === 'Grupo 1') {
                    bgClass = 'bg-purple-600';
                    pingClass = 'bg-purple-400';
                    badgeText = `M${(idx % 4) + 1}`;
                    tooltipText = `Casilla #${spot.tileId} (Grupo 1 • Moradas • 50%)`;
                } else if (spot.group.includes('Verde') || spot.group === 'Grupo 2') {
                    bgClass = 'bg-emerald-600';
                    pingClass = 'bg-emerald-400';
                    badgeText = `V${(idx % 4) + 1}`;
                    tooltipText = `Casilla #${spot.tileId} (Grupo 2 • Verdes • 50%)`;
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
                } else if (spot.group.includes('Morada') || spot.group === 'Grupo 1') {
                    btnBg = 'bg-purple-600 hover:bg-purple-500';
                    label = `M${(idx % 4) + 1} (${spot.tileId})`;
                } else if (spot.group.includes('Verde') || spot.group === 'Grupo 2') {
                    btnBg = 'bg-emerald-600 hover:bg-emerald-500';
                    label = `V${(idx % 4) + 1} (${spot.tileId})`;
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
 * Normaliza texto para búsqueda insensible a tildes/mayúsculas en el modal del Bosque Blanco.
 */
function normalizeWfText(str) {
    return (str || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

/**
 * Renderiza el resumen de la configuración actual del Bosque Blanco dentro del modal de Configuración.
 */
export function renderWhiteForestConfigSummary() {
    const summaryBox = document.getElementById('cfg-white-forest-summary');
    if (!summaryBox) return;

    const cfg = loadGameConfig('white');
    const savedIds = (cfg && Array.isArray(cfg.whiteForestResidents)) ? cfg.whiteForestResidents : [];
    const results = calculateWhiteForestResults(savedIds);

    if (results.selectedResidents.length === 0) {
        summaryBox.className = 'mb-3 p-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 text-xs text-slate-600 font-bold';
        summaryBox.innerHTML = 'Sin residentes configurados todavía. El filtro <strong>Bosque Blanco</strong> mostrará las 33 especies posibles.';
        return;
    }

    const chipsHtml = results.selectedResidents.map(r => `
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg border border-slate-950 bg-white text-[11px] font-black text-slate-900 shadow-[1px_1px_0px_#0f172a]">
            <img src="${r.sprite}" alt="" class="w-4 h-4 object-contain pixel-art shrink-0">
            <span>${r.name}</span>
        </span>
    `).join('');

    summaryBox.className = 'mb-3 p-3 rounded-xl border-2 border-slate-950 bg-emerald-50/80 text-xs text-slate-900 space-y-2 shadow-[1.5px_1.5px_0px_#0f172a]';
    summaryBox.innerHTML = `
        <div class="flex flex-wrap items-center justify-between gap-1.5">
            <span class="text-[11px] font-black uppercase tracking-wider text-emerald-900">
                ${results.selectedResidents.length} / ${WHITE_FOREST_MAX_RESIDENTS} Residentes Activos
            </span>
            <span class="text-[10px] font-black text-emerald-800">
                ${results.grassEncounters.length} hierba · ${results.surfEncounters.length} surf · ${results.dailyItems.length} objetos
            </span>
        </div>
        <div class="flex flex-wrap gap-1.5">
            ${chipsHtml}
        </div>
    `;
}

/**
 * Formatea el nombre de un Pokémon del Bosque Blanco resaltando los símbolos de género (♀/♂).
 */
function formatWfPokemonName(name) {
    if (!name) return '';
    if (name.includes('♀')) {
        return name.replace(
            '♀',
            '<svg class="inline-block w-3.5 h-3.5 ml-0.5 -mt-0.5 text-rose-600 shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-label="♀"><circle cx="8" cy="5.75" r="3.5"/><path d="M8 9.25v5M5.75 12.25h4.5"/></svg>'
        );
    }
    if (name.includes('♂')) {
        return name.replace(
            '♂',
            '<svg class="inline-block w-3.5 h-3.5 ml-0.5 -mt-0.5 text-sky-600 shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-label="♂"><circle cx="6.25" cy="9.75" r="3.5"/><path d="M8.75 7.25l4.5-4.5M9.5 2.75h3.75V6.5"/></svg>'
        );
    }
    return name;
}

/**
 * Renderiza la cuadrícula de los 30 entrenadores del Bosque Blanco.
 */
function renderWhiteForestGrid() {
    const grid = document.getElementById('wf-residents-grid');
    const counter = document.getElementById('wf-selected-counter');
    const limitHint = document.getElementById('wf-limit-hint');
    if (!grid) return;

    const selectedSet = new Set(wfDraftSelection);
    const isFull = selectedSet.size >= WHITE_FOREST_MAX_RESIDENTS;
    const normQ = normalizeWfText(wfSearchQuery);

    if (counter) {
        counter.textContent = `${selectedSet.size} / ${WHITE_FOREST_MAX_RESIDENTS}`;
        if (isFull) {
            counter.classList.remove('bg-white', 'text-slate-950');
            counter.classList.add('bg-amber-300', 'text-slate-950');
        } else {
            counter.classList.remove('bg-amber-300');
            counter.classList.add('bg-white', 'text-slate-950');
        }
    }

    const filtered = WHITE_FOREST_RESIDENTS.filter(r => {
        if (!normQ) return true;
        const haystack = normalizeWfText(`${r.name} ${r.trainerClass} ${r.grass.name} ${r.surf.name} ${r.item.name}`);
        return haystack.includes(normQ);
    });

    if (limitHint) {
        if (isFull) {
            limitHint.textContent = 'Límite máximo (10/10) alcanzado';
            limitHint.className = 'text-[10px] font-black uppercase tracking-wide text-amber-800 shrink-0 text-right';
        } else if (normQ) {
            limitHint.textContent = `${filtered.length} de 30 residentes`;
            limitHint.className = 'text-[10px] font-black uppercase tracking-wide text-slate-600 shrink-0 text-right';
        } else {
            limitHint.textContent = '30 residentes disponibles';
            limitHint.className = 'text-[10px] font-black uppercase tracking-wide text-slate-600 shrink-0 text-right';
        }
    }

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-8 text-center text-xs font-bold text-slate-500">
                No se encontraron residentes para "${wfSearchQuery.replace(/</g, '&lt;')}".
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(r => {
        const isSelected = selectedSet.has(r.id);
        const isLocked = !isSelected && isFull;
        const cardClass = isSelected
            ? 'border-emerald-700 bg-emerald-50 ring-2 ring-emerald-500 shadow-[2px_2px_0px_0px_#065f46]'
            : (isLocked
                ? 'border-slate-300 bg-slate-100/70 opacity-55 cursor-not-allowed'
                : 'border-slate-950 bg-white hover:bg-amber-50/70 shadow-[2px_2px_0px_0px_#0f172a] cursor-pointer');

        return `
            <button
                type="button"
                onclick="toggleWhiteForestResident('${r.id}')"
                data-resident-id="${r.id}"
                aria-pressed="${isSelected ? 'true' : 'false'}"
                class="relative text-left p-2 rounded-xl border-2 transition-all flex flex-col justify-between gap-1.5 ${cardClass}"
            >
                <div class="flex items-center gap-2 min-w-0">
                    <div class="w-10 h-10 rounded-lg border-2 ${isSelected ? 'border-emerald-700 bg-white' : 'border-slate-900 bg-slate-50'} flex items-center justify-center shrink-0 overflow-hidden">
                        <img src="${r.sprite}" alt="${r.trainerClass} ${r.name}" class="w-8 h-8 object-contain pixel-art" loading="lazy">
                    </div>
                    <div class="min-w-0 flex-1 pr-4">
                        <div class="text-xs font-black text-slate-950 truncate leading-tight">${r.name}</div>
                        <div class="text-[10px] font-bold text-slate-500 truncate leading-tight">${r.trainerClass}</div>
                    </div>
                    <span class="absolute top-1.5 right-1.5 w-4 h-4 rounded-full border border-slate-950 flex items-center justify-center text-[10px] font-black ${isSelected ? 'bg-emerald-500 text-white' : 'bg-white text-transparent'}">
                        ✓
                    </span>
                </div>
                <div class="flex items-center justify-between gap-1.5 pt-1.5 border-t border-slate-200/80 text-[11px] font-bold text-slate-700">
                    <span class="inline-flex items-center gap-1.5 min-w-0 truncate" title="Hierba Alta: ${r.grass.name}">
                        <span class="w-12 h-12 overflow-hidden flex items-center justify-center shrink-0">
                            <img src="/media/pokemon/sprites/white/${r.grass.id}.png" alt="" class="w-full h-full object-contain pixel-art scale-[1.5]" loading="lazy">
                        </span>
                        <span class="truncate">${formatWfPokemonName(r.grass.name)}</span>
                    </span>
                    <span class="inline-flex items-center justify-center shrink-0 pr-0.5 text-slate-600" title="Objeto diario: ${r.item.name} (${r.item.chance}%)">
                        <img src="/media/items/${r.item.slug}.png" alt="" class="w-10 h-10 object-contain pixel-art shrink-0" loading="lazy">
                    </span>
                </div>
            </button>
        `;
    }).join('');
}

/**
 * Renderiza los resultados calculados (Hierba Alta, Surf y Objetos Diarios) en tiempo real.
 */
function renderWhiteForestResults() {
    const emptyEl = document.getElementById('wf-results-empty');
    const contentEl = document.getElementById('wf-results-content');
    const grassList = document.getElementById('wf-grass-list');
    const surfList = document.getElementById('wf-surf-list');
    const itemsList = document.getElementById('wf-items-list');
    const grassCount = document.getElementById('wf-grass-count');
    const surfCount = document.getElementById('wf-surf-count');
    const itemsCount = document.getElementById('wf-items-count');

    const results = calculateWhiteForestResults(wfDraftSelection);
    if (results.selectedResidents.length === 0) {
        if (emptyEl) emptyEl.classList.remove('hidden');
        if (contentEl) contentEl.classList.add('hidden');
        return;
    }

    if (emptyEl) emptyEl.classList.add('hidden');
    if (contentEl) contentEl.classList.remove('hidden');

    if (grassCount) {
        grassCount.textContent = `${results.grassEncounters.length} ${results.grassEncounters.length === 1 ? 'especie' : 'especies'}`;
    }
    if (surfCount) {
        surfCount.textContent = `${results.surfEncounters.length} ${results.surfEncounters.length === 1 ? 'especie' : 'especies'}`;
    }
    if (itemsCount) {
        itemsCount.textContent = `${results.dailyItems.length} ${results.dailyItems.length === 1 ? 'objeto' : 'objetos'}`;
    }

    if (grassList) {
        grassList.innerHTML = results.grassEncounters.map(enc => `
            <div class="flex items-center justify-between gap-2 px-2.5 py-1 rounded-lg bg-emerald-50/70 border border-emerald-200">
                <div class="flex items-center gap-2 min-w-0">
                    <span class="w-16 h-16 overflow-hidden flex items-center justify-center shrink-0">
                        <img src="/media/pokemon/sprites/white/${enc.id}.png" alt="${enc.name}" class="w-full h-full object-contain pixel-art scale-[1.5]">
                    </span>
                    <div class="min-w-0">
                        <div class="text-xs font-black text-slate-900 truncate leading-tight">
                            <span class="font-mono text-[10px] text-slate-500">#${String(enc.id).padStart(3, '0')}</span> ${formatWfPokemonName(enc.name)}
                        </div>
                        <div class="text-[10px] font-bold text-slate-500 truncate leading-tight">
                            ${enc.resident.trainerClass} ${enc.resident.name}
                        </div>
                    </div>
                </div>
                <span class="px-2.5 py-0.5 rounded-md border border-slate-950 bg-emerald-300 text-slate-950 font-mono font-extrabold tracking-wide text-[11px] shrink-0 tabular-nums">
                    ${enc.percentLabel}
                </span>
            </div>
        `).join('');
    }

    if (surfList) {
        surfList.innerHTML = results.surfEncounters.map(enc => {
            const names = enc.contributors.map(r => r.name).join(', ');
            return `
                <div class="flex items-center justify-between gap-2 px-2.5 py-1 rounded-lg bg-sky-50/70 border border-sky-200">
                    <div class="flex items-center gap-2 min-w-0">
                        <span class="w-16 h-16 overflow-hidden flex items-center justify-center shrink-0">
                            <img src="/media/pokemon/sprites/white/${enc.id}.png" alt="${enc.name}" class="w-full h-full object-contain pixel-art scale-[1.5]">
                        </span>
                        <div class="min-w-0">
                            <div class="text-xs font-black text-slate-900 truncate leading-tight">
                                <span class="font-mono text-[10px] text-slate-500">#${String(enc.id).padStart(3, '0')}</span> ${formatWfPokemonName(enc.name)}
                            </div>
                            <div class="text-[10px] font-bold text-slate-500 truncate leading-tight" title="${names}">
                                Por: ${names}
                            </div>
                        </div>
                    </div>
                    <span class="px-2.5 py-0.5 rounded-md border border-slate-950 bg-sky-300 text-slate-950 font-mono font-extrabold tracking-wide text-[11px] shrink-0 tabular-nums">
                        ${enc.percentLabel}
                    </span>
                </div>
            `;
        }).join('');
    }

    if (itemsList) {
        itemsList.innerHTML = results.dailyItems.map(item => {
            const contribText = item.contributors
                .map(c => item.contributors.length > 1 ? `${c.resident.name} (${c.chance}%)` : `${c.resident.trainerClass} ${c.resident.name}`)
                .join(' + ');
            return `
                <div class="flex items-center justify-between gap-2 px-2.5 py-1 rounded-lg bg-amber-50/70 border border-amber-200">
                    <div class="flex items-center gap-2.5 min-w-0">
                        <img src="${item.icon}" alt="${item.name}" class="w-12 h-12 object-contain pixel-art shrink-0">
                        <div class="min-w-0">
                            <div class="text-xs font-black text-slate-900 truncate leading-tight">${item.name}</div>
                            <div class="text-[10px] font-bold text-slate-500 truncate leading-tight" title="${contribText}">
                                ${contribText}
                            </div>
                        </div>
                    </div>
                    <span class="px-2.5 py-0.5 rounded-md border border-slate-950 bg-amber-300 text-slate-950 font-mono font-extrabold tracking-wide text-[11px] shrink-0 tabular-nums" title="Probabilidad diaria">
                        ${item.chanceLabel} / día
                    </span>
                </div>
            `;
        }).join('');
    }
}

/**
 * Abre el modal secundario de Entrenadores del Bosque Blanco.
 */
export function openWhiteForestModal() {
    const modal = document.getElementById('white-forest-modal');
    const cardPanel = document.getElementById('white-forest-modal-card');
    if (!modal) return;

    const cfg = loadGameConfig('white');
    const saved = (cfg && Array.isArray(cfg.whiteForestResidents)) ? cfg.whiteForestResidents : [];
    wfDraftSelection = saved.filter(id => Boolean(WHITE_FOREST_RESIDENTS_BY_ID[id])).slice(0, WHITE_FOREST_MAX_RESIDENTS);
    wfSearchQuery = '';

    const searchInput = document.getElementById('wf-search-input');
    const searchClear = document.getElementById('wf-search-clear');
    if (searchInput) searchInput.value = '';
    if (searchClear) searchClear.classList.add('hidden');

    renderWhiteForestGrid();
    renderWhiteForestResults();

    modal.style.display = 'flex';
    modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100', 'pointer-events-auto');

    if (cardPanel) {
        cardPanel.classList.remove('scale-95');
        cardPanel.classList.add('scale-100');
    }

    bringModalToFront(modal);
    lockModalScroll();
}

/**
 * Cierra el modal de Entrenadores del Bosque Blanco.
 */
export function closeWhiteForestModal() {
    const modal = document.getElementById('white-forest-modal');
    const cardPanel = document.getElementById('white-forest-modal-card');
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
        releaseScrollIfNoModalOpen();
    }, 150);
}

/**
 * Maneja clic en el fondo oscuro del modal del Bosque Blanco.
 */
export function handleWhiteForestBackdropClick(e) {
    if (e && e.target && e.target.id === 'white-forest-modal') {
        closeWhiteForestModal();
    }
}

/**
 * Alterna la selección de un residente del Bosque Blanco (máximo 10).
 */
export function toggleWhiteForestResident(residentId) {
    if (!WHITE_FOREST_RESIDENTS_BY_ID[residentId]) return;

    const idx = wfDraftSelection.indexOf(residentId);
    if (idx !== -1) {
        wfDraftSelection.splice(idx, 1);
    } else if (wfDraftSelection.length < WHITE_FOREST_MAX_RESIDENTS) {
        wfDraftSelection.push(residentId);
    } else {
        const counter = document.getElementById('wf-selected-counter');
        if (counter) {
            counter.classList.add('scale-110', 'bg-rose-300');
            setTimeout(() => counter.classList.remove('scale-110', 'bg-rose-300'), 280);
        }
        return;
    }

    renderWhiteForestGrid();
    renderWhiteForestResults();
}

/**
 * Filtra visualmente los 30 residentes por nombre, clase, Pokémon u objeto.
 */
export function filterWhiteForestResidents(query) {
    wfSearchQuery = query || '';
    const clearBtn = document.getElementById('wf-search-clear');
    if (clearBtn) {
        clearBtn.classList.toggle('hidden', wfSearchQuery.trim() === '');
    }
    renderWhiteForestGrid();
}

/**
 * Limpia el buscador del modal del Bosque Blanco.
 */
export function clearWhiteForestSearch() {
    const input = document.getElementById('wf-search-input');
    if (input) {
        input.value = '';
        input.focus();
    }
    filterWhiteForestResidents('');
}

/**
 * Vacía la selección temporal de residentes del Bosque Blanco.
 */
export function clearWhiteForestSelection() {
    wfDraftSelection = [];
    renderWhiteForestGrid();
    renderWhiteForestResults();
}

/**
 * Guarda la selección del Bosque Blanco en localStorage y actualiza UI, filtros y modal cómic.
 */
export function saveWhiteForestConfig() {
    const cleanIds = wfDraftSelection.filter(id => Boolean(WHITE_FOREST_RESIDENTS_BY_ID[id])).slice(0, WHITE_FOREST_MAX_RESIDENTS);
    if (cleanIds.length === 0) {
        saveGameConfigData(null, 'white');
    } else {
        saveGameConfigData({
            whiteForestResidents: cleanIds,
            updatedAt: new Date().toISOString()
        }, 'white');
    }

    renderWhiteForestConfigSummary();
    closeWhiteForestModal();
    refreshOpenModals();
    if (typeof window.filterCards === 'function') {
        window.filterCards();
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
    const seedInput = document.getElementById('cfg-feebas-gen4-seed');

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
    if (seedInput) {
        seedInput.addEventListener('input', () => {
            let val = seedInput.value.trim();
            if (val.toLowerCase().startsWith('0x')) {
                val = '0x' + val.slice(2).replace(/[^0-9a-fA-F]/g, '').slice(0, 8);
            } else {
                val = val.replace(/[^0-9a-fA-F]/g, '').slice(0, 8);
            }
            seedInput.value = val.toUpperCase();
            renderConfigPreview();
        });
    }

    const hgssTidInput = document.getElementById('cfg-hgss-trainer-id');
    const hgssLangSelect = document.getElementById('cfg-hgss-lang');
    if (hgssTidInput) {
        hgssTidInput.addEventListener('input', () => {
            sanitizeDigits(hgssTidInput);
            renderConfigPreview();
        });
    }
    if (hgssLangSelect) {
        hgssLangSelect.addEventListener('change', () => {
            renderConfigPreview();
        });
    }

    updateConfigDotIndicator();
}
