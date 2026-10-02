/**
 * Pokédex Global - Modal Estilo Cómic del Pokémon (modal_comic.js)
 * Visualización de biometría, textos de Pokédex, sprites con rotación y formas alternas.
 */

import { state } from './state.js';
import { setActiveModalCryUrl } from './audio.js';
import { setModalUrlHash, syncUrlToCurrentOpenModal, releaseScrollIfNoModalOpen } from './url_sync.js';
import { openStoneModal } from './modal_stones.js';
import { openUnownModal } from './modal_unown.js';
import { toggleCatch } from './cards.js';

const _entryDataCache = new Map();
const _cardFormIndex = new Map();
let activeModalFormIndex = 0;
let isModalBackView = false;

export function openPokemonModal(entryId, updateHistory = true) {
    const card = document.getElementById(`card-${entryId}`);
    if (card && card.dataset.name === 'unown') {
        const unownModal = document.getElementById('unown-modal');
        if (unownModal) {
            openUnownModal(updateHistory);
            return;
        }
    }
    openPokemonModalDirect(entryId);
    if (updateHistory && card) {
        const slug = card.dataset.name || String(card.dataset.number);
        setModalUrlHash(slug);
    }
}

export function updateRotateButtonUI() {
    const btnText = document.getElementById('modal-rotate-btn-text');
    const btnIcon = document.getElementById('modal-rotate-btn-icon');
    if (btnText) {
        btnText.textContent = isModalBackView ? 'Frente' : 'Girar';
    }
    if (btnIcon) {
        if (isModalBackView) {
            btnIcon.classList.add('rotate-180');
        } else {
            btnIcon.classList.remove('rotate-180');
        }
    }
}

export function updateModalSpriteDisplay() {
    if (!state.activeModalEntryId) return;
    const data = getEntryData(state.activeModalEntryId);
    if (!data) return;

    const modalImg = document.getElementById('modal-pokemon-img');
    if (!modalImg) return;

    const hasForms = data.forms && data.forms.length > 1;
    let targetSrc = '';

    if (hasForms) {
        const form = data.forms[activeModalFormIndex] || data.forms[0];
        if (isModalBackView) {
            if (state.isShinydexMode) {
                targetSrc = form.sprite_retro_shiny_back || form.sprite_retro_shiny;
            } else {
                targetSrc = form.sprite_retro_back || form.sprite_retro;
            }
        } else {
            if (state.isShinydexMode) {
                if (state.currentSpriteStyle === 'retro') {
                    targetSrc = form.modal_retro_sprite_shiny_url || (activeModalFormIndex === 0 ? data.sprite_retro_shiny : null) || form.sprite_retro_shiny;
                } else {
                    targetSrc = form.sprite_modern_shiny || form.modal_retro_sprite_shiny_url || form.sprite_retro_shiny || form.sprite_modern;
                }
            } else {
                if (state.currentSpriteStyle === 'retro') {
                    targetSrc = form.modal_retro_sprite_url || (activeModalFormIndex === 0 ? data.sprite_retro : null) || form.sprite_retro;
                } else {
                    targetSrc = form.sprite_modern || form.modal_retro_sprite_url || form.sprite_retro;
                }
            }
        }
        modalImg.alt = `${form.display_name || form.name || data.name} (${isModalBackView ? 'Espalda' : 'Frente'})`;
    } else {
        if (isModalBackView) {
            if (state.isShinydexMode) {
                targetSrc = data.sprite_retro_shiny_back || data.sprite_retro_shiny;
            } else {
                targetSrc = data.sprite_retro_back || data.sprite_retro;
            }
        } else {
            if (state.isShinydexMode) {
                if (state.currentSpriteStyle === 'retro' && data.sprite_retro_shiny) {
                    targetSrc = data.sprite_retro_shiny;
                } else {
                    targetSrc = data.sprite_modern_shiny || data.sprite_retro_shiny || data.sprite_modern;
                }
            } else {
                if (state.currentSpriteStyle === 'retro' && data.sprite_retro) {
                    targetSrc = data.sprite_retro;
                } else {
                    targetSrc = data.sprite_modern;
                }
            }
        }
        modalImg.alt = `${data.name} (${isModalBackView ? 'Espalda' : 'Frente'})`;
    }

    if (targetSrc) {
        modalImg.onerror = () => {
            modalImg.onerror = null;
            const fallback = hasForms
                ? (form.sprite_retro || form.sprite_modern)
                : (data.sprite_modern || data.sprite_retro);
            if (fallback && modalImg.src !== fallback) {
                modalImg.src = fallback;
            }
        };
        modalImg.src = targetSrc;
    }

    if (isModalBackView || state.currentSpriteStyle === 'retro') {
        modalImg.classList.add('pixel-art');
    } else {
        modalImg.classList.remove('pixel-art');
    }

    updateRotateButtonUI();
}

