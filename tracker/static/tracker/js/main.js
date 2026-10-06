/**
 * Pokédex Global - Entrada Principal (main.js)
 * Orquestador de módulos ES6, registro de eventos globales y compatibilidad con templates HTML.
 */

import { state, config, currentGameSlug, UNOWN_CHAMBER_HINTS } from './state.js';
import { getCsrfToken, postJson } from './api.js';
import { playPokemonCry, playModalCry, setActiveModalCryUrl } from './audio.js';
import { 
    toggleShinydexMode, 
    updateProgressBarUI, 
    updateCardUI, 
    applyShinydexMode, 
    setSpriteStyle, 
    toggleCatch,
    updateNationalRegionsBadgeUI
} from './cards.js';
import { 
    switchNationalRegion, 
    updateBarButtonsUI, 
    initNationalGenerationBar 
} from './national_bar.js';
import { 
    setStatusFilter, 
    normalizeSearchText, 
    matchesLocationQuery, 
    toggleFilterPanel, 
    updateFilterUI, 
    toggleFilterTag, 
    toggleFilterType, 
    clearAllFilters, 
    filterCards 
} from './filters.js';
import { 
    openStoneModal, 
    closeStoneModal, 
    handleStoneModalBackdropClick 
} from './modal_stones.js';
import { 
    openExclusivesModal, 
    closeExclusivesModal, 
    handleExclusivesBackdropClick, 
    switchExclusivesTab, 
    toggleExclusiveCatch, 
    updateExclusivesProgressUI, 
    updateExclusivesModalUI, 
    updateExclusivesCardStatus 
} from './modal_exclusives.js';
import { 
    openTransfersModal, 
    closeTransfersModal, 
    handleTransfersBackdropClick, 
    toggleTransferCatch, 
    updateTransfersCardStatus,
    toggleTransfersInfoAccordion
} from './modal_transfers.js';
import { 
    openUnownModal, 
    closeUnownModal, 
    openClassicUnownModal, 
    openUnownLetterCard,
    switchToUnownModal, 
    filterUnownChamber, 
    updateUnownModalUI, 
    toggleUnownFormCatch 
} from './modal_unown.js';
import { 
    openPokemonModal, 
    openPokemonModalDirect, 
    closePokemonModal, 
    handleModalBackdropClick, 
    updateModalCatchStatus, 
    modalToggleCatch, 
    updateModalNavButtons, 
    getModalNavigableCards, 
    navigatePokemonModal, 
    updateRotateButtonUI, 
    updateModalSpriteDisplay, 
    toggleModalSpriteOrientation, 
    getEntryData, 
    applyCardForm, 
    cycleCardPokemonForm, 
    applyModalForm, 
    cycleModalPokemonForm 
} from './modal_comic.js';
import { 
    setModalUrlHash, 
    clearModalUrlHash, 
    syncUrlToCurrentOpenModal, 
    syncModalFromUrlHash, 
    closeAllModals, 
    releaseScrollIfNoModalOpen 
} from './url_sync.js';

// Exposición al objeto window para compatibilidad total con eventos inline onclick="..." de los templates
window.toggleShinydexMode = toggleShinydexMode;
window.updateProgressBarUI = updateProgressBarUI;
window.updateCardUI = updateCardUI;
window.applyShinydexMode = applyShinydexMode;
window.setSpriteStyle = setSpriteStyle;
window.toggleCatch = toggleCatch;
window.updateNationalRegionsBadgeUI = updateNationalRegionsBadgeUI;
window.switchNationalRegion = switchNationalRegion;
window.updateBarButtonsUI = updateBarButtonsUI;

window.setStatusFilter = setStatusFilter;
window.normalizeSearchText = normalizeSearchText;
window.matchesLocationQuery = matchesLocationQuery;
window.toggleFilterPanel = toggleFilterPanel;
window.updateFilterUI = updateFilterUI;
window.toggleFilterTag = toggleFilterTag;
window.toggleFilterType = toggleFilterType;
window.clearAllFilters = clearAllFilters;
window.filterCards = filterCards;

