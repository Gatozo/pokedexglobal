/**
 * Pokédex Global - Modal de Ruinas Alfa / Bloc Unown (modal_unown.js)
 */

import { state, UNOWN_CHAMBER_HINTS } from './state.js';
import { getCsrfToken } from './api.js';
import { setModalUrlHash, syncUrlToCurrentOpenModal, releaseScrollIfNoModalOpen } from './url_sync.js';
import { updateCardUI, updateProgressBarUI } from './cards.js';
import { openPokemonModalDirect, closePokemonModal } from './modal_comic.js';

export function openUnownModal(updateHistory = true) {
    const modal = document.getElementById('unown-modal');
    const card = document.getElementById('unown-modal-card');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
    }
    if (card) {
        card.classList.remove('scale-95');
        card.classList.add('scale-100');
    }
    document.body.classList.add('overflow-hidden');
    try {
        updateUnownModalUI();
    } catch (err) {
        console.error('Error updating unown modal UI:', err);
    }
    if (updateHistory) {
        setModalUrlHash('unown');
    }
}

export function closeUnownModal(syncUrl = true) {
    const modal = document.getElementById('unown-modal');
    const card = document.getElementById('unown-modal-card');
    if (modal) {
        modal.classList.remove('backdrop-blur-sm', 'opacity-100', 'pointer-events-auto');
        modal.classList.add('hidden', 'opacity-0', 'pointer-events-none');
        modal.style.display = 'none';
    }
    if (card) {
        card.classList.remove('scale-100');
        card.classList.add('scale-95');
    }
    releaseScrollIfNoModalOpen();
    if (syncUrl) syncUrlToCurrentOpenModal();
}

export function openClassicUnownModal() {
    closeUnownModal();
    const unownCard = document.querySelector(".pokemon-card[data-name='unown']");
    const modalEl = document.getElementById('unown-modal');
    const entryId = unownCard 
        ? parseInt(unownCard.dataset.entryId, 10) 
        : parseInt(modalEl?.dataset?.unownEntryId || 0, 10);
    if (entryId) {
        openPokemonModalDirect(entryId);
    }
}

export function openUnownLetterCard(letter) {
    closeUnownModal(false);
    const unownCard = document.querySelector(".pokemon-card[data-name='unown']");
    const modalEl = document.getElementById('unown-modal');
    const entryId = unownCard 
        ? parseInt(unownCard.dataset.entryId, 10) 
        : parseInt(modalEl?.dataset?.unownEntryId || 0, 10);
    if (!entryId) return;
    openPokemonModalDirect(entryId, { selectedLetter: letter });
}

export function switchToUnownModal() {
    closePokemonModal();
    openUnownModal();
}

