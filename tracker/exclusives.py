"""
Módulo centralizado para la gestión de versiones emparejadas y Pokémon exclusivos por edición.
Diseñado para ser escalable a todas las generaciones Pokémon presentes y futuras.
"""
from typing import Dict, List, Optional, Any
from .models import Game, Pokedex
from .catalog_service import CatalogEntry, get_pokemon_by_national_number


# Emparejamiento de juegos por slug de versión (Juego -> [Juegos Contraparte])
GAME_COUNTERPARTS: Dict[str, List[str]] = {
    # Gen 1
    'red': ['blue'],
    'blue': ['red'],
    'yellow': ['red', 'blue'],
    # Gen 2
    'gold': ['silver', 'crystal'],
    'silver': ['gold', 'crystal'],
    'crystal': ['gold', 'silver'],
    # Gen 3
    'ruby': ['sapphire'],
    'sapphire': ['ruby'],
    'emerald': ['ruby', 'sapphire'],
    'firered': ['leafgreen'],
    'leafgreen': ['firered'],
    # Gen 4
    'diamond': ['pearl'],
    'pearl': ['diamond'],
    'platinum': ['diamond', 'pearl'],
    'heartgold': ['soulsilver'],
    'soulsilver': ['heartgold'],
    # Gen 5
    'black': ['white'],
    'white': ['black'],
    'black-2': ['white-2'],
    'white-2': ['black-2'],
    # Gen 6
    'x': ['y'],
    'y': ['x'],
    'omega-ruby': ['alpha-sapphire'],
    'alpha-sapphire': ['omega-ruby'],
    # Gen 7
    'sun': ['moon'],
    'moon': ['sun'],
    'ultra-sun': ['ultra-moon'],
    'ultra-moon': ['ultra-sun'],
    'lets-go-pikachu': ['lets-go-eevee'],
    'lets-go-eevee': ['lets-go-pikachu'],
    # Gen 8
    'sword': ['shield'],
    'shield': ['sword'],
    'brilliant-diamond': ['shining-pearl'],
    'shining-pearl': ['brilliant-diamond'],
    # Gen 9
    'scarlet': ['violet'],
    'violet': ['scarlet'],
}

# Catálogo canónico de números de Pokédex Nacional exclusivos de cada versión
VERSION_EXCLUSIVES_CATALOG: Dict[str, List[int]] = {
    # Gen 1
    'red': [
        23, 24,      # Ekans, Arbok
        43, 44, 45,  # Oddish, Gloom, Vileplume
        56, 57,      # Mankey, Primeape
        58, 59,      # Growlithe, Arcanine
        123,         # Scyther
        125,         # Electabuzz
    ],
    'blue': [
        27, 28,      # Sandshrew, Sandslash
        37, 38,      # Vulpix, Ninetales
        52, 53,      # Meowth, Persian
        69, 70, 71,  # Bellsprout, Weepinbell, Victreebel
        126,         # Magmar
        127,         # Pinsir
    ],
    'yellow': [],    # Amarillo no tiene exclusivos propios bloqueados hacia Rojo/Azul
    # Gen 2
    'gold': [56, 57, 58, 59, 167, 168, 207, 216, 217, 226],
    'silver': [37, 38, 52, 53, 165, 166, 225, 227, 231, 232],
    'crystal': [251],
    # Gen 3
    'ruby': [273, 274, 275, 303, 335, 338, 381, 383],
    'sapphire': [270, 271, 272, 302, 336, 337, 380, 382],
    'emerald': [
        52, 53,                             # Meowth (Intercambio en Frente de Batalla), Persian (Evolución)
        132,                                # Ditto (Túnel del Desierto)
        151,                                # Mew (Evento Isla Suprema con Mapa Viejo)
        152, 153, 154,                      # Chikorita (Regalo Abedul), Bayleef, Meganium
        155, 156, 157,                      # Cyndaquil (Regalo Abedul), Quilava, Typhlosion
        158, 159, 160,                      # Totodile (Regalo Abedul), Croconaw, Feraligatr
        163, 164,                           # Hoothoot, Noctowl (Zona Safari expansión)
        165, 166,                           # Ledyba, Ledian (Zona Safari expansión)
        167, 168,                           # Spinarak, Ariados (Zona Safari expansión)
        179, 180, 181,                      # Mareep, Flaaffy, Ampharos (Zona Safari expansión)
        185,                                # Sudowoodo (Frente de Batalla)
        190,                                # Aipom (Zona Safari expansión)
        191, 192,                           # Sunkern, Sunflora (Zona Safari expansión)
        194, 195,                           # Wooper, Quagsire (Zona Safari expansión)
        204, 205,                           # Pineco, Forretress (Zona Safari expansión)
        207,                                # Gligar (Zona Safari expansión)
        209, 210,                           # Snubbull, Granbull (Zona Safari expansión)
        213,                                # Shuckle (Zona Safari expansión)
        216, 217,                           # Teddiursa, Ursaring (Zona Safari expansión)
        223, 224,                           # Remoraid, Octillery (Zona Safari expansión)
        228, 229,                           # Houndour, Houndoom (Zona Safari expansión)
        234,                                # Stantler (Zona Safari expansión)
        235,                                # Smeargle (Cueva Taller)
        241,                                # Miltank (Zona Safari expansión)
        249, 250,                           # Lugia, Ho-Oh (Evento Roca Ombligo con Ticket Místico)
        386,                                # Deoxys (Evento Isla Origen con Ori-Ticket)
    ],
    'firered': [
        23, 24,           # Ekans, Arbok
        43, 44, 45, 182,  # Oddish, Gloom, Vileplume, Bellossom
        54, 55,           # Psyduck, Golduck
        58, 59,           # Growlithe, Arcanine
        90, 91,           # Shellder, Cloyster
        123, 212,         # Scyther, Scizor
        125, 239,         # Electabuzz, Elekid
        194, 195,         # Wooper, Quagsire
        198,              # Murkrow
        211,              # Qwilfish
        225,              # Delibird
        227,              # Skarmory
    ],
    'leafgreen': [
        27, 28,           # Sandshrew, Sandslash
        37, 38,           # Vulpix, Ninetales
        69, 70, 71,       # Bellsprout, Weepinbell, Victreebel
        79, 80, 199,      # Slowpoke, Slowbro, Slowking
        120, 121,         # Staryu, Starmie
        126, 240,         # Magmar, Magby
        127,              # Pinsir
        183, 184, 298,    # Marill, Azumarill, Azurill
        200,              # Misdreavus
        215,              # Sneasel
        223, 224,         # Remoraid, Octillery
        226,              # Mantine
    ],
    # Gen 4
    'diamond': [
        86, 87,           # Seel, Dewgong (Surf / Supercaña en Rutas 226, 230)
        123, 212,         # Scyther (Ruta 229), Scizor
        198, 430,         # Murkrow (Bosque Vetusto y Torre Perdida por la noche), Honchkrow
        246, 247, 248,    # Larvitar (Ruta 207 con Poké Radar), Pupitar, Tyranitar
        261, 262,         # Poochyena (Ruta 214 con Poké Radar), Mightyena
        304, 305, 306,    # Aron (Forja Fuego con Poké Radar), Lairon, Aggron
        352,              # Kecleon (Ruta 210 norte con Poké Radar)
        408, 409,         # Cranidos (Fósil Cráneo en Subterráneo de Sinnoh), Rampardos
        434, 435,         # Stunky (Rutas 206, 214, 221), Skuntank
        483,              # Dialga (Columna Lanza)
    ],
    'pearl': [
        79, 80, 199,      # Slowpoke, Slowbro, Slowking
        127,              # Pinsir
        200, 429,         # Misdreavus, Mismagius
        228, 229,         # Houndour, Houndoom
        234,              # Stantler
        363, 364, 365,    # Spheal, Sealeo, Walrein
        371, 372, 373,    # Bagon, Shelgon, Salamence
        410, 411,         # Shieldon, Bastiodon
        431, 432,         # Glameow, Purugly
        484,              # Palkia
    ],
}

