/**
 * Pokédex Global - Controlador de Interacciones y Modales
 * Extraído y modularizado para máximo rendimiento y mantenibilidad.
 */

// Leer configuración inyectada por el servidor
const pokedexConfig = window.POKEDEX_CONFIG || {};
const currentGameSlug = pokedexConfig.gameSlug || '';
const currentGameDisplayName = pokedexConfig.gameDisplayName || '';
const evolutionStonesCatalog = pokedexConfig.evolutionStones || {};

// Constantes de estilo temático según el juego activo
const THEME_ACTIVE_BTN = currentGameSlug === 'yellow'
    ? 'bg-amber-400 text-slate-950 font-black'
    : (currentGameSlug === 'blue' 
        ? 'bg-blue-600 text-white font-black' 
        : (currentGameSlug === 'gold' 
            ? 'bg-[#c59b27] text-slate-950 font-black' 
            : 'bg-red-600 text-white font-black'));
const THEME_STATUS_CAUGHT_CLASS = 'status-caught-active';
const THEME_UNCAUGHT_BTN = 'card-action-btn mt-3 w-full h-9 px-3 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer shrink-0 bg-emerald-500 hover:bg-emerald-400 text-white';
const THEME_CAUGHT_BTN = 'card-action-btn mt-3 w-full h-9 px-3 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer shrink-0 bg-rose-500 hover:bg-rose-600 text-white';

let currentStatusFilter = 'all';
let currentSpriteStyle = 'retro';
let activeModalEntryId = null;
let isShinydexMode = false;

let normalStats = {
    caught: parseInt(document.getElementById('initial-normal-caught')?.value || 0, 10),
    percent: parseFloat(document.getElementById('initial-normal-percent')?.value || 0.0)
};
let shinyStats = {
    caught: parseInt(document.getElementById('initial-shiny-caught')?.value || 0, 10),
    percent: parseFloat(document.getElementById('initial-shiny-percent')?.value || 0.0)
};

function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}

function toggleShinydexMode() {
    isShinydexMode = !isShinydexMode;
    try {
        localStorage.setItem('pokedex_shinydex_' + currentGameSlug, isShinydexMode ? '1' : '0');
        document.cookie = 'pokedex_shinydex_' + currentGameSlug + '=' + (isShinydexMode ? '1' : '0') + '; path=/; max-age=31536000; SameSite=Lax';
    } catch (e) {}
    applyShinydexMode(isShinydexMode);
}

function updateProgressBarUI() {
    const statCaught = document.getElementById('stat-caught');
    const statPercent = document.getElementById('stat-percent');
    const progressBar = document.getElementById('progress-bar');

    const currentStats = isShinydexMode ? shinyStats : normalStats;
    if (statCaught) statCaught.textContent = currentStats.caught;
    if (statPercent) statPercent.textContent = currentStats.percent;
    if (progressBar) {
        progressBar.style.width = `${currentStats.percent}%`;
        if (isShinydexMode) {
            progressBar.className = 'bg-gradient-to-r from-amber-400 to-yellow-300 h-full rounded-full transition-all duration-300 shadow-[0_0_8px_rgba(251,191,36,0.6)]';
        } else {
            progressBar.className = (
                currentGameSlug === 'yellow' ? 'bg-amber-400' :
                (currentGameSlug === 'blue' ? 'bg-blue-600' :
                (currentGameSlug === 'gold' ? 'bg-[#c59b27]' : 'bg-red-600'))
            ) + ' h-full rounded-full transition-all duration-300';
        }
    }
}

function updateCardUI(card, isCaught) {
    const entryId = card.dataset.entryId;
    const btn = document.getElementById(`btn-${entryId}`);
    const btnText = document.getElementById(`btn-text-${entryId}`);
    const statusBadge = document.getElementById(`status-badge-${entryId}`);

    if (isCaught) {
        card.classList.remove('uncaught-card');
        card.classList.add('caught-card');
        if (btnText) btnText.textContent = 'Liberar';
        if (btn) btn.className = THEME_CAUGHT_BTN;
        if (statusBadge) {
            statusBadge.innerHTML = '<span class="status-check-box w-2.5 h-2.5 rounded-sm border border-current flex items-center justify-center text-[8px] leading-none shrink-0">✓</span><span class="status-text font-black">' + (isShinydexMode ? 'Variocolor' : 'Atrapado') + '</span>';
            statusBadge.className = 'card-status-indicator h-6 min-w-[78px] flex items-center justify-center gap-1 px-1.5 rounded-md text-[10px] font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1px_1px_0px_#0f172a] shrink-0 ' + (isShinydexMode ? 'bg-amber-400 text-slate-950' : THEME_STATUS_CAUGHT_CLASS);
        }
    } else {
        card.classList.remove('caught-card');
        card.classList.add('uncaught-card');
        if (btnText) btnText.textContent = 'Capturar';
        if (btn) btn.className = THEME_UNCAUGHT_BTN;
        if (statusBadge) {
            statusBadge.innerHTML = '<span class="status-check-box w-2.5 h-2.5 rounded-sm border border-current flex items-center justify-center text-[8px] leading-none shrink-0"></span><span class="status-text font-black">Falta</span>';
            statusBadge.className = 'card-status-indicator h-6 min-w-[78px] flex items-center justify-center gap-1 px-1.5 rounded-md text-[10px] font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1px_1px_0px_#0f172a] shrink-0 bg-slate-100 text-slate-500';
        }
    }
}

