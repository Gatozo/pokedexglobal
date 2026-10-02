/**
 * Pokédex Global - Modal de Pokémon Transferibles desde Gen 1 (modal_transfers.js)
 */

import { setModalUrlHash, syncUrlToCurrentOpenModal, releaseScrollIfNoModalOpen } from './url_sync.js';
import { toggleCatch } from './cards.js';

export function openTransfersModal(updateHistory = true) {
    const modal = document.getElementById('transfers-modal');
    const modalCard = document.getElementById('transfers-modal-card');
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
        setModalUrlHash('transferir');
    }
}

export function closeTransfersModal(syncUrl = true) {
    const modal = document.getElementById('transfers-modal');
    const modalCard = document.getElementById('transfers-modal-card');
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

export function handleTransfersBackdropClick(e) {
    if (e.target.id === 'transfers-modal') {
        closeTransfersModal();
    }
}

export async function toggleTransferCatch(entryId, nationalNumber) {
    await toggleCatch(entryId);
}

export function updateTransfersCardStatus(entryId, isCaught) {
    const card = document.querySelector(`[id^='transfer-card-'][data-entry-id='${entryId}']`);
    if (card) {
        card.dataset.caught = isCaught ? 'true' : 'false';
        const nationalNum = card.id.replace('transfer-card-', '');
        const badge = document.getElementById(`transfer-status-badge-${nationalNum}`);
        const btn = document.getElementById(`transfer-btn-${nationalNum}`);
        const btnText = document.getElementById(`transfer-btn-text-${nationalNum}`);

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

    // Recalcular métricas de transferencias
    const transferCards = document.querySelectorAll("[id^='transfer-card-']");
    if (transferCards.length > 0) {
        let caughtCount = 0;
        transferCards.forEach(c => {
            if (c.dataset.caught === 'true') caughtCount++;
        });
        const totalCount = transferCards.length;
        const percent = Math.round((caughtCount / totalCount) * 100);

        const badgeElem = document.getElementById('transfers-caught-badge');
        if (badgeElem) badgeElem.textContent = caughtCount;

        const caughtElem = document.getElementById('transfers-progress-caught');
        if (caughtElem) caughtElem.textContent = caughtCount;

        const percentElem = document.getElementById('transfers-progress-percent');
        if (percentElem) percentElem.textContent = percent;

        const barElem = document.getElementById('transfers-progress-bar');
        if (barElem) barElem.style.width = `${percent}%`;
    }
}
