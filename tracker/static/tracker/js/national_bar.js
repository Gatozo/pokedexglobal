/**
 * Pokédex Global - Módulo de Navegación por Regiones en Pokédex Nacional (national_bar.js)
 * Carga parcial ultra-ligera por AJAX (SPA), caché en memoria, aislamiento estricto de regiones
 * y transiciones fluidas de alta respuesta.
 */

import { state } from './state.js';
import { filterCards } from './filters.js';
import { setSpriteStyle } from './cards.js';

const _regionCache = new Map();
let _activeAbortController = null;
let _currentRequestId = 0;
let _currentActiveSlug = null;
let _gridObserver = null;
let _isGlobalFilterActive = false;
let _savedActiveSlug = null;
let _isManualRegionLock = false;
let _allRegionsPrefetchPromise = null;

export function isGlobalFilterActive() {
    return _isGlobalFilterActive;
}

export function isManualRegionLock() {
    return _isManualRegionLock;
}

export function setManualRegionLock(val) {
    _isManualRegionLock = Boolean(val);
}

/**
 * Invalida la caché en memoria cuando se modifica el estado de captura de un Pokémon.
 */
export function invalidateNationalRegionCache() {
    _regionCache.clear();
    const bar = document.getElementById('national-generation-bar');
    if (bar) {
        prefetchAllRegionsGrid();
    }
}

/**
 * Obtiene el rango numérico (start_id, end_id) definido en el botón de una región.
 * @param {string} slug Slug de la región (kanto, johto, hoenn, etc.)
 * @returns {{start: number, end: number}|null}
 */
export function getRegionBounds(slug) {
    const btn = document.getElementById(`btn-nat-gen-${slug}`);
    if (!btn) return null;
    const start = parseInt(btn.dataset.start, 10);
    const end = parseInt(btn.dataset.end, 10);
    if (isNaN(start) || isNaN(end)) return null;
    return { start, end };
}

/**
 * Aísla y purga estrictamente cualquier tarjeta en la grilla que no pertenezca al rango de la región activa.
 * Previene que el parser del navegador o respuestas cruzadas filtren Pokémon de otra región.
 * @param {string} slug Slug de la región que debe quedar aislada
 */
export function isolateGridCards(slug) {
    if (_isGlobalFilterActive) return;

    const grid = document.getElementById('pokemon-grid');
    if (!grid) return;

    const bounds = getRegionBounds(slug);
    if (!bounds) return;

    const cards = grid.querySelectorAll('.pokemon-card');
    cards.forEach(card => {
        const natNum = parseInt(card.dataset.nationalNumber || card.dataset.number, 10);
        if (!isNaN(natNum) && (natNum < bounds.start || natNum > bounds.end)) {
            card.remove();
        }
    });
}

/**
 * Configura un MutationObserver permanente sobre la grilla para interceptar y purgar al vuelo
 * cualquier nodo o tarjeta ajena al rango de la región activa mientras la página se estabiliza.
 */
export function setupGridObserver() {
    const grid = document.getElementById('pokemon-grid');
    if (!grid) return;

    if (_gridObserver) {
        _gridObserver.disconnect();
    }

    _gridObserver = new MutationObserver(mutations => {
        if (_isGlobalFilterActive) return;
        if (!_currentActiveSlug) return;
        const bounds = getRegionBounds(_currentActiveSlug);
        if (!bounds) return;

        let needsPurge = false;
        for (const m of mutations) {
            for (const node of m.addedNodes) {
                if (node.nodeType === 1) { // Node.ELEMENT_NODE
                    if (node.classList && node.classList.contains('pokemon-card')) {
                        const num = parseInt(node.dataset.nationalNumber || node.dataset.number, 10);
                        if (!isNaN(num) && (num < bounds.start || num > bounds.end)) {
                            node.remove();
                        }
                    } else if (node.querySelector && node.querySelector('.pokemon-card')) {
                        needsPurge = true;
                    }
                }
            }
        }
        if (needsPurge) {
            isolateGridCards(_currentActiveSlug);
        }
    });

    _gridObserver.observe(grid, { childList: true, subtree: false });
}

/**
 * Desactiva visualmente la selección de todas las regiones en la barra de navegación.
 */