function applyShinydexMode(active) {
    const btnToggle = document.getElementById('btn-toggle-shinydex');
    const icon = document.getElementById('shinydex-icon');
    const title = document.getElementById('progress-card-title');
    const dot = document.getElementById('progress-dot');
    const btnTransfers = document.getElementById('btn-transfers');

    if (active) {
        if (btnToggle) {
            btnToggle.setAttribute('title', 'Modo Shinydex activo (Clic para volver a la Pokédex normal)');
        }
        if (icon) {
            icon.className = 'w-7 h-7 sm:w-8 sm:h-8 object-contain pixel-art drop-shadow-[0_0_10px_rgba(245,158,11,1)]';
        }
        if (title) title.textContent = 'Progreso Shinydex';
        if (dot) dot.className = 'w-2 h-2 rounded-full bg-amber-400';

        // Ocultar botón de transferencias en Shinydex (los de Gen 1 no pueden ser shiny)
        if (btnTransfers) {
            btnTransfers.style.display = 'none';
        }
    } else {
        if (btnToggle) {
            btnToggle.setAttribute('title', 'Alternar entre Pokédex normal y Shinydex (Variocolor)');
        }
        if (icon) {
            icon.className = 'w-7 h-7 sm:w-8 sm:h-8 object-contain pixel-art drop-shadow';
        }
        if (title) title.textContent = 'Progreso de Captura';
        if (dot) {
            dot.className = 'w-2 h-2 rounded-full ' + (
                currentGameSlug === 'blue' ? 'bg-blue-600' :
                (currentGameSlug === 'yellow' ? 'bg-amber-500' :
                (currentGameSlug === 'gold' ? 'bg-[#c59b27]' : 'bg-red-600'))
            );
        }

        // Restaurar botón de transferencias si existe
        if (btnTransfers) {
            btnTransfers.style.display = '';
        }
    }

    // Actualizar métricas de progreso
    updateProgressBarUI();

    // Actualizar imágenes y estados de todas las tarjetas
    document.querySelectorAll('.pokemon-card').forEach(card => {
        const entryId = card.dataset.entryId;
        const img = document.getElementById(`img-${entryId}`);
        const isCaught = active 
            ? (card.dataset.shinyCaught === 'true')
            : (card.dataset.caught === 'true');

        if (img) {
            if (active) {
                if (currentSpriteStyle === 'retro') {
                    img.src = card.dataset.spriteRetroShiny || card.dataset.spriteModernShiny;
                    img.classList.add('pixel-art');
                } else {
                    img.src = card.dataset.spriteModernShiny || card.dataset.spriteRetroShiny;
                    img.classList.remove('pixel-art');
                }
            } else {
                if (currentSpriteStyle === 'retro') {
                    img.src = card.dataset.spriteRetro;
                    img.classList.add('pixel-art');
                } else {
                    img.src = card.dataset.spriteModern;
                    img.classList.remove('pixel-art');
                }
            }
        }

        updateCardUI(card, isCaught);
    });

    // Reevaluar filtro activo de estado
    filterCards();
}

