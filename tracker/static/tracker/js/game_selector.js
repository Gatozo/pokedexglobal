/**
 * Pokédex Global - Módulo Interactivo del Selector de Juegos (game_selector.js)
 * Provee filtrado cruzado instantáneo por Generación y Consola, panel desplegable cómic y buscador en vivo.
 */

(function () {
    let pokemonSearchData = [];
    const searchDataEl = document.getElementById('pokemon-search-data');
    if (searchDataEl) {
        try {
            pokemonSearchData = JSON.parse(searchDataEl.textContent || '[]');
        } catch (e) {
            console.error('Error al parsear datos de búsqueda de Pokémon:', e);
        }
    }

    const searchInput = document.getElementById('pokemon-search-input');
    const searchClear = document.getElementById('pokemon-search-clear');
    const searchFeedback = document.getElementById('search-feedback');
    const gameCards = document.querySelectorAll('.game-card');

    const hubFilterPanel = document.getElementById('hub-filter-panel');
    const hubFilterBtn = document.getElementById('btn-hub-filter-toggle');
    const activeFiltersBadge = document.getElementById('active-filters-badge');
    const hubFilterMatchesCount = document.getElementById('hub-filter-matches-count');
    const clearHubFiltersBtn = document.getElementById('btn-clear-hub-filters');

    let currentGenFilter = 'all';
    let currentConsoleFilter = 'all';

    function normalizeText(text) {
        return (text || '')
            .toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .trim();
    }

    // --- Panel de Filtros Cómic ---
    window.toggleHubFilterPanel = function () {
        if (!hubFilterPanel) return;
        const isCurrentlyHidden = hubFilterPanel.classList.contains('hidden');
        if (isCurrentlyHidden) {
            hubFilterPanel.classList.remove('hidden');
            if (hubFilterBtn) {
                hubFilterBtn.classList.add('ring-2', 'ring-amber-400');
            }
        } else {
            hubFilterPanel.classList.add('hidden');
            if (hubFilterBtn) {
                hubFilterBtn.classList.remove('ring-2', 'ring-amber-400');
            }
        }
    };

    // --- Filtro por Generación ---
    window.filterByGeneration = function (gen) {
        currentGenFilter = gen;

        document.querySelectorAll('.gen-filter-btn').forEach(btn => {
            if (btn.dataset.gen === String(gen)) {
                btn.className = 'gen-filter-btn px-2.5 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-amber-400 text-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] transition-all cursor-pointer active:translate-y-0.5';
            } else {
                btn.className = 'gen-filter-btn px-2.5 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-slate-900 text-slate-300 shadow-[1.5px_1.5px_0px_#0f172a] transition-all hover:bg-slate-700 hover:text-white cursor-pointer active:translate-y-0.5';
            }
        });

        applyCombinedFilters();
    };

    // --- Filtro por Consola / Plataforma ---
    window.filterByConsole = function (consoleName) {
        currentConsoleFilter = consoleName;

        document.querySelectorAll('.console-filter-btn').forEach(btn => {
            if (btn.dataset.console === String(consoleName)) {
                btn.className = 'console-filter-btn px-3 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-amber-400 text-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] transition-all cursor-pointer active:translate-y-0.5';
            } else {
                btn.className = 'console-filter-btn px-3 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-slate-900 text-slate-300 shadow-[1.5px_1.5px_0px_#0f172a] transition-all hover:bg-slate-700 hover:text-white cursor-pointer active:translate-y-0.5';
            }
        });

        applyCombinedFilters();
    };

    // --- Limpiar Todos los Filtros ---
    window.clearHubFilters = function () {
        currentGenFilter = 'all';
        currentConsoleFilter = 'all';

        // Restablecer estilos de botones de Generación
        document.querySelectorAll('.gen-filter-btn').forEach(btn => {
            if (btn.dataset.gen === 'all') {
                btn.className = 'gen-filter-btn px-2.5 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-amber-400 text-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] transition-all cursor-pointer active:translate-y-0.5';
            } else {
                btn.className = 'gen-filter-btn px-2.5 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-slate-900 text-slate-300 shadow-[1.5px_1.5px_0px_#0f172a] transition-all hover:bg-slate-700 hover:text-white cursor-pointer active:translate-y-0.5';
            }
        });

        // Restablecer estilos de botones de Consola
        document.querySelectorAll('.console-filter-btn').forEach(btn => {
            if (btn.dataset.console === 'all') {
                btn.className = 'console-filter-btn px-3 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-amber-400 text-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] transition-all cursor-pointer active:translate-y-0.5';
            } else {
                btn.className = 'console-filter-btn px-3 py-1 rounded-lg border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-slate-900 text-slate-300 shadow-[1.5px_1.5px_0px_#0f172a] transition-all hover:bg-slate-700 hover:text-white cursor-pointer active:translate-y-0.5';
            }
        });

        // Limpiar buscador si tenía texto
        if (searchInput && searchInput.value) {
            searchInput.value = '';
            if (searchClear) searchClear.classList.add('hidden');
        }

        applyCombinedFilters();
    };

    // --- Buscador de Pokémon ---
    function handlePokemonSearch() {
        const query = normalizeText(searchInput.value);

        if (query.length > 0) {
            if (searchClear) searchClear.classList.remove('hidden');
        } else {
            if (searchClear) searchClear.classList.add('hidden');
        }

        applyCombinedFilters();
    }

    // --- Aplicación Combinada de Filtros ---
    function applyCombinedFilters() {
        const query = normalizeText(searchInput ? searchInput.value : '');
        let matchedPokemon = null;

        if (query) {
            const cleanQueryNum = query.replace('#', '');
            const isNumeric = /^\d+$/.test(cleanQueryNum);

            if (isNumeric) {
                const targetNum = parseInt(cleanQueryNum, 10);
                matchedPokemon = pokemonSearchData.find(p => p.id === targetNum);
            } else {
                matchedPokemon = pokemonSearchData.find(p => normalizeText(p.name) === query)
                    || pokemonSearchData.find(p => normalizeText(p.name).startsWith(query))
                    || pokemonSearchData.find(p => normalizeText(p.name).includes(query));
            }
        }

        let totalVisibleCards = 0;
        let matchingGamesCount = 0;

        gameCards.forEach(card => {
            const cardGen = card.dataset.generation;
            const cardSlug = card.dataset.slug;
            const isAvailable = card.dataset.available === 'true';
            const cardPlatforms = (card.dataset.platforms || '').split(',').map(p => p.trim());

            // 1. Filtro por Generación
            const matchesGen = (currentGenFilter === 'all') || (cardGen === currentGenFilter);

            // 2. Filtro por Consola
            const matchesConsole = (currentConsoleFilter === 'all') || cardPlatforms.includes(currentConsoleFilter);

            // Coincidencia combinada de filtros de catálogo
            const matchesCatalogFilters = matchesGen && matchesConsole;

            if (!matchesCatalogFilters) {
                card.classList.add('hidden');
                return;
            } else {
                card.classList.remove('hidden');
                totalVisibleCards++;
            }

            // 3. Verificar coincidencia del buscador de Pokémon
            const matchBadge = card.querySelector('.search-match-badge');
            const badgeSpan = matchBadge ? matchBadge.querySelector('span') : null;

            if (query && matchedPokemon) {
                const gameInfo = matchedPokemon.games[cardSlug];

                if (gameInfo && isAvailable) {
                    matchingGamesCount++;
                    card.classList.remove('opacity-30');
                    card.classList.add('ring-3', 'ring-amber-400');

                    if (matchBadge && badgeSpan) {
                        matchBadge.classList.remove('hidden');
                        if (gameInfo.is_caught) {
                            badgeSpan.className = 'inline-flex items-center gap-1 text-[11px] font-black px-2 py-0.5 rounded border border-slate-950 bg-emerald-400 text-slate-950 shadow-xs';
                            badgeSpan.innerHTML = `✓ Capturado: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                        } else {
                            badgeSpan.className = 'inline-flex items-center gap-1 text-[11px] font-black px-2 py-0.5 rounded border border-slate-950 bg-amber-300 text-slate-950 shadow-xs';
                            badgeSpan.innerHTML = `★ Disponible: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                        }
                    }
                } else {
                    card.classList.add('opacity-30');
                    card.classList.remove('ring-3', 'ring-amber-400');
                    if (matchBadge) matchBadge.classList.add('hidden');
                }
            } else {
                // Sin búsqueda activa o sin coincidencia
                card.classList.remove('opacity-30', 'ring-3', 'ring-amber-400');
                if (matchBadge) matchBadge.classList.add('hidden');
            }
        });

        // 4. Actualizar badge del botón de filtros y estado del botón limpiar
        let activeFilterCount = 0;
        if (currentGenFilter !== 'all') activeFilterCount++;
        if (currentConsoleFilter !== 'all') activeFilterCount++;

        if (activeFiltersBadge) {
            if (activeFilterCount > 0) {
                activeFiltersBadge.textContent = activeFilterCount;
                activeFiltersBadge.classList.remove('hidden');
            } else {
                activeFiltersBadge.classList.add('hidden');
            }
        }

        if (hubFilterBtn) {
            if (activeFilterCount > 0) {
                hubFilterBtn.classList.add('bg-amber-400', 'text-slate-950');
                hubFilterBtn.classList.remove('bg-white', 'text-slate-900');
            } else {
                hubFilterBtn.classList.remove('bg-amber-400', 'text-slate-950');
                hubFilterBtn.classList.add('bg-white', 'text-slate-900');
            }
        }

        if (clearHubFiltersBtn) {
            clearHubFiltersBtn.disabled = (activeFilterCount === 0 && (!searchInput || !searchInput.value));
        }

        if (hubFilterMatchesCount) {
            hubFilterMatchesCount.textContent = `(${totalVisibleCards} juego${totalVisibleCards === 1 ? '' : 's'})`;
        }

        // 5. Actualizar visibilidad de secciones de generación completas
        document.querySelectorAll('.generation-section').forEach(section => {
            const sectionGen = section.dataset.generation;

            // Si el filtro de generación está activo y no coincide con esta sección
            if (currentGenFilter !== 'all' && sectionGen !== currentGenFilter) {
                section.classList.add('hidden');
                section.hidden = true;
                return;
            }

            // Comprobar si hay al menos una tarjeta visible en esta sección
            const visibleCardsInSection = section.querySelectorAll('.game-card:not(.hidden)');
            if (visibleCardsInSection.length === 0) {
                section.classList.add('hidden');
                section.hidden = true;
                return;
            }

            // Si hay búsqueda activa y coincide algún Pokémon, ocultar secciones sin coincidencias destacadas
            if (query && matchedPokemon) {
                const hasMatchingCards = section.querySelector('.game-card.ring-3') !== null;
                if (!hasMatchingCards) {
                    section.classList.add('hidden');
                    section.hidden = true;
                } else {
                    section.classList.remove('hidden');
                    section.hidden = false;
                }
            } else {
                section.classList.remove('hidden');
                section.hidden = false;
            }
        });

        // 6. Actualizar mensaje de feedback del buscador
        if (searchFeedback) {
            if (query) {
                searchFeedback.classList.remove('hidden');
                if (matchedPokemon) {
                    searchFeedback.textContent = `Mostrando disponibilidad para ${matchedPokemon.name} (#${matchedPokemon.id}) en ${matchingGamesCount} juego(s) instalado(s).`;
                } else {
                    searchFeedback.textContent = `No se encontraron juegos compatibles para "${searchInput.value}".`;
                }
            } else {
                searchFeedback.classList.add('hidden');
                searchFeedback.textContent = '';
            }
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', handlePokemonSearch);
    }

    if (searchClear) {
        searchClear.addEventListener('click', function () {
            searchInput.value = '';
            searchClear.classList.add('hidden');
            searchInput.focus();
            applyCombinedFilters();
        });
    }

    // Atajos de teclado: '/' para enfocar buscador, 'Escape' para limpiar/cerrar panel
    document.addEventListener('keydown', function (e) {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        } else if (e.key === 'Escape') {
            if (document.activeElement === searchInput) {
                searchInput.value = '';
                if (searchClear) searchClear.classList.add('hidden');
                searchInput.blur();
                applyCombinedFilters();
            } else if (hubFilterPanel && !hubFilterPanel.classList.contains('hidden')) {
                toggleHubFilterPanel();
            }
        }
    });

    // Ejecutar filtro inicial para configurar contadores
    applyCombinedFilters();
})();
