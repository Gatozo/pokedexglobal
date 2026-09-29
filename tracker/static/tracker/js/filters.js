/**
 * Pokédex Global - Módulo de Filtros y Búsqueda (filters.js)
 * Manejo de filtros por texto, ruta/localización, tipos elementales, etiquetas y estado de captura.
 */

import { state, THEME_ACTIVE_BTN } from './state.js';

export function setStatusFilter(status) {
    state.currentStatusFilter = status;

    const activeBaseClass = 'h-full text-xs font-black uppercase flex items-center justify-center transition-colors select-none ' + THEME_ACTIVE_BTN;
    const inactiveBaseClass = 'h-full text-xs font-black uppercase flex items-center justify-center text-slate-700 hover:text-slate-950 hover:bg-slate-100 transition-colors select-none';

    const btnAll = document.getElementById('filter-all');
    const btnCaught = document.getElementById('filter-caught');
    const btnUncaught = document.getElementById('filter-uncaught');

    if (btnAll) {
        btnAll.className = (status === 'all' ? activeBaseClass : inactiveBaseClass) + ' w-[64px] border-r-2 border-slate-950';
    }
    if (btnCaught) {
        btnCaught.className = (status === 'caught' ? activeBaseClass : inactiveBaseClass) + ' w-[98px] border-r-2 border-slate-950';
    }
    if (btnUncaught) {
        btnUncaught.className = (status === 'uncaught' ? activeBaseClass : inactiveBaseClass) + ' w-[94px]';
    }

    filterCards();
}