export function toggleModalSpriteOrientation() {
    isModalBackView = !isModalBackView;
    updateModalSpriteDisplay();
}

export function getEntryData(entryId) {
    let data = _entryDataCache.get(entryId);
    if (!data) {
        const dataScript = document.getElementById(`entry-data-${entryId}`);
        if (!dataScript) return null;
        try {
            data = JSON.parse(dataScript.textContent);
            _entryDataCache.set(entryId, data);
        } catch (e) {
            console.error("Error al parsear datos del Pokémon", e);
            return null;
        }
    }
    return data;
}

export function applyCardForm(entryId, formIdx) {
    const data = getEntryData(entryId);
    if (!data || !data.forms || !data.forms.length) return;
    const form = data.forms[formIdx];
    if (!form) return;

    _cardFormIndex.set(entryId, formIdx);

    // 1. Imagen en la tarjeta
    const img = document.getElementById(`img-${entryId}`);
    if (img) {
        if (state.isShinydexMode) {
            if (state.currentSpriteStyle === 'retro' && form.sprite_retro_shiny) {
                img.src = form.sprite_retro_shiny;
                img.classList.add('pixel-art');
            } else {
                img.src = form.sprite_modern_shiny || form.sprite_retro_shiny || form.sprite_modern;
                img.classList.remove('pixel-art');
            }
        } else {
            if (state.currentSpriteStyle === 'retro' && form.sprite_retro) {
                img.src = form.sprite_retro;
                img.classList.add('pixel-art');
            } else {
                img.src = form.sprite_modern || form.sprite_retro;
                img.classList.remove('pixel-art');
            }
        }
        img.alt = form.display_name || form.name || data.name;
    }

    // 2. Tipos elementales en la tarjeta
    const cardTypes = document.getElementById(`card-types-${entryId}`);
    if (cardTypes) {
        cardTypes.innerHTML = '';
        const t1 = document.createElement('span');
        const pType = String(form.primary_type || '').toLowerCase();
        t1.className = `type-${pType} border border-slate-950 px-2 py-0.5 rounded text-[9px] font-black uppercase shadow-sm`;
        t1.textContent = form.primary_type_es;
        cardTypes.appendChild(t1);

        if (form.secondary_type && form.secondary_type_es) {
            const t2 = document.createElement('span');
            const sType = String(form.secondary_type || '').toLowerCase();
            t2.className = `type-${sType} border border-slate-950 px-2 py-0.5 rounded text-[9px] font-black uppercase shadow-sm`;
            t2.textContent = form.secondary_type_es;
            cardTypes.appendChild(t2);
        }
    }

    // 3. Nombre / indicador de forma en la tarjeta
    const cardName = document.getElementById(`card-name-${entryId}`);
    if (cardName) {
        cardName.textContent = form.display_name || form.name || data.name;
    }
}

export function cycleCardPokemonForm(entryId, direction) {
    const data = getEntryData(entryId);
    if (!data || !data.forms || data.forms.length <= 1) return;
    const curIdx = _cardFormIndex.get(entryId) || 0;
    const newIdx = (curIdx + direction + data.forms.length) % data.forms.length;
    applyCardForm(entryId, newIdx);

    // Si el modal está abierto con este mismo Pokémon, sincronizar también el modal
    if (state.activeModalEntryId === entryId) {
        applyModalForm(newIdx);
    }
}