export function clearActiveBarButtonsUI() {
    const bar = document.getElementById('national-generation-bar');
    if (!bar) return;

    const activeClasses = (bar.dataset.activeClasses || '').split(' ').filter(Boolean);
    const inactiveClasses = (bar.dataset.inactiveClasses || '').split(' ').filter(Boolean);
    const badgeActive = (bar.dataset.badgeActive || '').split(' ').filter(Boolean);
    const badgeInactive = (bar.dataset.badgeInactive || '').split(' ').filter(Boolean);

    const buttons = bar.querySelectorAll("[id^='btn-nat-gen-']");
    buttons.forEach(btn => {
        btn.dataset.active = 'false';
        if (activeClasses.length) btn.classList.remove(...activeClasses);
        if (inactiveClasses.length) btn.classList.add(...inactiveClasses);
        const slug = btn.dataset.slug;
        const badge = document.getElementById(`nat-reg-badge-${slug}`);
        if (badge) {
            if (badgeActive.length) badge.classList.remove(...badgeActive);
            if (badgeInactive.length) badge.classList.add(...badgeInactive);
        }
    });
}

/**
 * Actualiza visualmente los botones de la barra de regiones según la región activa.
 */
export function updateBarButtonsUI(activeSlug) {
    const bar = document.getElementById('national-generation-bar');
    if (!bar) return;

    const activeClasses = (bar.dataset.activeClasses || '').split(' ').filter(Boolean);
    const inactiveClasses = (bar.dataset.inactiveClasses || '').split(' ').filter(Boolean);
    const badgeActive = (bar.dataset.badgeActive || '').split(' ').filter(Boolean);
    const badgeInactive = (bar.dataset.badgeInactive || '').split(' ').filter(Boolean);

    const buttons = bar.querySelectorAll("[id^='btn-nat-gen-']");
    buttons.forEach(btn => {
        const slug = btn.dataset.slug;
        const badge = document.getElementById(`nat-reg-badge-${slug}`);
        const isActive = slug === activeSlug;

        btn.dataset.active = isActive ? 'true' : 'false';

        if (isActive) {
            if (inactiveClasses.length) btn.classList.remove(...inactiveClasses);
            if (activeClasses.length) btn.classList.add(...activeClasses);
            if (badge) {
                if (badgeInactive.length) badge.classList.remove(...badgeInactive);
                if (badgeActive.length) badge.classList.add(...badgeActive);
            }
        } else {
            if (activeClasses.length) btn.classList.remove(...activeClasses);
            if (inactiveClasses.length) btn.classList.add(...inactiveClasses);
            if (badge) {
                if (badgeActive.length) badge.classList.remove(...badgeActive);
                if (badgeInactive.length) badge.classList.add(...badgeInactive);
            }
        }
    });
}

/**
 * Actualiza los badges de la barra nacional para mostrar el número de coincidencias por región.
 */
export function updateNationalBadgesForFilter() {
    const bar = document.getElementById('national-generation-bar');
    if (!bar) return;

    const buttons = bar.querySelectorAll("[id^='btn-nat-gen-']");
    const visibleCards = document.querySelectorAll('.pokemon-card:not([style*="display: none"])');

    const visibleNums = [];
    visibleCards.forEach(card => {
        const num = parseInt(card.dataset.nationalNumber || card.dataset.number, 10);
        if (!isNaN(num)) visibleNums.push(num);
    });

    buttons.forEach(btn => {
        const slug = btn.dataset.slug;
        const start = parseInt(btn.dataset.start, 10);
        const end = parseInt(btn.dataset.end, 10);
        const badge = document.getElementById(`nat-reg-badge-${slug}`);
        if (!badge) return;

        let matches = 0;
        for (let i = 0; i < visibleNums.length; i++) {
            if (visibleNums[i] >= start && visibleNums[i] <= end) {
                matches++;
            }
        }

        if (matches > 0) {
            badge.innerHTML = `<span class="font-mono font-black">${matches}</span>`;
            badge.title = `${matches} coincidencias en esta región`;
            badge.classList.remove('opacity-40');
        } else {
            badge.innerHTML = `<span class="font-mono opacity-40">0</span>`;
            badge.title = `0 coincidencias en esta región`;
            badge.classList.add('opacity-40');
        }
    });
}

/**
 * Restaura los badges de la barra nacional a su valor por defecto (capturados / total).
 */
export function restoreDefaultNationalBadges() {
    const bar = document.getElementById('national-generation-bar');
    if (!bar) return;

    const buttons = bar.querySelectorAll("[id^='btn-nat-gen-']");
    buttons.forEach(btn => {
        const slug = btn.dataset.slug;
        const total = btn.dataset.total || '';
        const caught = btn.dataset.caught || '0';
        const badge = document.getElementById(`nat-reg-badge-${slug}`);
        if (!badge) return;

        badge.classList.remove('opacity-40');
        badge.removeAttribute('title');
        badge.innerHTML = `<span id="nat-reg-caught-${slug}">${caught}</span>/${total}`;
    });
}