# 184 especies no nativas de Hoenn requeridas para completar la Pokédex Nacional en Pokémon Rubí y Zafiro
NON_HOENN_TRANSFERS_RUBY = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 29, 30, 31, 32, 33, 34, 35, 36, 46, 47, 48, 49, 50, 51,
    52, 53, 56, 57, 58, 59, 60, 61, 62, 69, 70, 71, 77, 78, 79, 80, 83, 86,
    87, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 102, 103, 104, 105, 106, 107,
    108, 113, 114, 115, 122, 123, 124, 125, 126, 128, 131, 132, 133, 134, 135,
    136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150,
    151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165,
    166, 167, 168, 173, 175, 176, 179, 180, 181, 185, 186, 187, 188, 189, 190,
    191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 204, 205, 206, 207,
    208, 209, 210, 211, 212, 213, 215, 216, 217, 220, 221, 223, 224, 225, 226,
    228, 229, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245,
    246, 247, 248, 249, 250, 251
]

# En Pokémon Esmeralda, 45 especies no nativas de Hoenn pueden conseguirse directamente en el juego:
# - Expansión postgame de la Zona Safari (Áreas 5 y 6): 30 especies de Johto
# - Túnel del Desierto: Ditto (#132)
# - Frente de Batalla: Sudowoodo (#185), Smeargle (#235) y Meowth (#052 por intercambio NPC) -> Persian (#053)
# - Villa Raíz: Regalo de iniciales de Johto del Prof. Abedul tras completar las 200 de Hoenn (#152-#160)
# - Eventos insulares del cartucho: Mew (#151 en Isla Suprema con Mapa Viejo), Lugia (#249) y Ho-Oh (#250 en Roca Ombligo con Ticket Místico)
# Por tanto, solo 139 especies de la Pokédex Nacional requieren transferencia externa obligatoria.
EMERALD_IN_GAME_OBTAINABLE_NON_HOENN = {
    52, 53,                             # Meowth (Intercambio en Frente de Batalla), Persian (Evolución)
    132,                                # Ditto (Túnel del Desierto)
    151,                                # Mew (Evento Isla Suprema con Mapa Viejo)
    152, 153, 154,                      # Chikorita (Regalo Abedul), Bayleef, Meganium
    155, 156, 157,                      # Cyndaquil (Regalo Abedul), Quilava, Typhlosion
    158, 159, 160,                      # Totodile (Regalo Abedul), Croconaw, Feraligatr
    163, 164, 165, 166, 167, 168,       # Hoothoot, Noctowl, Ledyba, Ledian, Spinarak, Ariados (Zona Safari)
    179, 180, 181,                      # Mareep, Flaaffy, Ampharos (Zona Safari)
    185,                                # Sudowoodo (Frente de Batalla)
    190,                                # Aipom (Zona Safari)
    191, 192,                           # Sunkern, Sunflora (Zona Safari)
    194, 195,                           # Wooper, Quagsire (Zona Safari)
    204, 205,                           # Pineco, Forretress (Zona Safari)
    207,                                # Gligar (Zona Safari)
    209, 210,                           # Snubbull, Granbull (Zona Safari)
    213,                                # Shuckle (Zona Safari)
    216, 217,                           # Teddiursa, Ursaring (Zona Safari)
    223, 224,                           # Remoraid, Octillery (Zona Safari)
    228, 229,                           # Houndour, Houndoom (Zona Safari)
    234,                                # Stantler (Zona Safari)
    235,                                # Smeargle (Cueva Taller)
    241,                                # Miltank (Zona Safari)
    249, 250,                           # Lugia, Ho-Oh (Evento Roca Ombligo con Ticket Místico)
}
EMERALD_CATCHABLE_JOHTO = EMERALD_IN_GAME_OBTAINABLE_NON_HOENN
NON_HOENN_TRANSFERS_EMERALD = [num for num in NON_HOENN_TRANSFERS_RUBY if num not in EMERALD_IN_GAME_OBTAINABLE_NON_HOENN]

# 167 especies no nativas de Kanto y de las Islas Sétima requeridas para completar la Pokédex Nacional en Pokémon Rojo Fuego
NON_KANTO_SEVII_TRANSFERS_FIRERED = sorted(list(
    # Iniciales de Johto (9)
    set(range(152, 161)) |
    # Especies de Johto ausentes en FRLG (24)
    {179, 180, 181, 185, 190, 191, 192, 196, 197, 203, 204, 205, 209, 210, 213, 216, 217, 222, 228, 229, 234, 235, 241, 251} |
    # Especies de Hoenn ausentes en FRLG (#252 a #385, 134; #386 Deoxys es evento insular en Isla Origen)
    set(range(252, 386))
))

# 90 especies requeridas mediante transferencia externa o intercambio para completar la Pokédex Nacional
# en Pokémon Diamante:
# 1. Iniciales y legendarios foráneos de Kanto, Johto y Hoenn (48 especies).
# 2. Especies de Inserción Dual exclusiva (Ranura 2 de GBA) y sus evoluciones (39 especies).
# 3. Especies completamente ausentes en estado salvaje en Sinnoh en D/P y sus evoluciones (3 especies: Tangela #114, Tangrowth #465 y Tropius #357).
# (Nota: Especies como Koffing, Ledyba, Spinarak, Poochyena, Taillow, Whismur, Shuppet y Wynaut no requieren transferencia externa
#  ya que sus evoluciones o progenitores -Weezing, Ledian, Ariados, Mightyena, Swellow, Loudred, Banette y Wobbuffet- aparecen de forma nativa en Sinnoh.
#  Gengar tampoco requiere transferencia externa ya que Gastly y Haunter aparecen salvajes en Sinnoh y Gengar se obtiene evolucionando por intercambio).
NON_SINNOH_TRANSFERS_DIAMOND = sorted(list(
    # Iniciales de Kanto, Johto y Hoenn (27)
    set(range(1, 10)) | set(range(152, 161)) | set(range(252, 261)) |
    # Legendarios y singulares de Kanto (5)
    {144, 145, 146, 150, 151} |
    # Legendarios y singulares de Johto (6)
    {243, 244, 245, 249, 250, 251} |
    # Legendarios y singulares de Hoenn (10)
    {377, 378, 379, 380, 381, 382, 383, 384, 385, 386} |
    # Inserción Dual exclusiva (Ranura 2 de GBA) y sus líneas evolutivas (39)
    {
        # Rojo Fuego: Caterpie (10-12), Ekans (23-24), Growlithe (58-59), Elekid (239, 125, 466)
        10, 11, 12, 23, 24, 58, 59, 239, 125, 466,
        # Verde Hoja: Weedle (13-15), Sandshrew (27-28), Vulpix (37-38), Magby (240, 126, 467)
        13, 14, 15, 27, 28, 37, 38, 240, 126, 467,
        # Rubí: Seedot (273-275), Mawile (303), Zangoose (335), Solrock (338)
        273, 274, 275, 303, 335, 338,
        # Zafiro: Lotad (270-272), Sableye (302), Seviper (336), Lunatone (337)
        270, 271, 272, 302, 336, 337,
        # Esmeralda: Pineco (204-205), Gligar (207, 472), Shuckle (213), Teddiursa (216-217)
        204, 205, 207, 472, 213, 216, 217
    } |
    # Especies totalmente ausentes en Sinnoh en D/P y sus evoluciones (3)
    {
        114, 465,           # Tangela, Tangrowth
        357                 # Tropius
    }
))