window.playPokemonCry = playPokemonCry;
window.playModalCry = playModalCry;

window.openStoneModal = openStoneModal;
window.closeStoneModal = closeStoneModal;
window.handleStoneModalBackdropClick = handleStoneModalBackdropClick;

window.openExclusivesModal = openExclusivesModal;
window.closeExclusivesModal = closeExclusivesModal;
window.handleExclusivesBackdropClick = handleExclusivesBackdropClick;
window.switchExclusivesTab = switchExclusivesTab;
window.toggleExclusiveCatch = toggleExclusiveCatch;
window.updateExclusivesProgressUI = updateExclusivesProgressUI;
window.updateExclusivesModalUI = updateExclusivesModalUI;
window.updateExclusivesCardStatus = updateExclusivesCardStatus;

window.openTransfersModal = openTransfersModal;
window.closeTransfersModal = closeTransfersModal;
window.handleTransfersBackdropClick = handleTransfersBackdropClick;
window.toggleTransferCatch = toggleTransferCatch;
window.updateTransfersCardStatus = updateTransfersCardStatus;
window.toggleTransfersInfoAccordion = toggleTransfersInfoAccordion;

window.openUnownModal = openUnownModal;
window.closeUnownModal = closeUnownModal;
window.openClassicUnownModal = openClassicUnownModal;
window.openUnownLetterCard = openUnownLetterCard;
window.switchToUnownModal = switchToUnownModal;
window.filterUnownChamber = filterUnownChamber;
window.updateUnownModalUI = updateUnownModalUI;
window.toggleUnownFormCatch = toggleUnownFormCatch;

window.openPokemonModal = openPokemonModal;
window.openPokemonModalDirect = openPokemonModalDirect;
window.closePokemonModal = closePokemonModal;
window.handleModalBackdropClick = handleModalBackdropClick;
window.updateModalCatchStatus = updateModalCatchStatus;
window.modalToggleCatch = modalToggleCatch;
window.navigatePokemonModal = navigatePokemonModal;
window.updateRotateButtonUI = updateRotateButtonUI;
window.updateModalSpriteDisplay = updateModalSpriteDisplay;
window.toggleModalSpriteOrientation = toggleModalSpriteOrientation;
window.applyCardForm = applyCardForm;
window.cycleCardPokemonForm = cycleCardPokemonForm;
window.applyModalForm = applyModalForm;
window.cycleModalPokemonForm = cycleModalPokemonForm;

window.setModalUrlHash = setModalUrlHash;
window.clearModalUrlHash = clearModalUrlHash;
window.syncModalFromUrlHash = syncModalFromUrlHash;
window.closeAllModals = closeAllModals;
window.getCsrfToken = getCsrfToken;

// Marcar el framework interactivo modular como 100% cargado y listo
window.__pokedexReady = true;

// Procesar inmediatamente la cola de acciones prioritarias solicitadas durante la carga inicial
if (window.__pokedexActionQueue && window.__pokedexActionQueue.length > 0) {
    const queue = window.__pokedexActionQueue.slice();
    window.__pokedexActionQueue = [];
    queue.forEach(item => {
        if (typeof window[item.fnName] === 'function') {
            try {
                window[item.fnName].apply(null, item.args);
            } catch (err) {
                console.error('Error al ejecutar acción diferida prioritaria:', item.fnName, err);
            }
        }
    });
}

// Atajos de teclado (Escape para cerrar modales, flechas ←/→ para navegar Pokémon)
document.addEventListener('keydown', (e) => {
    const comicModal = document.getElementById('comic-modal');
    const isComicOpen = comicModal && !comicModal.classList.contains('opacity-0');

    if (isComicOpen) {
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            navigatePokemonModal(-1);
            return;
        }
        if (e.key === 'ArrowRight') {
            e.preventDefault();
            navigatePokemonModal(1);
            return;
        }
    }

    if (e.key === 'Escape') {
        const unownModal = document.getElementById('unown-modal');
        if (unownModal && !unownModal.classList.contains('opacity-0')) {
            closeUnownModal();
            return;
        }
        const stoneModal = document.getElementById('stone-location-modal');
        if (stoneModal && !stoneModal.classList.contains('opacity-0')) {
            closeStoneModal();
            return;
        }
        if (isComicOpen) {
            closePokemonModal();
            return;
        }
        const transModal = document.getElementById('transfers-modal');
        if (transModal && !transModal.classList.contains('opacity-0')) {
            closeTransfersModal();
            return;
        }
        closeExclusivesModal();
    }
});