function setSpriteStyle(style) {
    currentSpriteStyle = style;
    const btnRetro = document.getElementById('btn-style-retro');
    const btnModern = document.getElementById('btn-style-modern');

    if (btnRetro && btnModern) {
        if (style === 'retro') {
            btnRetro.className = 'px-2 py-1 rounded-lg text-xs font-black uppercase flex items-center gap-1 border-2 border-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 ' + THEME_ACTIVE_BTN;
            btnModern.className = 'px-2 py-1 rounded-lg text-xs font-bold uppercase text-slate-600 hover:text-slate-950 flex items-center gap-1 border border-transparent';
        } else {
            btnModern.className = 'px-2 py-1 rounded-lg text-xs font-black uppercase flex items-center gap-1 border-2 border-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 ' + THEME_ACTIVE_BTN;
            btnRetro.className = 'px-2 py-1 rounded-lg text-xs font-bold uppercase text-slate-600 hover:text-slate-950 flex items-center gap-1 border border-transparent';
        }
    }

    document.querySelectorAll('.pokemon-card').forEach(card => {
        const entryId = card.dataset.entryId;
        const img = document.getElementById(`img-${entryId}`);
        if (img) {
            if (isShinydexMode) {
                if (style === 'retro') {
                    img.src = card.dataset.spriteRetroShiny || card.dataset.spriteModernShiny;
                    img.classList.add('pixel-art');
                } else {
                    img.src = card.dataset.spriteModernShiny || card.dataset.spriteRetroShiny;
                    img.classList.remove('pixel-art');
                }
            } else {
                if (style === 'retro') {
                    img.src = card.dataset.spriteRetro;
                    img.classList.add('pixel-art');
                } else {
                    img.src = card.dataset.spriteModern;
                    img.classList.remove('pixel-art');
                }
            }
        }
    });

    document.querySelectorAll("img[id^='excl-img-']").forEach(img => {
        if (style === 'retro') {
            img.src = img.dataset.spriteRetro;
            img.classList.add('pixel-art');
        } else {
            img.src = img.dataset.spriteModern;
            img.classList.remove('pixel-art');
        }
    });

    document.querySelectorAll("img[id^='transfer-img-']").forEach(img => {
        if (style === 'retro') {
            img.src = img.dataset.spriteRetro;
            img.classList.add('pixel-art');
        } else {
            img.src = img.dataset.spriteModern;
            img.classList.remove('pixel-art');
        }
    });

    if (activeModalEntryId) {
        const dataScript = document.getElementById(`entry-data-${activeModalEntryId}`);
        if (dataScript) {
            try {
                const d = JSON.parse(dataScript.textContent);
                const modalImg = document.getElementById('modal-pokemon-img');
                if (modalImg) {
                    if (isShinydexMode) {
                        if (style === 'retro' && d.sprite_retro_shiny) {
                            modalImg.src = d.sprite_retro_shiny;
                            modalImg.classList.add('pixel-art');
                        } else {
                            modalImg.src = d.sprite_modern_shiny || d.sprite_retro_shiny || d.sprite_modern;
                            modalImg.classList.remove('pixel-art');
                        }
                    } else {
                        if (style === 'retro' && d.sprite_retro) {
                            modalImg.src = d.sprite_retro;
                            modalImg.classList.add('pixel-art');
                        } else {
                            modalImg.src = d.sprite_modern;
                            modalImg.classList.remove('pixel-art');
                        }
                    }
                }
            } catch (e) {
                console.error("Error parsing entry-data script in setSpriteStyle:", e);
            }
        }
    }

    try {
        localStorage.setItem('pokedex_sprite_style', style);
    } catch (e) {}
}

function setStatusFilter(status) {
    currentStatusFilter = status;
    const buttons = {
        'all': document.getElementById('filter-all'),
        'caught': document.getElementById('filter-caught'),
        'uncaught': document.getElementById('filter-uncaught'),
    };

    for (const [key, btn] of Object.entries(buttons)) {
        if (btn) {
            if (key === status) {
                btn.className = 'px-2 py-1 rounded-lg text-xs font-black uppercase border-2 border-slate-950 shadow-[1.5px_1.5px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 ' + THEME_ACTIVE_BTN;
            } else {
                btn.className = 'px-2 py-1 rounded-lg text-xs font-bold uppercase text-slate-600 hover:text-slate-950 border border-transparent';
            }
        }
    }
    filterCards();
}

function filterCards() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const cards = document.querySelectorAll('.pokemon-card');

    cards.forEach(card => {
        const name = card.dataset.name || '';
        const display = card.dataset.display || '';
        const number = card.dataset.number || '';
        const type1 = card.dataset.type1 || '';
        const type2 = card.dataset.type2 || '';
        const type1Es = card.dataset.type1Es || '';
        const type2Es = card.dataset.type2Es || '';
        const isCaught = isShinydexMode 
            ? (card.dataset.shinyCaught === 'true')
            : (card.dataset.caught === 'true');

        // Filtro de texto (nombre, número de Pokédex o tipo en español/inglés)
        const matchesText = !query || 
            name.includes(query) || 
            display.includes(query) || 
            number.includes(query) ||
            type1.includes(query) ||
            type2.includes(query) ||
            type1Es.includes(query) ||
            type2Es.includes(query);

        // Filtro de estado
        let matchesStatus = true;
        if (currentStatusFilter === 'caught') {
            matchesStatus = isCaught;
        } else if (currentStatusFilter === 'uncaught') {
            matchesStatus = !isCaught;
        }

        if (matchesText && matchesStatus) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

async function toggleCatch(entryId) {
    const card = document.getElementById(`card-${entryId}`);
    const btn = document.getElementById(`btn-${entryId}`);

    if (btn) {
        btn.disabled = true;
        btn.classList.add('opacity-50');
    }

    try {
        const response = await fetch('/api/catch/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({ 
                entry_id: entryId,
                is_shiny: isShinydexMode
            })
        });

        if (!response.ok) {
            throw new Error('Error al registrar captura');
        }

        const data = await response.json();
        if (data.success) {
            // Actualizar tarjeta
            if (card) {
                if (isShinydexMode) {
                    card.dataset.shinyCaught = data.is_caught ? 'true' : 'false';
                } else {
                    card.dataset.caught = data.is_caught ? 'true' : 'false';
                }
                updateCardUI(card, data.is_caught);
            }

            // Sincronizar con el modal si está abierto para este Pokémon
            if (activeModalEntryId === entryId) {
                updateModalCatchStatus(data.is_caught);
            }

            // Sincronizar con la tarjeta de exclusivos si este Pokémon está en ella
            if (!isShinydexMode) {
                updateExclusivesCardStatus(entryId, data.is_caught);
                updateTransfersCardStatus(entryId, data.is_caught);
            }

            // Actualizar métricas globales
            if (isShinydexMode) {
                shinyStats.caught = data.caught_count;
                shinyStats.percent = data.percent;
            } else {
                normalStats.caught = data.caught_count;
                normalStats.percent = data.percent;
            }
            updateProgressBarUI();

            // Si hay filtro activo, evaluar visibilidad
            if (currentStatusFilter !== 'all') {
                filterCards();
            }
        }
    } catch (err) {
        console.error(err);
        alert('No se pudo actualizar el estado de captura.');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('opacity-50');
        }
    }
}