# Catálogo canónico de Pokémon a transferir (Cápsula del Tiempo / Ediciones previas o externas)
# Especies ausentes en estado salvaje en la versión que requieren transferencia externa obligatoria.
VERSION_TRANSFERS_CATALOG: Dict[str, List[int]] = {
    # Gen 1 (Amarillo no tiene versión gemela y requiere transferir 13 Pokémon de Rojo/Azul)
    'yellow': [
        13, 14, 15,  # Weedle, Kakuna, Beedrill (Rojo / Azul)
        23, 24,      # Ekans, Arbok (Rojo)
        26,          # Raichu (El Pikachu inicial rehúsa evolucionar; requiere intercambio)
        52, 53,      # Meowth, Persian (Azul)
        109, 110,    # Koffing, Weezing (Rojo / Azul)
        124,         # Jynx (Rojo / Azul mediante intercambio NPC en Celeste)
        125,         # Electabuzz (Rojo)
        126,         # Magmar (Azul)
    ],
    # Gen 2 (Oro, Plata y Cristal no tienen fósiles ni iniciales ni legendarios de Kanto salvajes;
    # requieren transferencia desde Gen 1 mediante la Cápsula del Tiempo de Bill).
    'gold': [
        1, 2, 3,     # Bulbasaur, Ivysaur, Venusaur
        4, 5, 6,     # Charmander, Charmeleon, Charizard
        7, 8, 9,     # Squirtle, Wartortle, Blastoise
        138, 139,    # Omanyte, Omastar
        140, 141,    # Kabuto, Kabutops
        144, 145, 146, # Articuno, Zapdos, Moltres
        150, 151,    # Mewtwo, Mew
    ],
    'silver': [
        1, 2, 3,     # Bulbasaur, Ivysaur, Venusaur
        4, 5, 6,     # Charmander, Charmeleon, Charizard
        7, 8, 9,     # Squirtle, Wartortle, Blastoise
        138, 139,    # Omanyte, Omastar
        140, 141,    # Kabuto, Kabutops
        144, 145, 146, # Articuno, Zapdos, Moltres
        150, 151,    # Mewtwo, Mew
    ],
    'crystal': [
        1, 2, 3,        # Bulbasaur, Ivysaur, Venusaur
        4, 5, 6,        # Charmander, Charmeleon, Charizard
        7, 8, 9,        # Squirtle, Wartortle, Blastoise
        138, 139,       # Omanyte, Omastar
        140, 141,       # Kabuto, Kabutops
        144, 145, 146,  # Articuno, Zapdos, Moltres
        150, 151,       # Mewtwo, Mew
    ],
    # Gen 3 (Pokédex Nacional de Rubí, Zafiro, Esmeralda y Rojo Fuego)
    'ruby': NON_HOENN_TRANSFERS_RUBY,
    'sapphire': NON_HOENN_TRANSFERS_RUBY,
    'emerald': NON_HOENN_TRANSFERS_EMERALD,
    'firered': NON_KANTO_SEVII_TRANSFERS_FIRERED,
    'leafgreen': NON_KANTO_SEVII_TRANSFERS_FIRERED,
    # Gen 4 (Pokédex Nacional de Diamante)
    'diamond': NON_SINNOH_TRANSFERS_DIAMOND,
}

