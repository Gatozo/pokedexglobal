/**
 * Pokédex Global - Módulo de Tarjetas y Capturas (cards.js)
 * Sincronización de tarjetas de Pokémon, progreso global, modo Shinydex y estilos de sprite (Retro/Moderno).
 */

import { state, currentGameSlug, THEME_ACTIVE_BTN, THEME_STATUS_CAUGHT_CLASS, THEME_UNCAUGHT_BTN, THEME_CAUGHT_BTN } from './state.js';
import { getCsrfToken } from './api.js';
import { filterCards } from './filters.js';
import { updateModalCatchStatus, updateModalSpriteDisplay } from './modal_comic.js';
import { updateExclusivesCardStatus, updateExclusivesModalUI } from './modal_exclusives.js';
import { updateTransfersCardStatus } from './modal_transfers.js';
import { updateUnownModalUI } from './modal_unown.js';

export function toggleShinydexMode() {
    state.isShinydexMode = !state.isShinydexMode;
    try {
        localStorage.setItem('pokedex_shinydex_' + currentGameSlug, state.isShinydexMode ? '1' : '0');
        document.cookie = 'pokedex_shinydex_' + currentGameSlug + '=' + (state.isShinydexMode ? '1' : '0') + '; path=/; max-age=31536000; SameSite=Lax';
    } catch (e) {}
    applyShinydexMode(state.isShinydexMode);
}

export function updateProgressBarUI() {
    const statCaught = document.getElementById('stat-caught');
    const statPercent = document.getElementById('stat-percent');
    const progressBar = document.getElementById('progress-bar');

    const currentStats = state.isShinydexMode ? state.shinyStats : state.normalStats;
    if (statCaught) statCaught.textContent = currentStats.caught;
    if (statPercent) statPercent.textContent = currentStats.percent;
    if (progressBar) {
        progressBar.style.width = `${currentStats.percent}%`;
        if (state.isShinydexMode) {
            progressBar.className = 'bg-gradient-to-r from-amber-400 to-yellow-300 h-full rounded-full transition-all duration-300 shadow-[0_0_8px_rgba(251,191,36,0.6)]';
        } else {
            progressBar.className = (
                currentGameSlug === 'yellow' ? 'bg-amber-400' :
                (currentGameSlug === 'blue' ? 'bg-blue-600' :
                (currentGameSlug === 'gold' ? 'bg-[#c59b27]' :
                (currentGameSlug === 'silver' ? 'bg-slate-500' :
                (currentGameSlug === 'crystal' ? 'bg-sky-500' : 'bg-red-600'))))
            ) + ' h-full rounded-full transition-all duration-300';
        }
    }
}

export function updateCardUI(card, isCaught) {
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
            statusBadge.innerHTML = '<span class="status-check-box w-2.5 h-2.5 rounded-sm border border-current flex items-center justify-center text-[8px] leading-none shrink-0">✓</span><span class="status-text font-black">' + (state.isShinydexMode ? 'Variocolor' : 'Atrapado') + '</span>';
            statusBadge.className = 'card-status-indicator h-6 min-w-[78px] flex items-center justify-center gap-1 px-1.5 rounded-md text-[10px] font-black uppercase tracking-wider border-2 border-slate-950 shadow-[1px_1px_0px_#0f172a] shrink-0 ' + (state.isShinydexMode ? 'bg-amber-400 text-slate-950' : THEME_STATUS_CAUGHT_CLASS);
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

export function applyShinydexMode(active) {
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
                (currentGameSlug === 'gold' ? 'bg-[#c59b27]' :
                (currentGameSlug === 'silver' ? 'bg-slate-400' :
                (currentGameSlug === 'crystal' ? 'bg-sky-500' : 'bg-red-600'))))
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

        updateCardUI(card, isCaught);
    });

    if (state.activeModalEntryId) {
        updateModalSpriteDisplay();
    }

    // Reevaluar filtro activo de estado
    filterCards();

    updateUnownModalUI();
    updateExclusivesModalUI();
}

