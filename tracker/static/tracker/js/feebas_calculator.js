/**
 * Pokédex Global - Calculadora Matemática de Feebas para Gen 3 (feebas_calculator.js)
 * Implementa el algoritmo canónico de ingeniería inversa de la ROM de Hoenn (Rubí, Zafiro y Esmeralda).
 * Créditos: MucksX / pret/pokeemerald
 */

import { 
    FEEBAS_CONDITIONS_ES, 
    FEEBAS_LIFESTYLE_ES, 
    FEEBAS_HOBBIES_ES, 
    FEEBAS_TILE_COORDINATES,
    FEEBAS_MT_CORONET_TILES
} from './feebas_data.js';

const UNREACHABLE_TILES = [105, 119, 144, 296, 297, 298];

/**
 * Función de avance LCG de 32 bits de Game Boy Advance.
 */
function next(seed, n = 1, isFeebas = false) {
    let rng = BigInt(seed);
    const mult = BigInt(1103515245);
    const add = isFeebas ? BigInt(12345) : BigInt(24691);
    const mask = BigInt(0xFFFFFFFF);

    for (let i = 0; i < n; i++) {
        rng = (mult * rng + add) & mask;
    }
    return rng;
}

/**
 * Avanza el estado del PRNG hasta que se genera el Trainer ID en Rubí/Zafiro.
 */
function advanceToTID(seed, tid) {
    let current = BigInt(seed);
    const targetTid = BigInt(tid);
    let attempts = 0;
    while ((current >> BigInt(16)) !== targetTid && attempts < 100000) {
        current = next(current);
        attempts++;
    }
    return current;
}

/**
 * En Esmeralda salta los avances imposibles previos a la generación de la frase.
 */
function skipImpossibleAdvances(seed) {
    let current = BigInt(seed);
    for (let i = 0; i < 700; i++) {
        current = next(current);
    }
    return current;
}

/**
 * Mapea las dos palabras a los índices numéricos de grupos de Easy Chat en español.
 */
export function getPhraseIndices(word1, word2) {
    const w1 = String(word1 || '').trim().toUpperCase();
    const w2 = String(word2 || '').trim().toUpperCase();

    const firstWordIndex = FEEBAS_CONDITIONS_ES.findIndex(w => w.toUpperCase() === w1);
    let secondWordGroupLifestyle = 0;
    let secondWordIndex = -1;

    const lifestyleIdx = FEEBAS_LIFESTYLE_ES.findIndex(w => w.toUpperCase() === w2);
    if (lifestyleIdx !== -1) {
        secondWordGroupLifestyle = 1;
        secondWordIndex = lifestyleIdx;
    } else {
        secondWordIndex = FEEBAS_HOBBIES_ES.findIndex(w => w.toUpperCase() === w2);
    }

    if (firstWordIndex === -1 || secondWordIndex === -1) {
        return null;
    }

    return [firstWordIndex, secondWordGroupLifestyle, secondWordIndex];
}

/**
 * Calcula las semillas candidatas de Feebas a partir de la frase y el TID.
 */
export function getFeebasRands(tid, word1, word2, isEmerald) {
    const phrase = getPhraseIndices(word1, word2);
    if (!phrase) return [];

    const firstWordIndex = BigInt(phrase[0]);
    const secondWordGroupLifestyle = BigInt(phrase[1]);
    const secondWordIndex = BigInt(phrase[2]);

    let seed = isEmerald ? BigInt(tid) : BigInt(0x5A0);
    seed = isEmerald ? skipImpossibleAdvances(seed) : advanceToTID(seed, tid);

    const feebasRands = [];
    const maxResults = isEmerald ? 5 : 3;
    let attempts = 0;

    while (feebasRands.length < maxResults && attempts < 200000) {
        seed = next(seed);
        attempts++;

        if (((seed >> BigInt(16)) % BigInt(69)) === firstWordIndex) {
            const nextSeed1 = next(seed);
            if (((nextSeed1 >> BigInt(16)) & BigInt(1)) === secondWordGroupLifestyle) {
                const elementsInSecondGroup = (secondWordGroupLifestyle === BigInt(1)) ? BigInt(45) : BigInt(54);
                const nextSeed2 = next(seed, 2);

                if (((nextSeed2 >> BigInt(16)) % elementsInSecondGroup) === secondWordIndex) {
                    let numAdvances = 6;
                    const nextSeed4 = next(seed, 4);
                    if (((nextSeed4 >> BigInt(16)) % BigInt(98)) > BigInt(50)) {
                        const nextSeed5 = next(seed, 5);
                        if (((nextSeed5 >> BigInt(16)) % BigInt(98)) > BigInt(80)) {
                            numAdvances = 8;
                        } else {
                            numAdvances = 7;
                        }
                    }
                    feebasRands.push(next(seed, numAdvances) >> BigInt(16));
                }
            }
        }
    }

    return feebasRands;
}