# Metadatos descriptivos de la mecánica de transferencia según la generación y juego
VERSION_TRANSFERS_META: Dict[str, Dict[str, Any]] = {
    'yellow': {
        'mechanic_title': 'Transferencia Link • Gen 1',
        'mechanic_badge': 'Transferencia Link',
        'description': 'Estos 13 Pokémon no aparecen salvajes ni pueden evolucionar en tu edición de Pokémon Amarillo. Para completar la Pokédex requieres conseguirlos mediante transferencia o intercambio con un jugador de Pokémon Rojo o Pokémon Azul.',
        'origins': {
            13: 'Rojo / Azul',
            14: 'Rojo / Azul',
            15: 'Rojo / Azul',
            23: 'Rojo',
            24: 'Rojo',
            26: 'Rojo / Azul',
            52: 'Azul',
            53: 'Azul',
            109: 'Rojo / Azul',
            110: 'Rojo / Azul',
            124: 'Rojo / Azul',
            125: 'Rojo',
            126: 'Azul',
        }
    },
    'gold': {
        'mechanic_title': 'Cápsula del Tiempo • Gen 1',
        'mechanic_badge': 'Cápsula del Tiempo',
        'description': 'Estos 18 Pokémon no aparecen salvajes ni pueden conseguirse en Johto o Kanto de la 2.ª Generación. Para completar la Pokédex requieres transferirlos desde la 1.ª Generación (Pokémon Rojo, Azul o Amarillo) utilizando la Cápsula del Tiempo de Bill en la planta superior del Centro Pokémon.',
        'default_origin': 'Rojo / Azul / Amarillo',
        'origins': {
            1: 'Rojo / Azul / Amarillo',
            2: 'Rojo / Azul / Amarillo',
            3: 'Rojo / Azul / Amarillo',
            4: 'Rojo / Azul / Amarillo',
            5: 'Rojo / Azul / Amarillo',
            6: 'Rojo / Azul / Amarillo',
            7: 'Rojo / Azul / Amarillo',
            8: 'Rojo / Azul / Amarillo',
            9: 'Rojo / Azul / Amarillo',
            138: 'Rojo / Azul / Amarillo',
            139: 'Rojo / Azul / Amarillo',
            140: 'Rojo / Azul / Amarillo',
            141: 'Rojo / Azul / Amarillo',
            144: 'Rojo / Azul / Amarillo',
            145: 'Rojo / Azul / Amarillo',
            146: 'Rojo / Azul / Amarillo',
            150: 'Rojo / Azul / Amarillo',
            151: 'Evento Gen 1 / Rojo / Azul',
        }
    },
    'silver': {
        'mechanic_title': 'Cápsula del Tiempo • Gen 1',
        'mechanic_badge': 'Cápsula del Tiempo',
        'description': 'Estos 18 Pokémon no aparecen salvajes ni pueden conseguirse en Johto o Kanto de la 2.ª Generación. Para completar la Pokédex requieres transferirlos desde la 1.ª Generación (Pokémon Rojo, Azul o Amarillo) utilizando la Cápsula del Tiempo de Bill en la planta superior del Centro Pokémon.',
        'default_origin': 'Rojo / Azul / Amarillo',
        'origins': {
            1: 'Rojo / Azul / Amarillo',
            2: 'Rojo / Azul / Amarillo',
            3: 'Rojo / Azul / Amarillo',
            4: 'Rojo / Azul / Amarillo',
            5: 'Rojo / Azul / Amarillo',
            6: 'Rojo / Azul / Amarillo',
            7: 'Rojo / Azul / Amarillo',
            8: 'Rojo / Azul / Amarillo',
            9: 'Rojo / Azul / Amarillo',
            138: 'Rojo / Azul / Amarillo',
            139: 'Rojo / Azul / Amarillo',
            140: 'Rojo / Azul / Amarillo',
            141: 'Rojo / Azul / Amarillo',
            144: 'Rojo / Azul / Amarillo',
            145: 'Rojo / Azul / Amarillo',
            146: 'Rojo / Azul / Amarillo',
            150: 'Rojo / Azul / Amarillo',
            151: 'Evento Gen 1 / Rojo / Azul',
        }
    },
    'crystal': {
        'mechanic_title': 'Cápsula del Tiempo • Gen 1',
        'mechanic_badge': 'Cápsula del Tiempo',
        'description': 'Estos 18 Pokémon no aparecen salvajes ni pueden conseguirse en Johto o Kanto de la 2.ª Generación. Para completar la Pokédex requieres transferirlos desde la 1.ª Generación (Pokémon Rojo, Azul o Amarillo) utilizando la Cápsula del Tiempo de Bill en la planta superior del Centro Pokémon.',
        'default_origin': 'Rojo / Azul / Amarillo',
        'origins': {
            1: 'Rojo / Azul / Amarillo',
            2: 'Rojo / Azul / Amarillo',
            3: 'Rojo / Azul / Amarillo',
            4: 'Rojo / Azul / Amarillo',
            5: 'Rojo / Azul / Amarillo',
            6: 'Rojo / Azul / Amarillo',
            7: 'Rojo / Azul / Amarillo',
            8: 'Rojo / Azul / Amarillo',
            9: 'Rojo / Azul / Amarillo',
            138: 'Rojo / Azul / Amarillo',
            139: 'Rojo / Azul / Amarillo',
            140: 'Rojo / Azul / Amarillo',
            141: 'Rojo / Azul / Amarillo',
            144: 'Rojo / Azul / Amarillo',
            145: 'Rojo / Azul / Amarillo',
            146: 'Rojo / Azul / Amarillo',
            150: 'Rojo / Azul / Amarillo',
            151: 'Evento Gen 1 / Rojo / Azul',
        }
    },
    'ruby': {
        'mechanic_title': 'Transferencia Interjuegos • Gen 3',
        'mechanic_badge': 'GBA / GameCube',
        'description': (
            'La Pokédex Nacional de Pokémon Rubí consta de 386 Pokémon. Las 184 especies no nativas de Hoenn '
            'deben ser transferidas mediante cable link desde Pokémon Rojo Fuego, Pokémon Verde Hoja o Pokémon Esmeralda, '
            'o importadas desde títulos de Nintendo GameCube (Pokémon Colosseum y Pokémon XD: Gale of Darkness). '
            '¡IMPORTANTE!: Debido al cambio de arquitectura de hardware y datos, NO ES POSIBLE transferir Pokémon '
            'de ninguna forma desde los juegos de Primera Generación (Rojo, Azul, Amarillo) ni Segunda Generación (Oro, Plata, Cristal).'
        ),
        'default_origin': 'Rojo Fuego / Verde Hoja / GameCube',
        'incompatible_warning': 'Incompatible con 1.ª y 2.ª Generación (Hardware break). Todas las transferencias deben provenir de títulos de GBA o Nintendo GameCube.',
        'origins': {
            1: 'Rojo Fuego / Verde Hoja',
            2: 'Rojo Fuego / Verde Hoja',
            3: 'Rojo Fuego / Verde Hoja',
            4: 'Rojo Fuego / Verde Hoja',
            5: 'Rojo Fuego / Verde Hoja',
            6: 'Rojo Fuego / Verde Hoja',
            7: 'Rojo Fuego / Verde Hoja',
            8: 'Rojo Fuego / Verde Hoja',
            9: 'Rojo Fuego / Verde Hoja',
            144: 'Rojo Fuego / Verde Hoja',
            145: 'Rojo Fuego / Verde Hoja',
            146: 'Rojo Fuego / Verde Hoja',
            150: 'Rojo Fuego / Verde Hoja',
            151: 'Evento Isla Suprema (Mapa Viejo)',
            152: 'Pokémon Colosseum (GameCube)',
            153: 'Pokémon Colosseum (GameCube)',
            154: 'Pokémon Colosseum (GameCube)',
            155: 'Pokémon Colosseum (GameCube)',
            156: 'Pokémon Colosseum (GameCube)',
            157: 'Pokémon Colosseum (GameCube)',
            158: 'Pokémon Colosseum (GameCube)',
            159: 'Pokémon Colosseum (GameCube)',
            160: 'Pokémon Colosseum (GameCube)',
            243: 'Pokémon Colosseum / Rojo Fuego',
            244: 'Pokémon Colosseum / Verde Hoja',
            245: 'Pokémon Colosseum / RF / VH',
            249: 'Pokémon XD: Gale of Darkness (GameCube)',
            250: 'Pokémon Colosseum (GameCube)',
            251: 'Disco Bonus Colosseum / Evento Ageto',
        }
    },
    'sapphire': {
        'mechanic_title': 'Transferencia Interjuegos • Gen 3',
        'mechanic_badge': 'GBA / GameCube',
        'description': (
            'La Pokédex Nacional de Pokémon Zafiro consta de 386 Pokémon. Las 184 especies no nativas de Hoenn '
            'deben ser transferidas mediante cable link desde Pokémon Rojo Fuego, Pokémon Verde Hoja o Pokémon Esmeralda, '
            'o importadas desde títulos de Nintendo GameCube (Pokémon Colosseum y Pokémon XD: Gale of Darkness). '
            '¡IMPORTANTE!: Debido al cambio de arquitectura de hardware y datos, NO ES POSIBLE transferir Pokémon '
            'de ninguna forma desde los juegos de Primera Generación (Rojo, Azul, Amarillo) ni Segunda Generación (Oro, Plata, Cristal).'
        ),
        'default_origin': 'Rojo Fuego / Verde Hoja / GameCube',
        'incompatible_warning': 'Incompatible con 1.ª y 2.ª Generación (Hardware break). Todas las transferencias deben provenir de títulos de GBA o Nintendo GameCube.',
        'origins': {
            1: 'Rojo Fuego / Verde Hoja',
            2: 'Rojo Fuego / Verde Hoja',
            3: 'Rojo Fuego / Verde Hoja',
            4: 'Rojo Fuego / Verde Hoja',
            5: 'Rojo Fuego / Verde Hoja',
            6: 'Rojo Fuego / Verde Hoja',
            7: 'Rojo Fuego / Verde Hoja',
            8: 'Rojo Fuego / Verde Hoja',
            9: 'Rojo Fuego / Verde Hoja',
            144: 'Rojo Fuego / Verde Hoja',
            145: 'Rojo Fuego / Verde Hoja',
            146: 'Rojo Fuego / Verde Hoja',
            150: 'Rojo Fuego / Verde Hoja',
            151: 'Evento Isla Suprema (Mapa Viejo)',
            152: 'Pokémon Colosseum (GameCube)',
            153: 'Pokémon Colosseum (GameCube)',
            154: 'Pokémon Colosseum (GameCube)',
            155: 'Pokémon Colosseum (GameCube)',
            156: 'Pokémon Colosseum (GameCube)',
            157: 'Pokémon Colosseum (GameCube)',
            158: 'Pokémon Colosseum (GameCube)',
            159: 'Pokémon Colosseum (GameCube)',
            160: 'Pokémon Colosseum (GameCube)',
            243: 'Pokémon Colosseum / Rojo Fuego',
            244: 'Pokémon Colosseum / Verde Hoja',
            245: 'Pokémon Colosseum / RF / VH',
            249: 'Pokémon XD: Gale of Darkness (GameCube)',
            250: 'Pokémon Colosseum (GameCube)',
            251: 'Disco Bonus Colosseum / Evento Ageto',
        }
    },
    'emerald': {
        'mechanic_title': 'Transferencia Interjuegos • Gen 3',
        'mechanic_badge': 'GBA / GameCube',
        'description': (
            'La Pokédex Nacional de Pokémon Esmeralda consta de 386 Pokémon. Gracias a la ampliación postgame de la Zona Safari de Hoenn, '
            'la Cueva Taller, el Túnel del Desierto, el intercambio en el Frente de Batalla, el regalo inicial de Johto del Prof. Abedul '
            'y los eventos en islas (Roca Ombligo e Isla Suprema), 45 especies de Johto y Kanto ahora son obtenibles en el propio cartucho. '
            'Las 139 especies restantes no nativas deben transferirse mediante cable link desde Pokémon Rojo Fuego, Pokémon Verde Hoja '
            'o importarse desde Nintendo GameCube (Pokémon Colosseum y Pokémon XD: Gale of Darkness). '
            '¡IMPORTANTE!: Incompatible con 1.ª y 2.ª Generación (Hardware break).'
        ),
        'default_origin': 'Rojo Fuego / Verde Hoja / GameCube',
        'incompatible_warning': 'Incompatible con 1.ª y 2.ª Generación (Hardware break). Todas las transferencias deben provenir de títulos de GBA o Nintendo GameCube.',
        'origins': {
            1: 'Rojo Fuego / Verde Hoja',
            2: 'Rojo Fuego / Verde Hoja',
            3: 'Rojo Fuego / Verde Hoja',
            4: 'Rojo Fuego / Verde Hoja',
            5: 'Rojo Fuego / Verde Hoja',
            6: 'Rojo Fuego / Verde Hoja',
            7: 'Rojo Fuego / Verde Hoja',
            8: 'Rojo Fuego / Verde Hoja',
            9: 'Rojo Fuego / Verde Hoja',
            144: 'Rojo Fuego / Verde Hoja',
            145: 'Rojo Fuego / Verde Hoja',
            146: 'Rojo Fuego / Verde Hoja',
            150: 'Rojo Fuego / Verde Hoja',
            243: 'Pokémon Colosseum / Rojo Fuego',
            244: 'Pokémon Colosseum / Verde Hoja',
            245: 'Pokémon Colosseum / RF / VH',
            251: 'Disco Bonus Colosseum / Evento Ageto',
        }
    },
    'firered': {
        'mechanic_title': 'Transferencia Interjuegos • Gen 3',
        'mechanic_badge': 'GBA / GameCube',
        'description': (
            'La Pokédex Nacional de Pokémon Rojo Fuego consta de 386 Pokémon. Las 167 especies no nativas de Kanto y de las Islas Sétima '
            'deben transferirse mediante cable link desde Pokémon Rubí, Zafiro o Esmeralda (Hoenn), '
            'o importarse desde Nintendo GameCube (Pokémon Colosseum y Pokémon XD: Gale of Darkness). '
            '¡IMPORTANTE!: Debido al salto tecnológico, es incompatible con la 1.ª y 2.ª Generación (Hardware break).'
        ),
        'altering_cave_note': (
            'Nota sobre la Cueva Cambiante: Especies como Mareep, Aipom, Pineco, Shuckle, Teddiursa, Houndour, '
            'Stantler y Smeargle fueron programadas internamente en la Cueva Cambiante para activarse mediante tarjetas del periférico '
            'Nintendo e-Reader (Mystery Event). Como dichas tarjetas nunca llegaron a distribuirse en ninguna región del mundo, '
            'en los cartuchos originales únicamente aparece Zubat (100%), siendo técnicamente imposible capturarlas allí de forma salvaje '
            'y requiriendo transferencia externa obligatoria (desde Pokémon Esmeralda o títulos de GameCube).'
        ),
        'default_origin': 'Rubí / Zafiro / Esmeralda / GameCube',
        'incompatible_warning': 'Incompatible con 1.ª y 2.ª Generación (Hardware break). Todas las transferencias deben provenir de títulos de GBA o Nintendo GameCube.',
        'origins': {
            152: 'Pokémon Esmeralda / Colosseum',
            153: 'Pokémon Esmeralda / Colosseum',
            154: 'Pokémon Esmeralda / Colosseum',
            155: 'Pokémon Esmeralda / Colosseum',
            156: 'Pokémon Esmeralda / Colosseum',
            157: 'Pokémon Esmeralda / Colosseum',
            158: 'Pokémon Esmeralda / Colosseum',
            159: 'Pokémon Esmeralda / Colosseum',
            160: 'Pokémon Esmeralda / Colosseum',
            179: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            190: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            196: 'Rubí / Zafiro / Esmeralda (Evolución Día)',
            197: 'Rubí / Zafiro / Esmeralda (Evolución Noche)',
            204: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            213: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            216: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            228: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            234: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            235: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            251: 'Disco Bonus Colosseum / Evento Ageto',
            385: 'Pokémon Channel / Disco Bonus Colosseum',
        }
    },
    'leafgreen': {
        'mechanic_title': 'Transferencia Interjuegos • Gen 3',
        'mechanic_badge': 'GBA / GameCube',
        'description': (
            'La Pokédex Nacional de Pokémon Verde Hoja consta de 386 Pokémon. Las 167 especies no nativas de Kanto y de las Islas Sétima '
            'deben transferirse mediante cable link desde Pokémon Rubí, Zafiro o Esmeralda (Hoenn), '
            'o importarse desde Nintendo GameCube (Pokémon Colosseum y Pokémon XD: Gale of Darkness). '
            '¡IMPORTANTE!: Debido al salto tecnológico, es incompatible con la 1.ª y 2.ª Generación (Hardware break).'
        ),
        'altering_cave_note': (
            'Nota sobre la Cueva Cambiante: Especies como Mareep, Aipom, Pineco, Shuckle, Teddiursa, Houndour, '
            'Stantler y Smeargle fueron programadas internamente en la Cueva Cambiante para activarse mediante tarjetas del periférico '
            'Nintendo e-Reader (Mystery Event). Como dichas tarjetas nunca llegaron a distribuirse en ninguna región del mundo, '
            'en los cartuchos originales únicamente aparece Zubat (100%), siendo técnicamente imposible capturarlas allí de forma salvaje '
            'y requiriendo transferencia externa obligatoria (desde Pokémon Esmeralda o títulos de GameCube).'
        ),
        'default_origin': 'Rubí / Zafiro / Esmeralda / GameCube',
        'incompatible_warning': 'Incompatible con 1.ª y 2.ª Generación (Hardware break). Todas las transferencias deben provenir de títulos de GBA o Nintendo GameCube.',
        'origins': {
            152: 'Pokémon Esmeralda / Colosseum',
            153: 'Pokémon Esmeralda / Colosseum',
            154: 'Pokémon Esmeralda / Colosseum',
            155: 'Pokémon Esmeralda / Colosseum',
            156: 'Pokémon Esmeralda / Colosseum',
            157: 'Pokémon Esmeralda / Colosseum',
            158: 'Pokémon Esmeralda / Colosseum',
            159: 'Pokémon Esmeralda / Colosseum',
            160: 'Pokémon Esmeralda / Colosseum',
            179: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            190: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            196: 'Rubí / Zafiro / Esmeralda (Evolución Día)',
            197: 'Rubí / Zafiro / Esmeralda (Evolución Noche)',
            204: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            213: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            216: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            228: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            234: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            235: 'Esmeralda / Colosseum (Cueva Cambiante inactiva)',
            251: 'Disco Bonus Colosseum / Evento Ageto',
            385: 'Pokémon Channel / Disco Bonus Colosseum',
        }
    },
    'diamond': {
        'mechanic_title': 'Transferencia y Parque Compi • Gen 4',
        'mechanic_badge': 'Transferir / GBA',
        'description': (
            'La Pokédex Nacional de Pokémon Diamante consta de 493 Pokémon. Estas 90 especies comprenden los iniciales '
            'y criaturas legendarias foráneas, las especies cuya única presencia salvaje requiere cartuchos de GBA en la Ranura 2 '
            '(Inserción Dual), y las especies totalmente ausentes en estado salvaje en Sinnoh (Tangela, Tangrowth y Tropius). '
            'Para completar tu partida, puedes transferirlos permanentemente desde cartuchos de Game Boy Advance '
            '(Pokémon Rubí, Zafiro, Esmeralda, Rojo Fuego o Verde Hoja) a través del Parque Compi en la Ruta 221, '
            'o intercambiarlos de forma directa en Nintendo DS con entregas posteriores de la misma generación '
            '(Pokémon Platino y Pokémon HeartGold / SoulSilver).'
        ),
        'default_origin': 'Parque Compi (GBA) / Platino / HGSS',
        'origins': {
            # Iniciales y legendarios de Kanto, Johto y Hoenn
            1: 'Rojo Fuego / Verde Hoja',
            2: 'Rojo Fuego / Verde Hoja',
            3: 'Rojo Fuego / Verde Hoja',
            4: 'Rojo Fuego / Verde Hoja',
            5: 'Rojo Fuego / Verde Hoja',
            6: 'Rojo Fuego / Verde Hoja',
            7: 'Rojo Fuego / Verde Hoja',
            8: 'Rojo Fuego / Verde Hoja',
            9: 'Rojo Fuego / Verde Hoja',
            144: 'Rojo Fuego / Verde Hoja / Platino',
            145: 'Rojo Fuego / Verde Hoja / Platino',
            146: 'Rojo Fuego / Verde Hoja / Platino',
            150: 'Rojo Fuego / Verde Hoja / HGSS',
            151: 'Evento GBA (Mapa Viejo)',
            152: 'Esmeralda / HGSS',
            153: 'Esmeralda / HGSS',
            154: 'Esmeralda / HGSS',
            155: 'Esmeralda / HGSS',
            156: 'Esmeralda / HGSS',
            157: 'Esmeralda / HGSS',
            158: 'Esmeralda / HGSS',
            159: 'Esmeralda / HGSS',
            160: 'Esmeralda / HGSS',
            243: 'Rojo Fuego / HGSS',
            244: 'Verde Hoja / HGSS',
            245: 'Rojo Fuego / Verde Hoja / HGSS',
            249: 'XD: Gale of Darkness / HGSS',
            250: 'Colosseum / HGSS',
            251: 'Evento GBA / Ageto / HGSS',
            252: 'Rubí / Zafiro / Esmeralda / HGSS',
            253: 'Rubí / Zafiro / Esmeralda / HGSS',
            254: 'Rubí / Zafiro / Esmeralda / HGSS',
            255: 'Rubí / Zafiro / Esmeralda / HGSS',
            256: 'Rubí / Zafiro / Esmeralda / HGSS',
            257: 'Rubí / Zafiro / Esmeralda / HGSS',
            258: 'Rubí / Zafiro / Esmeralda / HGSS',
            259: 'Rubí / Zafiro / Esmeralda / HGSS',
            260: 'Rubí / Zafiro / Esmeralda / HGSS',
            377: 'Rubí / Zafiro / Esmeralda / Platino',
            378: 'Rubí / Zafiro / Esmeralda / Platino',
            379: 'Rubí / Zafiro / Esmeralda / Platino',
            380: 'Rubí / Esmeralda / HGSS',
            381: 'Zafiro / Esmeralda / HGSS',
            382: 'Zafiro / Esmeralda / HGSS',
            383: 'Rubí / Esmeralda / HGSS',
            384: 'Rubí / Zafiro / Esmeralda / HGSS',
            385: 'Disco Bonus Colosseum / Evento GBA',
            386: 'Evento Isla Origen (Ori-Ticket)',

            # Inserción Dual exclusiva (Ranura 2 de GBA) y sus líneas evolutivas
            10: 'GBA: Rojo Fuego / HGSS',
            11: 'GBA: Rojo Fuego / HGSS',
            12: 'GBA: Rojo Fuego / HGSS',
            13: 'GBA: Verde Hoja / HGSS',
            14: 'GBA: Verde Hoja / HGSS',
            15: 'GBA: Verde Hoja / HGSS',
            23: 'GBA: Rojo Fuego / HGSS',
            24: 'GBA: Rojo Fuego / HGSS',
            27: 'GBA: Verde Hoja / HGSS',
            28: 'GBA: Verde Hoja / HGSS',
            37: 'GBA: Verde Hoja / HGSS',
            38: 'GBA: Verde Hoja / HGSS',
            58: 'GBA: Rojo Fuego / HGSS',
            59: 'GBA: Rojo Fuego / HGSS',
            125: 'GBA: Rojo Fuego / Platino',
            126: 'GBA: Verde Hoja / Platino',
            204: 'GBA: Esmeralda / HGSS',
            205: 'GBA: Esmeralda / HGSS',
            207: 'GBA: Esmeralda / Platino / HGSS',
            213: 'GBA: Esmeralda / HGSS',
            216: 'GBA: Esmeralda / HGSS',
            217: 'GBA: Esmeralda / HGSS',
            239: 'GBA: Rojo Fuego / Platino',
            240: 'GBA: Verde Hoja / Platino',
            270: 'GBA: Zafiro / HGSS',
            271: 'GBA: Zafiro / HGSS',
            272: 'GBA: Zafiro / HGSS',
            273: 'GBA: Rubí / HGSS',
            274: 'GBA: Rubí / HGSS',
            275: 'GBA: Rubí / HGSS',
            302: 'GBA: Zafiro / HGSS',
            303: 'GBA: Rubí / HGSS',
            335: 'GBA: Rubí / HGSS',
            336: 'GBA: Zafiro / HGSS',
            337: 'GBA: Zafiro / HGSS',
            338: 'GBA: Rubí / HGSS',
            466: 'GBA: Rojo Fuego / Platino',
            467: 'GBA: Verde Hoja / Platino',
            472: 'GBA: Esmeralda / Platino / HGSS',

            # Especies totalmente ausentes en estado salvaje en Sinnoh en D/P y sus evoluciones
            114: 'GBA / Platino / HGSS',
            357: 'GBA / Platino / HGSS',
            465: 'GBA / Platino / HGSS',
        }
    },
}