/* ===== Audio Cry Player ===== */
let currentCryAudio = null;

function playPokemonCry(cryUrl, btnElem) {
    if (!cryUrl) return;
    try {
        if (currentCryAudio) {
            currentCryAudio.pause();
            currentCryAudio.currentTime = 0;
        }
        currentCryAudio = new Audio(cryUrl);
        currentCryAudio.volume = 0.6;
        currentCryAudio.play().catch(err => console.log("Audio play error:", err));

        if (btnElem) {
            btnElem.classList.add('text-amber-400', 'scale-125');
            setTimeout(() => {
                btnElem.classList.remove('text-amber-400', 'scale-125');
            }, 400);
        }
    } catch (err) {
        console.error("Error al reproducir audio:", err);
    }
}

let activeModalCryUrl = '';

function playModalCry(btnElem) {
    if (activeModalCryUrl) {
        playPokemonCry(activeModalCryUrl, btnElem);
    }
}

/* ===== Comic Book Modal Controller ===== */
function openPokemonModal(entryId) {
    const dataScript = document.getElementById(`entry-data-${entryId}`);
    if (!dataScript) return;

    let data;
    try {
        data = JSON.parse(dataScript.textContent);
    } catch (e) {
        console.error("Error al parsear datos del Pokémon", e);
        return;
    }

    activeModalEntryId = entryId;
    activeModalCryUrl = data.cry_url || '';
    const modalCryBtn = document.getElementById('modal-cry-btn');
    if (modalCryBtn) {
        if (activeModalCryUrl) {
            modalCryBtn.classList.remove('hidden');
        } else {
            modalCryBtn.classList.add('hidden');
        }
    }

    // 1. Textos principales
    const numEl = document.getElementById('modal-pokemon-number');
    const nameEl = document.getElementById('modal-pokemon-name');
    const catEl = document.getElementById('modal-pokemon-category');
    const flavorEl = document.getElementById('modal-flavor-text');
    if (numEl) numEl.textContent = `#${data.number}`;
    if (nameEl) nameEl.textContent = data.name;
    if (catEl) catEl.textContent = data.category || 'Pokémon';
    if (flavorEl) {
        flavorEl.textContent = data.flavor_text 
            ? `"${data.flavor_text}"` 
            : '"No hay descripción de Pokédex registrada para esta versión."';
    }

    // 2. Sprite según estilo activo (retro o modern) y modo (normal o shiny)
    const modalImg = document.getElementById('modal-pokemon-img');
    if (modalImg) {
        if (isShinydexMode) {
            if (currentSpriteStyle === 'retro' && data.sprite_retro_shiny) {
                modalImg.src = data.sprite_retro_shiny;
                modalImg.classList.add('pixel-art');
            } else {
                modalImg.src = data.sprite_modern_shiny || data.sprite_retro_shiny || data.sprite_modern;
                modalImg.classList.remove('pixel-art');
            }
        } else {
            if (currentSpriteStyle === 'retro' && data.sprite_retro) {
                modalImg.src = data.sprite_retro;
                modalImg.classList.add('pixel-art');
            } else {
                modalImg.src = data.sprite_modern;
                modalImg.classList.remove('pixel-art');
            }
        }
        modalImg.alt = data.name;
    }

    // 3. Tipos elementales
    const typesContainer = document.getElementById('modal-types-container');
    if (typesContainer) {
        typesContainer.innerHTML = '';
        
        const badge1 = document.createElement('span');
        badge1.className = `type-${data.primary_type} border-2 border-slate-950 font-black text-[10px] sm:text-xs uppercase px-2.5 py-0.5 rounded shadow-[1.5px_1.5px_0px_0px_#0f172a] text-white`;
        badge1.textContent = data.primary_type_es;
        typesContainer.appendChild(badge1);

        if (data.secondary_type && data.secondary_type_es) {
            const badge2 = document.createElement('span');
            badge2.className = `type-${data.secondary_type} border-2 border-slate-950 font-black text-[10px] sm:text-xs uppercase px-2.5 py-0.5 rounded shadow-[1.5px_1.5px_0px_0px_#0f172a] text-white`;
            badge2.textContent = data.secondary_type_es;
            typesContainer.appendChild(badge2);
        }
    }

    // 4. Biometría (Altura y Peso)
    const heightEl = document.getElementById('modal-pokemon-height');
    const weightEl = document.getElementById('modal-pokemon-weight');
    if (heightEl) heightEl.textContent = data.height ? `${(data.height / 10).toFixed(1)} m` : '--';
    if (weightEl) weightEl.textContent = data.weight ? `${(data.weight / 10).toFixed(1)} kg` : '--';

    // 5. Método de Obtención y Localización
    const obt = data.obtaining || {};
    const uniqueBadgeElem = document.getElementById('modal-unique-badge');
    if (uniqueBadgeElem) {
        if (obt.is_unique) {
            uniqueBadgeElem.classList.remove('hidden');
        } else {
            uniqueBadgeElem.classList.add('hidden');
        }
    }

    const badgeElem = document.getElementById('modal-obtaining-badge');
    if (badgeElem) {
        badgeElem.textContent = obt.badge_label || 'Desconocido';

        // Color del badge
        const badgeColorMap = {
            'emerald': 'bg-emerald-400 text-slate-950',
            'amber': 'bg-amber-400 text-slate-950',
            'indigo': 'bg-indigo-400 text-white',
            'sky': 'bg-sky-400 text-slate-950',
            'rose': 'bg-rose-500 text-white',
            'violet': 'bg-purple-400 text-white',
            'pink': 'bg-pink-400 text-slate-950',
            'slate': 'bg-slate-300 text-slate-900',
        };
        const badgeColorClass = badgeColorMap[obt.badge_color] || 'bg-amber-300 text-slate-950';
        badgeElem.className = `border-2 border-slate-950 font-black text-[10px] sm:text-xs uppercase px-2.5 py-0.5 rounded shadow-[1.5px_1.5px_0px_0px_#0f172a] ${badgeColorClass}`;
    }

    const summaryEl = document.getElementById('modal-obtaining-summary');
    if (summaryEl) {
        summaryEl.textContent = obt.summary || 'Sin información de obtención registrada.';
    }

    // Lista detallada de ubicaciones y/o evolución
    const detailsContainer = document.getElementById('modal-obtaining-details');
    if (detailsContainer) {
        detailsContainer.innerHTML = '';

        // 1. Mostrar información de evolución si el Pokémon proviene de una evolución
        if (obt.evolution_info) {
            const evoBox = document.createElement('div');
            const stone = data.evolution_stone;
            const evoText = obt.evolution_info.text || `Evoluciona de ${obt.evolution_info.from} (${obt.evolution_info.condition || ''})`;

            if (stone) {
                evoBox.className = 'text-xs bg-indigo-50/90 border-2 border-indigo-300 text-indigo-950 rounded-lg p-2.5 font-bold flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-2 shadow-sm';
                evoBox.innerHTML = `
                    <div class="flex items-center gap-2">
                        <img src="${stone.icon_url}" alt="${stone.name}" class="w-5 h-5 object-contain inline-block shrink-0 drop-shadow-sm">
                        <span><strong>Evolución:</strong> ${evoText}</span>
                    </div>
                    <button 
                        type="button" 
                        onclick="event.stopPropagation(); openStoneModal('${stone.slug}', '${stone.name}')"
                        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white hover:bg-amber-50 border-2 border-slate-950 text-slate-900 text-[10px] font-black uppercase shadow-[1.5px_1.5px_0px_0px_#0f172a] transition-transform active:translate-x-0.5 active:translate-y-0.5 shrink-0 self-start sm:self-auto cursor-pointer"
                        title="Ver dónde conseguir ${stone.name}"
                    >
                        <img src="${stone.icon_url}" alt="" class="w-3.5 h-3.5 object-contain">
                        <span>Dónde conseguirlo</span>
                    </button>
                `;
            } else {
                evoBox.className = 'text-xs bg-indigo-50 border-2 border-indigo-200 text-indigo-950 rounded-lg p-2.5 font-bold flex items-center gap-2 mb-2 shadow-sm';
                const evoIcon = (obt.evolution_info.trigger === 'trade') ? '/media/items/town-map.png' : '/media/items/rare-candy.png';
                evoBox.innerHTML = `<img src="${evoIcon}" alt="Evolución" class="w-4 h-4 object-contain inline-block shrink-0"> <span><strong>Evolución:</strong> ${evoText}</span>`;
            }
            detailsContainer.appendChild(evoBox);
        }

        // 2. Mostrar ubicaciones salvajes o de crianza si las tiene
        if (obt.locations && obt.locations.length > 0) {
            if (obt.evolution_info) {
                const wildTitle = document.createElement('div');
                wildTitle.className = 'text-[11px] font-bold text-slate-700 uppercase tracking-wide mb-1';
                wildTitle.textContent = 'Lugares de obtención:';
                detailsContainer.appendChild(wildTitle);
            }

            const locList = document.createElement('div');
            locList.className = 'grid grid-cols-1 sm:grid-cols-2 gap-1.5';
            obt.locations.forEach(loc => {
                const item = document.createElement('div');
                const isBreedingOrEgg = loc.method && (loc.method.includes('Crianza') || loc.method.includes('Huevo'));
                const locIcon = isBreedingOrEgg ? '/media/items/mystery-egg.png' : '/media/items/town-map.png';
                const cardBg = isBreedingOrEgg ? 'bg-pink-50/70 border-pink-200 text-pink-950' : 'bg-slate-50 border-slate-300 text-slate-800';
                item.className = `flex items-center justify-between text-[11px] border rounded px-2.5 py-1 font-semibold overflow-hidden min-h-[30px] ${cardBg}`;
                item.title = `${loc.area} (${loc.method})`;
                item.innerHTML = `
                    <div class="flex items-center gap-1.5 min-w-0 flex-1 mr-1.5 overflow-hidden">
                        <img src="${locIcon}" alt="" class="w-3.5 h-3.5 object-contain inline-block shrink-0 drop-shadow-sm">
                        <div class="location-marquee-wrapper overflow-hidden whitespace-nowrap min-w-0 flex-1 relative">
                            <span class="location-marquee-text inline-block whitespace-nowrap">${loc.area}</span>
                        </div>
                    </div>
                    <span class="text-[10px] text-slate-500 font-medium shrink-0">(${loc.method})</span>
                `;
                locList.appendChild(item);
            });
            detailsContainer.appendChild(locList);
        }
    }

    // 6. Estado de captura actual
    const card = document.getElementById(`card-${entryId}`);
    const isCaught = card ? (
        isShinydexMode ? (card.dataset.shinyCaught === 'true') : (card.dataset.caught === 'true')
    ) : false;
    updateModalCatchStatus(isCaught);

    // 7. Mostrar modal
    const modal = document.getElementById('comic-modal');
    const modalCard = document.getElementById('comic-modal-card');
    if (modal && modalCard) {
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
        modalCard.classList.remove('scale-95');
        modalCard.classList.add('scale-100');
        document.body.classList.add('overflow-hidden');
    }

    // 8. Activar marquesina suave en ubicaciones cuyo texto desborde
    requestAnimationFrame(() => {
        document.querySelectorAll('#modal-obtaining-details .location-marquee-wrapper').forEach(wrapper => {
            const textSpan = wrapper.querySelector('.location-marquee-text');
            if (textSpan) {
                const overflowDiff = textSpan.scrollWidth - wrapper.clientWidth;
                if (overflowDiff > 3) {
                    textSpan.style.setProperty('--marquee-dist', `-${overflowDiff + 6}px`);
                    const duration = Math.max(4.5, (overflowDiff / 18) + 3);
                    textSpan.style.setProperty('--marquee-dur', `${duration.toFixed(1)}s`);
                    textSpan.classList.add('marquee-pingpong');
                }
            }
        });
    });
}