// Interceptor de máxima prioridad en fase de captura (capture: true) para respuesta inmediata al hacer clic
document.addEventListener('click', (e) => {
    // 1. Clic en botón Exclusivos
    if (e.target.closest('#btn-exclusives')) {
        openExclusivesModal();
        e.stopPropagation();
        return;
    }
    // 2. Clic en botón Transferir
    if (e.target.closest('#btn-transfers')) {
        openTransfersModal();
        e.stopPropagation();
        return;
    }
    // 3. Clic en botón Filtros
    if (e.target.closest('#btn-filter-toggle')) {
        toggleFilterPanel();
        e.stopPropagation();
        return;
    }
    // 4. Clic en tarjeta de Pokémon (abre el modal cómic de inmediato sin esperar a otros eventos)
    const card = e.target.closest('.pokemon-card');
    if (card && !e.target.closest('button') && !e.target.closest('a') && !e.target.closest('input')) {
        const entryId = parseInt(card.dataset.entryId, 10);
        if (entryId) {
            openPokemonModal(entryId);
            e.stopPropagation();
            return;
        }
    }
}, { capture: true, passive: false });

// Navegación con historial del navegador (Atrás / Adelante con deep links y cambio de región)
window.addEventListener('popstate', () => {
    syncModalFromUrlHash();
    const url = new URL(window.location.href);
    const gen = url.searchParams.get('gen');
    if (gen && typeof window.switchNationalRegion === 'function') {
        window.switchNationalRegion(gen, null, false);
    }
});

// Sincronización inicial si la URL ya contiene un hash al cargar
if (window.location.hash) {
    syncModalFromUrlHash();
}

// Configuración inicial sincronizada sin salto de frame (soporta ejecución asíncrona)
function onDOMReady(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

onDOMReady(() => {
    try {
        const savedStyle = localStorage.getItem('pokedex_sprite_style');
        if (savedStyle && savedStyle !== 'retro' && document.getElementById('btn-style-retro')) {
            setSpriteStyle(savedStyle);
        }
    } catch (e) {}

    try {
        const gameGen = parseInt(document.getElementById('game-generation')?.value || config.gameGeneration || 1, 10);
        if (gameGen >= 2) {
            const savedShinydex = localStorage.getItem('pokedex_shinydex_' + currentGameSlug);
            // Si la cookie no estaba sincronizada pero en localStorage sí
            if (savedShinydex === '1' && !state.isShinydexMode) {
                state.isShinydexMode = true;
                applyShinydexMode(true);
                document.cookie = 'pokedex_shinydex_' + currentGameSlug + '=1; path=/; max-age=31536000; SameSite=Lax';
            } else if (savedShinydex === '0' && state.isShinydexMode) {
                state.isShinydexMode = false;
                applyShinydexMode(false);
                document.cookie = 'pokedex_shinydex_' + currentGameSlug + '=0; path=/; max-age=31536000; SameSite=Lax';
            } else if (savedShinydex === null && state.isShinydexMode) {
                localStorage.setItem('pokedex_shinydex_' + currentGameSlug, '1');
            }
        }
    } catch (e) {}

    try {
        updateFilterUI();
        filterCards();
    } catch (e) {}

    try {
        initNationalGenerationBar();
    } catch (e) {}

    // Re-evaluar deep link por si la tarjeta se encontraba más abajo en el render inicial
    if (window.location.hash) {
        syncModalFromUrlHash();
    }
});
