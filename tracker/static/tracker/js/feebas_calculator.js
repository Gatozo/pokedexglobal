/**
 * Pokédex Global - Calculadora Matemática de Feebas para Gen 3 y Gen 4 (feebas_calculator.js)
 * Implementa los algoritmos canónicos de ingeniería inversa de las ROMs originales:
 * - Gen 3 (Rubí, Zafiro y Esmeralda): MucksX / pret/pokeemerald
 * - Gen 4 (Diamante, Perla y Platino): Mow (PokéMow) / pret / RNG Research Community
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

// ============================================================================
// CÁLCULO CANÓNICO DE CASILLAS DE FEEBAS EN MONTE CORONA B1F (GEN 4 NDS: DPPt)
// Basado en el algoritmo de ingeniería inversa de la ROM de NDS (PokéMow).
// ============================================================================

/**
 * Tabla de desplazamiento para búsqueda inversa rápida de semillas diarias en NDS.
 * Precalculada al cargar el módulo para rendimiento instantáneo.
 */
const daySeedOffsetTable = new Uint32Array(65536);

(function buildTable() {
    let acc = 0;
    let accInv = 0;
    let i = 0;
    daySeedOffsetTable[i++] = acc;
    while (i < 65536) {
        if (accInv < 18933) {
            accInv += 17799;
            daySeedOffsetTable[i++] = (acc += 46423);
            daySeedOffsetTable[i++] = (acc += 63468);
        } else if (accInv > 28803) {
            accInv -= 28804;
            daySeedOffsetTable[i++] = (acc += 63468);
        } else {
            accInv += 17799;
            daySeedOffsetTable[i++] = (acc += 109891);
        }
    }
})();

/**
 * Deduce las semillas de grupo de 32 bits a partir de 2 números de lotería de NDS.
 * @param {number} prevLotto - Número de lotería de ayer (0 - 65535).
 * @param {number} currLotto - Número de lotería de hoy (0 - 65535).
 * @returns {Array<number>} Semillas de grupo coincidentes (0, 1 o 2 semillas).
 */
export function calculateGen4DaySeeds(prevLotto, currLotto) {
    const pLotto = parseInt(prevLotto, 10);
    const cLotto = parseInt(currLotto, 10);
    if (isNaN(pLotto) || isNaN(cLotto) || pLotto < 0 || pLotto > 65535 || cLotto < 0 || cLotto > 65535) {
        return [];
    }

    const matches = [];
    let base = Math.imul(pLotto, 2305097728);
    base += 3394631465;

    const target = ((cLotto << 16) - base) >>> 0;

    let lm = 0;
    let hm = 65535;
    while (lm !== hm) {
        const cm = (lm + hm) >>> 1;
        if (daySeedOffsetTable[cm] < target) {
            lm = cm + 1;
        } else {
            hm = cm;
        }
    }

    let candidate = (base + daySeedOffsetTable[lm]) >>> 0;
    while ((candidate >>> 16) === cLotto) {
        matches.push(candidate);
        lm = (lm + 1) % 65536;
        candidate = (base + daySeedOffsetTable[lm]) >>> 0;
    }

    return matches.map(s => (Math.imul(s, 4005161829) + 4235699843) >>> 0);
}

/**
 * Calcula los 4 índices de casillas de Feebas a partir de una semilla de grupo de NDS.
 * Los 528 tiles se dividen en 4 cuadrantes exactos de 132 casillas (0x84).
 * @param {number} seedValue - Semilla de grupo de 32 bits.
 * @returns {Array<number>} Los 4 índices (0 a 527) en FEEBAS_MT_CORONET_TILES.
 */
export function getFeebasTilesGen4(seedValue) {
    const val = [
        (seedValue >>> 24) & 0xFF,
        (seedValue >>> 16) & 0xFF,
        (seedValue >>>  8) & 0xFF,
        (seedValue       ) & 0xFF,
    ];

    const chunkSize = 132;
    const indices = [];
    for (let i = 0; i < 4; i++) {
        indices.push((chunkSize * i) + (val[i] % chunkSize));
    }
    return indices;
}

/**
 * Mapea las coordenadas internas de la cuadrícula de Monte Corona B1F a píxeles.
 * Las coordenadas van de X: 9..26 (18 casillas) e Y: 18..51 (34 casillas).
 * En escala 2x (576x1088), cada tile de 16x16 pasa a medir 32x32 píxeles.
 */
function mapGen4Tile(tilePos, idx, group, certainty) {
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
}