function releaseScrollIfNoModalOpen() {
    const comicModal = document.getElementById('comic-modal');
    const exclModal = document.getElementById('exclusives-modal');
    const stoneModal = document.getElementById('stone-location-modal');
    const transModal = document.getElementById('transfers-modal');
    const isComicOpen = comicModal && !comicModal.classList.contains('opacity-0');
    const isExclOpen = exclModal && !exclModal.classList.contains('opacity-0');
    const isStoneOpen = stoneModal && !stoneModal.classList.contains('opacity-0');
    const isTransOpen = transModal && !transModal.classList.contains('opacity-0');
    if (!isComicOpen && !isExclOpen && !isStoneOpen && !isTransOpen) {
        document.body.classList.remove('overflow-hidden');
    }
}

function closePokemonModal() {
    const modal = document.getElementById('comic-modal');
    const modalCard = document.getElementById('comic-modal-card');
    if (modal) {
        modal.classList.remove('opacity-100', 'pointer-events-auto');
        modal.classList.add('opacity-0', 'pointer-events-none');
    }
    if (modalCard) {
        modalCard.classList.remove('scale-100');
        modalCard.classList.add('scale-95');
    }
    releaseScrollIfNoModalOpen();
    activeModalEntryId = null;
}

function handleModalBackdropClick(e) {
    if (e.target.id === 'comic-modal') {
        closePokemonModal();
    }
}