export function renderModalObtaining(data, activeForm = null) {
    const isUnownWithForm = (data.name && data.name.toLowerCase() === 'unown') && activeForm && activeForm.locations;
    const obt = isUnownWithForm ? {
        type: activeForm.type || (data.obtaining ? data.obtaining.type : 'wild'),
        summary: activeForm.summary || (data.obtaining ? data.obtaining.summary : `Exclusivo de ${activeForm.chamber_name || 'su cámara'}.`),
        locations: activeForm.locations || (data.obtaining ? data.obtaining.locations : []),
        badge_label: activeForm.badge_label || (data.obtaining ? data.obtaining.badge_label : 'Salvaje'),
        badge_color: activeForm.badge_color || (data.obtaining ? data.obtaining.badge_color : 'emerald'),
        is_unique: activeForm.is_unique || (data.obtaining ? data.obtaining.is_unique : false),
    } : (data.obtaining || {});

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
                        data-stone-slug="${stone.slug}"
                        data-stone-name="${stone.name}"
                        class="btn-open-stone inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white hover:bg-amber-50 border-2 border-slate-950 text-slate-900 text-[10px] font-black uppercase shadow-[1.5px_1.5px_0px_0px_#0f172a] transition-transform active:translate-x-0.5 active:translate-y-0.5 shrink-0 self-start sm:self-auto cursor-pointer"
                        title="Ver dónde conseguir ${stone.name}"
                    >
                        <img src="${stone.icon_url}" alt="" class="w-3.5 h-3.5 object-contain">
                        <span>Dónde conseguirlo</span>
                    </button>
                `;
                const btnStone = evoBox.querySelector('.btn-open-stone');
                if (btnStone) {
                    btnStone.addEventListener('click', (e) => {
                        e.stopPropagation();
                        openStoneModal(stone.slug, stone.name);
                    });
                }
            } else {
                evoBox.className = 'text-xs bg-indigo-50 border-2 border-indigo-200 text-indigo-950 rounded-lg p-2.5 font-bold flex items-center gap-2 mb-2 shadow-sm';
                const evoIcon = (obt.evolution_info.trigger === 'trade') ? '/media/items/town-map.png' : '/media/items/rare-candy.png';
                evoBox.innerHTML = `<img src="${evoIcon}" alt="Evolución" class="w-4 h-4 object-contain inline-block shrink-0"> <span><strong>Evolución:</strong> ${evoText}</span>`;
            }
            detailsContainer.appendChild(evoBox);
        } else if (data.evolution_stone && !isUnownWithForm) {
            const stone = data.evolution_stone;
            const itemBox = document.createElement('div');
            const isIncense = stone.slug.includes('incense');
            const labelText = isIncense ? 'Incienso Requerido:' : 'Objeto Requerido:';
            itemBox.className = 'text-xs bg-amber-50/90 border-2 border-amber-300 text-amber-950 rounded-lg p-2.5 font-bold flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-2 shadow-sm';
            itemBox.innerHTML = `
                <div class="flex items-center gap-2">
                    <img src="${stone.icon_url}" alt="${stone.name}" class="w-5 h-5 object-contain inline-block shrink-0 drop-shadow-sm pixel-art">
                    <span><strong>${labelText}</strong> ${stone.name}</span>
                </div>
                <button 
                    type="button" 
                    data-stone-slug="${stone.slug}"
                    data-stone-name="${stone.name}"
                    class="btn-open-stone inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white hover:bg-amber-100 border-2 border-slate-950 text-slate-900 text-[10px] font-black uppercase shadow-[1.5px_1.5px_0px_0px_#0f172a] transition-transform active:translate-x-0.5 active:translate-y-0.5 shrink-0 self-start sm:self-auto cursor-pointer"
                    title="Ver dónde conseguir ${stone.name}"
                >
                    <img src="${stone.icon_url}" alt="" class="w-3.5 h-3.5 object-contain pixel-art">
                    <span>Dónde conseguirlo</span>
                </button>
            `;
            const btnStone = itemBox.querySelector('.btn-open-stone');
            if (btnStone) {
                btnStone.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openStoneModal(stone.slug, stone.name);
                });
            }
            detailsContainer.appendChild(itemBox);
        }

        if (obt.locations && obt.locations.length > 0) {
            if (obt.evolution_info || data.evolution_stone) {
                const wildTitle = document.createElement('div');
                wildTitle.className = 'text-[11px] font-bold text-slate-700 uppercase tracking-wide mb-1';
                wildTitle.textContent = (obt.type === 'breeding' || obt.type === 'gift') ? 'Lugares de obtención:' : ((obt.type === 'transfer') ? 'Método de transferencia:' : 'Lugares de captura / encuentro:');
                detailsContainer.appendChild(wildTitle);
            }

            const locList = document.createElement('div');
            locList.className = (obt.locations.length === 1) ? 'grid grid-cols-1 gap-1.5' : 'grid grid-cols-1 sm:grid-cols-2 gap-1.5';
            obt.locations.forEach(loc => {
                const item = document.createElement('div');
                const isBreedingOrEgg = loc.method && (loc.method.includes('Crianza') || loc.method.includes('Huevo'));
                const isTransfer = (obt.type === 'transfer') || (loc.area && loc.area.includes('Transferencia'));
                const locIcon = isBreedingOrEgg ? '/media/items/mystery-egg.png' : '/media/items/town-map.png';
                const cardBg = isBreedingOrEgg ? 'bg-pink-50/70 border-pink-200 text-pink-950' : (isTransfer ? 'bg-slate-100 border-slate-300 text-slate-800' : 'bg-slate-50 border-slate-300 text-slate-800');
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
}

export function applyModalForm(formIdx) {
    if (!state.activeModalEntryId) return;
    const data = getEntryData(state.activeModalEntryId);
    if (!data || !data.forms || !data.forms.length) return;
    const form = data.forms[formIdx];
    if (!form) return;

    activeModalFormIndex = formIdx;
    _cardFormIndex.set(state.activeModalEntryId, formIdx);

    // 1. Sprite en modal
    updateModalSpriteDisplay();

    // 2. Tipos en modal
    const typesContainer = document.getElementById('modal-types-container');
    if (typesContainer) {
        typesContainer.innerHTML = '';
        const badge1 = document.createElement('span');
        const pType = String(form.primary_type || '').toLowerCase();
        badge1.className = `type-${pType} border-2 border-slate-950 font-black text-xs sm:text-[13px] uppercase px-3.5 py-1 rounded-md shadow-[2px_2px_0px_0px_#0f172a] select-none pointer-events-none`;
        badge1.textContent = form.primary_type_es;
        typesContainer.appendChild(badge1);

        if (form.secondary_type && form.secondary_type_es) {
            const badge2 = document.createElement('span');
            const sType = String(form.secondary_type || '').toLowerCase();
            badge2.className = `type-${sType} border-2 border-slate-950 font-black text-xs sm:text-[13px] uppercase px-3.5 py-1 rounded-md shadow-[2px_2px_0px_0px_#0f172a] select-none pointer-events-none`;
            badge2.textContent = form.secondary_type_es;
            typesContainer.appendChild(badge2);
        }
    }

    // 3. Form badge en modal
    const formBadge = document.getElementById('modal-form-badge');
    if (formBadge) {
        formBadge.textContent = form.name;
        formBadge.classList.remove('hidden');
    }

    // 4. Ubicación específica si la forma define ubicaciones propias (Unown)
    renderModalObtaining(data, form);
}