/**
 * Prefetch en background del catálogo nacional completo (todas las regiones).
 */
export function prefetchAllRegionsGrid() {
    if (_regionCache.has('all') || _allRegionsPrefetchPromise) return;
    const url = new URL(window.location.href);
    url.searchParams.set('gen', 'all');
    url.searchParams.set('partial', 'grid');

    _allRegionsPrefetchPromise = fetch(url.toString(), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(resp => {
        if (!resp.ok) throw new Error('Prefetch failed');
        return resp.text();
    })
    .then(html => {
        _regionCache.set('all', html);
        return html;
    })
    .catch(() => null)
    .finally(() => {
        _allRegionsPrefetchPromise = null;
    });
}

/**
 * Entra en modo de filtrado global (desactiva selección fija de región y carga todas las especies).
 */
export async function enterGlobalFilterMode() {
    const bar = document.getElementById('national-generation-bar');
    const grid = document.getElementById('pokemon-grid');
    if (!bar || !grid) return;

    if (!_isGlobalFilterActive) {
        _savedActiveSlug = _currentActiveSlug || 'kanto';
        _isGlobalFilterActive = true;
        _currentActiveSlug = 'all';
        clearActiveBarButtonsUI();
    }

    let allHtml = _regionCache.get('all');
    if (!allHtml && _allRegionsPrefetchPromise) {
        try {
            allHtml = await _allRegionsPrefetchPromise;
        } catch (e) {}
    }

    if (!allHtml) {
        const url = new URL(window.location.href);
        url.searchParams.set('gen', 'all');
        url.searchParams.set('partial', 'grid');
        try {
            const resp = await fetch(url.toString(), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (resp.ok) {
                allHtml = await resp.text();
                _regionCache.set('all', allHtml);
            }
        } catch (e) {
            console.error('Error cargando cuadrícula completa para filtrado:', e);
        }
    }

    if (allHtml && grid.children.length < 200) {
        grid.innerHTML = allHtml;
        if (state.currentSpriteStyle && typeof setSpriteStyle === 'function') {
            setSpriteStyle(state.currentSpriteStyle);
        }
    }
}

/**
 * Sale del modo de filtrado global y restaura la región que estaba activa previamente.
 */
export function exitGlobalFilterMode() {
    if (!_isGlobalFilterActive) return;
    _isGlobalFilterActive = false;
    _isManualRegionLock = false;

    const restoreSlug = _savedActiveSlug || 'kanto';
    _currentActiveSlug = restoreSlug;
    _savedActiveSlug = null;

    updateBarButtonsUI(restoreSlug);
    restoreDefaultNationalBadges();

    const grid = document.getElementById('pokemon-grid');
    if (!grid) return;

    const cachedHtml = _regionCache.get(restoreSlug);
    if (cachedHtml) {
        grid.innerHTML = cachedHtml;
        isolateGridCards(restoreSlug);
        if (state.currentSpriteStyle && typeof setSpriteStyle === 'function') {
            setSpriteStyle(state.currentSpriteStyle);
        }
    } else {
        isolateGridCards(restoreSlug);
    }
}

/**
 * Cambia suavemente la generación activa en la Pokédex Nacional sin recargar la página completa.
 * Aísla la región destino abortando cualquier carga en curso y purga nodos cruzados.
 * @param {string} slug Slug de la región (kanto, johto, hoenn, etc.)
 * @param {Event|null} event Evento del clic (opcional)
 * @param {boolean} pushState Si se debe agregar una entrada al historial de navegación
 */
export async function switchNationalRegion(slug, event = null, pushState = true) {
    if (event) {
        event.preventDefault();
    }

    const grid = document.getElementById('pokemon-grid');
    const bar = document.getElementById('national-generation-bar');
    if (!grid || !bar) return;

    const targetBtn = document.getElementById(`btn-nat-gen-${slug}`);
    if (!targetBtn) return;

    // Si ya estamos en esta región y no hay petición en vuelo
    if (targetBtn.dataset.active === 'true' && _currentActiveSlug === slug && !_activeAbortController) {
        if (_isManualRegionLock) {
            _isManualRegionLock = false;
            filterCards();
        }
        return;
    }

    if (_isGlobalFilterActive) {
        _isGlobalFilterActive = false;
        _isManualRegionLock = true;
        _savedActiveSlug = slug;
    } else {
        _isManualRegionLock = true;
    }

    // 1. Cancelar cualquier petición AJAX previa en curso
    if (_activeAbortController) {
        try {
            _activeAbortController.abort();
        } catch (e) {}
    }
    _activeAbortController = new AbortController();
    const requestId = ++_currentRequestId;

    _currentActiveSlug = slug;

    // 3. Actualización visual instantánea de botones
    updateBarButtonsUI(slug);

    // 4. Aislar de inmediato cualquier tarjeta previa antes o durante la transición
    isolateGridCards(slug);

    // 5. Transición suave de salida
    grid.style.transition = 'opacity 120ms ease-out, transform 120ms ease-out';
    grid.style.opacity = '0';
    grid.style.transform = 'scale(0.99)';

    try {
        let html = _regionCache.get(slug);

        if (!html) {
            const url = new URL(targetBtn.href, window.location.href);
            url.searchParams.set('gen', slug);
            url.searchParams.set('partial', 'grid');

            const resp = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                signal: _activeAbortController.signal
            });

            if (!resp.ok) {
                throw new Error(`HTTP error! status: ${resp.status}`);
            }

            html = await resp.text();
        }

        // Si otra petición de región fue disparada por el usuario mientras esperábamos, descartar esta
        if (requestId !== _currentRequestId) {
            return;
        }

        // Breve pausa para completar la animación CSS de desvanecimiento
        await new Promise(resolve => setTimeout(resolve, 120));

        if (requestId !== _currentRequestId) {
            return;
        }

        // 6. Reemplazar los nodos de las tarjetas en el DOM
        grid.innerHTML = html;

        // 7. Sanitización y aislamiento estricto de la grilla por rango
        isolateGridCards(slug);

        // 8. Guardar en caché únicamente el contenido validado y libre de fugas
        _regionCache.set(slug, grid.innerHTML);

        // 9. Actualizar URL e historial sin recargar
        if (pushState) {
            const pageUrl = new URL(window.location.href);
            pageUrl.searchParams.set('gen', slug);
            pageUrl.searchParams.delete('partial');
            history.pushState({ gen: slug }, '', pageUrl.toString());
        }

        // 10. Reaplicar estilo de sprites activo (Retro / Moderno)
        if (state.currentSpriteStyle && typeof setSpriteStyle === 'function') {
            setSpriteStyle(state.currentSpriteStyle);
        }

        // 11. Reaplicar filtros y búsqueda activos sobre las nuevas tarjetas cargadas
        if (typeof filterCards === 'function') {
            filterCards();
        }

        // 12. Si el usuario estaba muy abajo en el scroll, recolocar suavemente sobre la barra
        const barRect = bar.getBoundingClientRect();
        if (barRect.top < 0) {
            bar.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            // Petición cancelada intencionalmente por un nuevo cambio de región
            return;
        }
        console.error('Error al cambiar de generación/región:', err);
        // Fallback a navegación estándar en caso de fallo crítico de red
        window.location.href = targetBtn.href;
    } finally {
        if (requestId === _currentRequestId) {
            _activeAbortController = null;
            requestAnimationFrame(() => {
                grid.style.opacity = '1';
                grid.style.transform = 'scale(1)';
            });
        }
    }
}

/**
 * Inicialización al cargar el DOM.
 */
export function initNationalGenerationBar() {
    const bar = document.getElementById('national-generation-bar');
    const grid = document.getElementById('pokemon-grid');
    if (!bar || !grid) return;

    setupGridObserver();

    const activeBtn = bar.querySelector("[id^='btn-nat-gen-'][data-active='true']");
    if (activeBtn) {
        const slug = activeBtn.dataset.slug;
        if (slug) {
            _currentActiveSlug = slug;
            // Aislar inmediatamente para asegurar que la grilla inicial esté libre de mezclas
            isolateGridCards(slug);

            if (grid.innerHTML.trim().length > 0) {
                _regionCache.set(slug, grid.innerHTML);
            }
        }
    }

    prefetchAllRegionsGrid();
}

// Asegurar que si el usuario cambia de pestaña durante una animación,
// la grilla recupere su visibilidad completa al regresar a la pestaña activa.
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        const grid = document.getElementById('pokemon-grid');
        if (grid) {
            grid.style.opacity = '1';
            grid.style.transform = 'scale(1)';
        }
    }
});
