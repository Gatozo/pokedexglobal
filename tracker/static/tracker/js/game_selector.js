/**
 * Pokédex Global - Módulo Interactivo del Selector de Juegos (game_selector.js)
 * Provee filtrado instantáneo por generación y buscador en vivo de Pokémon.
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

    let currentGenFilter = 'all';

    function normalizeText(text) {
        return (text || '')
            .toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .trim();
    }

    // --- Filtro por Generación ---
    window.filterByGeneration = function (gen) {
        currentGenFilter = gen;

        // Actualizar estilos de los botones de filtro
        document.querySelectorAll('.gen-filter-btn').forEach(btn => {
            if (btn.dataset.gen === gen) {
                btn.className = 'gen-filter-btn px-3 py-1.5 rounded-xl border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-amber-400 text-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all hover:bg-amber-300 cursor-pointer active:translate-y-0.5';
            } else {
                btn.className = 'gen-filter-btn px-3 py-1.5 rounded-xl border-2 border-slate-950 text-xs font-black uppercase tracking-wider bg-slate-800 text-slate-300 shadow-[2px_2px_0px_0px_#0f172a] transition-all hover:bg-slate-700 hover:text-white cursor-pointer active:translate-y-0.5';
            }
        });

        // Aplicar visibilidad sobre las tarjetas
        applyCombinedFilters();
    };

    // --- Buscador de Pokémon ---
    function handlePokemonSearch() {
        const query = normalizeText(searchInput.value);

        if (query.length > 0) {
            searchClear.classList.remove('hidden');
        } else {
            searchClear.classList.add('hidden');
        }

        applyCombinedFilters();
    }

    function applyCombinedFilters() {
        const query = normalizeText(searchInput ? searchInput.value : '');
        let matchedPokemon = null;

        if (query) {
            // Buscar coincidencia exacta o inicial por número o nombre
            const cleanQueryNum = query.replace('#', '');
            const isNumeric = /^\d+$/.test(cleanQueryNum);

            if (isNumeric) {
                const targetNum = parseInt(cleanQueryNum, 10);
                matchedPokemon = pokemonSearchData.find(p => p.id === targetNum);
            } else {
                // Búsqueda por nombre (coincidencia exacta o contiene)
                matchedPokemon = pokemonSearchData.find(p => normalizeText(p.name) === query)
                    || pokemonSearchData.find(p => normalizeText(p.name).startsWith(query))
                    || pokemonSearchData.find(p => normalizeText(p.name).includes(query));
            }
        }

        let matchingGamesCount = 0;

        gameCards.forEach(card => {
            const cardGen = card.dataset.generation;
            const cardSlug = card.dataset.slug;
            const isAvailable = card.dataset.available === 'true';

            // 1. Verificar filtro de generación
            const matchesGen = (currentGenFilter === 'all') || (cardGen === currentGenFilter);

            if (!matchesGen) {
                card.classList.add('hidden');
                return;
            } else {
                card.classList.remove('hidden');
            }

            // 2. Verificar coincidencia del buscador
            const matchBadge = card.querySelector('.search-match-badge');
            const badgeSpan = matchBadge ? matchBadge.querySelector('span') : null;

            if (query && matchedPokemon) {
                const gameInfo = matchedPokemon.games[cardSlug];

                if (gameInfo && isAvailable) {
                    matchingGamesCount++;
                    card.classList.remove('opacity-30', 'grayscale');
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
                // Sin búsqueda o sin coincidencia
                card.classList.remove('opacity-30', 'ring-3', 'ring-amber-400');
                if (card.dataset.available !== 'true') {
                    card.classList.add('grayscale', 'opacity-60');
                }
                if (matchBadge) matchBadge.classList.add('hidden');
            }
        });

        // Actualizar mensaje de feedback
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

    // Atajos de teclado: '/' para enfocar buscador, 'Escape' para limpiar
    document.addEventListener('keydown', function (e) {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        } else if (e.key === 'Escape' && document.activeElement === searchInput) {
            searchInput.value = '';
            searchClear.classList.add('hidden');
            searchInput.blur();
            applyCombinedFilters();
        }
    });

})();
