/**
 * Pokédex Global - Modal de Pokémon Exclusivos de Versión (modal_exclusives.js)
 */

import { state } from './state.js';
import { setModalUrlHash, syncUrlToCurrentOpenModal, releaseScrollIfNoModalOpen, lockModalScroll } from './url_sync.js';
import { toggleCatch } from './cards.js';

export function openExclusivesModal(updateHistory = true) {
    const modal = document.getElementById('exclusives-modal');
    const modalCard = document.getElementById('exclusives-modal-card');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
    }
    if (modalCard) {
        modalCard.classList.remove('scale-95');
        modalCard.classList.add('scale-100');
    }
    lockModalScroll();
    try {
        updateExclusivesModalUI();
    } catch (err) {
        console.error('Error updating exclusives modal UI:', err);
    }
    if (updateHistory) {
        setModalUrlHash('exclusivos');
    }
}

export function closeExclusivesModal(syncUrl = true) {
    const modal = document.getElementById('exclusives-modal');
    const modalCard = document.getElementById('exclusives-modal-card');
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

export function handleExclusivesBackdropClick(e) {
    if (e.target.id === 'exclusives-modal') {
        closeExclusivesModal();
    }
}

export function switchExclusivesTab(tab) {
    const panelCounterpart = document.getElementById('exclusives-panel-counterpart');
    const panelOwn = document.getElementById('exclusives-panel-own');
    const btnCounterpart = document.getElementById('tab-btn-counterpart');
    const btnOwn = document.getElementById('tab-btn-own');

    if (!panelCounterpart || !panelOwn) return;

    const modal = document.getElementById('exclusives-modal');
    const counterpartTheme = modal ? modal.dataset.counterpartTheme : 'red';
    const counterpartActiveBg = (counterpartTheme === 'gold_silver') ? 'bg-gradient-to-r from-amber-400 to-slate-200' : 'bg-amber-400';

    if (tab === 'counterpart') {
        panelCounterpart.classList.remove('hidden');
        panelOwn.classList.add('hidden');
        if (btnCounterpart) btnCounterpart.className = `flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all ${counterpartActiveBg} text-slate-950 flex items-center justify-center gap-2`;
        if (btnOwn) btnOwn.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-white hover:bg-slate-50 text-slate-700 flex items-center justify-center gap-2';
    } else {
        panelOwn.classList.remove('hidden');
        panelCounterpart.classList.add('hidden');
        if (btnOwn) btnOwn.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-amber-400 text-slate-950 flex items-center justify-center gap-2';
        if (btnCounterpart) btnCounterpart.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-white hover:bg-slate-50 text-slate-700 flex items-center justify-center gap-2';
    }
}

export async function toggleExclusiveCatch(entryId, nationalNumber) {
    await toggleCatch(entryId);
}

export function updateExclusivesProgressUI() {
    const counterpartCards = document.querySelectorAll("#exclusives-panel-counterpart [id^='excl-card-']");
    if (counterpartCards.length === 0) return;

    let caughtCount = 0;
    counterpartCards.forEach(c => {
        const isCaught = state.isShinydexMode ? (c.dataset.shinyCaught === 'true') : (c.dataset.caught === 'true');
        if (isCaught) caughtCount++;
    });
    const totalCount = counterpartCards.length;
    const percent = Math.round((caughtCount / totalCount) * 100);

    const badgeElem = document.getElementById('exclusives-counterpart-caught-badge');
    if (badgeElem) badgeElem.textContent = caughtCount;

    const modal = document.getElementById('exclusives-modal');
    const counterpartTheme = modal ? modal.dataset.counterpartTheme : 'red';
    const themeColorClass = (counterpartTheme === 'blue') ? 'text-blue-600' :
        ((counterpartTheme === 'amber') ? 'text-amber-600' :
        ((counterpartTheme === 'silver') ? 'text-slate-600' :
        ((counterpartTheme === 'gold') ? 'text-[#9e7514]' :
        ((counterpartTheme === 'gold_silver') ? 'text-amber-700' :
        ((counterpartTheme === 'crystal') ? 'text-sky-600' : 'text-red-600')))));
    const themeBarClass = (counterpartTheme === 'blue') ? 'bg-blue-600' :
        ((counterpartTheme === 'amber') ? 'bg-amber-500' :
        ((counterpartTheme === 'silver') ? 'bg-slate-500' :
        ((counterpartTheme === 'gold') ? 'bg-[#c59b27]' :
        ((counterpartTheme === 'gold_silver') ? 'bg-gradient-to-r from-[#c59b27] to-[#94a3b8]' :
        ((counterpartTheme === 'crystal') ? 'bg-sky-500' : 'bg-red-600')))));

    const caughtElem = document.getElementById('excl-progress-caught');
    if (caughtElem) {
        caughtElem.textContent = caughtCount;
        caughtElem.className = (state.isShinydexMode ? 'text-amber-600' : themeColorClass) + ' font-black';
    }

    const percentElem = document.getElementById('excl-progress-percent');
    if (percentElem) percentElem.textContent = percent;

    const barElem = document.getElementById('excl-progress-bar');
    if (barElem) {
        barElem.style.width = `${percent}%`;
        barElem.className = state.isShinydexMode 
            ? 'bg-gradient-to-r from-amber-400 to-yellow-300 shadow-[0_0_8px_rgba(251,191,36,0.6)] h-full rounded-full transition-all duration-300'
            : `${themeBarClass} h-full rounded-full transition-all duration-300`;
    }

    const dotElem = document.getElementById('excl-progress-dot');
    if (dotElem) {
        const themeDotClass = (counterpartTheme === 'gold_silver')
            ? 'bg-gradient-to-r from-[#d4af37] to-[#94a3b8]'
            : themeBarClass;
        dotElem.className = 'w-3.5 h-3.5 rounded-full border border-slate-950 shrink-0 ' + (state.isShinydexMode ? 'bg-amber-400' : themeDotClass);
    }

    const titleElem = document.getElementById('excl-progress-title');
    if (titleElem) {
        const cpName = modal ? modal.dataset.counterpartShortName : '';
        titleElem.textContent = state.isShinydexMode 
            ? `Exclusivos shiny de ${cpName} obtenidos:` 
            : `Exclusivos de ${cpName} obtenidos en tu partida:`;
    }
}

export function updateExclusivesModalUI() {
    const counterpartCards = document.querySelectorAll("#exclusives-panel-counterpart [id^='excl-card-']");
    if (counterpartCards.length === 0) return;

    counterpartCards.forEach(card => {
        const nationalNum = card.id.replace('excl-card-', '');
        const img = document.getElementById(`excl-img-${nationalNum}`);
        const badge = document.getElementById(`excl-status-badge-${nationalNum}`);
        const btn = document.getElementById(`excl-btn-${nationalNum}`);
        const btnText = document.getElementById(`excl-btn-text-${nationalNum}`);
        const isCaught = state.isShinydexMode 
            ? (card.dataset.shinyCaught === 'true')
            : (card.dataset.caught === 'true');

        if (img) {
            if (state.isShinydexMode) {
                if (state.currentSpriteStyle === 'retro') {
                    img.src = card.dataset.spriteRetroShiny || card.dataset.spriteModernShiny;
                    img.classList.add('pixel-art');
                } else {
                    img.src = card.dataset.spriteModernShiny || card.dataset.spriteRetroShiny;
                    img.classList.remove('pixel-art');
                }
            } else {
                if (state.currentSpriteStyle === 'retro') {
                    img.src = card.dataset.spriteRetro;
                    img.classList.add('pixel-art');
                } else {
                    img.src = card.dataset.spriteModern;
                    img.classList.remove('pixel-art');
                }
            }
        }

        if (badge) {
            if (isCaught) {
                badge.className = 'px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-tight border border-slate-950 shrink-0 text-center bg-emerald-400 text-slate-950';
                badge.textContent = '✓ Atrapado';
            } else {
                badge.className = 'px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-tight border border-slate-950 shrink-0 text-center bg-slate-200 text-slate-600';
                badge.textContent = 'Pendiente';
            }
        }

        if (btn) {
            if (isCaught) {
                btn.className = 'mt-2.5 w-full py-1.5 px-2 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center justify-center gap-1 bg-rose-500 hover:bg-rose-600 text-white';
                if (btnText) btnText.textContent = 'Liberar';
            } else {
                btn.className = 'mt-2.5 w-full py-1.5 px-2 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center justify-center gap-1 bg-emerald-500 hover:bg-emerald-600 text-white';
                if (btnText) btnText.textContent = 'Capturar';
            }
        }
    });

    updateExclusivesProgressUI();
}

export function updateExclusivesCardStatus(entryId, isCaught) {
    const card = document.querySelector(`[id^='excl-card-'][data-entry-id='${entryId}']`);
    if (card) {
        if (state.isShinydexMode) {
            card.dataset.shinyCaught = isCaught ? 'true' : 'false';
        } else {
            card.dataset.caught = isCaught ? 'true' : 'false';
        }
        const nationalNum = card.id.replace('excl-card-', '');
        const badge = document.getElementById(`excl-status-badge-${nationalNum}`);
        const btn = document.getElementById(`excl-btn-${nationalNum}`);
        const btnText = document.getElementById(`excl-btn-text-${nationalNum}`);

        if (badge) {
            if (isCaught) {
                badge.className = 'px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-tight border border-slate-950 shrink-0 text-center bg-emerald-400 text-slate-950';
                badge.textContent = '✓ Atrapado';
            } else {
                badge.className = 'px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-tight border border-slate-950 shrink-0 text-center bg-slate-200 text-slate-600';
                badge.textContent = 'Pendiente';
            }
        }

        if (btn) {
            if (isCaught) {
                btn.className = 'mt-2.5 w-full py-1.5 px-2 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center justify-center gap-1 bg-rose-500 hover:bg-rose-600 text-white';
                if (btnText) btnText.textContent = 'Liberar';
            } else {
                btn.className = 'mt-2.5 w-full py-1.5 px-2 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center justify-center gap-1 bg-emerald-500 hover:bg-emerald-600 text-white';
                if (btnText) btnText.textContent = 'Capturar';
            }
        }
    }

    updateExclusivesProgressUI();
}

export function toggleExclusivesAccordion(panelKey) {
    const btn = document.getElementById(`exclusives-${panelKey}-accordion-btn`);
    const content = document.getElementById(`exclusives-${panelKey}-accordion-content`);
    const icon = document.getElementById(`exclusives-${panelKey}-accordion-icon`);
    const label = document.getElementById(`exclusives-${panelKey}-accordion-label`);
    if (!btn || !content) return;

    const isExpanded = btn.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
        content.classList.add('hidden');
        btn.setAttribute('aria-expanded', 'false');
        if (icon) icon.classList.remove('rotate-180');
        if (label) label.textContent = 'Mostrar aviso';
    } else {
        content.classList.remove('hidden');
        btn.setAttribute('aria-expanded', 'true');
        if (icon) icon.classList.add('rotate-180');
        if (label) label.textContent = 'Ocultar aviso';
    }
}
