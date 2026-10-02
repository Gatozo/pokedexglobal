/**
 * Pokédex Global - Módulo de Estado y Configuración (state.js)
 * Centraliza las variables de estado reactivo, temas visuales y configuración del servidor.
 */

export const config = window.POKEDEX_CONFIG || {};
export const currentGameSlug = config.gameSlug || '';
export const currentGameDisplayName = config.gameDisplayName || '';
export const evolutionStonesCatalog = config.evolutionStonesCatalog || {};

// Constantes de estilo temático según el juego activo (Game Boy Palette)
export const THEME_ACTIVE_BTN = currentGameSlug === 'yellow'
    ? 'bg-amber-400 text-slate-950 font-black'
    : (currentGameSlug === 'blue' 
        ? 'bg-blue-600 text-white font-black' 
        : (currentGameSlug === 'gold' 
            ? 'bg-[#c59b27] text-slate-950 font-black' 
            : (currentGameSlug === 'silver'
                ? 'bg-slate-500 text-white font-black'
                : (currentGameSlug === 'crystal'
                    ? 'bg-sky-500 text-slate-950 font-black'
                    : (currentGameSlug === 'ruby'
                        ? 'bg-rose-900 text-rose-100 font-black'
                        : (currentGameSlug === 'sapphire'
                            ? 'bg-[#0f3870] text-sky-100 font-black'
                            : (currentGameSlug === 'emerald'
                                ? 'bg-[#059669] text-emerald-100 font-black'
                                : (currentGameSlug === 'firered'
                                    ? 'bg-orange-600 text-white font-black'
                                    : 'bg-red-600 text-white font-black'))))))));

export const THEME_STATUS_CAUGHT_CLASS = 'status-caught-active';
export const THEME_UNCAUGHT_BTN = 'card-action-btn mt-3 w-full h-9 px-3 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer shrink-0 bg-emerald-500 hover:bg-emerald-400 text-white';
export const THEME_CAUGHT_BTN = 'card-action-btn mt-3 w-full h-9 px-3 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 border-2 border-slate-950 shadow-[2px_2px_0px_0px_#0f172a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer shrink-0 bg-rose-500 hover:bg-rose-600 text-white';

// Estado mutable compartido
export const state = {
    currentStatusFilter: 'all',
    currentSpriteStyle: 'retro',
    activeModalEntryId: null,
    isShinydexMode: !!config.isShinydexActive,
    selectedFilterTags: new Set(),
    selectedFilterTypes: new Set(),
    isFilterPanelOpen: false,
    activeModalCryUrl: '',
    normalStats: {
        caught: (config.normalStats && config.normalStats.caught) || parseInt(document.getElementById('initial-normal-caught')?.value || 0, 10),
        percent: (config.normalStats && config.normalStats.percent) || parseFloat(document.getElementById('initial-normal-percent')?.value || 0.0)
    },
    shinyStats: {
        caught: (config.shinyStats && config.shinyStats.caught) || parseInt(document.getElementById('initial-shiny-caught')?.value || 0, 10),
        percent: (config.shinyStats && config.shinyStats.percent) || parseFloat(document.getElementById('initial-shiny-percent')?.value || 0.0)
    },
    unownStats: config.unownStats || {
        normal: { caught: 0, percent: 0.0 },
        shiny: { caught: 0, percent: 0.0 }
    }
};

// Pistas oficiales y metadatos de las cámaras de Unown (Ruinas Alfa en Gen 2 y Ruinas Sete en Rojo Fuego / Verde Hoja)
export const UNOWN_CHAMBER_HINTS = {
    // Ruinas Alfa (Johto - Gen 2)
    kabuto: {
        title: "Cámara de Kabuto (Entrada Principal)",
        text: "Alberga las formas A - K. Sala secreta: Usar Cuerda Huida (Escape Rope) frente a la inscripción trasera."
    },
    omanyte: {
        title: "Cámara de Omanyte (Noreste - Surf)",
        text: "Alberga las formas L - R. Sala secreta: Usar Piedra Agua (Water Stone) frente a la inscripción trasera."
    },
    aerodactyl: {
        title: "Cámara de Aerodactyl (Suroeste - Cueva Unión)",
        text: "Alberga las formas S - W. Sala secreta: Usar Destello (Flash) frente a la inscripción trasera."
    },
    ho_oh: {
        title: "Cámara de Ho-Oh (Noroeste - Cueva Unión)",
        text: "Alberga las formas X - Z. Sala secreta: Llevar a Ho-Oh de 1.º en el equipo frente a la inscripción trasera."
    },
    // Ruinas Sete / Cámaras Sete (Archi7 - Rojo Fuego / Verde Hoja)
    anemuna: {
        title: "Cámara Anémuna (Islote 1 - Sureste)",
        text: "Alberga a Unown A (99%) y Unown ? (1%). Requiere resolver el puzzle de la Llave Sete con Fuerza en Cañón Sétano."
    },
    tulipdos: {
        title: "Cámara Tulipdos (Islote 2)",
        text: "Alberga a Unown C (50%), D (30%), H (14%), U (5%) y O (1%). Requiere la Llave Sete."
    },
    trisante: {
        title: "Cámara Trisante (Islote 3)",
        text: "Alberga a Unown N (60%), S (30%), I (8%) y E (2%). Requiere la Llave Sete."
    },
    quarciso: {
        title: "Cámara Quarciso (Islote 4)",
        text: "Alberga a Unown P (40%), J (20%), L (20%), R (14%) y Q (6%). Requiere la Llave Sete."
    },
    hibinca: {
        title: "Cámara Hibinca (Islote 5)",
        text: "Alberga a Unown Y (40%), G (25%), T (20%), F (13%) y K (2%). Requiere la Llave Sete."
    },
    seiris: {
        title: "Cámara Seiris (Islote 6)",
        text: "Alberga a Unown V (50%), W (30%), X (10%), M (8%) y B (2%). Requiere la Llave Sete."
    },
    pasiete: {
        title: "Cámara Pasiete (Islote 7 - Norte de Seiris)",
        text: "Alberga a Unown Z (99%) y Unown ! (1%). Requiere la Llave Sete."
    }
};