export function setSpriteStyle(style) {
    state.currentSpriteStyle = style;
    const btnRetro = document.getElementById('btn-style-retro');
    const btnModern = document.getElementById('btn-style-modern');

    if (btnRetro && btnModern) {
        if (style === 'retro') {
            btnRetro.className = 'h-full w-[80px] text-xs font-black uppercase flex items-center justify-center gap-1.5 border-r-2 border-slate-950 transition-colors select-none ' + THEME_ACTIVE_BTN;
            btnModern.className = 'h-full w-[96px] text-xs font-black uppercase text-slate-700 hover:text-slate-950 hover:bg-slate-100 transition-colors flex items-center justify-center gap-1.5 select-none';
        } else {
            btnRetro.className = 'h-full w-[80px] text-xs font-black uppercase text-slate-700 hover:text-slate-950 hover:bg-slate-100 border-r-2 border-slate-950 transition-colors flex items-center justify-center gap-1.5 select-none';
            btnModern.className = 'h-full w-[96px] text-xs font-black uppercase flex items-center justify-center gap-1.5 transition-colors select-none ' + THEME_ACTIVE_BTN;
        }
    }

    document.querySelectorAll('.pokemon-card').forEach(card => {
        const entryId = card.dataset.entryId;
        const img = document.getElementById(`img-${entryId}`);
        if (img) {
            if (state.isShinydexMode) {
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

    if (state.activeModalEntryId) {
        updateModalSpriteDisplay();
    }

    document.querySelectorAll("img[id^='excl-img-']").forEach(img => {
        if (state.isShinydexMode) {
            if (style === 'retro') {
                img.src = img.dataset.spriteRetroShiny || img.dataset.spriteModernShiny;
                img.classList.add('pixel-art');
            } else {
                img.src = img.dataset.spriteModernShiny || img.dataset.spriteRetroShiny;
                img.classList.remove('pixel-art');
            }
        } else {
            if (style === 'retro') {
                img.src = img.dataset.spriteRetro;
                img.classList.add('pixel-art');
            } else {
                img.src = img.dataset.spriteModern;
                img.classList.remove('pixel-art');
            }
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

    if (state.activeModalEntryId) {
        const dataScript = document.getElementById(`entry-data-${state.activeModalEntryId}`);
        if (dataScript) {
            try {
                const d = JSON.parse(dataScript.textContent);
                const modalImg = document.getElementById('modal-pokemon-img');
                if (modalImg) {
                    if (state.isShinydexMode) {
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
                console.error("Error parsing dataScript:", e);
            }
        }
    }

    try {
        localStorage.setItem('pokedex_sprite_style', style);
    } catch (e) {}
}

export async function toggleCatch(entryId) {
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
                is_shiny: state.isShinydexMode
            })
        });

        if (!response.ok) {
            throw new Error('Error al registrar captura');
        }

        const data = await response.json();
        if (data.success) {
            // Actualizar dataset y aspecto de la tarjeta
            if (card) {
                if (state.isShinydexMode) {
                    card.dataset.shinyCaught = data.is_caught ? 'true' : 'false';
                } else {
                    card.dataset.caught = data.is_caught ? 'true' : 'false';
                }
                updateCardUI(card, data.is_caught);
            }

            // Sincronizar con el modal si está abierto para este Pokémon
            if (state.activeModalEntryId === entryId) {
                updateModalCatchStatus(data.is_caught);
            }

            // Sincronizar exclusivos y transferencias
            updateExclusivesCardStatus(entryId, data.is_caught);
            if (!state.isShinydexMode) {
                updateTransfersCardStatus(entryId, data.is_caught);
            }

            // Actualizar métricas globales de la barra activa
            if (state.isShinydexMode) {
                state.shinyStats.caught = data.caught_count;
                state.shinyStats.percent = data.percent;
            } else {
                state.normalStats.caught = data.caught_count;
                state.normalStats.percent = data.percent;
            }
            updateProgressBarUI();

            // Si hay filtro activo, evaluar visibilidad
            if (state.currentStatusFilter !== 'all') {
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
