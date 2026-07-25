"""DefendAble — target-airline weighted European airport list.

The single source-of-truth for every airport-dependent pull (weather, NOTAMs,
per-airport ops, tracks). Curated toward the network hotspots of the airlines
DefendAble targets: easyJet (U2), Swiss (LX/H2), Ryanair (FR), Wizz (W6),
Vueling (VY), British Airways (BA), Lufthansa (LH).

62 airports across 15 European countries. Balanced so every plausible claim
airfield for those seven airlines is covered without over-fetching data for
airports that produce ~zero traffic for them.

Fields per airport:
    icao        ICAO 4-letter code (used for METAR/TAF/NOTAM queries)
    iata        IATA 3-letter code (used for public-facing display)
    name        Human airport name
    city        Nearest city
    country     Country name (English)
    country_iso ISO-3166-1 alpha-2
    region      Grouping (British Isles / Iberia / Alpine / Balkans / Nordic / ...)
    airlines    List of target-airline tags whose network includes this airport
    tier        1 = must-have (multi-airline hub), 2 = important (single-airline base or heavy leisure)
"""

AIRPORTS = [
    # ─────────────── British Isles ───────────────
    {"icao": "EGLL", "iata": "LHR", "name": "Heathrow",            "city": "London",       "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["BA", "LH", "LX", "VY"],       "tier": 1},
    {"icao": "EGKK", "iata": "LGW", "name": "Gatwick",             "city": "London",       "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "BA", "VY", "W6"],       "tier": 1},
    {"icao": "EGSS", "iata": "STN", "name": "Stansted",            "city": "London",       "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR"],                    "tier": 1},
    {"icao": "EGGW", "iata": "LTN", "name": "Luton",               "city": "London",       "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR", "W6"],              "tier": 1},
    {"icao": "EGLC", "iata": "LCY", "name": "City",                "city": "London",       "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["BA", "LX"],                    "tier": 2},
    {"icao": "EGCC", "iata": "MAN", "name": "Manchester",          "city": "Manchester",   "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR", "BA"],              "tier": 1},
    {"icao": "EGPH", "iata": "EDI", "name": "Edinburgh",           "city": "Edinburgh",    "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR", "BA"],              "tier": 1},
    {"icao": "EGPF", "iata": "GLA", "name": "Glasgow",             "city": "Glasgow",      "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR"],                    "tier": 2},
    {"icao": "EGGD", "iata": "BRS", "name": "Bristol",             "city": "Bristol",      "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR"],                    "tier": 2},
    {"icao": "EGBB", "iata": "BHX", "name": "Birmingham",          "city": "Birmingham",   "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR"],                    "tier": 2},
    {"icao": "EGAA", "iata": "BFS", "name": "Belfast International","city": "Belfast",     "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["U2", "FR"],                    "tier": 2},
    {"icao": "EGNX", "iata": "EMA", "name": "East Midlands",       "city": "Nottingham",   "country": "United Kingdom", "country_iso": "GB", "region": "British Isles", "airlines": ["FR"],                          "tier": 2},
    {"icao": "EIDW", "iata": "DUB", "name": "Dublin",              "city": "Dublin",       "country": "Ireland",        "country_iso": "IE", "region": "British Isles", "airlines": ["FR", "U2"],                    "tier": 1},

    # ─────────────── France ───────────────
    {"icao": "LFPG", "iata": "CDG", "name": "Charles de Gaulle",   "city": "Paris",        "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["VY", "LX", "LH", "U2", "BA"], "tier": 1},
    {"icao": "LFPO", "iata": "ORY", "name": "Orly",                "city": "Paris",        "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["VY", "U2"],                    "tier": 1},
    {"icao": "LFMN", "iata": "NCE", "name": "Côte d'Azur",         "city": "Nice",         "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["U2", "VY", "LX"],              "tier": 1},
    {"icao": "LFML", "iata": "MRS", "name": "Provence",            "city": "Marseille",    "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["U2", "VY", "FR"],              "tier": 2},
    {"icao": "LFLL", "iata": "LYS", "name": "Saint-Exupéry",       "city": "Lyon",         "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["U2", "VY"],                    "tier": 2},
    {"icao": "LFBO", "iata": "TLS", "name": "Blagnac",             "city": "Toulouse",     "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["U2", "VY"],                    "tier": 2},
    {"icao": "LFBD", "iata": "BOD", "name": "Bordeaux",            "city": "Bordeaux",     "country": "France",         "country_iso": "FR", "region": "France",        "airlines": ["U2"],                          "tier": 2},

    # ─────────────── Low Countries ───────────────
    {"icao": "EHAM", "iata": "AMS", "name": "Schiphol",            "city": "Amsterdam",    "country": "Netherlands",    "country_iso": "NL", "region": "Low Countries", "airlines": ["U2", "VY", "LX", "BA"],       "tier": 1},
    {"icao": "EBBR", "iata": "BRU", "name": "Brussels",            "city": "Brussels",     "country": "Belgium",        "country_iso": "BE", "region": "Low Countries", "airlines": ["LX", "LH", "BA"],              "tier": 2},

    # ─────────────── Germany ───────────────
    {"icao": "EDDF", "iata": "FRA", "name": "Frankfurt",           "city": "Frankfurt",    "country": "Germany",        "country_iso": "DE", "region": "Germany",       "airlines": ["LH", "LX", "BA"],              "tier": 1},
    {"icao": "EDDM", "iata": "MUC", "name": "Munich",              "city": "Munich",       "country": "Germany",        "country_iso": "DE", "region": "Germany",       "airlines": ["LH", "LX", "BA"],              "tier": 1},
    {"icao": "EDDL", "iata": "DUS", "name": "Düsseldorf",          "city": "Düsseldorf",   "country": "Germany",        "country_iso": "DE", "region": "Germany",       "airlines": ["LH", "LX"],                    "tier": 2},
    {"icao": "EDDB", "iata": "BER", "name": "Berlin Brandenburg",  "city": "Berlin",       "country": "Germany",        "country_iso": "DE", "region": "Germany",       "airlines": ["U2", "FR", "LH"],              "tier": 1},
    {"icao": "EDDH", "iata": "HAM", "name": "Hamburg",             "city": "Hamburg",      "country": "Germany",        "country_iso": "DE", "region": "Germany",       "airlines": ["LH", "U2", "FR"],              "tier": 2},
    {"icao": "EDDK", "iata": "CGN", "name": "Cologne-Bonn",        "city": "Cologne",      "country": "Germany",        "country_iso": "DE", "region": "Germany",       "airlines": ["FR", "LH"],                    "tier": 2},

    # ─────────────── Alpine ───────────────
    {"icao": "LSZH", "iata": "ZRH", "name": "Zürich",              "city": "Zürich",       "country": "Switzerland",    "country_iso": "CH", "region": "Alpine",        "airlines": ["LX", "U2"],                    "tier": 1},
    {"icao": "LSGG", "iata": "GVA", "name": "Genève",              "city": "Geneva",       "country": "Switzerland",    "country_iso": "CH", "region": "Alpine",        "airlines": ["LX", "U2", "BA"],              "tier": 1},
    {"icao": "LFSB", "iata": "BSL", "name": "EuroAirport",         "city": "Basel",        "country": "Switzerland",    "country_iso": "CH", "region": "Alpine",        "airlines": ["LX", "U2"],                    "tier": 2},
    {"icao": "LOWW", "iata": "VIE", "name": "Schwechat",           "city": "Vienna",       "country": "Austria",        "country_iso": "AT", "region": "Alpine",        "airlines": ["W6", "LH", "LX", "BA"],       "tier": 1},

    # ─────────────── Iberia ───────────────
    {"icao": "LEMD", "iata": "MAD", "name": "Barajas",             "city": "Madrid",       "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["VY", "U2", "LX", "BA"],       "tier": 1},
    {"icao": "LEBL", "iata": "BCN", "name": "El Prat",             "city": "Barcelona",    "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["VY", "U2", "LX", "BA"],       "tier": 1},
    {"icao": "LEPA", "iata": "PMI", "name": "Son Sant Joan",       "city": "Palma",        "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["U2", "VY", "FR"],              "tier": 1},
    {"icao": "LEAL", "iata": "ALC", "name": "Alicante-Elche",      "city": "Alicante",     "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["U2", "FR", "VY"],              "tier": 2},
    {"icao": "LEIB", "iata": "IBZ", "name": "Ibiza",               "city": "Ibiza",        "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["U2", "VY"],                    "tier": 2},
    {"icao": "LEMG", "iata": "AGP", "name": "Málaga-Costa del Sol","city": "Málaga",       "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["U2", "FR", "VY"],              "tier": 2},
    {"icao": "GCLP", "iata": "LPA", "name": "Gran Canaria",        "city": "Las Palmas",   "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["U2", "FR", "VY"],              "tier": 2},
    {"icao": "GCTS", "iata": "TFS", "name": "Tenerife South",      "city": "Tenerife",     "country": "Spain",          "country_iso": "ES", "region": "Iberia",        "airlines": ["U2", "FR", "VY"],              "tier": 2},
    {"icao": "LPPT", "iata": "LIS", "name": "Humberto Delgado",    "city": "Lisbon",       "country": "Portugal",       "country_iso": "PT", "region": "Iberia",        "airlines": ["U2", "VY"],                    "tier": 2},
    {"icao": "LPPR", "iata": "OPO", "name": "Francisco Sá Carneiro","city": "Porto",       "country": "Portugal",       "country_iso": "PT", "region": "Iberia",        "airlines": ["U2", "VY"],                    "tier": 2},

    # ─────────────── Italy ───────────────
    {"icao": "LIRF", "iata": "FCO", "name": "Fiumicino",           "city": "Rome",         "country": "Italy",          "country_iso": "IT", "region": "Italy",         "airlines": ["VY", "LX", "BA"],              "tier": 1},
    {"icao": "LIMC", "iata": "MXP", "name": "Malpensa",            "city": "Milan",        "country": "Italy",          "country_iso": "IT", "region": "Italy",         "airlines": ["U2", "VY", "LX"],              "tier": 1},
    {"icao": "LIML", "iata": "LIN", "name": "Linate",              "city": "Milan",        "country": "Italy",          "country_iso": "IT", "region": "Italy",         "airlines": ["U2", "LX"],                    "tier": 2},
    {"icao": "LIPZ", "iata": "VCE", "name": "Marco Polo",          "city": "Venice",       "country": "Italy",          "country_iso": "IT", "region": "Italy",         "airlines": ["U2", "VY"],                    "tier": 2},
    {"icao": "LIRN", "iata": "NAP", "name": "Capodichino",         "city": "Naples",       "country": "Italy",          "country_iso": "IT", "region": "Italy",         "airlines": ["U2", "VY"],                    "tier": 2},
    {"icao": "LIME", "iata": "BGY", "name": "Il Caravaggio",       "city": "Bergamo",      "country": "Italy",          "country_iso": "IT", "region": "Italy",         "airlines": ["FR"],                          "tier": 2},

    # ─────────────── Central & Eastern Europe ───────────────
    {"icao": "LKPR", "iata": "PRG", "name": "Václav Havel",        "city": "Prague",       "country": "Czechia",        "country_iso": "CZ", "region": "Central Europe","airlines": ["W6", "FR", "LX"],              "tier": 2},
    {"icao": "EPWA", "iata": "WAW", "name": "Chopin",              "city": "Warsaw",       "country": "Poland",         "country_iso": "PL", "region": "Central Europe","airlines": ["W6", "LH"],                    "tier": 1},
    {"icao": "EPKK", "iata": "KRK", "name": "John Paul II",        "city": "Kraków",       "country": "Poland",         "country_iso": "PL", "region": "Central Europe","airlines": ["W6", "FR"],                    "tier": 2},
    {"icao": "EPGD", "iata": "GDN", "name": "Lech Wałęsa",         "city": "Gdańsk",       "country": "Poland",         "country_iso": "PL", "region": "Central Europe","airlines": ["W6", "FR"],                    "tier": 2},
    {"icao": "LHBP", "iata": "BUD", "name": "Ferenc Liszt",        "city": "Budapest",     "country": "Hungary",        "country_iso": "HU", "region": "Central Europe","airlines": ["W6", "FR"],                    "tier": 2},

    # ─────────────── Balkans ───────────────
    {"icao": "LROP", "iata": "OTP", "name": "Henri Coandă",        "city": "Bucharest",    "country": "Romania",        "country_iso": "RO", "region": "Balkans",       "airlines": ["W6", "FR"],                    "tier": 2},
    {"icao": "LBSF", "iata": "SOF", "name": "Sofia",               "city": "Sofia",        "country": "Bulgaria",       "country_iso": "BG", "region": "Balkans",       "airlines": ["W6", "FR"],                    "tier": 2},

    # ─────────────── Nordic ───────────────
    {"icao": "ESSA", "iata": "ARN", "name": "Arlanda",             "city": "Stockholm",    "country": "Sweden",         "country_iso": "SE", "region": "Nordic",        "airlines": ["LX", "BA"],                    "tier": 2},
    {"icao": "ENGM", "iata": "OSL", "name": "Gardermoen",          "city": "Oslo",         "country": "Norway",         "country_iso": "NO", "region": "Nordic",        "airlines": ["U2", "LX"],                    "tier": 2},
    {"icao": "EKCH", "iata": "CPH", "name": "Kastrup",             "city": "Copenhagen",   "country": "Denmark",        "country_iso": "DK", "region": "Nordic",        "airlines": ["U2", "LX", "BA"],              "tier": 2},

    # ─────────────── Greek & Mediterranean ───────────────
    {"icao": "LGAV", "iata": "ATH", "name": "Eleftherios Venizelos","city": "Athens",      "country": "Greece",         "country_iso": "GR", "region": "Mediterranean", "airlines": ["U2", "FR", "LX"],              "tier": 2},
    {"icao": "LGIR", "iata": "HER", "name": "Nikos Kazantzakis",   "city": "Heraklion",    "country": "Greece",         "country_iso": "GR", "region": "Mediterranean", "airlines": ["U2", "FR"],                    "tier": 2},
    {"icao": "LGRP", "iata": "RHO", "name": "Diagoras",            "city": "Rhodes",       "country": "Greece",         "country_iso": "GR", "region": "Mediterranean", "airlines": ["U2", "FR"],                    "tier": 2},
    {"icao": "LCLK", "iata": "LCA", "name": "Larnaca",             "city": "Larnaca",      "country": "Cyprus",         "country_iso": "CY", "region": "Mediterranean", "airlines": ["U2", "W6", "BA"],              "tier": 2},
    {"icao": "LMML", "iata": "MLA", "name": "Malta International", "city": "Luqa",         "country": "Malta",          "country_iso": "MT", "region": "Mediterranean", "airlines": ["U2", "FR"],                    "tier": 2},
]

# Helper: list of ICAO codes only, comma-joined — used by AviationWeather source
ICAO_LIST = [a["icao"] for a in AIRPORTS]

# Helper: list of tier-1 ICAO codes — used for higher-frequency pulls (e.g. NOTAMs)
TIER1_ICAO = [a["icao"] for a in AIRPORTS if a["tier"] == 1]

# Helper: airport lookup by ICAO code
BY_ICAO = {a["icao"]: a for a in AIRPORTS}

# Helper: airport lookup by IATA code
BY_IATA = {a["iata"]: a for a in AIRPORTS}