/**
 * Convierte un Feebas Random Value en las 6 casillas de pesca válidas.
 */
export function getFeebasTiles(seedValue) {
    const tilesList = [];
    let tilesFound = 0;
    let seed = BigInt(seedValue);

    let attempts = 0;
    while (tilesFound < 6 && attempts < 2000) {
        seed = next(seed, 1, true);
        attempts++;
        let tile = (seed >> BigInt(16)) % BigInt(0x1BF);

        if (tile === BigInt(0)) tile = BigInt(447);
        if (tile < BigInt(4)) continue;

        const tileNum = Number(tile);
        if (UNREACHABLE_TILES.includes(tileNum)) {
            tilesFound++;
            continue;
        }

        if (!tilesList.includes(tileNum)) {
            tilesList.push(tileNum);
        }
        tilesFound++;
    }

    return tilesList;
}

/**
 * Función principal: Calcula las 6 casillas y sus coordenadas en píxeles.
 * @param {number} tid - Trainer ID (0 - 65535)
 * @param {string} word1 - Primera palabra de la frase
 * @param {string} word2 - Segunda palabra de la frase
 * @param {boolean} isEmerald - True si es Esmeralda, False si es Rubí/Zafiro
 * @returns {Array<{tileId: number, x: number, y: number}>} Las casillas calculadas
 */
export function calculateFeebasFishingSpots(tid, word1, word2, isEmerald = false) {
    const rands = getFeebasRands(tid, word1, word2, isEmerald);
    if (!rands || rands.length === 0) return [];

    // Tomar la semilla principal de mayor probabilidad (índice 0)
    const primaryRand = rands[0];
    const tileIds = getFeebasTiles(primaryRand);

    return tileIds.map(tileId => {
        const coords = FEEBAS_TILE_COORDINATES[tileId] || [0, 0];
        return {
            tileId: tileId,
            x: coords[0],
            y: coords[1]
        };
    });
}

/**
 * Operaciones PRNG de 32 bits para Gen 4 (Monte Corona B1F).
 * Créditos: DRayX, Lincoln-LM, EzPzStreamz (RNG Research Community).
 */
function mrngr4(seed) {
    return (seed * 0xEEB9EB65n + 0xFC77A683n) & 0xFFFFFFFFn;
}

function arng4(seed) {
    return (seed * 0x6C078965n + 0x1n) & 0xFFFFFFFFn;
}

function mrng4(seed) {
    return (seed * 0x41C64E6Dn + 0x3039n) & 0xFFFFFFFFn;
}

function intabs4(seed) {
    if (seed > 0x80000000n) {
        return 0x100000000n - seed;
    }
    return seed;
}

/**
 * Calcula las casillas de Feebas en el Monte Corona (Gen 4: Diamante, Perla y Platino).
 * Si se ingresan 2 números de lotería (ayer y hoy), calcula con 100% de certeza las 4 casillas de hoy.
 * Si solo se ingresa el de hoy, calcula las 4 casillas tentativas divididas en dos grupos (A y B) con 50% de probabilidad cada uno.
 *
 * @param {number} lottoToday - Número de lotería de Jubilife TV de hoy (0 - 99999).
 * @param {number|null} lottoYesterday - Número de lotería de ayer (0 - 99999, opcional).
 * @returns {Array<{tileId: number, x: number, y: number, certainty: number, group: string, rawX: number, rawY: number}>}
 */