/* ===== Stone Location Modal Controller ===== */
function openStoneModal(stoneSlug, stoneName) {
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
    if (modal && modalCard) {
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
        modalCard.classList.remove('scale-95');
        modalCard.classList.add('scale-100');
        document.body.classList.add('overflow-hidden');
    }
}

function closeStoneModal() {
    const modal = document.getElementById('stone-location-modal');
    const modalCard = document.getElementById('stone-modal-card');
    if (modal) {
        modal.classList.remove('opacity-100', 'pointer-events-auto');
        modal.classList.add('opacity-0', 'pointer-events-none');
    }
    if (modalCard) {
        modalCard.classList.remove('scale-100');
        modalCard.classList.add('scale-95');
    }
    releaseScrollIfNoModalOpen();
}

function handleStoneModalBackdropClick(e) {
    if (e.target.id === 'stone-location-modal') {
        closeStoneModal();
    }
}

function updateModalCatchStatus(isCaught) {
    const badge = document.getElementById('modal-status-badge');
    const btn = document.getElementById('modal-toggle-catch-btn');
    const text = document.getElementById('modal-toggle-text');

    if (badge && btn && text) {
        if (isCaught) {
            badge.className = isShinydexMode
                ? 'px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider border-2 border-slate-950 bg-amber-400 text-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a]'
                : 'px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider border-2 border-slate-950 bg-emerald-400 text-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a]';
            badge.textContent = isShinydexMode ? '★ Variocolor atrapado' : '✓ Atrapado en tu partida';
            btn.className = 'py-1.5 px-4 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] bg-rose-500 hover:bg-rose-600 text-white transition-all active:translate-x-0.5 active:translate-y-0.5 flex items-center gap-1.5';
            text.textContent = 'Liberar';
        } else {
            badge.className = 'px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider border-2 border-slate-950 bg-slate-200 text-slate-700 shadow-[1.5px_1.5px_0px_0px_#0f172a]';
            badge.textContent = isShinydexMode ? 'Variocolor pendiente' : 'Pendiente de capturar';
            btn.className = 'py-1.5 px-4 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] bg-emerald-500 hover:bg-emerald-600 text-white transition-all active:translate-x-0.5 active:translate-y-0.5 flex items-center gap-1.5';
            text.textContent = 'Capturar';
        }
    }
}

