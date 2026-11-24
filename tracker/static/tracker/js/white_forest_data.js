/**
 * Pokédex Global - Datos y Calculadora Oficial del Bosque Blanco (Pokémon Blanco - Gen 5)
 *
 * Fuente de mecánicas y pesos de encuentro: datos extraídos de la ROM (Bulbapedia / WikiDex ES).
 * - Máximo 10 residentes activos simultáneamente de un catálogo total de 30 residentes.
 * - Cada residente aporta exactamente 1 especie de Hierba Alta (Nv. 5), 1 especie de Surf (Nv. 5)
 *   y 1 objeto diario en el suelo (con probabilidad independiente).
 * - Probabilidad de aparición en Hierba Alta / Surf:
 *     (peso acumulado de la especie) / (suma de pesos de todos los residentes activos) * 100
 */

export const WHITE_FOREST_MAX_RESIDENTS = 10;

export const WHITE_FOREST_RESIDENTS = [
    {
        id: 'pietro',
        name: 'Pietro',
        trainerClass: 'Escolar',
        sprite: '/media/entrenadores/gen5/school_kid_m.png',
        initialPoints: 30,
        grass: { id: 16, name: 'Pidgey', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'stardust', name: 'Polvoestelar', chance: 10 },
    },
    {
        id: 'rober',
        name: 'Rober',
        trainerClass: 'Científico',
        sprite: '/media/entrenadores/gen5/scientist_m.png',
        initialPoints: 70,
        grass: { id: 29, name: 'Nidoran♀', weight: 10 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'dive-ball', name: 'Buceo Ball', chance: 5 },
    },
    {
        id: 'ken',
        name: 'Ken',
        trainerClass: 'Veterano',
        sprite: '/media/entrenadores/gen5/veteran_m.png',
        initialPoints: 30,
        grass: { id: 32, name: 'Nidoran♂', weight: 10 },
        surf: { id: 341, name: 'Corphish', weight: 6 },
        item: { slug: 'thunder-stone', name: 'Piedratrueno', chance: 3 },
    },
    {
        id: 'romina',
        name: 'Romina',
        trainerClass: 'Damisela',
        sprite: '/media/entrenadores/gen5/lady.png',
        initialPoints: 30,
        grass: { id: 43, name: 'Oddish', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'heart-scale', name: 'Escama corazón', chance: 5 },
    },
    {
        id: 'tristan',
        name: 'Tristán',
        trainerClass: 'Empresario',
        sprite: '/media/entrenadores/gen5/clerk_m.png',
        initialPoints: 70,
        grass: { id: 63, name: 'Abra', weight: 10 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'yellow-shard', name: 'Parte amarilla', chance: 10 },
    },
    {
        id: 'pascual',
        name: 'Pascual',
        trainerClass: 'Karateka',
        sprite: '/media/entrenadores/gen5/black_belt.png',
        initialPoints: 30,
        grass: { id: 66, name: 'Machop', weight: 20 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'quick-ball', name: 'Veloz Ball', chance: 5 },
    },
    {
        id: 'esther',
        name: 'Esther',
        trainerClass: 'Oficinista',
        sprite: '/media/entrenadores/gen5/clerk_f.png',
        initialPoints: 30,
        grass: { id: 69, name: 'Bellsprout', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'nest-ball', name: 'Nido Ball', chance: 10 },
    },
    {
        id: 'sole',
        name: 'Sole',
        trainerClass: 'Científica',
        sprite: '/media/entrenadores/gen5/scientist_f.png',
        initialPoints: 30,
        grass: { id: 81, name: 'Magnemite', weight: 20 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'green-shard', name: 'Parte verde', chance: 10 },
    },
    {
        id: 'honorio',
        name: 'Honorio',
        trainerClass: 'Calvo',
        sprite: '/media/entrenadores/gen5/roughneck.png',
        initialPoints: 30,
        grass: { id: 92, name: 'Gastly', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'tiny-mushroom', name: 'Miniseta', chance: 30 },
    },
    {
        id: 'olao',
        name: 'Olao',
        trainerClass: 'Escolar',
        sprite: '/media/entrenadores/gen5/school_kid_m.png',
        initialPoints: 70,
        grass: { id: 111, name: 'Rhyhorn', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'net-ball', name: 'Malla Ball', chance: 5 },
    },
    {
        id: 'don',
        name: 'Don',
        trainerClass: 'Mochilero',
        sprite: '/media/entrenadores/gen5/backpacker_m.png',
        initialPoints: 20,
        grass: { id: 137, name: 'Porygon', weight: 4 },
        surf: { id: 194, name: 'Wooper', weight: 6 },
        item: { slug: 'dusk-stone', name: 'Piedra noche', chance: 2 },
    },
    {
        id: 'carme',
        name: 'Carme',
        trainerClass: 'Chica',
        sprite: '/media/entrenadores/gen5/lass.png',
        initialPoints: 70,
        grass: { id: 175, name: 'Togepi', weight: 10 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'repeat-ball', name: 'Acopio Ball', chance: 5 },
    },
    {
        id: 'alonso',
        name: 'Alonso',
        trainerClass: 'Niño bien',
        sprite: '/media/entrenadores/gen5/rich_boy.png',
        initialPoints: 70,
        grass: { id: 179, name: 'Mareep', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'poke-ball', name: 'Poké Ball', chance: 30 },
    },
    {
        id: 'cira',
        name: 'Cira',
        trainerClass: 'Oficinista',
        sprite: '/media/entrenadores/gen5/clerk_f.png',
        initialPoints: 70,
        grass: { id: 187, name: 'Hoppip', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'rare-bone', name: 'Hueso raro', chance: 5 },
    },
    {
        id: 'max',
        name: 'Max',
        trainerClass: 'Joven',
        sprite: '/media/entrenadores/gen5/youngster.png',
        initialPoints: 30,
        grass: { id: 239, name: 'Elekid', weight: 10 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'great-ball', name: 'Superball', chance: 10 },
    },
    {
        id: 'vito',
        name: 'Vito',
        trainerClass: 'Entrenador guay',
        sprite: '/media/entrenadores/gen5/ace_trainer_m.png',
        initialPoints: 70,
        grass: { id: 240, name: 'Magby', weight: 10 },
        surf: { id: 341, name: 'Corphish', weight: 6 },
        item: { slug: 'fire-stone', name: 'Piedra fuego', chance: 3 },
    },
    {
        id: 'azucena',
        name: 'Azucena',
        trainerClass: 'Escolar',
        sprite: '/media/entrenadores/gen5/school_kid_f.png',
        initialPoints: 70,
        grass: { id: 265, name: 'Wurmple', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'poke-ball', name: 'Poké Ball', chance: 20 },
    },
    {
        id: 'melas',
        name: 'Melas',
        trainerClass: 'Pokémon Ranger',
        sprite: '/media/entrenadores/gen5/pokemon_ranger_m.png',
        initialPoints: 70,
        grass: { id: 270, name: 'Lotad', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'water-stone', name: 'Piedra agua', chance: 3 },
    },
    {
        id: 'lola',
        name: 'Lola',
        trainerClass: 'Seño',
        sprite: '/media/entrenadores/gen5/nursery_aide.png',
        initialPoints: 30,
        grass: { id: 273, name: 'Seedot', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'ultra-ball', name: 'Ultraball', chance: 10 },
    },
    {
        id: 'malena',
        name: 'Malena',
        trainerClass: 'Entrenadora guay',
        sprite: '/media/entrenadores/gen5/ace_trainer_f.png',
        initialPoints: 80,
        grass: { id: 280, name: 'Ralts', weight: 6 },
        surf: { id: 194, name: 'Wooper', weight: 6 },
        item: { slug: 'sun-stone', name: 'Piedra solar', chance: 3 },
    },
    {
        id: 'irais',
        name: 'Iraís',
        trainerClass: 'Luchadora',
        sprite: '/media/entrenadores/gen5/battle_girl.png',
        initialPoints: 70,
        grass: { id: 287, name: 'Slakoth', weight: 20 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'leaf-stone', name: 'Piedra hoja', chance: 3 },
    },
    {
        id: 'lila',
        name: 'Lila',
        trainerClass: 'Veterana',
        sprite: '/media/entrenadores/gen5/veteran_f.png',
        initialPoints: 20,
        grass: { id: 293, name: 'Whismur', weight: 10 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'moon-stone', name: 'Piedra lunar', chance: 3 },
    },
    {
        id: 'sarah',
        name: 'Sarah',
        trainerClass: 'Mochilera',
        sprite: '/media/entrenadores/gen5/backpacker_f.png',
        initialPoints: 80,
        grass: { id: 298, name: 'Azurill', weight: 4 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'shiny-stone', name: 'Piedra día', chance: 2 },
    },
    {
        id: 'loeb',
        name: 'Loeb',
        trainerClass: 'Montañero',
        sprite: '/media/entrenadores/gen5/hiker.png',
        initialPoints: 70,
        grass: { id: 304, name: 'Aron', weight: 20 },
        surf: { id: 283, name: 'Surskit', weight: 20 },
        item: { slug: 'big-mushroom', name: 'Seta grande', chance: 20 },
    },
    {
        id: 'dorita',
        name: 'Dorita',
        trainerClass: 'Pokémon Ranger',
        sprite: '/media/entrenadores/gen5/pokemon_ranger_f.png',
        initialPoints: 30,
        grass: { id: 328, name: 'Trapinch', weight: 20 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'blue-shard', name: 'Parte azul', chance: 10 },
    },
    {
        id: 'pitu',
        name: 'Pitu',
        trainerClass: 'Marquesa',
        sprite: '/media/entrenadores/gen5/socialite.png',
        initialPoints: 30,
        grass: { id: 371, name: 'Bagon', weight: 4 },
        surf: { id: 194, name: 'Wooper', weight: 6 },
        item: { slug: 'dawn-stone', name: 'Piedra alba', chance: 1 },
    },
    {
        id: 'giuseppe',
        name: 'Giuseppe',
        trainerClass: 'Mochilero',
        sprite: '/media/entrenadores/gen5/backpacker_m.png',
        initialPoints: 30,
        grass: { id: 396, name: 'Starly', weight: 20 },
        surf: { id: 341, name: 'Corphish', weight: 6 },
        item: { slug: 'oval-stone', name: 'Piedra oval', chance: 3 },
    },
    {
        id: 'jerry',
        name: 'Jerry',
        trainerClass: 'Empresario',
        sprite: '/media/entrenadores/gen5/clerk_m.png',
        initialPoints: 30,
        grass: { id: 403, name: 'Shinx', weight: 20 },
        surf: { id: 270, name: 'Lotad', weight: 10 },
        item: { slug: 'red-shard', name: 'Parte roja', chance: 10 },
    },
    {
        id: 'cirilo',
        name: 'Cirilo',
        trainerClass: 'Duque',
        sprite: '/media/entrenadores/gen5/gentleman.png',
        initialPoints: 20,
        grass: { id: 406, name: 'Budew', weight: 6 },
        surf: { id: 194, name: 'Wooper', weight: 6 },
        item: { slug: 'honey', name: 'Miel', chance: 5 },
    },
    {
        id: 'elisa',
        name: 'Elisa',
        trainerClass: 'Mochilera',
        sprite: '/media/entrenadores/gen5/backpacker_f.png',
        initialPoints: 70,
        grass: { id: 440, name: 'Happiny', weight: 10 },
        surf: { id: 341, name: 'Corphish', weight: 6 },
        item: { slug: 'timer-ball', name: 'Turno Ball', chance: 5 },
    },
];

