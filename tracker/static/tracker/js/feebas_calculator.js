/**
 * Pokédex Global - Calculadora Matemática de Feebas para Gen 3 (feebas_calculator.js)
 * Implementa el algoritmo canónico de ingeniería inversa de la ROM de Hoenn (Rubí, Zafiro y Esmeralda).
 * Créditos: MucksX / pret/pokeemerald
 */

import { 
    FEEBAS_CONDITIONS_ES, 
    FEEBAS_LIFESTYLE_ES, 
    FEEBAS_HOBBIES_ES, 
    FEEBAS_TILE_COORDINATES 
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
