/**
 * Pokédex Global - Sincronización de URL y Enlaces Profundos (url_sync.js)
 * Manejo de Deep Links (#bulbasaur, #exclusivos, #objeto-moon-stone) y gestión de historial.
 */

import { state } from './state.js';
import { openExclusivesModal, closeExclusivesModal } from './modal_exclusives.js';
import { openTransfersModal, closeTransfersModal } from './modal_transfers.js';
import { openUnownModal, closeUnownModal } from './modal_unown.js';
import { openStoneModal, closeStoneModal } from './modal_stones.js';
import { openPokemonModal, closePokemonModal } from './modal_comic.js';

let _isUpdatingHashFromPopState = false;

export function setModalUrlHash(hashString, replace = false) {
    if (_isUpdatingHashFromPopState) return;
    const cleanHash = (hashString || '').replace(/^#/, '');
    const currentHash = decodeURIComponent(window.location.hash.replace(/^#/, '')).trim().toLowerCase();
    if (currentHash === cleanHash.toLowerCase()) return;

    const newUrl = cleanHash 
        ? `${window.location.pathname}${window.location.search}#${cleanHash}`
        : `${window.location.pathname}${window.location.search}`;

    try {
        if (replace) {
            history.replaceState({ modalHash: cleanHash }, document.title, newUrl);
        } else {
            history.pushState({ modalHash: cleanHash }, document.title, newUrl);
        }
    } catch (e) {
        window.location.hash = cleanHash;
    }
}

export function clearModalUrlHash() {
    if (_isUpdatingHashFromPopState) return;
    if (!window.location.hash) return;
    const cleanUrl = `${window.location.pathname}${window.location.search}`;
    try {
        history.pushState({ modalHash: '' }, document.title, cleanUrl);
    } catch (e) {
        window.location.hash = '';
    }
}

export function releaseScrollIfNoModalOpen() {
    const comicModal = document.getElementById('comic-modal');
    const exclModal = document.getElementById('exclusives-modal');
    const stoneModal = document.getElementById('stone-location-modal');
    const transModal = document.getElementById('transfers-modal');
    const unownModal = document.getElementById('unown-modal');
    const isComicOpen = comicModal && !comicModal.classList.contains('opacity-0');
    const isExclOpen = exclModal && !exclModal.classList.contains('opacity-0');
    const isStoneOpen = stoneModal && !stoneModal.classList.contains('opacity-0');
    const isTransOpen = transModal && !transModal.classList.contains('opacity-0');
    const isUnownOpen = unownModal && !unownModal.classList.contains('opacity-0');
    if (!isComicOpen && !isExclOpen && !isStoneOpen && !isTransOpen && !isUnownOpen) {
        document.body.classList.remove('overflow-hidden');
    }
}

export function syncUrlToCurrentOpenModal() {
    if (_isUpdatingHashFromPopState) return;
    const comicModal = document.getElementById('comic-modal');
    const exclModal = document.getElementById('exclusives-modal');
    const stoneModal = document.getElementById('stone-location-modal');
    const transModal = document.getElementById('transfers-modal');
    const unownModal = document.getElementById('unown-modal');

    if (stoneModal && !stoneModal.classList.contains('opacity-0')) {
        return;
    }
    if (comicModal && !comicModal.classList.contains('opacity-0') && state.activeModalEntryId) {
        const card = document.getElementById(`card-${state.activeModalEntryId}`);
        if (card) {
            const slug = card.dataset.name || String(card.dataset.number);
            setModalUrlHash(slug, true);
            return;
        }
    }
    if (exclModal && !exclModal.classList.contains('opacity-0')) {
        setModalUrlHash('exclusivos', true);
        return;
    }
    if (transModal && !transModal.classList.contains('opacity-0')) {
        setModalUrlHash('transferir', true);
        return;
    }
    if (unownModal && !unownModal.classList.contains('opacity-0')) {
        setModalUrlHash('unown', true);
        return;
    }

    clearModalUrlHash();
}

export function syncModalFromUrlHash(retries = 3) {
    const rawHash = decodeURIComponent(window.location.hash.replace(/^#/, '')).trim().toLowerCase();
    if (!rawHash) {
        closeAllModals(false);
        return;
    }

    _isUpdatingHashFromPopState = true;
    try {
        // 1. Modales especiales
        if (rawHash === 'exclusivos' || rawHash === 'exclusives') {
            openExclusivesModal(false);
            return;
        }
        if (rawHash === 'transferir' || rawHash === 'transferencias' || rawHash === 'transfers') {
            openTransfersModal(false);
            return;
        }
        if (rawHash === 'unown' || rawHash === 'unowndex' || rawHash === 'ruinas-alfa') {
            openUnownModal(false);
            return;
        }
        if (rawHash.startsWith('objeto-') || rawHash.startsWith('item-') || rawHash.startsWith('piedra-') || rawHash.startsWith('stone-')) {
            const stoneSlug = rawHash.replace(/^(objeto|item|piedra|stone)-/, '');
            openStoneModal(stoneSlug, '', false);
            return;
        }

        // 2. Ficha de Pokémon por nombre o número (compatible con ambos formatos)
        const cleanKey = rawHash.replace(/^(pokemon|p)-/, '');
        let card = null;

        // Búsqueda por número (#001, #1, #252, etc.)
        if (/^\d+$/.test(cleanKey)) {
            const numInt = parseInt(cleanKey, 10);
            card = document.querySelector(`.pokemon-card[data-number="${numInt}"]`) ||
                   document.querySelector(`.pokemon-card[data-number="${cleanKey}"]`) ||
                   document.querySelector(`.pokemon-card[data-number="${String(numInt).padStart(3, '0')}"]`);
        }

        // Búsqueda por nombre / slug (#treecko, #bulbasaur, etc.)
        if (!card) {
            card = document.querySelector(`.pokemon-card[data-name="${cleanKey}"]`) ||
                   document.querySelector(`.pokemon-card[data-display="${cleanKey}"]`);
        }

        if (card) {
            const entryId = parseInt(card.dataset.entryId, 10);
            if (entryId) {
                openPokemonModal(entryId, false);
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else if (retries > 0) {
            setTimeout(() => syncModalFromUrlHash(retries - 1), 120);
        }
    } finally {
        _isUpdatingHashFromPopState = false;
    }
}

export function closeAllModals(syncUrl = true) {
    closePokemonModal(syncUrl);
    closeExclusivesModal(syncUrl);
    closeTransfersModal(syncUrl);
    closeStoneModal(syncUrl);
    closeUnownModal(syncUrl);
}