export const WHITE_FOREST_RESIDENTS_BY_ID = Object.fromEntries(
    WHITE_FOREST_RESIDENTS.map(r => [r.id, r])
);

export const WHITE_FOREST_SPECIES_IDS = new Set([
    ...WHITE_FOREST_RESIDENTS.map(r => r.grass.id),
    ...WHITE_FOREST_RESIDENTS.map(r => r.surf.id),
]);

/**
 * Formatea un porcentaje limpiamente (ej. 50 -> "50%", 27.777 -> "27.8%").
 */
export function formatEncounterPercent(value) {
    if (!isFinite(value) || value <= 0) return '0%';
    const rounded = Math.round(value * 10) / 10;
    return Number.isInteger(rounded) ? `${rounded}%` : `${rounded.toFixed(1)}%`;
}

/**
 * Calcula encuentros en Hierba Alta, encuentros en Surf y objetos diarios
 * para una selección de entre 0 y 10 IDs de residentes.
 */
export function calculateWhiteForestResults(selectedIds = []) {
    const uniqueValid = [];
    const seen = new Set();
    for (const rawId of (selectedIds || [])) {
        if (uniqueValid.length >= WHITE_FOREST_MAX_RESIDENTS) break;
        if (WHITE_FOREST_RESIDENTS_BY_ID[rawId] && !seen.has(rawId)) {
            seen.add(rawId);
            uniqueValid.push(WHITE_FOREST_RESIDENTS_BY_ID[rawId]);
        }
    }

    const grassTotalWeight = uniqueValid.reduce((sum, r) => sum + r.grass.weight, 0);
    const surfTotalWeight = uniqueValid.reduce((sum, r) => sum + r.surf.weight, 0);

    // 1. Hierba Alta (cada residente aporta 1 especie distinta)
    const grassEncounters = uniqueValid.map(r => {
        const percent = grassTotalWeight > 0 ? (r.grass.weight / grassTotalWeight) * 100 : 0;
        return {
            id: r.grass.id,
            name: r.grass.name,
            weight: r.grass.weight,
            percent,
            percentLabel: formatEncounterPercent(percent),
            resident: r,
        };
    }).sort((a, b) => (b.percent - a.percent) || (a.id - b.id));

    // 2. Surf (varios residentes pueden aportar la misma especie; sus pesos se acumulan)
    const surfMap = new Map();
    uniqueValid.forEach(r => {
        const key = r.surf.id;
        if (!surfMap.has(key)) {
            surfMap.set(key, {
                id: r.surf.id,
                name: r.surf.name,
                totalWeight: 0,
                contributors: [],
            });
        }
        const entry = surfMap.get(key);
        entry.totalWeight += r.surf.weight;
        entry.contributors.push(r);
    });

    const surfEncounters = Array.from(surfMap.values()).map(entry => {
        const percent = surfTotalWeight > 0 ? (entry.totalWeight / surfTotalWeight) * 100 : 0;
        return {
            ...entry,
            percent,
            percentLabel: formatEncounterPercent(percent),
        };
    }).sort((a, b) => (b.percent - a.percent) || (a.id - b.id));

    // 3. Objetos diarios (cada residente tira su probabilidad de forma independiente;
    //    si dos residentes comparten objeto como Poké Ball, se combina como P(al menos 1) = 1 - Π(1 - p_i))
    const itemMap = new Map();
    uniqueValid.forEach(r => {
        const slug = r.item.slug;
        if (!itemMap.has(slug)) {
            itemMap.set(slug, {
                slug,
                name: r.item.name,
                icon: `/media/items/${slug}.png`,
                missProb: 1,
                contributors: [],
            });
        }
        const entry = itemMap.get(slug);
        entry.missProb *= (1 - r.item.chance / 100);
        entry.contributors.push({ resident: r, chance: r.item.chance });
    });

    const dailyItems = Array.from(itemMap.values()).map(entry => {
        const combinedChance = (1 - entry.missProb) * 100;
        return {
            slug: entry.slug,
            name: entry.name,
            icon: entry.icon,
            chance: combinedChance,
            chanceLabel: formatEncounterPercent(combinedChance),
            contributors: entry.contributors,
        };
    }).sort((a, b) => (b.chance - a.chance) || a.name.localeCompare(b.name, 'es'));

    const activeSpeciesIds = new Set([
        ...grassEncounters.map(e => e.id),
        ...surfEncounters.map(e => e.id),
    ]);

    return {
        selectedResidents: uniqueValid,
        grassEncounters,
        surfEncounters,
        dailyItems,
        activeSpeciesIds,
        grassTotalWeight,
        surfTotalWeight,
    };
}

