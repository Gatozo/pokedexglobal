/**
 * Pokédex Global - Modal de Ubicaciones de Piedras y Objetos Evolutivos (modal_stones.js)
 */

import { currentGameSlug, currentGameDisplayName, evolutionStonesCatalog } from './state.js';
import { setModalUrlHash, syncUrlToCurrentOpenModal, releaseScrollIfNoModalOpen } from './url_sync.js';

export function openStoneModal(stoneSlug, stoneName, updateHistory = true) {
    if (!stoneSlug) return;
    const stone = evolutionStonesCatalog[stoneSlug] || {};
    const name = stone.name_es || stoneName || stoneSlug.replace(/-/g, ' ').toUpperCase();
    const iconUrl = stone.icon_url || `/media/items/${stoneSlug}.png`;
    const desc = stone.description_es || 'Objeto evolutivo especial.';
    const isPurchasable = stone.is_purchasable;
    const price = stone.price;

    // 1. Textos y cabecera
    const stoneTitle = document.getElementById('stone-modal-name');
    if (stoneTitle) stoneTitle.textContent = name.toUpperCase();
    const headerIcon = document.getElementById('stone-modal-icon-header');
    if (headerIcon) headerIcon.src = iconUrl;

    const catBadge = document.getElementById('stone-modal-category-badge');
    if (catBadge) {
        let catLabel = 'Objeto Evolutivo';
        if (stone.category === 'incense' || stoneSlug.includes('incense')) {
            catLabel = 'Incienso Especial';
        } else if (stone.category === 'trade' || ['kings-rock', 'metal-coat', 'dragon-scale', 'up-grade', 'deep-sea-tooth', 'deep-sea-scale'].includes(stoneSlug)) {
            catLabel = 'Objeto de Intercambio';
        } else if (stoneSlug.endsWith('-stone')) {
            catLabel = 'Piedra Evolutiva';
        }
        catBadge.textContent = `${catLabel} • ${currentGameDisplayName.toUpperCase()}`;
    }

    const footerText = document.getElementById('stone-modal-footer-text');
    if (footerText) {
        let guideType = 'objetos especiales';
        if (stone.category === 'incense' || stoneSlug.includes('incense')) {
            guideType = 'inciensos y crianza especial';
        } else if (stoneSlug.endsWith('-stone')) {
            guideType = 'piedras evolutivas';
        } else if (stone.category === 'trade' || ['kings-rock', 'metal-coat', 'dragon-scale', 'up-grade', 'deep-sea-tooth', 'deep-sea-scale'].includes(stoneSlug)) {
            guideType = 'objetos de intercambio';
        }
        footerText.textContent = `Guía de ${guideType} • ${currentGameDisplayName}`;
    }

    // 2. Ficha del objeto
    const stoneImg = document.getElementById('stone-modal-img');
    const badgeName = document.getElementById('stone-modal-badge-name');
    const descEl = document.getElementById('stone-modal-description');
    if (stoneImg) stoneImg.src = iconUrl;
    if (badgeName) badgeName.textContent = name;
    if (descEl) descEl.textContent = `"${desc}"`;

    const priceBadge = document.getElementById('stone-modal-price-badge');
    if (priceBadge) {
        if (isPurchasable) {
            priceBadge.className = 'border border-emerald-950 bg-emerald-200 text-emerald-950 text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded shadow-sm';
            priceBadge.textContent = price ? `En tienda: ${price.toLocaleString('es-ES')} ₽` : 'Compra en tienda';
        } else {
            priceBadge.className = 'border border-amber-950 bg-amber-200 text-amber-950 text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded shadow-sm';
            priceBadge.textContent = 'Objeto Limitado';
        }
    }

    // 3. Localizaciones para la versión actual
    const locContainer = document.getElementById('stone-modal-locations-list');
    if (locContainer) {
        locContainer.innerHTML = '';
        const gamesMap = stone.games || {};
        const locations = gamesMap[currentGameSlug] || [];

        if (locations.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'p-3 text-xs text-slate-500 font-semibold italic bg-slate-50 rounded-lg border border-slate-200';
            emptyMsg.textContent = 'Sin ubicaciones específicas registradas para esta edición.';
            locContainer.appendChild(emptyMsg);
        } else {
            locations.forEach((loc, index) => {
                const locItem = document.createElement('div');
                locItem.className = 'bg-white border-2 border-slate-950 rounded-xl p-2.5 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex items-start gap-2.5';
                locItem.innerHTML = `
                    <span class="w-6 h-6 rounded-full bg-amber-300 border border-slate-950 font-black text-xs text-slate-950 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                        ${index + 1}
                    </span>
                    <div class="space-y-0.5 min-w-0 flex-1">
                        <h5 class="text-xs font-black text-slate-900 uppercase flex items-center gap-1.5">
                            <img src="/media/items/town-map.png" alt="" class="w-3.5 h-3.5 object-contain inline-block">
                            ${loc.area}
                        </h5>
                        <p class="text-[11px] text-slate-600 font-medium">
                            ${loc.detail}
                        </p>
                    </div>
                `;
                locContainer.appendChild(locItem);
            });
        }
    }

    // 4. Mostrar modal
    const modal = document.getElementById('stone-location-modal');
    const modalCard = document.getElementById('stone-modal-card');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
    }
    if (modalCard) {
        modalCard.classList.remove('scale-95');
        modalCard.classList.add('scale-100');
    }
    document.body.classList.add('overflow-hidden');
    if (updateHistory) {
        setModalUrlHash('objeto-' + stoneSlug);
    }
}

export function closeStoneModal(syncUrl = true) {
    const modal = document.getElementById('stone-location-modal');
    const modalCard = document.getElementById('stone-modal-card');
    if (modal) {
        modal.classList.remove('backdrop-blur-sm', 'opacity-100', 'pointer-events-auto');
        modal.classList.add('hidden', 'opacity-0', 'pointer-events-none');
        modal.style.display = 'none';
    }
    if (modalCard) {
        modalCard.classList.remove('scale-100');
        modalCard.classList.add('scale-95');
    }
    releaseScrollIfNoModalOpen();
    if (syncUrl) syncUrlToCurrentOpenModal();
}

export function handleStoneModalBackdropClick(e) {
    if (e.target.id === 'stone-location-modal') {
        closeStoneModal();
    }
}
