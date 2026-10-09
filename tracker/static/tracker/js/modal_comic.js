/**
 * Pokédex Global - Modal Estilo Cómic del Pokémon (modal_comic.js)
 * Visualización de biometría, textos de Pokédex, sprites con rotación y formas alternas.
 */

import { state } from './state.js';
import { setActiveModalCryUrl } from './audio.js';
import { setModalUrlHash, syncUrlToCurrentOpenModal, releaseScrollIfNoModalOpen, lockModalScroll } from './url_sync.js';
import { openStoneModal } from './modal_stones.js';
import { openUnownModal } from './modal_unown.js';
import { toggleCatch } from './cards.js';

const _entryDataCache = new Map();
const _cardFormIndex = new Map();
let activeModalFormIndex = 0;
let isModalBackView = false;
let activeModalGender = 'male';

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
    if (updateHistory) {
        let slug = null;
        if (card) {
            slug = card.dataset.name || String(card.dataset.number);
        } else {
            const data = getEntryData(entryId);
            if (data) {
                slug = (data.name ? data.name.toLowerCase().replace(/[^a-z0-9]/g, '') : '') || String(data.number);
            }
        }
        if (slug) {
            setModalUrlHash(slug);
        }
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
    const form = (hasForms && data.forms) ? (data.forms[activeModalFormIndex] || data.forms[0]) : null;
    let targetSrc = '';

    if (hasForms && form) {
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
        const isFemale = (activeModalGender === 'female');
        const femaleSprites = (isFemale && data.gender_info && data.gender_info.female_sprites) ? data.gender_info.female_sprites : null;

        if (isModalBackView) {
            if (state.isShinydexMode) {
                targetSrc = (femaleSprites && femaleSprites.retro_shiny_back) || data.sprite_retro_shiny_back || data.sprite_retro_shiny;
            } else {
                targetSrc = (femaleSprites && femaleSprites.retro_back) || data.sprite_retro_back || data.sprite_retro;
            }
        } else {
            if (state.isShinydexMode) {
                if (state.currentSpriteStyle === 'retro' && ((femaleSprites && femaleSprites.retro_shiny) || data.sprite_retro_shiny)) {
                    targetSrc = (femaleSprites && femaleSprites.retro_shiny) || data.sprite_retro_shiny;
                } else {
                    targetSrc = (femaleSprites && femaleSprites.modern_shiny) || (femaleSprites && femaleSprites.retro_shiny) || data.sprite_modern_shiny || data.sprite_retro_shiny || data.sprite_modern;
                }
            } else {
                if (state.currentSpriteStyle === 'retro' && ((femaleSprites && femaleSprites.retro) || data.sprite_retro)) {
                    targetSrc = (femaleSprites && femaleSprites.retro) || data.sprite_retro;
                } else {
                    targetSrc = (femaleSprites && femaleSprites.modern) || (femaleSprites && femaleSprites.retro) || data.sprite_modern;
                }
            }
        }
        const genderText = isFemale ? 'Hembra' : 'Macho';
        modalImg.alt = `${data.name} (${genderText}, ${isModalBackView ? 'Espalda' : 'Frente'})`;
    }

    if (targetSrc) {
        modalImg.onerror = () => {
            modalImg.onerror = null;
            const isFemale = (activeModalGender === 'female');
            const femaleSprites = (isFemale && data.gender_info && data.gender_info.female_sprites) ? data.gender_info.female_sprites : null;
            const fallback = (hasForms && form)
                ? (form.sprite_retro || form.sprite_modern)
                : ((femaleSprites && femaleSprites.retro) || data.sprite_modern || data.sprite_retro);
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

const GENDER_ICON_MALE_SVG = `<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9.5" cy="14.5" r="5.5"></circle><path d="M13.5 10.5L20 4M14.5 4H20v5.5"></path></svg>`;
const GENDER_ICON_FEMALE_SVG = `<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="9" r="5.5"></circle><path d="M12 14.5V21M8.5 18h7"></path></svg>`;

export function renderModalGender(data) {
    const container = document.getElementById('modal-gender-container');
    const btn = document.getElementById('modal-gender-btn');
    const icon = document.getElementById('modal-gender-icon');
    const label = document.getElementById('modal-gender-label');
    const notice = document.getElementById('modal-gender-notice');
    if (!container || !btn || !icon || !label || !notice) return;

    const gInfo = data ? data.gender_info : null;
    if (!gInfo || gInfo.gender_type === 'genderless') {
        container.classList.add('hidden');
        return;
    }

    container.classList.remove('hidden');

    if (gInfo.gender_type === 'female_only') {
        activeModalGender = 'female';
        btn.className = 'w-7 h-7 rounded-lg border-[1.5px] border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex items-center justify-center select-none cursor-default bg-pink-300 text-pink-950 pointer-events-none shrink-0';
        btn.title = 'Solo hembra';
        btn.setAttribute('aria-label', 'Solo hembra');
        icon.innerHTML = GENDER_ICON_FEMALE_SVG;
        label.textContent = 'Hembra';
        notice.className = 'absolute top-[calc(100%+4px)] right-0 text-[8px] sm:text-[8.5px] font-black tracking-wider uppercase text-pink-950 bg-pink-100/95 px-1.5 py-0.5 rounded border border-slate-950 shadow-[1px_1px_0px_0px_#0f172a] whitespace-nowrap select-none pointer-events-none z-30';
        notice.classList.remove('hidden');
        notice.textContent = 'Solo hembra';
        return;
    }

    if (gInfo.gender_type === 'male_only') {
        activeModalGender = 'male';
        btn.className = 'w-7 h-7 rounded-lg border-[1.5px] border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex items-center justify-center select-none cursor-default bg-sky-200 text-sky-950 pointer-events-none shrink-0';
        btn.title = 'Solo macho';
        btn.setAttribute('aria-label', 'Solo macho');
        icon.innerHTML = GENDER_ICON_MALE_SVG;
        label.textContent = 'Macho';
        notice.className = 'absolute top-[calc(100%+4px)] right-0 text-[8px] sm:text-[8.5px] font-black tracking-wider uppercase text-sky-950 bg-sky-100/95 px-1.5 py-0.5 rounded border border-slate-950 shadow-[1px_1px_0px_0px_#0f172a] whitespace-nowrap select-none pointer-events-none z-30';
        notice.classList.remove('hidden');
        notice.textContent = 'Solo macho';
        return;
    }

    // Especies con ambos géneros (con o sin diferencias visuales)
    activeModalGender = 'male';
    btn.className = 'w-7 h-7 rounded-lg border-[1.5px] border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex items-center justify-center transition-all select-none cursor-pointer bg-sky-200 text-sky-950 hover:bg-sky-300 active:translate-x-0.5 active:translate-y-0.5 shrink-0';
    btn.title = 'Cambiar género (Macho)';
    btn.setAttribute('aria-label', 'Cambiar género');
    icon.innerHTML = GENDER_ICON_MALE_SVG;
    label.textContent = 'Macho';
    notice.classList.add('hidden');
}

export function toggleModalGender() {
    if (!state.activeModalEntryId) return;
    const data = getEntryData(state.activeModalEntryId);
    if (!data || !data.gender_info || !data.gender_info.can_toggle) return;

    activeModalGender = (activeModalGender === 'male') ? 'female' : 'male';

    const btn = document.getElementById('modal-gender-btn');
    const icon = document.getElementById('modal-gender-icon');
    const label = document.getElementById('modal-gender-label');
    const notice = document.getElementById('modal-gender-notice');

    if (activeModalGender === 'female') {
        if (btn) {
            btn.className = 'w-7 h-7 rounded-lg border-[1.5px] border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex items-center justify-center transition-all select-none cursor-pointer bg-pink-300 text-pink-950 hover:bg-pink-400 active:translate-x-0.5 active:translate-y-0.5 shrink-0';
            btn.title = 'Cambiar género (Hembra)';
            btn.setAttribute('aria-label', 'Cambiar género');
        }
        if (icon) icon.innerHTML = GENDER_ICON_FEMALE_SVG;
        if (label) label.textContent = 'Hembra';
        if (notice) {
            if (!data.gender_info.has_visual_differences) {
                notice.className = 'absolute top-[calc(100%+4px)] right-0 text-[8px] sm:text-[8.5px] font-black tracking-wider uppercase text-slate-800 bg-white/95 px-1.5 py-0.5 rounded border border-slate-950 shadow-[1px_1px_0px_0px_#0f172a] whitespace-nowrap select-none pointer-events-none z-30';
                notice.classList.remove('hidden');
                notice.textContent = 'Sin cambios';
            } else {
                notice.classList.add('hidden');
            }
        }
    } else {
        if (btn) {
            btn.className = 'w-7 h-7 rounded-lg border-[1.5px] border-slate-950 shadow-[1.5px_1.5px_0px_0px_#0f172a] flex items-center justify-center transition-all select-none cursor-pointer bg-sky-200 text-sky-950 hover:bg-sky-300 active:translate-x-0.5 active:translate-y-0.5 shrink-0';
            btn.title = 'Cambiar género (Macho)';
            btn.setAttribute('aria-label', 'Cambiar género');
        }
        if (icon) icon.innerHTML = GENDER_ICON_MALE_SVG;
        if (label) label.textContent = 'Macho';
        if (notice) notice.classList.add('hidden');
    }

    updateModalSpriteDisplay();
}
window.toggleModalGender = toggleModalGender;

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

    // 3. Nombre en la tarjeta: siempre se mantiene el nombre normal de la especie
    const cardName = document.getElementById(`card-name-${entryId}`);
    if (cardName) {
        cardName.textContent = data.name;
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

export function getObtainingCtaHtml(isOpen) {
    const label = isOpen ? 'Ocultar detalles' : 'Ver detalles';
    const chevronClass = isOpen ? 'rotate-180' : '';
    return `<span id="modal-obtaining-cta" class="inline-flex items-center gap-1.5 whitespace-nowrap text-[10px] sm:text-xs font-black text-slate-950 bg-emerald-400 hover:bg-emerald-300 active:translate-y-0.5 border-2 border-slate-950 rounded px-2.5 py-0.5 shadow-[1.5px_1.5px_0px_0px_#0f172a] select-none transition-all cursor-pointer"><span class="cta-label">${label}</span><svg class="cta-icon w-3.5 h-3.5 text-slate-950 transform transition-transform duration-200 ${chevronClass}" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" /></svg></span>`;
}

export function renderModalObtaining(data, activeForm = null) {
    const isUnownWithForm = (data.name && data.name.toLowerCase() === 'unown') && activeForm && activeForm.locations;
    const hasFormObtaining = Boolean(activeForm && (activeForm.locations || activeForm.summary));

    let obt;
    if (isUnownWithForm) {
        obt = {
            type: activeForm.type || (data.obtaining ? data.obtaining.type : 'wild'),
            summary: activeForm.summary || (data.obtaining ? data.obtaining.summary : `Exclusivo de ${activeForm.chamber_name || 'su cámara'}.`),
            locations: activeForm.locations || (data.obtaining ? data.obtaining.locations : []),
            badge_label: activeForm.badge_label || (data.obtaining ? data.obtaining.badge_label : 'Salvaje'),
            badge_color: activeForm.badge_color || (data.obtaining ? data.obtaining.badge_color : 'emerald'),
            is_unique: activeForm.is_unique || (data.obtaining ? data.obtaining.is_unique : false),
        };
    } else if (hasFormObtaining) {
        obt = {
            type: activeForm.type || (data.obtaining ? data.obtaining.type : 'wild'),
            summary: activeForm.summary || (data.obtaining ? data.obtaining.summary : ''),
            locations: activeForm.locations || (data.obtaining ? data.obtaining.locations : []),
            badge_label: activeForm.badge_label || (data.obtaining ? data.obtaining.badge_label : 'Salvaje'),
            badge_color: activeForm.badge_color || (data.obtaining ? data.obtaining.badge_color : 'emerald'),
            is_unique: activeForm.is_unique || (data.obtaining ? data.obtaining.is_unique : false),
        };
    } else {
        obt = data.obtaining || {};
    }

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
    const ctaContainer = document.getElementById('modal-obtaining-cta-container');
    const detailsContainer = document.getElementById('modal-obtaining-details');
    const isDetailsOpen = Boolean(detailsContainer && !detailsContainer.classList.contains('hidden'));

    if (summaryEl) {
        const hasDetails = (obt.locations && obt.locations.length > 0) || Boolean(obt.evolution_info) || Boolean(data.evolution_stone) || Boolean(obt.historical_note);

        if (obt.locations && obt.locations.length > 2) {
            const loc1 = obt.locations[0].area;
            const loc2 = obt.locations[1].area;
            const remCount = obt.locations.length - 2;
            const typeLabel = (obt.type === 'wild') ? 'Salvaje' : ((obt.type === 'fishing') ? 'Pesca' : ((obt.type === 'transfer') ? 'Transferencia' : 'Disponible'));
            summaryEl.innerHTML = `${typeLabel} en <span class="text-slate-950 font-black">${loc1}</span>, <span class="text-slate-950 font-black">${loc2}</span> y <span class="text-emerald-700 font-black underline decoration-emerald-400 underline-offset-2">${remCount} ${remCount === 1 ? 'zona más' : 'zonas más'}</span>.`;
        } else if (obt.locations && obt.locations.length === 2) {
            const loc1 = obt.locations[0].area;
            const loc2 = obt.locations[1].area;
            const typeLabel = (obt.type === 'wild') ? 'Salvaje' : ((obt.type === 'fishing') ? 'Pesca' : ((obt.type === 'transfer') ? 'Transferencia' : 'Disponible'));
            summaryEl.innerHTML = `${typeLabel} en <span class="text-slate-950 font-black">${loc1}</span> y <span class="text-slate-950 font-black">${loc2}</span>.`;
        } else if (obt.locations && obt.locations.length === 1) {
            const loc1 = obt.locations[0].area;
            const typeLabel = (obt.type === 'wild') ? 'Salvaje' : ((obt.type === 'fishing') ? 'Pesca' : ((obt.type === 'transfer') ? 'Transferencia' : 'Disponible'));
            const textBase = obt.summary ? obt.summary : `${typeLabel} en <span class="text-slate-950 font-black">${loc1}</span>.`;
            summaryEl.innerHTML = `${textBase}`;
        } else if (obt.evolution_info) {
            const evoFrom = obt.evolution_info.from;
            summaryEl.innerHTML = `Evoluciona de <span class="text-slate-950 font-black">${evoFrom}</span>.`;
        } else {
            summaryEl.innerHTML = `${obt.summary || 'Sin información de obtención registrada.'}`;
        }

        if (ctaContainer) {
            ctaContainer.innerHTML = hasDetails ? getObtainingCtaHtml(isDetailsOpen) : '';
        }
    }

    // Lista detallada de ubicaciones y/o evolución
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
                const evoIcon = (obt.evolution_info.trigger === 'trade') ? '/media/items/linking-cord.png' : '/media/items/rare-candy.png';
                evoBox.innerHTML = `<img src="${evoIcon}" alt="Evolución" class="w-4 h-4 object-contain pixel-art inline-block shrink-0"> <span><strong>Evolución:</strong> ${evoText}</span>`;
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
            locList.className = (obt.locations.length === 1) ? 'grid grid-cols-1 gap-2' : 'grid grid-cols-1 sm:grid-cols-2 gap-2';
            obt.locations.forEach(loc => {
                const item = document.createElement('div');
                const isBreedingOrEgg = loc.method && (loc.method.includes('Crianza') || loc.method.includes('Huevo'));
                const isTransfer = (obt.type === 'transfer') || (loc.area && loc.area.includes('Transferencia'));
                const isDualSlot = loc.method && (loc.method.includes('Inserción Dual') || loc.method.includes('slot2-'));
                const isSwarm = loc.method && (loc.method.toLowerCase().includes('manada') || loc.method.toLowerCase().includes('swarm'));
                const isAlteringCave = loc.area && (loc.area.includes('Cueva Cambiante') || loc.area.toLowerCase().includes('altering-cave'));
                const isAlteringCaveInactive = isAlteringCave && (parseInt(data.number, 10) !== 41);

                const locIcon = isBreedingOrEgg 
                    ? '/media/items/mystery-egg.png' 
                    : (isDualSlot ? '/media/items/up-grade.png' : (isTransfer ? '/media/items/linking-cord.png' : '/media/items/town-map.png'));

                const cardBg = isAlteringCaveInactive 
                    ? 'bg-amber-50/90 border-amber-300 text-amber-950' 
                    : (isBreedingOrEgg 
                        ? 'bg-pink-50/70 border-pink-200 text-pink-950' 
                        : (isDualSlot 
                            ? 'bg-violet-50/90 border-violet-300 text-violet-950' 
                            : (isSwarm
                                ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
                                : (isTransfer ? 'bg-indigo-50/80 border-indigo-200 text-indigo-950' : 'bg-slate-50 border-slate-300 text-slate-800'))));
                
                let methodLabel = isAlteringCaveInactive ? 'e-Reader inactivo' : loc.method;
                if (isDualSlot && !isAlteringCaveInactive) {
                    if (loc.method.includes('Cualquier GBA') || (loc.method.match(/Inserción Dual/g) || []).length >= 4) {
                        methodLabel = 'Cualquier GBA';
                    } else if (loc.method.includes('GBA:')) {
                        const carts = [];
                        loc.method.split(',').forEach(part => {
                            if (part.includes('GBA:')) {
                                const c = part.split('GBA:')[1].replace('Pokémon', '').replace(')', '').trim();
                                if (c && !carts.includes(c)) carts.push(c);
                            }
                        });
                        if (carts.length >= 4) {
                            methodLabel = 'Cualquier GBA';
                        } else if (carts.length > 0) {
                            methodLabel = `GBA: ${carts.join(' / ')}`;
                        } else {
                            methodLabel = 'Inserción Dual';
                        }
                    }
                }
                const methodClass = isAlteringCaveInactive 
                    ? 'text-[10px] text-amber-800 font-bold' 
                    : (isDualSlot 
                        ? 'text-[10px] text-violet-700 font-bold' 
                        : (isSwarm
                            ? 'text-[10px] text-emerald-700 font-bold'
                            : (isBreedingOrEgg
                                ? 'text-[10px] text-pink-800/90 font-semibold'
                                : (isTransfer
                                    ? 'text-[10px] text-indigo-800/90 font-semibold'
                                    : 'text-[10px] text-slate-500 font-semibold'))));

                item.className = `flex items-center gap-3 px-3 py-2.5 border rounded-xl overflow-hidden min-h-[52px] shadow-[1px_1px_0px_0px_#0f172a] ${cardBg}`;
                item.title = isAlteringCaveInactive 
                    ? `${loc.area} (Evento e-Reader inactivo: imposible de encontrar in-game, solo Zubat aparece)` 
                    : `${loc.area} (${loc.method})`;
                item.innerHTML = `
                    <div class="w-7 h-7 flex items-center justify-center shrink-0">
                        <img src="${locIcon}" alt="" class="w-7 h-7 object-contain pixel-art drop-shadow-sm">
                    </div>
                    <div class="min-w-0 flex-1 space-y-0.5 text-left">
                        <div class="location-marquee-wrapper overflow-hidden whitespace-nowrap min-w-0 w-full relative">
                            <span class="location-marquee-text inline-block whitespace-nowrap font-black text-xs uppercase tracking-tight text-slate-900">${loc.area}</span>
                        </div>
                        <div class="${methodClass} truncate leading-tight" title="${methodLabel}">
                            ${methodLabel}
                        </div>
                    </div>
                `;
                locList.appendChild(item);
            });
            detailsContainer.appendChild(locList);

            // Nota explicativa histórica sobre Cueva Cambiante (evento e-Reader inactivo salvo para Zubat #41)
            const natNum = parseInt(data.number, 10);
            const hasAlteringCaveInactive = obt.locations.some(loc => 
                loc.area && (loc.area.includes('Cueva Cambiante') || loc.area.toLowerCase().includes('altering-cave'))
            ) && natNum !== 41;

            if (hasAlteringCaveInactive) {
                const caveNote = document.createElement('div');
                caveNote.className = 'mt-2 border-2 border-slate-950 rounded-xl overflow-hidden shadow-[2px_2px_0px_0px_#0f172a] bg-amber-50';
                caveNote.innerHTML = `
                    <button 
                        type="button" 
                        class="w-full px-3 py-2 bg-amber-100/90 hover:bg-amber-100 text-amber-950 flex items-center justify-between gap-2 text-left cursor-pointer select-none transition-colors"
                        onclick="toggleComicCaveAccordion(this)"
                        aria-expanded="false"
                    >
                        <div class="flex items-center gap-2 min-w-0">
                            <img src="/media/items/card-key.png" alt="Cueva Cambiante" class="w-4.5 h-4.5 object-contain pixel-art shrink-0 drop-shadow-sm">
                            <span class="font-black uppercase text-[10px] sm:text-xs text-amber-900 tracking-wide">
                                Nota Histórica • Cueva Cambiante
                            </span>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0">
                            <span class="text-[10px] font-black uppercase text-amber-900/80 label-text">Ver nota</span>
                            <svg class="w-4 h-4 text-slate-950 transform transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </div>
                    </button>
                    <div class="hidden p-3 border-t-2 border-slate-950 text-[11px] leading-relaxed font-semibold text-slate-800 bg-amber-50/70">
                        Aunque esta especie figura en los datos internos de la Cueva Cambiante, su aparición salvaje dependía de un evento especial con tarjetas del periférico <strong>Nintendo e-Reader (Mystery Event)</strong> que jamás llegó a distribuirse comercialmente en ningún lugar del mundo. Por ello, en el cartucho original únicamente aparece <strong>Zubat</strong> (con un ratio del 100%), siendo imposible encontrar a este Pokémon aquí en estado salvaje sin dicho periférico.
                    </div>
                `;
                detailsContainer.appendChild(caveNote);
            }

            // Nota explicativa de mecánica: Inserción Dual (Ranura 2 de GBA en Nintendo DS)
            const dualSlotLocs = obt.locations.filter(loc => loc.method && (loc.method.includes('Inserción Dual') || loc.method.includes('slot2-')));
            if (dualSlotLocs.length > 0) {
                // Extraer cartuchos únicos requeridos
                const cartridgesSet = new Set();
                let hasAnyGba = false;
                dualSlotLocs.forEach(loc => {
                    const m = loc.method || '';
                    if (m.includes('Cualquier GBA') || (m.match(/Inserción Dual/g) || []).length >= 4) {
                        hasAnyGba = true;
                    } else {
                        m.split(',').forEach(part => {
                            part = part.trim();
                            if (part.includes('GBA:')) {
                                const cName = part.split('GBA:')[1].replace(')', '').trim();
                                cartridgesSet.add(cName);
                            } else if (part.includes('Inserción Dual')) {
                                cartridgesSet.add('Cartucho de GBA compatible');
                            }
                        });
                    }
                });
                const cartridgesList = Array.from(cartridgesSet);
                if (cartridgesList.length >= 4) hasAnyGba = true;
                const isSingleCart = !hasAnyGba && cartridgesList.length === 1 && !cartridgesList[0].includes('compatible');
                const cartSummary = hasAnyGba
                    ? `Cartuchos de GBA compatibles: <strong>Cualquier cartucho de Game Boy Advance</strong> (Rubí, Zafiro, Esmeralda, Rojo Fuego o Verde Hoja).`
                    : (isSingleCart 
                        ? `Cartucho de Game Boy Advance requerido: <strong>${cartridgesList[0]}</strong>.` 
                        : (cartridgesList.length > 1 
                            ? `Cartuchos de GBA compatibles (cualquiera de ellos): <strong>${cartridgesList.join(', ')}</strong>.`
                            : `Requiere insertar un <strong>cartucho de GBA compatible</strong> (Rubí, Zafiro, Esmeralda, Rojo Fuego o Verde Hoja).`));

                const dualAccordion = document.createElement('div');
                dualAccordion.className = 'mt-2 border-2 border-slate-950 rounded-xl overflow-hidden shadow-[2px_2px_0px_0px_#0f172a] bg-violet-50';
                dualAccordion.innerHTML = `
                    <button 
                        type="button" 
                        class="w-full px-3 py-2 bg-violet-100/90 hover:bg-violet-100 text-violet-950 flex items-center justify-between gap-2 text-left cursor-pointer select-none transition-colors"
                        onclick="toggleComicCaveAccordion(this)"
                        aria-expanded="false"
                    >
                        <div class="flex items-center gap-2 min-w-0">
                            <img src="/media/items/up-grade.png" alt="Inserción Dual" class="w-4.5 h-4.5 object-contain pixel-art shrink-0 drop-shadow-sm">
                            <span class="font-black uppercase text-[10px] sm:text-xs text-violet-900 tracking-wide truncate">
                                Mecánica • Inserción Dual (Ranura 2 de NDS)
                            </span>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0">
                            <span class="text-[10px] font-black uppercase text-violet-900/80 label-text">Ver nota</span>
                            <svg class="w-4 h-4 text-slate-950 transform transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </div>
                    </button>
                    <div class="hidden p-3 border-t-2 border-slate-950 text-[11px] leading-relaxed font-semibold text-slate-800 bg-violet-50/70">
                        <p class="mb-1.5">
                            Esta especie aparece en estado salvaje en Sinnoh mediante la función de <strong>Inserción Dual</strong>. Para activar estos encuentros, debes insertar el cartucho físico de Game Boy Advance en la <strong>Ranura 2 (Slot 2)</strong> de una consola Nintendo DS / Nintendo DS Lite antes de encender tu partida.
                        </p>
                        <p class="text-violet-950 font-bold">
                            🎮 ${cartSummary}
                        </p>
                        <p class="mt-1.5 text-[10px] text-slate-600 font-medium italic">
                            * Si no dispones del cartucho físico o juegas en hardware sin Ranura 2 (DSi, 3DS o emulación), este Pokémon puede conseguirse transfiriéndolo desde el Parque Compi o mediante intercambio directo con Pokémon Platino o HeartGold / SoulSilver.
                        </p>
                    </div>
                `;
                detailsContainer.appendChild(dualAccordion);
            }

            // Nota explicativa de mecánica: Manadas Pokémon Diarias (Brotes)
            const swarmLocs = obt.locations.filter(loc => loc.method && (loc.method.toLowerCase().includes('manada') || loc.method.toLowerCase().includes('swarm')));
            if (swarmLocs.length > 0) {
                // Comprobar si es exclusivamente salvaje por manada (sin contar guardería / crianza)
                const otherWildLocs = obt.locations.filter(loc => {
                    const m = (loc.method || '').toLowerCase();
                    const a = (loc.area || '').toLowerCase();
                    return !m.includes('manada') && !m.includes('swarm') && !m.includes('crianza') && !a.includes('guardería') && !a.includes('guarderia');
                });
                const isExclusiveWild = otherWildLocs.length === 0;

                const introText = isExclusiveWild
                    ? `Esta especie aparece en estado salvaje exclusivamente durante eventos de <strong>Manada Pokémon diaria</strong> tras obtener la Pokédex Nacional.`
                    : `Esta especie aparece con una alta frecuencia especial durante eventos de <strong>Manada Pokémon diaria</strong> tras obtener la Pokédex Nacional.`;

                const swarmAccordion = document.createElement('div');
                swarmAccordion.className = 'mt-2 border-2 border-slate-950 rounded-xl overflow-hidden shadow-[2px_2px_0px_0px_#0f172a] bg-emerald-50';
                swarmAccordion.innerHTML = `
                    <button 
                        type="button" 
                        class="w-full px-3 py-2 bg-emerald-100/90 hover:bg-emerald-100 text-emerald-950 flex items-center justify-between gap-2 text-left cursor-pointer select-none transition-colors"
                        onclick="toggleComicCaveAccordion(this)"
                        aria-expanded="false"
                    >
                        <div class="flex items-center gap-2 min-w-0">
                            <img src="/media/items/town-map.png" alt="Manada Pokémon" class="w-4.5 h-4.5 object-contain pixel-art shrink-0 drop-shadow-sm">
                            <span class="font-black uppercase text-[10px] sm:text-xs text-emerald-900 tracking-wide truncate">
                                Mecánica • Manada Pokémon Diaria
                            </span>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0">
                            <span class="text-[10px] font-black uppercase text-emerald-900/80 label-text">Ver nota</span>
                            <svg class="w-4 h-4 text-slate-950 transform transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </div>
                    </button>
                    <div class="hidden p-3 border-t-2 border-slate-950 text-[11px] leading-relaxed font-semibold text-slate-800 bg-emerald-50/70">
                        <p class="mb-1.5">
                            ${introText}
                        </p>
                        <p class="text-emerald-950 font-bold">
                            📺 ¿Cómo funciona la mecánica?
                        </p>
                        <p class="mt-1 text-[10px] text-slate-700">
                            Visita diariamente Pueblo Arena y habla con la hermana pequeña de Maya / León en su casa, o sintoniza los boletines informativos de la televisión. Te anunciará qué ruta concreta está siendo visitada hoy por una manada, donde este Pokémon aparecerá con una alta tasa de encuentro (~40%). La especie de la manada cambia cada día a medianoche.
                        </p>
                    </div>
                `;
                detailsContainer.appendChild(swarmAccordion);
            }
        }


        // Nota histórica personalizada (ej: Flauta Azur y Sala del Origen para Arceus)
        if (obt.historical_note) {
            const noteData = obt.historical_note;
            const histNote = document.createElement('div');
            histNote.className = 'mt-2 border-2 border-slate-950 rounded-xl overflow-hidden shadow-[2px_2px_0px_0px_#0f172a] bg-amber-50';
            histNote.innerHTML = `
                <button 
                    type="button" 
                    class="w-full px-3 py-2 bg-amber-100/90 hover:bg-amber-100 text-amber-950 flex items-center justify-between gap-2 text-left cursor-pointer select-none transition-colors"
                    onclick="toggleComicCaveAccordion(this)"
                    aria-expanded="false"
                >
                    <div class="flex items-center gap-2 min-w-0">
                        <img src="${noteData.icon_url || '/media/items/card-key.png'}" alt="" class="w-4.5 h-4.5 object-contain pixel-art shrink-0 drop-shadow-sm">
                        <span class="font-black uppercase text-[10px] sm:text-xs text-amber-900 tracking-wide">
                            ${noteData.title || 'Nota Histórica'}
                        </span>
                    </div>
                    <div class="flex items-center gap-1.5 shrink-0">
                        <span class="text-[10px] font-black uppercase text-amber-900/80 label-text">Ver nota</span>
                        <svg class="w-4 h-4 text-slate-950 transform transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </div>
                </button>
                <div class="hidden p-3 border-t-2 border-slate-950 text-[11px] leading-relaxed font-semibold text-slate-800 bg-amber-50/70">
                    ${noteData.text}
                </div>
            `;
            detailsContainer.appendChild(histNote);
        }
    }
}

export function initObtainingMarquees() {
    requestAnimationFrame(() => {
        document.querySelectorAll('#modal-obtaining-details .location-marquee-wrapper').forEach(wrapper => {
            const textSpan = wrapper.querySelector('.location-marquee-text');
            if (textSpan) {
                const overflowDiff = textSpan.scrollWidth - wrapper.clientWidth;
                if (overflowDiff > 3) {
                    textSpan.style.setProperty('--marquee-dist', `-${overflowDiff + 6}px`);
                    const duration = Math.max(8.0, (overflowDiff / 10) + 5);
                    textSpan.style.setProperty('--marquee-dur', `${duration.toFixed(1)}s`);
                    textSpan.classList.add('marquee-pingpong');
                }
            }
        });
    });
}

export function updateModalObtainingCta(isOpen) {
    const cta = document.getElementById('modal-obtaining-cta');
    if (!cta) return;
    const label = cta.querySelector('.cta-label');
    const icon = cta.querySelector('.cta-icon');
    if (label) label.textContent = isOpen ? 'Ocultar detalles' : 'Ver detalles';
    if (icon) {
        if (isOpen) {
            icon.classList.add('rotate-180');
        } else {
            icon.classList.remove('rotate-180');
        }
    }
}

export function animateAccordionToggle(element, isOpen) {
    if (!element) return;
    if (element._animCleanup) {
        element._animCleanup();
    }

    if (isOpen) {
        element.classList.remove('hidden');
        element.style.overflow = 'hidden';
        element.style.transition = 'max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease-out';
        element.style.maxHeight = '0px';
        element.style.opacity = '0';

        requestAnimationFrame(() => {
            const targetHeight = element.scrollHeight;
            element.style.maxHeight = targetHeight + 'px';
            element.style.opacity = '1';
        });

        const onEnd = (e) => {
            if (e && e.target !== element) return;
            element.style.maxHeight = 'none';
            element.style.overflow = '';
            element.style.opacity = '';
            element.style.transition = '';
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
        element.addEventListener('transitionend', onEnd);
        element._animCleanup = () => {
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
    } else {
        element.style.overflow = 'hidden';
        element.style.transition = 'max-height 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease-in';
        element.style.maxHeight = element.scrollHeight + 'px';
        element.style.opacity = '1';

        requestAnimationFrame(() => {
            element.style.maxHeight = '0px';
            element.style.opacity = '0';
        });

        const onEnd = (e) => {
            if (e && e.target !== element) return;
            element.classList.add('hidden');
            element.style.maxHeight = '';
            element.style.overflow = '';
            element.style.opacity = '';
            element.style.transition = '';
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
        element.addEventListener('transitionend', onEnd);
        element._animCleanup = () => {
            element.removeEventListener('transitionend', onEnd);
            element._animCleanup = null;
        };
    }
}

export function toggleModalObtainingAccordion() {
    const details = document.getElementById('modal-obtaining-details');
    const chevron = document.getElementById('modal-obtaining-chevron');
    const btn = document.getElementById('modal-obtaining-accordion-btn');
    if (!details) return;
    const isCollapsed = details.classList.contains('hidden') || details.style.maxHeight === '0px';
    if (isCollapsed) {
        animateAccordionToggle(details, true);
        if (chevron) chevron.classList.add('rotate-180');
        if (btn) btn.setAttribute('aria-expanded', 'true');
        updateModalObtainingCta(true);
        initObtainingMarquees();
    } else {
        animateAccordionToggle(details, false);
        if (chevron) chevron.classList.remove('rotate-180');
        if (btn) btn.setAttribute('aria-expanded', 'false');
        updateModalObtainingCta(false);
    }
}
window.toggleModalObtainingAccordion = toggleModalObtainingAccordion;

export function resetModalObtainingAccordion() {
    const details = document.getElementById('modal-obtaining-details');
    const chevron = document.getElementById('modal-obtaining-chevron');
    const btn = document.getElementById('modal-obtaining-accordion-btn');
    if (details) {
        if (details._animCleanup) details._animCleanup();
        details.classList.add('hidden');
        details.style.maxHeight = '';
        details.style.overflow = '';
        details.style.opacity = '';
        details.style.transition = '';
    }
    if (chevron) chevron.classList.remove('rotate-180');
    if (btn) btn.setAttribute('aria-expanded', 'false');
    updateModalObtainingCta(false);
}
window.resetModalObtainingAccordion = resetModalObtainingAccordion;

export function toggleModalNotesAccordion() {
    const content = document.getElementById('modal-notes-content');
    const chevron = document.getElementById('modal-notes-chevron');
    const btn = document.getElementById('modal-notes-accordion-btn');
    if (!content || !chevron) return;
    const isCollapsed = content.classList.contains('hidden') || content.style.maxHeight === '0px';
    if (isCollapsed) {
        animateAccordionToggle(content, true);
        chevron.classList.add('rotate-180');
        if (btn) btn.setAttribute('aria-expanded', 'true');
    } else {
        animateAccordionToggle(content, false);
        chevron.classList.remove('rotate-180');
        if (btn) btn.setAttribute('aria-expanded', 'false');
    }
}
window.toggleModalNotesAccordion = toggleModalNotesAccordion;

export function resetModalNotesAccordion() {
    const content = document.getElementById('modal-notes-content');
    const chevron = document.getElementById('modal-notes-chevron');
    const btn = document.getElementById('modal-notes-accordion-btn');
    if (content) {
        if (content._animCleanup) content._animCleanup();
        content.classList.add('hidden');
        content.style.maxHeight = '';
        content.style.overflow = '';
        content.style.opacity = '';
        content.style.transition = '';
    }
    if (chevron) chevron.classList.remove('rotate-180');
    if (btn) btn.setAttribute('aria-expanded', 'false');
}
window.resetModalNotesAccordion = resetModalNotesAccordion;

export function renderModalNotes(data, activeForm = null) {
    const section = document.getElementById('modal-notes-section');
    const content = document.getElementById('modal-notes-content');
    const counter = document.getElementById('modal-notes-counter');
    const title = document.getElementById('modal-notes-title');
    const icon = document.getElementById('modal-notes-icon');
    if (!section || !content) return;

    const formNotes = (activeForm && Array.isArray(activeForm.notes)) ? activeForm.notes : [];
    const baseNotes = (data && Array.isArray(data.notes)) ? data.notes : [];
    const singleFormNote = (activeForm && activeForm.form_note) ? [{
        title: activeForm.name ? `Nota de ${activeForm.name}` : "Mecánica de Forma",
        text: activeForm.form_note,
        tag: "Mecánica",
        icon: "/media/items/rule-book.png"
    }] : [];

    const allNotes = [...formNotes, ...singleFormNote, ...baseNotes];

    if (allNotes.length === 0) {
        section.classList.add('hidden');
        content.innerHTML = '';
        return;
    }

    section.classList.remove('hidden');
    if (counter) counter.textContent = allNotes.length;

    if (allNotes.length > 1) {
        if (title) title.textContent = "Notas y Detalles";
        if (icon) icon.src = "/media/items/journal.png";
    } else {
        if (title) title.textContent = allNotes[0].title || "Notas y Detalles";
        if (icon) icon.src = allNotes[0].icon || "/media/items/journal.png";
    }

    content.innerHTML = '';
    allNotes.forEach(note => {
        const card = document.createElement('div');
        card.className = 'flex items-start gap-2.5 p-2.5 rounded-lg border-2 border-slate-950 bg-amber-50/80 shadow-[1px_1px_0px_0px_#0f172a]';
        const iconSrc = note.icon || '/media/items/rule-book.png';
        const tagHtml = note.tag ? `<span class="text-[9px] font-black uppercase px-1.5 py-0.2 rounded border border-slate-900 bg-amber-300 text-slate-950 shadow-sm">${note.tag}</span>` : '';

        card.innerHTML = `
            <div class="w-7 h-7 flex items-center justify-center shrink-0 pt-0.5">
                <img src="${iconSrc}" alt="" class="w-6 h-6 object-contain pixel-art drop-shadow-sm">
            </div>
            <div class="min-w-0 flex-1 space-y-0.5 text-left">
                <div class="flex items-center gap-1.5 flex-wrap">
                    <span class="text-xs font-black uppercase text-slate-900 tracking-tight">${note.title || 'Nota'}</span>
                    ${tagHtml}
                </div>
                <p class="text-xs font-semibold text-slate-700 leading-snug">${note.text}</p>
            </div>
        `;
        content.appendChild(card);
    });
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

    // 4. Ubicación específica si la forma define ubicaciones propias (Unown, Shellos, etc.)
    renderModalObtaining(data, form);

    // 5. Notas y mecánicas de la forma
    renderModalNotes(data, form);
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
    resetModalNotesAccordion();
    resetModalObtainingAccordion();
    renderModalGender(data);
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
        renderModalNotes(data, null);
    }

    // 4. Biometría (Altura y Peso)
    const heightEl = document.getElementById('modal-pokemon-height');
    const weightEl = document.getElementById('modal-pokemon-weight');
    if (heightEl) heightEl.textContent = data.height ? `${(data.height / 10).toFixed(1)} m` : '--';
    if (weightEl) weightEl.textContent = data.weight ? `${(data.weight / 10).toFixed(1)} kg` : '--';

    // 6. Estado de captura actual
    const card = document.getElementById(`card-${entryId}`);
    let isCaught = false;
    if (card) {
        isCaught = state.isShinydexMode ? (card.dataset.shinyCaught === 'true') : (card.dataset.caught === 'true');
    } else {
        const modalRelatedCard = document.querySelector(`[data-entry-id="${entryId}"]`);
        if (modalRelatedCard) {
            isCaught = state.isShinydexMode
                ? (modalRelatedCard.dataset.shinyCaught === 'true')
                : (modalRelatedCard.dataset.caught === 'true');
        } else {
            isCaught = state.isShinydexMode ? Boolean(data.is_shiny_caught) : Boolean(data.is_caught);
        }
    }
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
    lockModalScroll();

    // 9. Activar marquesina suave en ubicaciones
    requestAnimationFrame(() => {
        document.querySelectorAll('#modal-obtaining-details .location-marquee-wrapper').forEach(wrapper => {
            const textSpan = wrapper.querySelector('.location-marquee-text');
            if (textSpan) {
                const overflowDiff = textSpan.scrollWidth - wrapper.clientWidth;
                if (overflowDiff > 3) {
                    textSpan.style.setProperty('--marquee-dist', `-${overflowDiff + 6}px`);
                    const duration = Math.max(8.0, (overflowDiff / 10) + 5);
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

export function toggleComicCaveAccordion(btn) {
    if (!btn) return;
    const content = btn.nextElementSibling;
    const icon = btn.querySelector('svg');
    const label = btn.querySelector('.label-text');
    if (!content) return;
    const isExpanded = btn.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
        animateAccordionToggle(content, false);
        btn.setAttribute('aria-expanded', 'false');
        if (icon) icon.classList.remove('rotate-180');
        if (label) label.textContent = 'Ver nota';
    } else {
        animateAccordionToggle(content, true);
        btn.setAttribute('aria-expanded', 'true');
        if (icon) icon.classList.add('rotate-180');
        if (label) label.textContent = 'Ocultar';
    }
}