# Nombres cortos amigables para los botones y pestañas (ej: "Exclusivos de Azul")
GAME_SHORT_NAMES: Dict[str, str] = {
    'red': 'Rojo',
    'blue': 'Azul',
    'yellow': 'Amarillo',
    'gold': 'Oro',
    'silver': 'Plata',
    'crystal': 'Cristal',
    'ruby': 'Rubí',
    'sapphire': 'Zafiro',
    'emerald': 'Esmeralda',
    'firered': 'Rojo Fuego',
    'leafgreen': 'Verde Hoja',
    'diamond': 'Diamante',
    'pearl': 'Perla',
    'platinum': 'Platino',
    'heartgold': 'HeartGold',
    'soulsilver': 'SoulSilver',
    'black': 'Negro',
    'white': 'Blanco',
    'black-2': 'Negro 2',
    'white-2': 'Blanco 2',
    'x': 'X',
    'y': 'Y',
    'omega-ruby': 'Rubí Omega',
    'alpha-sapphire': 'Zafiro Alfa',
    'sun': 'Sol',
    'moon': 'Luna',
    'ultra-sun': 'Ultra Sol',
    'ultra-moon': 'Ultra Luna',
    'lets-go-pikachu': 'Pikachu',
    'lets-go-eevee': 'Eevee',
    'sword': 'Espada',
    'shield': 'Escudo',
    'brilliant-diamond': 'Diamante Brillante',
    'shining-pearl': 'Perla Reluciente',
    'scarlet': 'Escarlata',
    'violet': 'Púrpura',
}