export function calculateGen4FeebasSpots(lottoToday, lottoYesterday = null) {
    const lottoNum = parseInt(lottoToday, 10);
    if (isNaN(lottoNum) || lottoNum < 0 || lottoNum > 99999) {
        return [];
    }

    const yestNum = (lottoYesterday !== null && lottoYesterday !== undefined && String(lottoYesterday).trim() !== '') 
        ? parseInt(lottoYesterday, 10) 
        : null;
    const hasYesterday = (yestNum !== null && !isNaN(yestNum) && yestNum >= 0 && yestNum <= 99999);

    // Mapeo a píxeles en el mapa de Monte Corona B1F (288x544 escalado a 576x1088, cada tile de 16x16 pasa a medir 32x32)
    const mapTile = (tilePos, idx, group, certainty) => {
        const rawX = tilePos[0];
        const rawY = tilePos[1];
        const x = (rawX - 9) * 32 + 16;
        const y = (rawY - 18) * 32 + 16;
        return {
            tileId: idx + 1,
            rawX: rawX,
            rawY: rawY,
            x: x,
            y: y,
            group: group,
            certainty: certainty
        };
    };

    if (hasYesterday) {
        const lotto0 = yestNum;
        const lotto1 = lottoNum;
        const matchingSeeds = [];

        for (let lotto0_val = lotto0; lotto0_val < 0x100000; lotto0_val += 100000) {
            for (let low = 0; low < 0x1000; low++) {
                const yeste_seed = mrngr4((BigInt(lotto0_val) << 12n) | BigInt(low));
                const today_seed = arng4(yeste_seed);

                if (BigInt(lotto1) !== (((mrng4(today_seed)) >> 12n) % 100000n)) {
                    continue;
                }
                matchingSeeds.push(today_seed);
            }
        }

        if (matchingSeeds.length > 0) {
            const today_daily = intabs4(matchingSeeds[0]);
            const spots = [];
            for (let tile = 0; tile < 4; tile++) {
                const pos = ((Number(today_daily) >> (tile * 8)) & 0xFF) % 0x84;
                const idx = 0x85 * (3 - tile) + pos;
                const tilePos = FEEBAS_MT_CORONET_TILES[idx];
                if (tilePos) {
                    spots.push(mapTile(tilePos, idx, 'Garantizada', 100));
                }
            }
            return spots;
        }
    }

    // Modo 1 día (aproximación rápida de 4 casillas con 50% de probabilidad por par A/B)
    const seed = (lottoNum * 0xEB65 + 0xA683) & 0xFFFF;
    const seed_neg = (0x10000 - seed) & 0xFFFF;

    const low = seed & 0xFF;
    const high = (seed >> 8) & 0xFF;
    const low_neg = seed_neg & 0xFF;
    const high_neg = (seed_neg >> 8) & 0xFF;

    const idx_low_pos = 3 + 0x84 * 3 + (low % 0x84);
    const idx_high_pos = 2 + 0x84 * 2 + (high % 0x84);
    const idx_low_neg = 3 + 0x84 * 3 + (low_neg % 0x84);
    const idx_high_neg = 2 + 0x84 * 2 + (high_neg % 0x84);

    const tile_low_pos = FEEBAS_MT_CORONET_TILES[idx_low_pos];
    const tile_high_pos = FEEBAS_MT_CORONET_TILES[idx_high_pos];
    const tile_low_neg = FEEBAS_MT_CORONET_TILES[idx_low_neg];
    const tile_high_neg = FEEBAS_MT_CORONET_TILES[idx_high_neg];

    const spots = [];
    if (tile_low_pos) spots.push(mapTile(tile_low_pos, idx_low_pos, 'Grupo A', 50));
    if (tile_high_pos) spots.push(mapTile(tile_high_pos, idx_high_pos, 'Grupo A', 50));
    if (tile_low_neg) spots.push(mapTile(tile_low_neg, idx_low_neg, 'Grupo B', 50));
    if (tile_high_neg) spots.push(mapTile(tile_high_neg, idx_high_neg, 'Grupo B', 50));

    return spots;
}
