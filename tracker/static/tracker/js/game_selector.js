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
            }

            // 3. Verificar coincidencia del buscador de Pokémon
            const matchBadge = card.querySelector('.search-match-badge');
            const badgeSpan = matchBadge ? matchBadge.querySelector('span') : null;

            if (query && matchedPokemon) {
                const gameInfo = matchedPokemon.games[cardSlug];

                // Si hay búsqueda activa:
                // Solo se muestran los juegos ACTIVOS donde el Pokémon es obtenible de forma nativa
                if (gameInfo && isAvailable) {
                    matchingGamesCount++;
                    totalVisibleCards++;
                    card.classList.remove('hidden', 'opacity-30');
                    card.classList.add('ring-3', 'ring-amber-400');

                    if (matchBadge && badgeSpan) {
                        matchBadge.classList.remove('hidden');
                        const method = gameInfo.method_badge || 'Salvaje';

                        // Iconos oficiales de objetos (media/items/)
                        const methodIcons = {
                            'Poké Radar': '/media/items/poke-radar.png',
                            'Árbol de Miel': '/media/items/honey.png',
                            'Pesca Especial': '/media/items/super-rod.png',
                            'Fósil Restaurado': '/media/items/helix-fossil.png',
                            'Casino': '/media/items/coin-case.png',
                            'Concurso de Captura': '/media/items/sport-ball.png',
                            'Único': '/media/items/master-ball.png',
                            'Método Externo': '/media/items/cherish-ball.png',
                            'Evento': '/media/items/member-card.png',
                            'Crianza': '/media/items/lucky-egg.png',
                        };

                        if (gameInfo.is_caught) {
                            badgeSpan.className = 'inline-flex items-center gap-1.5 text-[11px] font-black px-2 py-0.5 rounded border border-slate-950 bg-emerald-400 text-slate-950 shadow-xs';
                            badgeSpan.innerHTML = `<img src="/media/items/poke-ball.png" alt="" class="w-3.5 h-3.5 object-contain inline-block shrink-0"> Capturado: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                        } else {
                            const iconUrl = methodIcons[method];
                            const iconHtml = iconUrl ? `<img src="${iconUrl}" alt="" class="w-3.5 h-3.5 object-contain inline-block shrink-0"> ` : '';

                            if (method === 'Único') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-violet-400 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Único: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Método Externo') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-indigo-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Método Externo: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Evento') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-fuchsia-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Evento: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Casino') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-amber-400 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Casino: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Concurso de Captura') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-lime-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Concurso: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Inicial') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-emerald-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Inicial: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Regalo') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-teal-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Regalo: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Crianza') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-pink-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Crianza: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Evolución') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-violet-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `Evolución: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method.includes('Inserción Dual')) {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-indigo-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Inserción Dual (GBA): ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Poké Radar') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-sky-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Poké Radar: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Árbol de Miel') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-amber-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Árbol de Miel: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Pesca Especial') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-cyan-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Pesca Especial: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Fósil Restaurado') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-amber-200 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}Fósil: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Manada Diaria') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-amber-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `Manada Diaria: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Intercambio NPC') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-purple-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `Intercambio NPC: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Evolución / Cría') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-violet-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `Evolución / Cría: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Regalo / Inicial') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-teal-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `Regalo / Inicial: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else if (method === 'Encuentro Especial') {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-orange-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `Encuentro Especial: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            } else {
                                badgeSpan.className = 'inline-flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded border border-slate-950 bg-amber-300 text-slate-950 shadow-xs';
                                badgeSpan.innerHTML = `${iconHtml}${method}: ${matchedPokemon.name} (#${matchedPokemon.id})`;
                            }
                        }
                    }
                } else {
                    // Ocultar cualquier juego que no esté disponible o donde el Pokémon no sea obtenible nativamente
                    card.classList.add('hidden');
                    card.classList.remove('ring-3', 'ring-amber-400');
                    if (matchBadge) matchBadge.classList.add('hidden');
                }
            } else {
                // Sin búsqueda activa: visible si coincide con el catálogo
                card.classList.remove('hidden', 'opacity-30', 'ring-3', 'ring-amber-400');
                totalVisibleCards++;
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
                    if (matchingGamesCount > 0) {
                        searchFeedback.textContent = `Disponible para capturar en ${matchingGamesCount} juego(s) instalado(s): ${matchedPokemon.name} (#${matchedPokemon.id}).`;
                    } else {
                        searchFeedback.textContent = `${matchedPokemon.name} (#${matchedPokemon.id}) no está disponible para captura directa en los juegos instalados actuales.`;
                    }
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