async function modalToggleCatch() {
    if (activeModalEntryId) {
        await toggleCatch(activeModalEntryId);
    }
}

/* ===== Modal de Pokémon Exclusivos de Versión ===== */
function openExclusivesModal() {
    const modal = document.getElementById('exclusives-modal');
    const modalCard = document.getElementById('exclusives-modal-card');
    if (modal && modalCard) {
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
        modalCard.classList.remove('scale-95');
        modalCard.classList.add('scale-100');
        document.body.classList.add('overflow-hidden');
    }
}

function closeExclusivesModal() {
    const modal = document.getElementById('exclusives-modal');
    const modalCard = document.getElementById('exclusives-modal-card');
    if (modal && modalCard) {
        modal.classList.remove('opacity-100', 'pointer-events-auto');
        modal.classList.add('opacity-0', 'pointer-events-none');
        modalCard.classList.remove('scale-100');
        modalCard.classList.add('scale-95');
    }
    releaseScrollIfNoModalOpen();
}

function handleExclusivesBackdropClick(e) {
    if (e.target.id === 'exclusives-modal') {
        closeExclusivesModal();
    }
}

function switchExclusivesTab(tab) {
    const panelCounterpart = document.getElementById('exclusives-panel-counterpart');
    const panelOwn = document.getElementById('exclusives-panel-own');
    const btnCounterpart = document.getElementById('tab-btn-counterpart');
    const btnOwn = document.getElementById('tab-btn-own');

    if (!panelCounterpart || !panelOwn) return;

    if (tab === 'counterpart') {
        panelCounterpart.classList.remove('hidden');
        panelOwn.classList.add('hidden');
        if (btnCounterpart) btnCounterpart.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-amber-400 text-slate-950 flex items-center justify-center gap-2';
        if (btnOwn) btnOwn.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-white hover:bg-slate-50 text-slate-700 flex items-center justify-center gap-2';
    } else {
        panelOwn.classList.remove('hidden');
        panelCounterpart.classList.add('hidden');
        if (btnOwn) btnOwn.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-amber-400 text-slate-950 flex items-center justify-center gap-2';
        if (btnCounterpart) btnCounterpart.className = 'flex-1 py-2 px-3 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] transition-all bg-white hover:bg-slate-50 text-slate-700 flex items-center justify-center gap-2';
    }
}