# Configuración específica para terceras versiones que hacen referencia a ambas versiones gemelas
THIRD_VERSION_COUNTERPART_EXCLUSIVES: Dict[str, Dict[str, Any]] = {
    'crystal': {
        'counterpart_short_name': 'Oro y Plata',
        'counterpart_name': 'Pokémon Oro o Pokémon Plata',
        'counterpart_slug': 'gold',
        'counterpart_theme': 'gold_silver',
        'exclusive_nums': [37, 38, 56, 57, 179, 180, 181, 203, 223, 224],
        'origins': {
            37: 'Plata',
            38: 'Plata',
            56: 'Oro',
            57: 'Oro',
            179: 'Oro / Plata',
            180: 'Oro / Plata',
            181: 'Oro / Plata',
            203: 'Oro / Plata',
            223: 'Oro / Plata',
            224: 'Oro / Plata',
        },
        'notice': 'Estos Pokémon <span class="underline">no aparecen salvajes</span> en tu edición de <strong>Pokémon Cristal</strong>. Para completar la Pokédex requieres conseguirlos mediante intercambio con un jugador de <strong>Pokémon Oro</strong> o <strong>Pokémon Plata</strong>.',
    },
    'emerald': {
        'counterpart_short_name': 'Rubí y Zafiro',
        'counterpart_name': 'Pokémon Rubí o Pokémon Zafiro',
        'counterpart_slug': 'ruby',
        'counterpart_theme': 'ruby_sapphire',
        'exclusive_nums': [283, 284, 307, 308, 315, 335, 337],
        'origins': {
            283: 'Rubí / Zafiro',
            284: 'Rubí / Zafiro',
            307: 'Rubí / Zafiro',
            308: 'Rubí / Zafiro',
            315: 'Rubí / Zafiro',
            335: 'Rubí',
            337: 'Zafiro',
        },
        'notice': 'Estos 7 Pokémon <span class="underline">no habitan en estado salvaje</span> en tu edición de <strong>Pokémon Esmeralda</strong>. Para completar la Pokédex de Hoenn requieres conseguirlos mediante intercambio con un jugador de <strong>Pokémon Rubí</strong> o <strong>Pokémon Zafiro</strong>.',
    }
}