/**
 * Calcula las 4 casillas canónicas de Feebas en el Monte Corona (B1F)
 * a partir de la Group Seed de 32 bits de cuarta generación (DPPt / NDS).
 *
 * @param {string|number|bigint} groupSeed - Semilla de 32 bits (hexadecimal o numérica).
 * @returns {Array<{tileId: number, x: number, y: number, certainty: number, group: string, rawX: number, rawY: number}>}
 */
export function calculateGen4FeebasFromSeed(groupSeed) {
    if (groupSeed === null || groupSeed === undefined) return [];

    let cleanHex = String(groupSeed).trim();
    if (cleanHex.toLowerCase().startsWith('0x')) {
        cleanHex = cleanHex.substring(2);
    }
    if (!/^[0-9a-fA-F]{1,8}$/.test(cleanHex)) {
        return [];
    }

    const seed = Number(BigInt('0x' + cleanHex) & 0xFFFFFFFFn) >>> 0;
    const tileIndices = getFeebasTilesGen4(seed);

    return tileIndices.map(idx => {
        const tilePos = FEEBAS_MT_CORONET_TILES[idx];
        return mapGen4Tile(tilePos, idx, 'Garantizada', 100);
    });
}

/**
 * Calcula las casillas de Feebas en el Monte Corona para Pokémon Diamante, Perla y Platino (NDS).
 *
 * 1. Si se proporciona `groupSeed`, calcula de inmediato las 4 casillas exactas (100% certeza).
 * 2. Si se ingresan 2 boletos consecutivos (ayer y hoy), ejecuta el algoritmo canónico de NDS:
 *    - Si arroja 1 semilla: devuelve 4 casillas garantizadas (100% certeza).
 *    - Si arroja 2 semillas: devuelve 8 casillas divididas en Grupo 1 (Moradas, 50%) y Grupo 2 (Verdes, 50%).
 *
 * @param {number|null} lottoToday - Número de lotería de hoy (0 - 65535).
 * @param {number|null} lottoYesterday - Número de lotería de ayer (0 - 65535).
 * @param {string|null} groupSeed - Semilla de grupo hexadecimal opcional.
 * @returns {Array<{tileId: number, x: number, y: number, certainty: number, group: string, rawX: number, rawY: number}>}
 */
export function calculateGen4FeebasSpots(lottoToday, lottoYesterday = null, groupSeed = null) {
    if (groupSeed !== null && groupSeed !== undefined && String(groupSeed).trim() !== '') {
        const fromSeedSpots = calculateGen4FeebasFromSeed(groupSeed);
        if (fromSeedSpots.length > 0) {
            return fromSeedSpots;
        }
    }

    const yestNum = (lottoYesterday !== null && lottoYesterday !== undefined && String(lottoYesterday).trim() !== '')
        ? parseInt(lottoYesterday, 10)
        : null;
    const todayNum = (lottoToday !== null && lottoToday !== undefined && String(lottoToday).trim() !== '')
        ? parseInt(lottoToday, 10)
        : null;

    if (yestNum === null || todayNum === null || isNaN(yestNum) || isNaN(todayNum)) {
        return [];
    }

    const seeds = calculateGen4DaySeeds(yestNum, todayNum);
    if (!seeds || seeds.length === 0) {
        return [];
    }

    if (seeds.length === 1) {
        const tileIndices = getFeebasTilesGen4(seeds[0]);
        return tileIndices.map(idx => {
            const tilePos = FEEBAS_MT_CORONET_TILES[idx];
            return mapGen4Tile(tilePos, idx, 'Garantizada', 100);
        });
    }

    // Caso 2 semillas (como en el ejemplo de PokéMow: Grupo 1 Moradas y Grupo 2 Verdes)
    const spots = [];
    const tilesSeed0 = getFeebasTilesGen4(seeds[0]);
    tilesSeed0.forEach(idx => {
        const tilePos = FEEBAS_MT_CORONET_TILES[idx];
        spots.push(mapGen4Tile(tilePos, idx, 'Grupo 1 (Moradas)', 50));
    });

    const tilesSeed1 = getFeebasTilesGen4(seeds[1]);
    tilesSeed1.forEach(idx => {
        const tilePos = FEEBAS_MT_CORONET_TILES[idx];
        spots.push(mapGen4Tile(tilePos, idx, 'Grupo 2 (Verdes)', 50));
    });

    return spots;
}

/**
 * Operaciones PRNG de BDSP (Switch - ILCA) preservadas para futura integración.
 */
export function calculateBDSPFeebasSpots(lottoToday, lottoYesterday = null) {
    // Preservado para BDSP
    return calculateGen4FeebasSpots(lottoToday, lottoYesterday);
}