export function filterUnownChamber(chamberKey) {
    document.querySelectorAll('.unown-tab').forEach(tab => {
        tab.className = 'unown-tab px-3 py-1 rounded-xl text-xs font-black uppercase border-2 border-transparent text-slate-600 hover:text-slate-950 hover:bg-slate-200/60 cursor-pointer shrink-0';
    });
    const activeTab = document.getElementById(`unown-tab-${chamberKey}`);
    if (activeTab) {
        activeTab.className = 'unown-tab px-3 py-1 rounded-xl text-xs font-black uppercase border-2 border-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] bg-amber-400 text-slate-950 cursor-pointer shrink-0';
    }

    const hintTitle = document.getElementById('unown-chamber-hint-title');
    const hintText = document.getElementById('unown-chamber-hint-text');

    if (chamberKey === 'all') {
        const isTanoby = !!document.getElementById('unown-tab-anemuna');
        if (hintTitle) hintTitle.textContent = isTanoby ? 'Ruinas Sete (Isla Sétima)' : 'Ruinas Alfa';
        if (hintText) hintText.textContent = isTanoby
            ? 'Selecciona una cámara para filtrar sus formas y consultar los porcentajes de aparición y acceso.'
            : 'Selecciona una cámara para filtrar las letras y consultar el acertijo de su sala secreta.';
    } else {
        const hint = UNOWN_CHAMBER_HINTS[chamberKey];
        if (hint && hintTitle && hintText) {
            hintTitle.textContent = hint.title;
            hintText.textContent = hint.text;
        }
    }

    document.querySelectorAll('.unown-card').forEach(card => {
        if (chamberKey === 'all' || card.dataset.chamber === chamberKey) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

export function updateUnownModalUI() {
    const title = document.getElementById('unown-modal-progress-title');
    const statCaught = document.getElementById('unown-stat-caught');
    const statPercent = document.getElementById('unown-stat-percent');
    const progressBar = document.getElementById('unown-progress-bar');

    const curStats = state.isShinydexMode ? state.unownStats.shiny : state.unownStats.normal;
    if (title) title.textContent = state.isShinydexMode ? 'Progreso Unowndex Shiny:' : 'Progreso Unowndex:';
    if (statCaught) statCaught.textContent = curStats.caught;
    if (statPercent) statPercent.textContent = curStats.percent;
    if (progressBar) {
        progressBar.style.width = `${curStats.percent}%`;
        progressBar.className = state.isShinydexMode
            ? 'bg-gradient-to-r from-amber-400 to-yellow-300 shadow-[0_0_8px_rgba(251,191,36,0.6)] h-full rounded-full transition-all duration-300'
            : 'bg-[#c59b27] h-full rounded-full transition-all duration-300';
    }

    const noteEl = document.getElementById('unown-historical-note');
    if (noteEl) {
        if (state.isShinydexMode) {
            noteEl.classList.remove('hidden');
        } else {
            noteEl.classList.add('hidden');
        }
    }

    document.querySelectorAll('.unown-card').forEach(card => {
        const letter = card.dataset.letter;
        const img = document.getElementById(`unown-img-${letter}`);
        const isCaught = state.isShinydexMode 
            ? (card.dataset.shinyCaught === 'true')
            : (card.dataset.caught === 'true');

        if (img) {
            img.src = state.isShinydexMode ? img.dataset.spriteShiny : img.dataset.spriteNormal;
        }

        const badge = document.getElementById(`unown-status-badge-${letter}`);
        const check = badge ? badge.querySelector('.unown-status-check') : null;
        const text = badge ? badge.querySelector('.unown-status-text') : null;
        const btn = document.getElementById(`unown-btn-${letter}`);
        const btnText = document.getElementById(`unown-btn-text-${letter}`);

        if (isCaught) {
            card.className = 'unown-card relative rounded-2xl p-3 flex flex-col justify-between border-2 border-emerald-950 bg-emerald-50/70 shadow-[3px_3px_0px_#0f172a] transition-all duration-200 select-none';
            if (badge) badge.className = 'card-status-indicator h-5 flex items-center justify-center gap-1 px-1 rounded-md text-[9px] font-black uppercase tracking-wider border border-slate-950 shrink-0 mb-2 bg-emerald-500 text-white';
            if (check) check.textContent = '✓';
            if (text) text.textContent = 'Atrapado';
            if (btn) btn.className = 'w-full h-8 px-2 rounded-xl text-[10px] font-black uppercase tracking-wider flex items-center justify-center gap-1 border-2 border-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer shrink-0 bg-rose-500 hover:bg-rose-600 text-white';
            if (btnText) btnText.textContent = 'Liberar';
        } else {
            card.className = 'unown-card relative rounded-2xl p-3 flex flex-col justify-between border-2 border-slate-950 bg-white shadow-[3px_3px_0px_#0f172a] transition-all duration-200 select-none';
            if (badge) badge.className = 'card-status-indicator h-5 flex items-center justify-center gap-1 px-1 rounded-md text-[9px] font-black uppercase tracking-wider border border-slate-950 shrink-0 mb-2 bg-slate-100 text-slate-500';
            if (check) check.textContent = '';
            if (text) text.textContent = 'Falta';
            if (btn) btn.className = 'w-full h-8 px-2 rounded-xl text-[10px] font-black uppercase tracking-wider flex items-center justify-center gap-1 border-2 border-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer shrink-0 bg-emerald-500 hover:bg-emerald-400 text-white';
            if (btnText) btnText.textContent = 'Capturar';
        }
    });
}

export async function toggleUnownFormCatch(letter) {
    const unownCardMain = document.querySelector(".pokemon-card[data-name='unown']");
    if (!unownCardMain) return;
    const entryId = unownCardMain.dataset.entryId;

    try {
        const resp = await fetch('/api/unown-catch/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                entry_id: parseInt(entryId, 10),
                letter: letter,
                is_shiny: state.isShinydexMode
            })
        });

        if (!resp.ok) return;
        const res = await resp.json();

        // 1. Actualizar datos de la tarjeta de la letra en la Unowndex
        const card = document.getElementById(`unown-card-${letter}`);
        if (card) {
            if (state.isShinydexMode) {
                card.dataset.shinyCaught = res.is_caught ? 'true' : 'false';
            } else {
                card.dataset.caught = res.is_caught ? 'true' : 'false';
            }
        }

        // 2. Actualizar estadísticas de Unown
        state.unownStats.normal.caught = res.unown_normal_count;
        state.unownStats.normal.percent = res.unown_normal_percent;
        state.unownStats.shiny.caught = res.unown_shiny_count;
        state.unownStats.shiny.percent = res.unown_shiny_percent;
        if (res.unown_total_forms) {
            const statTotal = document.getElementById('unown-stat-total');
            if (statTotal) statTotal.textContent = res.unown_total_forms;
        }
        updateUnownModalUI();

        // 3. Sincronizar tarjeta principal de Unown en la Pokédex general
        unownCardMain.dataset.caught = res.entry_is_caught ? 'true' : 'false';
        unownCardMain.dataset.shinyCaught = res.entry_is_shiny ? 'true' : 'false';
        updateCardUI(unownCardMain, state.isShinydexMode ? res.entry_is_shiny : res.entry_is_caught);

        // 4. Sincronizar progreso general de la Pokédex
        state.normalStats.caught = res.global_normal_caught;
        state.normalStats.percent = res.global_normal_percent;
        state.shinyStats.caught = res.global_shiny_caught;
        state.shinyStats.percent = res.global_shiny_percent;
        updateProgressBarUI();

    } catch (e) {
        console.error("Error al conmutar captura de Unown:", e);
    }
}

export function toggleUnownHistoricalAccordion() {
    const btn = document.getElementById('unown-historical-accordion-btn');
    const content = document.getElementById('unown-historical-accordion-content');
    const icon = document.getElementById('unown-historical-accordion-icon');
    const label = document.getElementById('unown-historical-accordion-label');
    if (!btn || !content) return;

    const isExpanded = btn.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
        content.classList.add('hidden');
        btn.setAttribute('aria-expanded', 'false');
        if (icon) icon.classList.remove('rotate-180');
        if (label) label.textContent = 'Mostrar nota';
    } else {
        content.classList.remove('hidden');
        btn.setAttribute('aria-expanded', 'true');
        if (icon) icon.classList.add('rotate-180');
        if (label) label.textContent = 'Ocultar nota';
    }
}