def _build_exclusive_item(
    national_num: int,
    current_pokedex: Pokedex,
    current_generation: int,
    caught_entry_ids: set,
    is_counterpart: bool,
    origin_badge: Optional[str] = None,
    entries_by_num: Optional[Dict[int, CatalogEntry]] = None,
    shiny_caught_entry_ids: Optional[set] = None
) -> Optional[Dict[str, Any]]:
    """Construye los datos estructurados de un Pokémon exclusivo o faltante para la plantilla."""
    if entries_by_num and national_num in entries_by_num:
        entry = entries_by_num[national_num]
    else:
        game_slug = current_pokedex.game.slug if (current_pokedex and hasattr(current_pokedex, 'game') and current_pokedex.game) else ""
        from .catalog_service import get_compiled_catalog
        entry = None
        if game_slug:
            nat_catalog = get_compiled_catalog(game_slug, is_national=True) or []
            entry = next((e for e in nat_catalog if e.pokemon and e.pokemon.national_number == national_num), None)
            if not entry:
                reg_catalog = get_compiled_catalog(game_slug, is_national=False) or []
                entry = next((e for e in reg_catalog if e.pokemon and e.pokemon.national_number == national_num), None)

    if entry:
        pokemon = entry.pokemon
        entry_id = entry.id
        number = entry.entry_number
        is_caught = entry.id in caught_entry_ids
        is_shiny_caught = (entry.id in shiny_caught_entry_ids) if shiny_caught_entry_ids else False
        primary_type = entry.primary_type_display
        primary_type_es = entry.primary_type_es
        secondary_type = entry.secondary_type_display
        secondary_type_es = entry.secondary_type_es
        sprite_retro = entry.game_sprite_url or pokemon.sprite_url
        sprite_modern = pokemon.sprite_url
        sprite_retro_shiny = entry.game_sprite_shiny_url
        sprite_modern_shiny = entry.modern_sprite_shiny_url
        obtaining_summary = entry.obtaining_info.get('summary', '') if entry.obtaining_info else ''
        evolution_stone = entry.evolution_stone
    else:
        # Fallback a catálogo en memoria en O(1)
        pokemon = get_pokemon_by_national_number(national_num)
        if not pokemon:
            return None
        entry_id = None
        number = pokemon.national_number
        is_caught = False
        is_shiny_caught = False
        primary_type = pokemon.primary_type
        primary_type_es = pokemon.primary_type_es
        secondary_type = pokemon.secondary_type
        secondary_type_es = pokemon.secondary_type_es
        sprite_retro = pokemon.sprite_url
        sprite_modern = pokemon.sprite_url
        sprite_retro_shiny = pokemon.sprite_shiny_url
        sprite_modern_shiny = pokemon.artwork_shiny_url
        obtaining_summary = ''
        evolution_stone = None

    game_slug = current_pokedex.game.slug if (current_pokedex and hasattr(current_pokedex, 'game') and current_pokedex.game) else ""
    if current_generation == 2 and game_slug and (not sprite_retro_shiny or "pokeapi" in sprite_retro_shiny.lower()):
        from django.conf import settings
        from pathlib import Path
        local_rel = f"pokemon/sprites/{game_slug}_shiny/{national_num}.png"
        if (Path(settings.MEDIA_ROOT) / local_rel).exists() or True:
            sprite_retro_shiny = f"{settings.MEDIA_URL}{local_rel}"

    pc_icon_url = pokemon.get_pc_icon_url(generation=current_generation)
    if game_slug == 'emerald' and national_num == 386:
        pc_icon_url = "/media/pokemon/icons/gen3/10003.png"
        sprite_retro = "/media/pokemon/sprites/emerald/386-speed.png"
        sprite_retro_shiny = "/media/pokemon/sprites/emerald_shiny/386-speed.png"

    return {
        'entry_id': entry_id,
        'national_number': national_num,
        'number': f"{number:03d}",
        'name': pokemon.display_name,
        'primary_type': (primary_type or '').lower(),
        'primary_type_es': primary_type_es,
        'secondary_type': (secondary_type or '').lower(),
        'secondary_type_es': secondary_type_es or '',
        'sprite_retro': sprite_retro,
        'sprite_modern': sprite_modern,
        'sprite_retro_shiny': sprite_retro_shiny,
        'sprite_modern_shiny': sprite_modern_shiny,
        'pc_icon_url': pc_icon_url,
        'is_caught': is_caught,
        'is_shiny_caught': is_shiny_caught,
        'summary': obtaining_summary,
        'is_counterpart': is_counterpart,
        'origin_badge': origin_badge,
        'evolution_stone': evolution_stone,
        'modal_data_json': getattr(entry, 'modal_data_json', '') if entry else '',
    }