export function normalizeSearchText(str) {
    return (str || '')
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

export function matchesLocationQuery(locationsStr, queryStr) {
    if (!locationsStr || !queryStr) return false;
    const normLoc = normalizeSearchText(locationsStr);
    const normQ = normalizeSearchText(queryStr).trim();
    if (!normQ) return true;
    const escapedQ = normQ.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(^|[^a-z0-9])${escapedQ}([^a-z0-9]|$)`, 'i');
    return regex.test(normLoc);
}

export function toggleFilterPanel() {
    const panel = document.getElementById('filter-panel');
    const btnToggle = document.getElementById('btn-filter-toggle');
    if (!panel) return;

    state.isFilterPanelOpen = !state.isFilterPanelOpen;
    if (state.isFilterPanelOpen) {
        panel.classList.remove('hidden');
        if (btnToggle) {
            btnToggle.classList.add('bg-amber-100', 'border-amber-950');
        }
    } else {
        panel.classList.add('hidden');
        if (btnToggle && (state.selectedFilterTags.size === 0 && state.selectedFilterTypes.size === 0)) {
            btnToggle.classList.remove('bg-amber-100', 'border-amber-950');
        }
    }
}

export function updateFilterUI() {
    const totalActive = state.selectedFilterTags.size + state.selectedFilterTypes.size;
    const badge = document.getElementById('active-filters-badge');
    const btnToggle = document.getElementById('btn-filter-toggle');
    const btnClear = document.getElementById('btn-clear-filters');

    if (badge) {
        if (totalActive > 0) {
            badge.textContent = totalActive;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    if (btnToggle) {
        if (totalActive > 0 || state.isFilterPanelOpen) {
            btnToggle.classList.add('bg-amber-100');
        } else {
            btnToggle.classList.remove('bg-amber-100');
        }
    }

    if (btnClear) {
        btnClear.disabled = (totalActive === 0);
    }

    // Actualizar visualmente botones de tipos
    const typePills = document.querySelectorAll('.filter-type-pill');
    typePills.forEach(pill => {
        const type = pill.dataset.type;
        if (state.selectedFilterTypes.size > 0) {
            if (state.selectedFilterTypes.has(type)) {
                pill.classList.remove('opacity-40');
                pill.classList.add('ring-2', 'ring-slate-950', 'brightness-110');
            } else {
                pill.classList.add('opacity-40');
                pill.classList.remove('ring-2', 'ring-slate-950', 'brightness-110');
            }
        } else {
            pill.classList.remove('opacity-40', 'ring-2', 'ring-slate-950', 'brightness-110');
        }
    });
}

export function toggleFilterTag(tag, el) {
    if (state.selectedFilterTags.has(tag)) {
        state.selectedFilterTags.delete(tag);
        if (el) {
            el.classList.remove('bg-amber-300', 'ring-2', 'ring-slate-950', 'text-slate-950');
            el.classList.add('bg-white', 'text-slate-800');
        }
    } else {
        state.selectedFilterTags.add(tag);
        if (el) {
            el.classList.remove('bg-white', 'text-slate-800');
            el.classList.add('bg-amber-300', 'ring-2', 'ring-slate-950', 'text-slate-950');
        }
    }
    updateFilterUI();
    filterCards();
}

export function toggleFilterType(type, el) {
    if (state.selectedFilterTypes.has(type)) {
        state.selectedFilterTypes.delete(type);
    } else {
        state.selectedFilterTypes.add(type);
    }
    updateFilterUI();
    filterCards();
}

export function clearAllFilters() {
    state.selectedFilterTags.clear();
    state.selectedFilterTypes.clear();

    document.querySelectorAll('.filter-tag-pill').forEach(el => {
        el.classList.remove('bg-amber-300', 'ring-2', 'ring-slate-950', 'text-slate-950');
        el.classList.add('bg-white', 'text-slate-800');
    });

    document.querySelectorAll('.filter-type-pill').forEach(el => {
        el.classList.remove('opacity-40', 'ring-2', 'ring-slate-950', 'brightness-110');
    });

    updateFilterUI();
    filterCards();
}

export function filterCards() {
    const searchInput = document.getElementById('search-input');
    const rawQuery = searchInput ? searchInput.value.trim() : '';
    const normQ = normalizeSearchText(rawQuery);

    // Optimización de prioridad inmediata: si no hay filtros activos ni tarjetas ocultas previamente, no bloquear el hilo principal
    const hasActiveFilters = Boolean(normQ) || (state.currentStatusFilter !== 'all') || (state.selectedFilterTags.size > 0) || (state.selectedFilterTypes.size > 0);
    if (!hasActiveFilters && document.querySelectorAll('.pokemon-card[style*="display: none"]').length === 0) {
        const emptyState = document.getElementById('empty-state');
        if (emptyState) emptyState.classList.add('hidden');
        return;
    }

    const cards = document.querySelectorAll('.pokemon-card');
    let visibleCount = 0;

    cards.forEach(card => {
        const name = card.dataset.name || '';
        const display = card.dataset.display || '';
        const number = card.dataset.number || '';
        const type1 = (card.dataset.type1 || '').toLowerCase();
        const type2 = (card.dataset.type2 || '').toLowerCase();
        const type1Es = card.dataset.type1Es || '';
        const type2Es = card.dataset.type2Es || '';
        const locations = card.dataset.locations || '';
        const tags = (card.dataset.tags || '').split(' ').filter(Boolean);
        const isCaught = state.isShinydexMode 
            ? (card.dataset.shinyCaught === 'true')
            : (card.dataset.caught === 'true');

        // 1. Filtro de texto / ubicación (nombre, número, tipo en es/en, o ruta/lugar)
        let matchesText = true;
        if (normQ) {
            const normDisplay = normalizeSearchText(display);
            const normType1Es = normalizeSearchText(type1Es);
            const normType2Es = normalizeSearchText(type2Es);

            const matchesName = name.toLowerCase().includes(normQ) || normDisplay.includes(normQ);
            const normNum = number.padStart(3, '0');
            const matchesNumber = number.includes(normQ) || normNum.includes(normQ) ||
                                  ('#' + number).includes(normQ) || ('#' + normNum).includes(normQ);
            const matchesType = type1.includes(normQ) || type2.includes(normQ) ||
                                normType1Es.includes(normQ) || normType2Es.includes(normQ);
            const matchesLoc = matchesLocationQuery(locations, normQ);

            matchesText = matchesName || matchesNumber || matchesType || matchesLoc;
        }

        // 2. Filtro de estado (Todos, Capturados, Pendientes)
        let matchesStatus = true;
        if (state.currentStatusFilter === 'caught') {
            matchesStatus = isCaught;
        } else if (state.currentStatusFilter === 'uncaught') {
            matchesStatus = !isCaught;
        }

        // 3. Filtro de etiquetas avanzadas (Iniciales, Legendarios, Regalos, Surf, Cañas, etc.)
        let matchesTags = true;
        if (state.selectedFilterTags.size > 0) {
            matchesTags = tags.some(tag => state.selectedFilterTags.has(tag));
        }

        // 4. Filtro de tipos elementales
        let matchesTypeFilter = true;
        if (state.selectedFilterTypes.size > 0) {
            matchesTypeFilter = state.selectedFilterTypes.has(type1) || (type2 && state.selectedFilterTypes.has(type2));
        }

        const isVisible = matchesText && matchesStatus && matchesTags && matchesTypeFilter;
        if (isVisible) {
            card.style.display = 'flex';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Actualizar indicador de coincidencias en el panel de filtros
    const matchesCountEl = document.getElementById('filter-matches-count');
    if (matchesCountEl) {
        matchesCountEl.textContent = `(${visibleCount} de ${cards.length} Pokémon)`;
    }
}