/**
 * Devuelve el estado de un Pokémon (por número nacional) respecto a la configuración
 * actual del Bosque Blanco, incluyendo qué entrenador(es) lo desbloquean si falta.
 */
export function getWhiteForestPokemonStatus(nationalNumber, selectedIds = []) {
    const num = parseInt(nationalNumber, 10);
    if (!WHITE_FOREST_SPECIES_IDS.has(num)) {
        return null;
    }

    const validIds = Array.isArray(selectedIds)
        ? selectedIds.filter(id => Boolean(WHITE_FOREST_RESIDENTS_BY_ID[id]))
        : [];
    const isConfigured = validIds.length > 0;
    const results = calculateWhiteForestResults(validIds);

    const grassMatch = results.grassEncounters.find(e => e.id === num) || null;
    const surfMatch = results.surfEncounters.find(e => e.id === num) || null;
    const isActive = Boolean(grassMatch || surfMatch);

    const requiredGrassResident = WHITE_FOREST_RESIDENTS.find(r => r.grass.id === num) || null;
    const requiredSurfResidents = WHITE_FOREST_RESIDENTS.filter(r => r.surf.id === num);

    return {
        nationalNumber: num,
        isConfigured,
        isActive,
        selectedCount: results.selectedResidents.length,
        grassMatch,
        surfMatch,
        requiredGrassResident,
        requiredSurfResidents,
    };
}
