/**
 * Pokédex Global - Módulo de Navegación por Regiones en Pokédex Nacional (national_bar.js)
 * Carga parcial ultra-ligera por AJAX (SPA), caché en memoria y transiciones fluidas.
 */

import { state } from './state.js';
import { filterCards } from './filters.js';
import { setSpriteStyle } from './cards.js';

const _regionCache = new Map();
let _isTransitioning = false;

/**
 * Invalida la caché en memoria cuando se modifica el estado de captura de un Pokémon.
 */
export function invalidateNationalRegionCache() {
    _regionCache.clear();
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
 * Cambia suavemente la generación activa en la Pokédex Nacional sin recargar la página completa.
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

    if (targetBtn.dataset.active === 'true' && !_isTransitioning) {
        return;
    }

    if (_isTransitioning) return;
    _isTransitioning = true;

    // 1. Actualización visual instantánea de botones
    updateBarButtonsUI(slug);

    // 2. Transición suave de salida (Cross-fade & subtle scale)
    grid.style.transition = 'opacity 140ms ease-out, transform 140ms ease-out';
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
                }
            });

            if (!resp.ok) {
                throw new Error(`HTTP error! status: ${resp.status}`);
            }

            html = await resp.text();
            _regionCache.set(slug, html);
        }

        // Breve pausa para completar la animación CSS de desvanecimiento
        await new Promise(resolve => setTimeout(resolve, 140));

        // 3. Reemplazar únicamente los nodos de las tarjetas en el DOM (~100-150 tarjetas)
        grid.innerHTML = html;

        // 4. Actualizar URL e historial sin recargar
        if (pushState) {
            const pageUrl = new URL(window.location.href);
            pageUrl.searchParams.set('gen', slug);
            pageUrl.searchParams.delete('partial');
            history.pushState({ gen: slug }, '', pageUrl.toString());
        }

        // 5. Reaplicar estilo de sprites activo (Retro / Moderno)
        if (state.currentSpriteStyle && typeof setSpriteStyle === 'function') {
            setSpriteStyle(state.currentSpriteStyle);
        }

        // 6. Reaplicar filtros y búsqueda activos sobre las nuevas tarjetas cargadas
        if (typeof filterCards === 'function') {
            filterCards();
        }

        // 7. Si el usuario estaba muy abajo en el scroll, recolocar suavemente sobre la cuadrícula
        const barRect = bar.getBoundingClientRect();
        if (barRect.top < 0) {
            bar.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } catch (err) {
        console.error('Error al cambiar de generación/región:', err);
        // Fallback a navegación estándar en caso de fallo de red
        window.location.href = targetBtn.href;
    } finally {
        // 8. Transición suave de entrada
        requestAnimationFrame(() => {
            grid.style.opacity = '1';
            grid.style.transform = 'scale(1)';
            setTimeout(() => {
                _isTransitioning = false;
            }, 140);
        });
    }
}

/**
 * Inicialización al cargar el DOM.
 */
export function initNationalGenerationBar() {
    const bar = document.getElementById('national-generation-bar');
    const grid = document.getElementById('pokemon-grid');
    if (!bar || !grid) return;

    const activeBtn = bar.querySelector("[id^='btn-nat-gen-'][data-active='true']");
    if (activeBtn) {
        const slug = activeBtn.dataset.slug;
        if (slug && grid.innerHTML.trim().length > 0) {
            _regionCache.set(slug, grid.innerHTML);
        }
    }
}