def get_version_exclusives_context(
    current_game: Game,
    current_pokedex: Pokedex,
    caught_entry_ids: set,
    entries_by_num: Optional[Dict[int, CatalogEntry]] = None,
    shiny_caught_entry_ids: Optional[set] = None
) -> Optional[Dict[str, Any]]:
    """
    Retorna el contexto completo para el botón y el modal de exclusivos de versión / Pokémon a transferir.
    Si el juego no tiene contrapartes o no tiene exclusivos/faltantes registrados, devuelve None.
    """
    counterparts = GAME_COUNTERPARTS.get(current_game.slug, [])
    if not counterparts:
        return None

    current_gen = current_game.generation
    current_short_name = GAME_SHORT_NAMES.get(current_game.slug, current_game.slug.title())

    # Si es Amarillo o no tiene contraparte, este juego no maneja exclusivos de versión gemela
    if current_game.slug == 'yellow':
        return None

    def _resolve_theme(slug: str) -> str:
        if slug in ['sapphire']:
            return 'sapphire'
        elif slug in ['ruby']:
            return 'ruby'
        elif slug in ['emerald']:
            return 'emerald'
        elif slug in ['firered']:
            return 'firered'
        elif slug in ['leafgreen']:
            return 'leafgreen'
        elif slug in ['diamond', 'brilliant-diamond']:
            return 'diamond'
        elif slug in ['pearl', 'shining-pearl']:
            return 'pearl'
        elif slug in ['blue', 'white', 'moon', 'shield', 'violet']:
            return 'blue'
        elif slug in ['crystal']:
            return 'crystal'
        elif slug in ['gold', 'heartgold']:
            return 'gold'
        elif slug in ['silver', 'soulsilver']:
            return 'silver'
        elif slug in ['yellow']:
            return 'amber'
        return 'red'

    own_theme = _resolve_theme(current_game.slug)

    if current_game.slug in THIRD_VERSION_COUNTERPART_EXCLUSIVES:
        conf = THIRD_VERSION_COUNTERPART_EXCLUSIVES[current_game.slug]
        counterpart_short_name = conf['counterpart_short_name']
        counterpart_name = conf['counterpart_name']
        counterpart_slug = conf.get('counterpart_slug', counterparts[0])
        counterpart_theme = conf.get('counterpart_theme', 'gold')
        counterpart_exclusive_nums = conf['exclusive_nums']
        origins = conf.get('origins', {})
        notice = conf.get('notice')
        own_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(current_game.slug, [])
    else:
        counterpart_slug = counterparts[0]
        counterpart_short_name = GAME_SHORT_NAMES.get(counterpart_slug, counterpart_slug.title())
        counterpart_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(counterpart_slug, [])
        own_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(current_game.slug, [])
        origins = {}
        notice = None
        counterpart_theme = _resolve_theme(counterpart_slug)
        counterpart_game = Game.objects.filter(slug=counterpart_slug).first()
        counterpart_name = counterpart_game.display_name if counterpart_game else f"Pokémon {counterpart_short_name}"

    if not counterpart_exclusive_nums and not own_exclusive_nums:
        return None

    button_label = "Exclusivos"
    full_button_label = f"Exclusivos de {counterpart_short_name}"

    # 1. Construir lista de exclusivos de la contraparte
    counterpart_list = []
    for num in counterpart_exclusive_nums:
        item = _build_exclusive_item(
            num,
            current_pokedex,
            current_gen,
            caught_entry_ids,
            is_counterpart=True,
            origin_badge=origins.get(num),
            entries_by_num=entries_by_num,
            shiny_caught_entry_ids=shiny_caught_entry_ids
        )
        if item:
            counterpart_list.append(item)

    # 2. Construir lista de exclusivos de la propia versión
    own_list = []
    for num in own_exclusive_nums:
        item = _build_exclusive_item(
            num, current_pokedex, current_gen, caught_entry_ids, is_counterpart=False, entries_by_num=entries_by_num, shiny_caught_entry_ids=shiny_caught_entry_ids
        )
        if item:
            own_list.append(item)

    # Estadísticas de exclusivos
    counterpart_total = len(counterpart_list)
    counterpart_caught = sum(1 for p in counterpart_list if p['is_caught'])
    counterpart_percent = round((counterpart_caught / counterpart_total * 100), 1) if counterpart_total else 0
    counterpart_shiny_caught = sum(1 for p in counterpart_list if p['is_shiny_caught'])
    counterpart_shiny_percent = round((counterpart_shiny_caught / counterpart_total * 100), 1) if counterpart_total else 0

    own_total = len(own_list)
    own_caught = sum(1 for p in own_list if p['is_caught'])
    own_shiny_caught = sum(1 for p in own_list if p['is_shiny_caught'])

    return {
        'has_exclusives': True,
        'button_label': button_label,
        'full_button_label': full_button_label,
        'counterpart_slug': counterpart_slug,
        'counterpart_short_name': counterpart_short_name,
        'current_short_name': current_short_name,
        'counterpart_name': counterpart_name,
        'counterpart_theme': counterpart_theme,
        'own_theme': own_theme,
        'notice': notice,
        'counterpart_list': counterpart_list,
        'own_list': own_list,
        'counterpart_total': counterpart_total,
        'counterpart_caught': counterpart_caught,
        'counterpart_percent': counterpart_percent,
        'counterpart_shiny_caught': counterpart_shiny_caught,
        'counterpart_shiny_percent': counterpart_shiny_percent,
        'own_total': own_total,
        'own_caught': own_caught,
        'own_shiny_caught': own_shiny_caught,
    }


def get_version_transfers_context(
    current_game: Game,
    current_pokedex: Pokedex,
    caught_entry_ids: set,
    entries_by_num: Optional[Dict[int, CatalogEntry]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retorna el contexto para el botón y el modal independiente de Pokémon a Transferir
    (Cápsula del Tiempo, transferencias intergeneracionales o faltantes de ediciones previas).
    Si el juego no requiere transferencias externas, devuelve None.
    """
    if (current_game.generation >= 3 or current_game.slug in ['ruby', 'sapphire', 'emerald', 'firered', 'leafgreen']) and current_pokedex and not current_pokedex.is_national and current_pokedex.slug != 'national':
        return None

    transfer_nums = VERSION_TRANSFERS_CATALOG.get(current_game.slug, [])
    if not transfer_nums:
        return None

    meta = VERSION_TRANSFERS_META.get(current_game.slug, {})
    mechanic_title = meta.get("mechanic_title", "Pokémon a Transferir")
    mechanic_badge = meta.get("mechanic_badge", "Transferencia")
    description = meta.get("description", "Pokémon requeridos mediante transferencia externa para completar la Pokédex.")
    incompatible_warning = meta.get("incompatible_warning", "")
    altering_cave_note = meta.get("altering_cave_note", "")
    origins_map = meta.get("origins", {})
    default_origin = meta.get("default_origin", "Transferencia Externa")

    transfer_list = []
    for num in transfer_nums:
        origin = origins_map.get(num, default_origin)
        item = _build_exclusive_item(
            num,
            current_pokedex,
            current_game.generation,
            caught_entry_ids,
            is_counterpart=False,
            origin_badge=origin,
            entries_by_num=entries_by_num
        )
        if item:
            transfer_list.append(item)

    total = len(transfer_list)
    caught = sum(1 for p in transfer_list if p['is_caught'])
    percent = round((caught / total * 100), 1) if total else 0

    return {
        'has_transfers': True,
        'button_label': "Transferir",
        'full_button_label': "Pokémon a Transferir",
        'mechanic_title': mechanic_title,
        'mechanic_badge': mechanic_badge,
        'description': description,
        'incompatible_warning': incompatible_warning,
        'altering_cave_note': altering_cave_note,
        'transfer_list': transfer_list,
        'total': total,
        'caught': caught,
        'percent': percent,
    }