export function cycleModalPokemonForm(direction) {
    if (!state.activeModalEntryId) return;
    const data = getEntryData(state.activeModalEntryId);
    if (!data || !data.forms || data.forms.length <= 1) return;
    const newIdx = (activeModalFormIndex + direction + data.forms.length) % data.forms.length;
    applyModalForm(newIdx);
    applyCardForm(state.activeModalEntryId, newIdx);
}

export function openPokemonModalDirect(entryId, options = {}) {
    const data = getEntryData(entryId);
    if (!data) return;

    state.activeModalEntryId = entryId;
    setActiveModalCryUrl(data.cry_url || '');
    isModalBackView = false;
    const modalCryBtn = document.getElementById('modal-cry-btn');
    if (modalCryBtn) {
        if (data.cry_url) {
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

    // 2 & 3. Sprite y Tipos (Soporte de Formas Alternas vs Carga Estándar)
    const hasForms = data.forms && data.forms.length > 1;
    const prevFormBtn = document.getElementById('modal-prev-form-btn');
    const nextFormBtn = document.getElementById('modal-next-form-btn');
    const formBadge = document.getElementById('modal-form-badge');

    if (hasForms) {
        if (prevFormBtn) prevFormBtn.classList.remove('hidden');
        if (nextFormBtn) nextFormBtn.classList.remove('hidden');
        let initialFormIdx = _cardFormIndex.get(entryId) || 0;
        if (options && options.selectedLetter) {
            const idx = data.forms.findIndex(f => f.form_key === options.selectedLetter);
            if (idx !== -1) {
                initialFormIdx = idx;
            }
        }
        applyModalForm(initialFormIdx);
        applyCardForm(entryId, initialFormIdx);
    } else {
        if (prevFormBtn) prevFormBtn.classList.add('hidden');
        if (nextFormBtn) nextFormBtn.classList.add('hidden');
        if (formBadge) formBadge.classList.add('hidden');

        updateModalSpriteDisplay();

        const typesContainer = document.getElementById('modal-types-container');
        if (typesContainer) {
            typesContainer.innerHTML = '';
            
            const badge1 = document.createElement('span');
            const pType = String(data.primary_type || '').toLowerCase();
            badge1.className = `type-${pType} border-2 border-slate-950 font-black text-xs sm:text-[13px] uppercase px-3.5 py-1 rounded-md shadow-[2px_2px_0px_0px_#0f172a] select-none pointer-events-none`;
            badge1.textContent = data.primary_type_es;
            typesContainer.appendChild(badge1);

            if (data.secondary_type && data.secondary_type_es) {
                const badge2 = document.createElement('span');
                const sType = String(data.secondary_type || '').toLowerCase();
                badge2.className = `type-${sType} border-2 border-slate-950 font-black text-xs sm:text-[13px] uppercase px-3.5 py-1 rounded-md shadow-[2px_2px_0px_0px_#0f172a] select-none pointer-events-none`;
                badge2.textContent = data.secondary_type_es;
                typesContainer.appendChild(badge2);
            }
        }

        // 5. Método de Obtención y Localización para especies sin formas
        renderModalObtaining(data, null);
    }

    // 4. Biometría (Altura y Peso)
    const heightEl = document.getElementById('modal-pokemon-height');
    const weightEl = document.getElementById('modal-pokemon-weight');
    if (heightEl) heightEl.textContent = data.height ? `${(data.height / 10).toFixed(1)} m` : '--';
    if (weightEl) weightEl.textContent = data.weight ? `${(data.weight / 10).toFixed(1)} kg` : '--';

    // 6. Estado de captura actual
    const card = document.getElementById(`card-${entryId}`);
    const isCaught = card ? (
        state.isShinydexMode ? (card.dataset.shinyCaught === 'true') : (card.dataset.caught === 'true')
    ) : false;
    updateModalCatchStatus(isCaught);

    // 7. Botones de retorno al Bloc Unown
    const isUnown = (data.name && data.name.toLowerCase() === 'unown') || (card && card.dataset.name === 'unown');
    const unownBtn = document.getElementById('modal-unowndex-btn');
    const unownHeaderBtn = document.getElementById('modal-unowndex-header-btn');
    const hasUnownModal = !!document.getElementById('unown-modal');

    if (unownBtn) {
        if (isUnown && hasUnownModal) {
            unownBtn.classList.remove('hidden');
            unownBtn.classList.add('flex');
        } else {
            unownBtn.classList.add('hidden');
            unownBtn.classList.remove('flex');
        }
    }
    if (unownHeaderBtn) {
        if (isUnown && hasUnownModal) {
            unownHeaderBtn.classList.remove('hidden');
            unownHeaderBtn.classList.add('flex');
        } else {
            unownHeaderBtn.classList.add('hidden');
            unownHeaderBtn.classList.remove('flex');
        }
    }

    // 8. Mostrar modal
    const modal = document.getElementById('comic-modal');
    const modalCard = document.getElementById('comic-modal-card');
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

    // 9. Activar marquesina suave en ubicaciones
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

    // 10. Actualizar botones de navegación anterior / siguiente
    updateModalNavButtons();
}

export function getModalNavigableCards() {
    const allCards = Array.from(document.querySelectorAll('.pokemon-card'));
    const visibleCards = allCards.filter(card => card.style.display !== 'none');
    return visibleCards.length > 0 ? visibleCards : allCards;
}

export function updateModalNavButtons() {
    if (!state.activeModalEntryId) return;
    const cards = getModalNavigableCards();
    if (!cards.length) return;

    const currentIndex = cards.findIndex(card => parseInt(card.dataset.entryId, 10) === state.activeModalEntryId);

    const hasPrev = currentIndex > 0;
    const hasNext = currentIndex >= 0 && currentIndex < cards.length - 1;

    const prevBtn = document.getElementById('modal-prev-pokemon-btn');
    const nextBtn = document.getElementById('modal-next-pokemon-btn');

    if (prevBtn) {
        prevBtn.disabled = !hasPrev;
        prevBtn.style.opacity = hasPrev ? '1' : '0.25';
        prevBtn.style.pointerEvents = hasPrev ? 'auto' : 'none';
    }

    if (nextBtn) {
        nextBtn.disabled = !hasNext;
        nextBtn.style.opacity = hasNext ? '1' : '0.25';
        nextBtn.style.pointerEvents = hasNext ? 'auto' : 'none';
    }
}

export function navigatePokemonModal(direction) {
    if (!state.activeModalEntryId) return;
    const cards = getModalNavigableCards();
    if (!cards.length) return;

    const currentIndex = cards.findIndex(card => parseInt(card.dataset.entryId, 10) === state.activeModalEntryId);
    if (currentIndex === -1) return;

    const targetIndex = currentIndex + direction;
    if (targetIndex >= 0 && targetIndex < cards.length) {
        const targetCard = cards[targetIndex];
        const nextEntryId = parseInt(targetCard.dataset.entryId, 10);
        openPokemonModalDirect(nextEntryId);
        const slug = targetCard.dataset.name || String(targetCard.dataset.number);
        setModalUrlHash(slug, true);
    }
}

export function closePokemonModal(syncUrl = true) {
    const modal = document.getElementById('comic-modal');
    const modalCard = document.getElementById('comic-modal-card');
    if (modal) {
        modal.classList.remove('backdrop-blur-sm', 'opacity-100', 'pointer-events-auto');
        modal.classList.add('hidden', 'opacity-0', 'pointer-events-none');
        modal.style.display = 'none';
    }
    const modalImg = document.getElementById('modal-pokemon-img');
    if (modalImg) modalImg.src = '';
    const detailsContainer = document.getElementById('modal-obtaining-details');
    if (detailsContainer) detailsContainer.innerHTML = '';
    if (modalCard) {
        modalCard.classList.remove('scale-100');
        modalCard.classList.add('scale-95');
    }
    const unownBtn = document.getElementById('modal-unowndex-btn');
    const unownHeaderBtn = document.getElementById('modal-unowndex-header-btn');
    if (unownBtn) {
        unownBtn.classList.add('hidden');
        unownBtn.classList.remove('flex');
    }
    if (unownHeaderBtn) {
        unownHeaderBtn.classList.add('hidden');
        unownHeaderBtn.classList.remove('flex');
    }
    releaseScrollIfNoModalOpen();
    state.activeModalEntryId = null;
    if (syncUrl) syncUrlToCurrentOpenModal();
}

export function handleModalBackdropClick(e) {
    if (e.target.id === 'comic-modal' || e.target.id === 'comic-modal-wrapper') {
        closePokemonModal();
    }
}

export function updateModalCatchStatus(isCaught) {
    const badge = document.getElementById('modal-status-badge');
    const btn = document.getElementById('modal-toggle-catch-btn');
    const text = document.getElementById('modal-toggle-text');

    if (badge && btn && text) {
        if (isCaught) {
            badge.className = state.isShinydexMode
                ? 'px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider border-2 border-slate-950 bg-amber-400 text-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a]'
                : 'px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider border-2 border-slate-950 bg-emerald-400 text-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a]';
            badge.textContent = state.isShinydexMode ? '★ Variocolor atrapado' : '✓ Atrapado en tu partida';
            btn.className = 'py-1.5 px-4 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] bg-rose-500 hover:bg-rose-600 text-white transition-all active:translate-x-0.5 active:translate-y-0.5 flex items-center gap-1.5';
            text.textContent = 'Liberar';
        } else {
            badge.className = 'px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider border-2 border-slate-950 bg-slate-200 text-slate-700 shadow-[1.5px_1.5px_0px_0px_#0f172a]';
            badge.textContent = state.isShinydexMode ? 'Variocolor pendiente' : 'Pendiente de capturar';
            btn.className = 'py-1.5 px-4 rounded-lg text-xs font-black uppercase tracking-wider border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] bg-emerald-500 hover:bg-emerald-600 text-white transition-all active:translate-x-0.5 active:translate-y-0.5 flex items-center gap-1.5';
            text.textContent = 'Capturar';
        }
    }
}

export async function modalToggleCatch() {
    if (state.activeModalEntryId) {
        await toggleCatch(state.activeModalEntryId);
    }
}