async function toggleExclusiveCatch(entryId, nationalNumber) {
    await toggleCatch(entryId);
}

function updateExclusivesCardStatus(entryId, isCaught) {
    const card = document.querySelector(`[id^='excl-card-'][data-entry-id='${entryId}']`);
    if (card) {
        card.dataset.caught = isCaught ? 'true' : 'false';
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

    // Recalcular métricas de exclusivos de la contraparte
    const counterpartCards = document.querySelectorAll("#exclusives-panel-counterpart [id^='excl-card-']");
    if (counterpartCards.length > 0) {
        let caughtCount = 0;
        counterpartCards.forEach(c => {
            if (c.dataset.caught === 'true') caughtCount++;
        });
        const totalCount = counterpartCards.length;
        const percent = Math.round((caughtCount / totalCount) * 100);

        const badgeElem = document.getElementById('exclusives-counterpart-caught-badge');
        if (badgeElem) badgeElem.textContent = caughtCount;

        const caughtElem = document.getElementById('excl-progress-caught');
        if (caughtElem) caughtElem.textContent = caughtCount;

        const percentElem = document.getElementById('excl-progress-percent');
        if (percentElem) percentElem.textContent = percent;

        const barElem = document.getElementById('excl-progress-bar');
        if (barElem) barElem.style.width = `${percent}%`;
    }
}

/* ===== Modal de Pokémon a Transferir ===== */
function openTransfersModal() {
    const modal = document.getElementById('transfers-modal');
    const modalCard = document.getElementById('transfers-modal-card');
    if (modal && modalCard) {
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
        modalCard.classList.remove('scale-95');
        modalCard.classList.add('scale-100');
        document.body.classList.add('overflow-hidden');
    }
}

function closeTransfersModal() {
    const modal = document.getElementById('transfers-modal');
    const modalCard = document.getElementById('transfers-modal-card');
    if (modal && modalCard) {
        modal.classList.remove('opacity-100', 'pointer-events-auto');
        modal.classList.add('opacity-0', 'pointer-events-none');
        modalCard.classList.remove('scale-100');
        modalCard.classList.add('scale-95');
    }
    releaseScrollIfNoModalOpen();
}

function handleTransfersBackdropClick(e) {
    if (e.target.id === 'transfers-modal') {
        closeTransfersModal();
    }
}

async function toggleTransferCatch(entryId, nationalNumber) {
    await toggleCatch(entryId);
}

function updateTransfersCardStatus(entryId, isCaught) {
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

// Atajos de teclado (Escape para cerrar modales en orden de superposición)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const stoneModal = document.getElementById('stone-location-modal');
        if (stoneModal && !stoneModal.classList.contains('opacity-0')) {
            closeStoneModal();
            return;
        }
        const comicModal = document.getElementById('comic-modal');
        if (comicModal && !comicModal.classList.contains('opacity-0')) {
            closePokemonModal();
            return;
        }
        const transModal = document.getElementById('transfers-modal');
        if (transModal && !transModal.classList.contains('opacity-0')) {
            closeTransfersModal();
            return;
        }
        closeExclusivesModal();
    }
});

// Configuración inicial de estilos de botones y sprites según preferencia guardada
document.addEventListener('DOMContentLoaded', () => {
    try {
        const savedStyle = localStorage.getItem('pokedex_sprite_style');
        if (savedStyle && savedStyle !== 'retro' && document.getElementById('btn-style-retro')) {
            setSpriteStyle(savedStyle);
        }
    } catch (e) {}

    try {
        const gameGen = parseInt(document.getElementById('game-generation')?.value || 1, 10);
        if (gameGen >= 2) {
            const savedShinydex = localStorage.getItem('pokedex_shinydex_' + currentGameSlug);
            // Si la cookie no estaba sincronizada pero en localStorage sí
            if (savedShinydex === '1' && !isShinydexMode) {
                isShinydexMode = true;
                applyShinydexMode(true);
                document.cookie = 'pokedex_shinydex_' + currentGameSlug + '=1; path=/; max-age=31536000; SameSite=Lax';
            } else if (savedShinydex === '0' && isShinydexMode) {
                isShinydexMode = false;
                applyShinydexMode(false);
                document.cookie = 'pokedex_shinydex_' + currentGameSlug + '=0; path=/; max-age=31536000; SameSite=Lax';
            } else if (savedShinydex === null && isShinydexMode) {
                // Sincronizar localStorage si el servidor inició en shiny
                localStorage.setItem('pokedex_shinydex_' + currentGameSlug, '1');
            }
        }
    } catch (e) {}
});
