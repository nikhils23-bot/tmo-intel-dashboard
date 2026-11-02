"""
config.py: every list the dashboard runs on.

This is the only file you should need to edit. It holds no logic: only lists,
numbers and switches. lens.py, collectors.py, streams.py and brain.py read it.

Editing tips
- Keep terms lowercase. Matching is done on lowercased text, except for the
  few entries in CASE_SENSITIVE_TERMS.
- Single words of 8 characters or fewer only match as whole words ("apac" does
  not match inside "capacity"). Longer words and phrases match anywhere.
- If a term is also an ordinary word, add it to AMBIGUOUS_TERMS with the
  phrases that mean "this is not the thing I want".
- A dead feed shows up on /sources. Fix it by deleting its line here.
"""

BUILD = "2026-10-31.b1"

# ---------------------------------------------------------------------------
# 1. Scope: regions (Part 2 of the build brief)
# ---------------------------------------------------------------------------
# type:  "special": World. Only gets stories with no APMEA market, or an
#                   explicit global marker.
#        "rollup":  never matched directly from a country. It is the union of
#                   its children, plus stories that use APAC_WIDE_TERMS.
#        "leaf":    matched from the story text, and gets its own searches.
# edition: the Google News edition used for that leaf's region searches.

REGIONS = [
    {"key": "global", "label": "World", "type": "special", "parent": None},
    {"key": "apac", "label": "Asia Pacific", "type": "rollup", "parent": None},
    {"key": "china", "label": "China", "type": "leaf", "parent": "apac",
     "edition": "US", "search_name": "China",
     "terms": [
         "china", "chinese", "mainland china", "prc", "beijing", "shanghai",
         "shenzhen", "guangzhou", "suzhou", "hangzhou", "nanjing", "wuhan",
         "chengdu", "tianjin", "chongqing", "xiamen", "jiangsu", "zhejiang",
         "guangdong", "shandong", "hong kong", "macau", "wuxi", "nmpa",
         "volume-based procurement", "made in china 2025",
     ]},
    {"key": "india", "label": "India & South Asia", "type": "leaf",
     "parent": "apac", "edition": "IN", "search_name": "India",
     "terms": [
         "india", "indian", "mumbai", "delhi", "new delhi", "bengaluru",
         "bangalore", "hyderabad", "pune", "chennai", "ahmedabad", "kolkata",
         "gujarat", "telangana", "karnataka", "maharashtra", "andhra pradesh",
         "tamil nadu", "visakhapatnam", "genome valley", "cdsco", "icmr",
         "birac", "bioe3", "make in india", "south asia", "bangladesh",
         "bangladeshi", "dhaka", "sri lanka", "pakistan", "pakistani",
         "karachi", "lahore", "nepal", "kathmandu",
     ]},
    {"key": "apac_rest", "label": "Rest of Asia Pacific", "type": "leaf",
     "parent": "apac", "edition": "SG", "search_name": "Japan OR Korea OR Singapore OR Australia",
     "terms": [
         "japan", "japanese", "tokyo", "osaka", "kyoto", "kobe", "yokohama",
         "south korea", "korea", "korean", "seoul", "incheon", "songdo",
         "taiwan", "taiwanese", "taipei", "hsinchu", "singapore",
         "singaporean", "tuas", "biopolis", "malaysia", "malaysian",
         "kuala lumpur", "penang", "thailand", "thai", "bangkok", "vietnam",
         "vietnamese", "hanoi", "ho chi minh", "indonesia", "indonesian",
         "jakarta", "philippines", "filipino", "manila", "asean",
         "southeast asia", "south-east asia", "south east asia", "australia",
         "australian", "melbourne", "brisbane", "queensland",
         "new south wales", "new zealand", "auckland", "papua new guinea",
         "pmda", "mfds", "therapeutic goods administration",
     ]},
    {"key": "mea", "label": "Middle East & Africa", "type": "leaf",
     "parent": None, "edition": "ZA", "search_name": "Saudi OR UAE OR Africa OR Israel",
     "terms": [
         "middle east", "middle east and africa", "mena", "gcc",
         "gulf states", "gulf cooperation council", "gulf region",
         "west asia", "saudi", "saudi arabia", "riyadh", "jeddah", "dammam",
         "neom", "kaust", "vision 2030", "sfda", "uae", "u.a.e.",
         "united arab emirates", "emirati", "emirates", "dubai", "abu dhabi",
         "sharjah", "qatar", "qatari", "doha", "kuwait", "oman", "muscat",
         "bahrain", "israel", "israeli", "tel aviv", "rehovot", "haifa",
         "turkey", "türkiye", "turkiye", "turkish", "istanbul", "ankara",
         "egypt", "egyptian", "cairo", "jordan", "jordanian", "amman",
         "morocco", "moroccan", "tunisia", "algeria", "north africa",
         "africa", "african", "sub-saharan", "south africa", "johannesburg",
         "cape town", "pretoria", "durban", "nigeria", "nigerian", "lagos",
         "abuja", "kenya", "kenyan", "nairobi", "ethiopia", "addis ababa",
         "ghana", "accra", "rwanda", "kigali", "senegal", "dakar",
         "tanzania", "uganda", "kampala", "guinea", "africa cdc", "sahpra",
         "nafdac", "mea",
     ]},
]

# Stories that name the wider region but no country go to the rollup.
APAC_WIDE_TERMS = [
    "asia pacific", "asia-pacific", "apac", "asia", "asian", "apj",
    "north asia", "greater asia", "pan-asian", "asia region",
]
# APMEA-wide terms go to both the APAC rollup and the MEA leaf.
APMEA_WIDE_TERMS = ["apmea", "amea", "asia, middle east and africa",
                    "asia pacific, middle east and africa", "imea"]

# APMEA stories get World as well only when one of these is present.
GLOBAL_MARKERS = [
    "worldwide", "across markets", "global rollout", "global launch",
    "worldwide launch", "global expansion", "across the globe",
    "around the world", "all regions", "global markets", "launched globally",
    "globally available", "global availability",
]

# Never rows. Used only for the origin chip on World stories.
OUTSIDE_REGIONS = {
    "US": [
        "united states", "u.s.", "usa", "american", "nih", "washington",
        "boston", "massachusetts", "california", "san diego",
        "san francisco", "bay area", "texas", "new york", "new jersey",
        "north carolina", "maryland", "chicago", "pennsylvania",
        "philadelphia", "canada", "canadian", "toronto", "ontario",
        "quebec", "montreal", "vancouver", "congress", "senate",
        "white house", "trump administration", "hhs",
    ],
    "Europe": [
        "europe", "european", "eu", "e.u.", "uk", "u.k.", "united kingdom",
        "britain", "british", "england", "london", "scotland", "germany",
        "german", "france", "french", "switzerland", "swiss", "netherlands",
        "dutch", "belgium", "belgian", "ireland", "irish", "sweden",
        "swedish", "denmark", "danish", "norway", "finland", "spain",
        "spanish", "italy", "italian", "poland", "austria", "nordic",
        "nordics", "horizon europe", "ivdr", "ema", "basel", "munich",
        "paris", "amsterdam", "copenhagen",
    ],
    "LatAm": [
        "latin america", "latam", "brazil", "brazilian", "mexico",
        "mexican", "argentina", "chile", "colombia", "peru", "sao paulo",
        "são paulo",
    ],
}

# Terms matched against the original (not lowercased) text.
CASE_SENSITIVE_TERMS = {"US": "US", "UK": "Europe", "EU": "Europe"}

# ---------------------------------------------------------------------------
# 2. Scope: segments (the category axis)
# ---------------------------------------------------------------------------
SEGMENTS = [
    {"key": "all", "label": "All", "terms": []},     # roll-up column, must stay
    {"key": "bioprocess", "label": "Bioprocessing", "terms": [
        "bioprocess", "bioprocessing", "biomanufacturing", "bioreactor",
        "bioreactors", "single-use", "single use", "upstream processing",
        "downstream processing", "purification", "chromatography resin",
        "protein a", "filtration", "tangential flow", "depth filter",
        "fill-finish", "fill finish", "fill and finish", "sterile injectable",
        "aseptic", "cell culture media", "culture media", "cell culture",
        "cell therapy manufacturing", "gene therapy manufacturing",
        "viral vector", "aav", "lentiviral", "mrna manufacturing",
        "plasmid dna", "biologics manufacturing", "biologics plant",
        "monoclonal antibody production", "perfusion", "biosimilar",
        "biosimilars", "drug substance", "microbial fermentation",
        "continuous manufacturing", "process development",
    ]},
    {"key": "genomics", "label": "Genomics", "terms": [
        "sequencing", "sequencer", "sequencers", "genomic", "genomics",
        "genome", "ngs", "next-generation sequencing", "whole genome",
        "whole-genome", "exome", "long-read", "short-read", "qpcr", "pcr",
        "dpcr", "digital pcr", "spatial biology", "spatial transcriptomics",
        "spatial omics", "single-cell", "single cell", "multiomics",
        "multi-omics", "transcriptomics", "genotyping", "oligo",
        "oligonucleotide", "dna synthesis", "gene synthesis", "crispr",
        "microarray", "genome programme", "genome program",
        "population genomics", "precision medicine", "biobank",
    ]},
    {"key": "instruments", "label": "Analytical instruments", "terms": [
        "mass spectrometry", "mass spectrometer", "mass spec", "lc-ms",
        "lc/ms", "lc-ms/ms", "gc-ms", "icp-ms", "chromatography", "hplc",
        "uhplc", "gas chromatography", "ion chromatography", "spectroscopy",
        "spectrometer", "ftir", "raman", "nmr", "x-ray diffraction", "xrd",
        "xrf", "electron microscopy", "electron microscope", "cryo-em",
        "cryo-electron", "scanning electron", "transmission electron",
        "microscopy", "analytical instrument", "analytical instruments",
        "elemental analysis", "materials analysis", "materials science",
        "surface analysis", "metrology", "failure analysis",
        "thermal analysis", "orbitrap", "triple quadrupole", "proteomics",
        "metabolomics", "lipidomics", "chromatography data",
        "particle analysis", "rheology",
    ]},
    {"key": "diagnostics", "label": "Diagnostics", "terms": [
        "diagnostic", "diagnostics", "ivd", "in vitro diagnostic",
        "immunoassay", "clinical chemistry", "clinical laboratory",
        "clinical laboratories", "clinical lab", "reference lab",
        "reference laboratory", "hospital lab", "pathology",
        "microbiology", "blood test", "point of care", "point-of-care",
        "molecular diagnostics", "companion diagnostic", "transplant",
        "hla typing", "hematology", "haematology",
        "laboratory developed test", "ldt", "newborn screening",
        "antimicrobial resistance", "sepsis", "test kit", "rapid test",
        "screening programme", "screening program", "cancer screening",
        "liquid biopsy", "allergy testing", "infectious disease testing",
    ]},
    {"key": "services", "label": "Pharma services & lab supply", "terms": [
        "cdmo", "cdmos", "cro", "cros", "crdmo", "contract development",
        "contract manufacturing", "contract research", "clinical trial",
        "clinical trials", "clinical supply", "clinical supplies",
        "trial logistics", "pharma services", "outsourcing", "outsourced",
        "tech transfer", "technology transfer", "consumables",
        "lab supplies", "laboratory supplies", "lab supply",
        "lab distribution", "distributor", "distribution agreement",
        "lab automation", "laboratory automation", "liquid handling",
        "robotics", "lims", "electronic lab notebook", "self-driving lab",
        "central lab", "biorepository", "cold chain", "lab equipment",
        "laboratory equipment", "lab services", "clinical research",
        "drug product manufacturing",
    ]},
]

# ---------------------------------------------------------------------------
# 3. Name ambiguity (Part 4e). term -> phrases that disqualify the match.
# ---------------------------------------------------------------------------
AMBIGUOUS_TERMS = {
    # Company traps
    "waters": ["wastewater", "drinking water", "water supply",
               "troubled waters", "coastal waters", "international waters",
               "territorial waters", "uncharted waters", "murky waters",
               "muddy waters", "floodwaters", "flood waters", "in the waters",
               "waters off", "waters of the", "maxine waters", "roger waters",
               "john waters", "rep. waters"],
    "icon": ["iconic", "icon of", "app icon", "fashion icon", "style icon",
             "pop icon", "cultural icon", "an icon"],
    "hamilton": ["hamilton musical", "hamilton ontario", "hamilton, ontario",
                 "hamilton county", "lewis hamilton", "alexander hamilton"],
    "abbott": ["greg abbott", "gov. abbott", "governor abbott",
               "tony abbott", "abbott elementary"],
    "charles river": ["the charles river", "charles river esplanade",
                      "charles river basin"],
    "wuxi": ["wuxi apptec", "wuxi biologics", "wuxi xdc", "wuxi sta",
             "wuxi advanced", "wuxi vaccines"],   # company names are not China news
    "ppd": ["tuberculin", "ppd test", "ppd skin"],
    "roche": ["roche bobois", "la roche"],
    "mettler": [],
    "corning": ["corning, new york", "corning, ny", "corning museum"],
    # Region traps
    "mea": ["ministry of external affairs", "external affairs", "mea spokesperson"],
    "guinea": ["guinea pig", "guinea pigs", "guinea-pig", "papua new guinea"],
    "china": ["fine china", "bone china", "china clay", "china syndrome"],
    "chinese": ["chinese medicine practitioner"],
    "turkey": ["thanksgiving", "roast turkey", "turkey sandwich",
               "wild turkey", "cold turkey", "turkey vulture"],
    "jordan": ["michael jordan", "jordan peterson", "air jordan",
               "jordan brand", "jordan river"],
    "emirates": ["emirates stadium", "fly emirates"],
    "korea": ["north korea", "north korean"],
    "korean": ["north korean"],
    "asia": ["west asia", "central asia"],
    "american": ["latin american", "south american", "central american"],
    "georgia": [],
    "washington": ["washington state"],
    "paris": ["paris hilton", "paris agreement"],
    "thai": [],
    "oman": [],
    "ema": [],
    "nih": [],
}

# ---------------------------------------------------------------------------
# 4. Competitors (Part 4a), checked 31 Oct 2026
# ---------------------------------------------------------------------------
# Changes from the brief's list, from the build-session check:
# - Waters completed its combination with BD's Biosciences & Diagnostic
#   Solutions businesses in Feb 2026. That business now trades as Waters
#   Biosciences and Waters Advanced Diagnostics, so Becton Dickinson is no
#   longer a starred diagnostics rival. Old "BD Biosciences" coverage is kept
#   as a Waters alias.
# - Merck KGaA announced an ~$11.3bn deal for Bio-Techne in June 2026.
#   Bio-Techne is added as a starred name to watch that deal.
# - Catalent is owned by Novo Holdings (since Dec 2024). The name still
#   searches fine.
# - APMEA additions: Sysmex, Mindray, Syngene, plus one batched search for
#   Chinese domestic bioprocess suppliers.
#
# Fields: name, segment, star, terms (for scoring and filing), query (Google
# News; quote multi-word names, per rule 10). Only starred names get a search.

COMPETITORS = [
    # Analytical instruments
    {"name": "Agilent", "segment": "instruments", "star": True,
     "terms": ["agilent"], "query": '"Agilent"'},
    {"name": "Waters", "segment": "instruments", "star": True,
     "terms": ["waters corporation", "waters corp", "waters biosciences",
               "waters advanced diagnostics", "waters analytical sciences",
               "waters materials sciences", "bd biosciences", "waters"],
     "query": '"Waters Corporation" OR "Waters Corp" OR "Waters Biosciences"'},
    {"name": "Bruker", "segment": "instruments", "star": True,
     "terms": ["bruker"], "query": '"Bruker"'},
    {"name": "Shimadzu", "segment": "instruments", "star": True,
     "terms": ["shimadzu"], "query": '"Shimadzu"'},
    {"name": "Revvity", "segment": "instruments", "star": True,
     "terms": ["revvity", "perkinelmer", "perkin elmer"],
     "query": '"Revvity" OR "PerkinElmer"'},
    {"name": "Mettler-Toledo", "segment": "instruments", "star": True,
     "terms": ["mettler-toledo", "mettler toledo", "mettler"],
     "query": '"Mettler-Toledo"'},
    {"name": "JEOL", "segment": "instruments", "star": False, "terms": ["jeol"]},
    {"name": "Hitachi High-Tech", "segment": "instruments", "star": False,
     "terms": ["hitachi high-tech", "hitachi high tech"]},
    {"name": "Oxford Instruments", "segment": "instruments", "star": False,
     "terms": ["oxford instruments"]},
    {"name": "Horiba", "segment": "instruments", "star": False, "terms": ["horiba"]},

    # Bioprocessing
    {"name": "Danaher", "segment": "bioprocess", "star": True,
     "terms": ["danaher"], "query": '"Danaher"'},
    {"name": "Cytiva", "segment": "bioprocess", "star": True,
     "terms": ["cytiva"], "query": '"Cytiva"'},
    {"name": "Sartorius", "segment": "bioprocess", "star": True,
     "terms": ["sartorius"], "query": '"Sartorius"'},
    {"name": "Merck KGaA / MilliporeSigma", "segment": "bioprocess", "star": True,
     "terms": ["merck kgaa", "milliporesigma", "millipore", "sigma-aldrich",
               "merck life science", "merck electronics"],
     "query": '"Merck KGaA" OR "MilliporeSigma"'},
    {"name": "Repligen", "segment": "bioprocess", "star": True,
     "terms": ["repligen"], "query": '"Repligen"'},
    {"name": "Lonza", "segment": "bioprocess", "star": True,
     "terms": ["lonza"], "query": '"Lonza"'},
    {"name": "Bio-Techne", "segment": "bioprocess", "star": True,
     "terms": ["bio-techne", "biotechne"], "query": '"Bio-Techne"'},
    {"name": "Pall", "segment": "bioprocess", "star": False,
     "terms": ["pall corporation", "pall corp", "pall biotech"]},
    {"name": "Getinge", "segment": "bioprocess", "star": False, "terms": ["getinge"]},
    {"name": "Eppendorf", "segment": "bioprocess", "star": False, "terms": ["eppendorf"]},
    {"name": "Solventum", "segment": "bioprocess", "star": False, "terms": ["solventum"]},
    {"name": "Chinese domestic bioprocess suppliers", "segment": "bioprocess",
     "star": True,
     "terms": ["nanomicro", "tofflon", "bestchrom", "duoning"],
     "query": '"Nanomicro" OR "Tofflon" OR "Bestchrom" OR "Duoning"'},

    # Genomics
    {"name": "Illumina", "segment": "genomics", "star": True,
     "terms": ["illumina"], "query": '"Illumina"'},
    {"name": "Oxford Nanopore", "segment": "genomics", "star": True,
     "terms": ["oxford nanopore"], "query": '"Oxford Nanopore"'},
    {"name": "PacBio", "segment": "genomics", "star": True,
     "terms": ["pacbio", "pacific biosciences"],
     "query": '"PacBio" OR "Pacific Biosciences"'},
    {"name": "Qiagen", "segment": "genomics", "star": True,
     "terms": ["qiagen"], "query": '"Qiagen"'},
    {"name": "10x Genomics", "segment": "genomics", "star": True,
     "terms": ["10x genomics"], "query": '"10x Genomics"'},
    {"name": "Element Biosciences", "segment": "genomics", "star": False,
     "terms": ["element biosciences"]},
    {"name": "Ultima Genomics", "segment": "genomics", "star": False,
     "terms": ["ultima genomics"]},
    {"name": "MGI / BGI", "segment": "genomics", "star": False,
     "terms": ["mgi tech", "bgi genomics", "bgi group", "mgi"]},
    {"name": "Twist Bioscience", "segment": "genomics", "star": False,
     "terms": ["twist bioscience"]},
    {"name": "Roche Sequencing", "segment": "genomics", "star": False,
     "terms": ["roche sequencing", "sequencing by expansion"]},

    # Diagnostics
    {"name": "Roche Diagnostics", "segment": "diagnostics", "star": True,
     "terms": ["roche diagnostics", "roche"], "query": '"Roche Diagnostics"'},
    {"name": "Abbott", "segment": "diagnostics", "star": True,
     "terms": ["abbott"], "query": '"Abbott" diagnostics'},
    {"name": "Siemens Healthineers", "segment": "diagnostics", "star": True,
     "terms": ["siemens healthineers", "healthineers"],
     "query": '"Siemens Healthineers"'},
    {"name": "bioMérieux", "segment": "diagnostics", "star": True,
     "terms": ["biomerieux", "biomérieux"], "query": '"bioMerieux"'},
    {"name": "Sysmex", "segment": "diagnostics", "star": True,
     "terms": ["sysmex"], "query": '"Sysmex"'},
    {"name": "Mindray", "segment": "diagnostics", "star": True,
     "terms": ["mindray"], "query": '"Mindray"'},
    {"name": "Becton Dickinson", "segment": "diagnostics", "star": False,
     "terms": ["becton dickinson", "becton, dickinson"]},
    {"name": "Beckman Coulter", "segment": "diagnostics", "star": False,
     "terms": ["beckman coulter"]},
    {"name": "Cepheid", "segment": "diagnostics", "star": False, "terms": ["cepheid"]},
    {"name": "QuidelOrtho", "segment": "diagnostics", "star": False,
     "terms": ["quidelortho"]},
    {"name": "Hologic", "segment": "diagnostics", "star": False, "terms": ["hologic"]},
    {"name": "Werfen", "segment": "diagnostics", "star": False, "terms": ["werfen"]},

    # Pharma services (CDMO / CRO)
    {"name": "Catalent", "segment": "services", "star": True,
     "terms": ["catalent"], "query": '"Catalent"'},
    {"name": "Samsung Biologics", "segment": "services", "star": True,
     "terms": ["samsung biologics"], "query": '"Samsung Biologics"'},
    {"name": "WuXi AppTec", "segment": "services", "star": True,
     "terms": ["wuxi apptec"], "query": '"WuXi AppTec"'},
    {"name": "WuXi Biologics", "segment": "services", "star": True,
     "terms": ["wuxi biologics", "wuxi xdc"], "query": '"WuXi Biologics"'},
    {"name": "IQVIA", "segment": "services", "star": True,
     "terms": ["iqvia"], "query": '"IQVIA"'},
    {"name": "Charles River", "segment": "services", "star": True,
     "terms": ["charles river laboratories", "charles river labs",
               "charles river"],
     "query": '"Charles River Laboratories"'},
    {"name": "Syngene", "segment": "services", "star": True,
     "terms": ["syngene"], "query": '"Syngene"'},
    {"name": "Fujifilm Diosynth", "segment": "services", "star": False,
     "terms": ["fujifilm diosynth", "fujifilm biotechnologies"]},
    {"name": "Boehringer Ingelheim", "segment": "services", "star": False,
     "terms": ["boehringer ingelheim biox", "biox"]},
    {"name": "ICON", "segment": "services", "star": False,
     "terms": ["icon plc", "icon clinical"]},
    {"name": "Fortrea", "segment": "services", "star": False, "terms": ["fortrea"]},
    {"name": "Parexel", "segment": "services", "star": False, "terms": ["parexel"]},
    {"name": "Labcorp", "segment": "services", "star": False, "terms": ["labcorp"]},
    {"name": "Siegfried", "segment": "services", "star": False, "terms": ["siegfried"]},
    {"name": "Recipharm", "segment": "services", "star": False, "terms": ["recipharm"]},

    # Lab products & distribution
    {"name": "Avantor", "segment": "services", "star": True,
     "terms": ["avantor", "vwr"], "query": '"Avantor"'},
    {"name": "Corning", "segment": "services", "star": False,
     "terms": ["corning life sciences", "corning incorporated", "corning inc"]},
    {"name": "Azenta", "segment": "services", "star": False, "terms": ["azenta"]},
    {"name": "Tecan", "segment": "services", "star": False, "terms": ["tecan"]},
    {"name": "Hamilton", "segment": "services", "star": False,
     "terms": ["hamilton company", "hamilton robotics", "hamilton storage"]},
]

# The company the dashboard is about. Scored, never searched as a rival.
SUBJECT_TERMS = [
    "thermo fisher", "thermofisher", "thermo scientific", "fisher scientific",
    "invitrogen", "applied biosystems", "patheon", "ppd", "olink", "gibco",
    "ion torrent", "unity lab services", "fisher clinical services",
]
SUBJECT_QUERY = '"Thermo Fisher"'

# ---------------------------------------------------------------------------
# 5. Relevance bands (Part 6). Weight is added once per band; a band that
#    fires on two or more distinct terms adds half its weight again.
# ---------------------------------------------------------------------------
BAND_WEIGHTS = {
    "TECHNOLOGY": 12, "COMPETITORS": 12, "SUBJECT": 12, "CUSTOMER_MOVES": 7,
    "REGULATION": 7, "MARKET_STRUCTURE": 6, "DEMAND_SHIFTS": 6,
    "SUPPLY_CHAIN": 5, "REPUTABLE_PRESS": 5, "SEGMENT_BASE": 3,
    "BUSINESS_VERBS": 3, "NOISE": -14, "WEAK_PUBLISHERS": -8, "LEARNED": 9,
}

BANDS = {
    "TECHNOLOGY": [
        "sequencing", "sequencer", "next-generation sequencing", "ngs",
        "long-read", "mass spectrometry", "mass spectrometer", "mass spec",
        "chromatography", "hplc", "uhplc", "lc-ms", "gc-ms", "icp-ms",
        "single-use bioreactor", "bioreactor", "bioprocessing",
        "biomanufacturing", "spatial biology", "spatial transcriptomics",
        "cryo-em", "electron microscopy", "electron microscope", "qpcr",
        "digital pcr", "flow cytometry", "cell sorting", "lab automation",
        "laboratory automation", "liquid handling", "spectroscopy", "nmr",
        "proteomics", "multiomics", "multi-omics", "single-cell",
        "immunoassay", "cell culture media", "chromatography resin",
        "viral vector", "orbitrap", "liquid biopsy", "microscopy",
        "spectrometer", "analytical instrument", "analytical instruments",
        "life science tools", "life sciences tools", "life-science tools",
        "laboratory equipment", "lab equipment", "lab instruments",
        "genomics", "gene sequencing", "crispr", "molecular diagnostics",
        "clinical chemistry", "in vitro diagnostic", "ivd", "fill-finish",
        "fill finish", "mrna manufacturing", "cell therapy manufacturing",
        "gene therapy manufacturing", "biologics manufacturing", "cdmo",
        "crdmo", "contract research organisation",
        "contract research organization", "self-driving lab",
    ],
    "CUSTOMER_MOVES": [
        "capex", "capital expenditure", "new plant", "manufacturing plant",
        "manufacturing facility", "manufacturing site", "production site",
        "plant build", "capacity expansion", "expands capacity",
        "expand capacity", "expanding capacity", "adds capacity",
        "site closure", "closes site", "plant closure", "cdmo award",
        "manufacturing agreement", "supply agreement", "tech transfer",
        "technology transfer", "greenfield", "groundbreaking",
        "breaks ground", "commissioning", "gmp facility", "new facility",
        "r&d centre", "r&d center", "innovation centre", "innovation center",
        "centre of excellence", "center of excellence", "opens lab",
        "new laboratory", "laboratory opening", "inaugurates", "inaugurated",
        "biologics plant", "fill-finish site", "reference laboratory",
        "lab network", "genome centre", "genome center",
    ],
    "REGULATION": [
        "fda", "usfda", "u.s. fda", "ema", "nmpa", "cdsco", "pmda", "mfds",
        "sfda", "sahpra", "nafdac", "ivdr", "ldt rule",
        "laboratory developed test", "laboratory-developed test",
        "biosecure", "biosecure act", "gmp", "cgmp", "inspection",
        "warning letter", "form 483", "import alert", "510(k)", "ce mark",
        "ce-ivd", "regulator", "regulatory", "guidance", "recall",
        "emergency use", "price control", "volume-based procurement", "vbp",
        "centralised procurement", "centralized procurement",
        "localisation requirement", "localization requirement",
        "local content", "anti-corruption", "export control",
        "export controls", "entity list",
    ],
    "MARKET_STRUCTURE": [
        "acquisition", "acquire", "acquires", "acquired", "to acquire",
        "divestiture", "divest", "divests", "divested", "spin-off",
        "spinoff", "spin off", "merger", "merge", "merges", "combination",
        "joint venture", "distribution agreement", "distribution partnership",
        "exclusive distributor", "distribution rights", "tender",
        "framework contract", "framework agreement", "takeover", "buyout",
        "carve-out", "majority stake", "minority stake", "strategic investment",
        "sells business", "sale of its",
    ],
    "DEMAND_SHIFTS": [
        "nih funding", "nih budget", "nih", "indirect cost", "indirect costs",
        "research funding", "research budget", "science budget",
        "grant funding", "funding cuts", "budget cut", "budget cuts",
        "biotech funding", "venture capital", "series a", "series b",
        "series c", "ipo", "layoffs", "job cuts", "restructuring",
        "instrument capex", "replacement cycle", "academic demand",
        "academic market", "government funding", "stimulus",
        "equipment renewal", "equipment upgrade", "demand recovery",
        "destocking", "order growth", "book-to-bill", "organic growth",
        "guidance cut", "raises guidance", "lowers guidance",
        "biopharma spending", "pharma spending", "funding environment",
        "horizon europe",
    ],
    "SUPPLY_CHAIN": [
        "tariff", "tariffs", "reshoring", "onshoring", "nearshoring",
        "lead time", "lead times", "shortage", "shortages", "logistics",
        "cold chain", "supply chain", "supply-chain", "china+1",
        "china plus one", "decoupling", "local manufacturing",
        "localisation", "localization", "make in india", "pli scheme",
        "production linked incentive", "production-linked incentive",
        "domestic substitution", "import substitution", "self-sufficiency",
        "dual sourcing", "second source",
    ],
    "REPUTABLE_PRESS": [
        "genomeweb", "360dx", "genetic engineering & biotechnology news",
        "gen - genetic engineering", "genengnews", "the scientist",
        "technology networks", "selectscience", "labmate", "drug discovery",
        "chemistry world", "chemical & engineering news", "c&en",
        "bioprocess international", "bioprocess online",
        "pharmaceutical technology", "pharma manufacturing",
        "european pharmaceutical review", "contract pharma",
        "outsourced pharma", "pharmasource", "endpoints", "fierce pharma",
        "fierce biotech", "fiercebiotech", "fiercepharma", "biospace",
        "biopharma dive", "medtech dive", "dark daily", "cap today",
        "clinical lab products", "diagnostics world", "lcgc",
        "spectroscopy online", "separation science", "azom", "news-medical",
        "nature", "science", "stat", "statnews", "research professional",
        "biospectrum", "express pharma", "pharmabiz", "ethealthworld",
        "asian scientist", "korea biomedical review", "labonline",
        "nikkei asia", "caixin", "evaluate vantage", "omnia health",
        "middle east health", "medicalbrief", "health policy watch",
        "reuters", "financial times", "bloomberg",
    ],
    "SEGMENT_BASE": [
        "reagent", "reagents", "consumable", "consumables", "assay",
        "assays", "instrument", "instruments", "bioreactor", "column",
        "columns", "kit", "kits", "antibody", "antibodies", "laboratory",
        "laboratories", "lab", "labs", "scientist", "scientists", "biotech",
        "biotechnology", "biopharma", "pharma", "pharmaceutical",
        "pharmaceuticals", "life sciences", "life science", "biologics",
        "researchers", "research institute", "university", "academic",
        "hospital", "clinical", "biomedical",
    ],
    "BUSINESS_VERBS": [
        "launches", "launched", "launch", "unveils", "introduces",
        "acquires", "invests", "investment", "invest", "expands",
        "expansion", "partners", "partnership", "collaboration",
        "collaborates", "wins", "awarded", "reports", "revenue", "sales",
        "earnings", "quarter", "q1", "q2", "q3", "q4", "results", "opens",
        "signs", "agreement", "deal", "contract", "selects", "deploys",
        "rolls out",
    ],
    "NOISE": [
        "price target", "shares jump", "shares rise", "shares fall",
        "shares drop", "shares slide", "stock price", "stock forecast",
        "buy rating", "sell rating", "hold rating", "overweight rating",
        "underweight rating", "analyst rating", "upgraded to", "downgraded to",
        "raises stake in", "boosts stake in", "trims stake in",
        "cuts stake in", "lowers stake in", "increases stake in",
        "acquires new position", "takes position in", "buys shares of",
        "sells shares of", "shares sold by", "shares bought by",
        "holdings in", "institutional investor", "13f", "dividend",
        "best stocks", "stocks to buy", "top 10", "top 5", "top five",
        "top ten", "market size", "market share report", "cagr",
        "forecast to 2030", "forecast to 2032", "forecast to 2033",
        "forecast to 2034", "forecast to 2035", "market report",
        "market analysis report", "market research report",
        "market to reach", "market will reach", "market is projected",
        "awards ceremony", "wins award", "award winner", "award-winning",
        "best places to work", "named a top", "recognized as", "recognised as",
        "career advice", "how to become", "salary", "job openings",
        "hiring now", "internship", "horoscope", "recipe", "weight loss",
        "home remedies", "home remedy", "obituary", "webinar", "sponsored",
        "podcast:", "quiz",
    ],
    "WEAK_PUBLISHERS": [
        "openpr", "ein presswire", "einpresswire", "marketbeat",
        "globe newswire", "globenewswire", "pr newswire", "prnewswire",
        "business wire", "businesswire", "accesswire", "newsfile",
        "benzinga", "zacks", "seeking alpha", "simply wall st",
        "investing.com", "motley fool", "fool.com", "tipranks",
        "defense world", "etf daily news", "ticker report",
        "american banking news", "market research future",
        "precedence research", "towards healthcare", "digital journal",
        "industry today", "newstrail", "medium.com", "linkedin",
        "yahoo finance", "msn", "stocktitan", "stock titan",
        "the globe and mail", "gurufocus", "insidermonkey", "insider monkey",
        "nasdaq.com", "marketscreener", "indexbox", "giiresearch",
        "researchandmarkets", "research and markets",
    ],
}

# Thresholds (rule 5)
KEEP_THRESHOLD = 9          # general press, including regional business press
SEARCH_THRESHOLD = 11       # open web / Google News theme searches
SPECIALIST_THRESHOLD = 2    # specialist trade press: trust their editors
RIVAL_THRESHOLD = 9         # competitor searches: the name must fire, noise must not
NEAR_MISS_MARGIN = 9        # stories this close below the bar get re-checked with learned terms

# ---------------------------------------------------------------------------
# 6. Trade press (Part 4b)
# ---------------------------------------------------------------------------
# Backbone: Google News searches scoped to each site. These never rot.
# kind: "specialist" or "general". home: fallback region (rule 2) or None.
# topic: extra terms added to the query for general titles.

LAB_TOPIC = ("(laboratory OR diagnostics OR biotech OR biotechnology OR "
             "genomics OR pharmaceutical OR \"life sciences\" OR biomanufacturing)")

PUBLICATIONS = [
    # Life science tools & genomics
    {"name": "GenomeWeb", "site": "genomeweb.com", "kind": "specialist", "home": None},
    {"name": "360Dx", "site": "360dx.com", "kind": "specialist", "home": None},
    {"name": "GEN", "site": "genengnews.com", "kind": "specialist", "home": None},
    {"name": "The Scientist", "site": "the-scientist.com", "kind": "specialist", "home": None},
    {"name": "Technology Networks", "site": "technologynetworks.com", "kind": "specialist", "home": None},
    {"name": "SelectScience", "site": "selectscience.net", "kind": "specialist", "home": None},
    {"name": "Labmate Online", "site": "labmate-online.com", "kind": "specialist", "home": None},
    {"name": "Drug Discovery & Development", "site": "drugdiscoverytrends.com", "kind": "specialist", "home": None},
    {"name": "Chemistry World", "site": "chemistryworld.com", "kind": "specialist", "home": None},
    {"name": "C&EN", "site": "cen.acs.org", "kind": "specialist", "home": None},
    # Bioprocess & biomanufacturing
    {"name": "BioProcess International", "site": "bioprocessintl.com", "kind": "specialist", "home": None},
    {"name": "Bioprocess Online", "site": "bioprocessonline.com", "kind": "specialist", "home": None},
    {"name": "Pharmaceutical Technology", "site": "pharmaceutical-technology.com", "kind": "specialist", "home": None},
    {"name": "Pharma Manufacturing", "site": "pharmamanufacturing.com", "kind": "specialist", "home": None},
    {"name": "European Pharmaceutical Review", "site": "europeanpharmaceuticalreview.com", "kind": "specialist", "home": None},
    # Pharma services / CDMO
    {"name": "Contract Pharma", "site": "contractpharma.com", "kind": "specialist", "home": None},
    {"name": "Outsourced Pharma", "site": "outsourcedpharma.com", "kind": "specialist", "home": None},
    {"name": "Endpoints News", "site": "endpts.com", "kind": "specialist", "home": None},
    {"name": "Fierce Pharma", "site": "fiercepharma.com", "kind": "specialist", "home": None},
    {"name": "Fierce Biotech", "site": "fiercebiotech.com", "kind": "specialist", "home": None},
    {"name": "BioSpace", "site": "biospace.com", "kind": "specialist", "home": None},
    {"name": "BioPharma Dive", "site": "biopharmadive.com", "kind": "specialist", "home": None},
    # Diagnostics & clinical labs
    {"name": "MedTech Dive", "site": "medtechdive.com", "kind": "specialist", "home": None},
    {"name": "Dark Daily", "site": "darkdaily.com", "kind": "specialist", "home": None},
    {"name": "CAP Today", "site": "captodayonline.com", "kind": "specialist", "home": None},
    {"name": "Clinical Lab Products", "site": "clinicallabproducts.com", "kind": "specialist", "home": None},
    # Analytical chemistry
    {"name": "LCGC International", "site": "chromatographyonline.com", "kind": "specialist", "home": None},
    {"name": "Spectroscopy Online", "site": "spectroscopyonline.com", "kind": "specialist", "home": None},
    {"name": "Separation Science", "site": "sepscience.com", "kind": "specialist", "home": None},
    {"name": "AZoM", "site": "azom.com", "kind": "specialist", "home": None},
    {"name": "News-Medical", "site": "news-medical.net", "kind": "general", "home": None},
    # Policy & funding
    {"name": "STAT News", "site": "statnews.com", "kind": "general", "home": None},
    {"name": "Science", "site": "science.org", "kind": "general", "home": None,
     "topic": "(funding OR NIH OR budget OR instruments OR laboratory)"},
    {"name": "Nature", "site": "nature.com", "kind": "general", "home": None,
     "topic": "(funding OR budget OR \"research spending\" OR laboratory)"},
    {"name": "Research Professional", "site": "researchprofessionalnews.com", "kind": "general", "home": None},
    # Market & analyst
    {"name": "Evaluate Vantage", "site": "evaluate.com", "kind": "specialist", "home": None},
    # India & South Asia
    {"name": "BioSpectrum India", "site": "biospectrumindia.com", "kind": "specialist", "home": "india"},
    {"name": "Express Pharma", "site": "expresspharma.in", "kind": "specialist", "home": "india"},
    {"name": "Pharmabiz", "site": "pharmabiz.com", "kind": "specialist", "home": "india"},
    {"name": "ETHealthworld", "site": "health.economictimes.indiatimes.com", "kind": "specialist", "home": "india"},
    # Asia Pacific
    {"name": "BioSpectrum Asia", "site": "biospectrumasia.com", "kind": "specialist", "home": "apac"},
    {"name": "Asian Scientist", "site": "asianscientist.com", "kind": "specialist", "home": "apac"},
    {"name": "Korea Biomedical Review", "site": "koreabiomed.com", "kind": "specialist", "home": "apac_rest"},
    {"name": "LabOnline", "site": "labonline.com.au", "kind": "specialist", "home": "apac_rest"},
    {"name": "Nikkei Asia", "site": "asia.nikkei.com", "kind": "general", "home": "apac", "topic": LAB_TOPIC},
    # China
    {"name": "South China Morning Post", "site": "scmp.com", "kind": "general", "home": "china", "topic": LAB_TOPIC},
    {"name": "Caixin Global", "site": "caixinglobal.com", "kind": "general", "home": "china", "topic": LAB_TOPIC},
    # Middle East & Africa (general press: KEEP_THRESHOLD applies)
    {"name": "Zawya", "site": "zawya.com", "kind": "general", "home": "mea", "topic": LAB_TOPIC},
    {"name": "Arabian Business", "site": "arabianbusiness.com", "kind": "general", "home": "mea", "topic": LAB_TOPIC},
    {"name": "Gulf News", "site": "gulfnews.com", "kind": "general", "home": "mea", "topic": LAB_TOPIC},
    {"name": "Omnia Health Insights", "site": "insights.omnia-health.com", "kind": "general", "home": "mea"},
    {"name": "Middle East Health", "site": "middleeasthealthmag.com", "kind": "general", "home": "mea"},
    {"name": "MedicalBrief", "site": "medicalbrief.co.za", "kind": "general", "home": "mea"},
    {"name": "Bizcommunity", "site": "bizcommunity.com", "kind": "general", "home": "mea", "topic": LAB_TOPIC},
    {"name": "Health Policy Watch", "site": "healthpolicy-watch.news", "kind": "general", "home": None,
     "topic": "(manufacturing OR diagnostics OR laboratory OR Africa)"},
    {"name": "Africa CDC", "site": "africacdc.org", "kind": "general", "home": "mea"},
    {"name": "Globes", "site": "globes.co.il", "kind": "general", "home": "mea", "topic": LAB_TOPIC},
    {"name": "Daily Sabah", "site": "dailysabah.com", "kind": "general", "home": "mea", "topic": LAB_TOPIC},
]

# Direct RSS feeds give fuller summaries than Google News. NONE of these could
# be checked from the build session (its network blocks them), so treat this
# list as unverified. /sources shows which ones work; delete the dead lines.
DIRECT_FEEDS = [
    {"name": "Fierce Biotech", "url": "https://www.fiercebiotech.com/rss/xml", "kind": "specialist", "home": None},
    {"name": "Fierce Pharma", "url": "https://www.fiercepharma.com/rss/xml", "kind": "specialist", "home": None},
    {"name": "BioPharma Dive", "url": "https://www.biopharmadive.com/feeds/news/", "kind": "specialist", "home": None},
    {"name": "MedTech Dive", "url": "https://www.medtechdive.com/feeds/news/", "kind": "specialist", "home": None},
    {"name": "GEN", "url": "https://www.genengnews.com/feed/", "kind": "specialist", "home": None},
    {"name": "STAT News", "url": "https://www.statnews.com/feed/", "kind": "general", "home": None},
    {"name": "Dark Daily", "url": "https://www.darkdaily.com/feed/", "kind": "specialist", "home": None},
    {"name": "Express Pharma", "url": "https://www.expresspharma.in/feed/", "kind": "specialist", "home": "india"},
    {"name": "Asian Scientist", "url": "https://www.asianscientist.com/feed/", "kind": "specialist", "home": "apac"},
    {"name": "Korea Biomedical Review", "url": "https://www.koreabiomed.com/rss/allArticle.xml", "kind": "specialist", "home": "apac_rest"},
    {"name": "MedicalBrief", "url": "https://www.medicalbrief.co.za/feed/", "kind": "general", "home": "mea"},
    {"name": "Health Policy Watch", "url": "https://healthpolicy-watch.news/feed/", "kind": "general", "home": None},
]

# Google News editions. The US edition under-reports APMEA (Part 2).
GN_EDITIONS = {
    "US": "hl=en-US&gl=US&ceid=US:en",
    "IN": "hl=en-IN&gl=IN&ceid=IN:en",
    "SG": "hl=en-SG&gl=SG&ceid=SG:en",
    "AU": "hl=en-AU&gl=AU&ceid=AU:en",
    "ZA": "hl=en-ZA&gl=ZA&ceid=ZA:en",
    "NG": "hl=en-NG&gl=NG&ceid=NG:en",
    "KE": "hl=en-KE&gl=KE&ceid=KE:en",
    "IL": "hl=en-IL&gl=IL&ceid=IL:en",
}
NEWS_WINDOW_DAYS = 30
SPECIALIST_WINDOW = "when:14d"     # site-scoped searches
SEARCH_WINDOW = "when:30d"

# ---------------------------------------------------------------------------
# 7. Themes (Part 4c): these drive the open searches.
# ---------------------------------------------------------------------------
# Unquoted on purpose (rule 10). Each runs in the US edition.
GLOBAL_THEMES = [
    'NIH funding cuts laboratory instruments',
    'NIH indirect costs universities research',
    'biotech funding IPO layoffs life science tools',
    'bioprocessing capacity single-use bioreactor',
    'fill-finish capacity GLP-1 sterile injectable',
    'pharma reshoring tariffs supply chain life sciences',
    'BIOSECURE Act WuXi',
    'FDA laboratory developed test rule',
    'IVDR transition diagnostics',
    'spatial biology multiomics launch',
    'long-read sequencing launch',
    'cryo-EM electron microscopy',
    'lab automation self-driving lab',
    'life science tools consumables demand',
    'cell and gene therapy manufacturing capacity',
    'mass spectrometry launch',
]

# Region themes run in that leaf's edition. Unquoted except place names.
REGION_THEMES = {
    "china": [
        'China volume-based procurement diagnostics',
        'China medical equipment renewal stimulus tender',
        'China domestic substitution bioprocessing',
        'China life science tools demand',
    ],
    "india": [
        'India CDMO China+1 biologics',
        'India BioE3 biomanufacturing policy',
        'India PLI scheme medical devices pharma',
        'India USFDA warning letter plant',
        'India genomics diagnostics laboratory',
    ],
    "apac_rest": [
        'Korea CDMO biologics plant',
        'Japan biologics manufacturing investment',
        'Singapore biomanufacturing',
        'Australia research funding laboratory',
        'Taiwan semiconductor electron microscopy materials analysis',
    ],
    "mea": [
        'Saudi Arabia biotechnology strategy',
        'Saudi localisation pharmaceutical manufacturing',
        'UAE genome programme',
        'Africa vaccine manufacturing Africa CDC',
        'South Africa pharmaceutical manufacturing',
        'GCC laboratory diagnostics hospital',
    ],
}
# Extra editions for MEA, because one edition cannot cover the region.
REGION_EXTRA_EDITIONS = {"mea": ["IL", "NG", "KE"], "apac_rest": ["AU"]}

# Leaf x segment searches: "<region> (<segment words>)" per leaf, per segment.
SEGMENT_QUERY_WORDS = {
    "bioprocess": '(bioprocessing OR biomanufacturing OR bioreactor OR "fill-finish" OR biologics plant)',
    "genomics": '(sequencing OR genomics OR genome OR qPCR OR "spatial biology")',
    "instruments": '("mass spectrometry" OR chromatography OR spectroscopy OR "electron microscopy" OR "analytical instruments")',
    "diagnostics": '(diagnostics OR "clinical laboratory" OR immunoassay OR IVD OR pathology)',
    "services": '(CDMO OR CRO OR "clinical trials" OR "lab automation" OR "laboratory equipment")',
}

# ---------------------------------------------------------------------------
# 8. Practitioner voice (Part 4d)
# ---------------------------------------------------------------------------
REDDIT_ENABLED = True
REDDIT_MAX_REQUESTS = 16
REDDIT_GIVE_UP_AFTER = 3            # consecutive 429s
REDDIT_TIME_LIMIT = 900             # seconds
REDDIT_SPACING = 20                 # seconds between requests
REDDIT_RETRY_SLEEP = 45
REDDIT_SUBS = ["labrats", "biotech", "massspectrometry", "bioinformatics",
               "Chempros", "medlabprofessionals", "PhD", "AskBiology"]
# Each entry is one request across all subs. Brands batched with OR (rule 9).
REDDIT_QUERIES = [
    "service contract", "instrument downtime", "consumable price",
    "procurement", "quote", "sales rep", "software license",
    "calibration", "reagent lead time",
    '"Thermo Fisher" OR Agilent OR Shimadzu OR Bruker',
    '"Waters" OR Sciex OR "mass spec" vendor',
    'Illumina OR Nanopore OR PacBio OR "10x Genomics"',
    'Cytiva OR Sartorius OR Repligen OR MilliporeSigma',
    'India lab OR Indian lab',
    'Singapore OR Japan OR Korea OR Australia lab',
    'Saudi OR UAE OR Dubai OR "South Africa" lab',
]
REDDIT_USER_AGENT = "tmo-intel-dashboard/1.0 (weekly research digest; RSS only)"

YOUTUBE_ENABLED = True
YOUTUBE_MAX_RESULTS = 15
# region: fallback leaf when the video text names no region.
YOUTUBE_QUERIES = [
    {"q": "HPLC troubleshooting", "regionCode": None, "region": None},
    {"q": "mass spectrometer maintenance service", "regionCode": None, "region": None},
    {"q": "LC-MS method development tutorial", "regionCode": None, "region": None},
    {"q": "qPCR protocol tips", "regionCode": None, "region": None},
    {"q": "flow cytometry tutorial", "regionCode": None, "region": None},
    {"q": "single-use bioreactor", "regionCode": None, "region": None},
    {"q": "next generation sequencing workflow", "regionCode": None, "region": None},
    {"q": "lab automation liquid handling", "regionCode": None, "region": None},
    {"q": "laboratory equipment India", "regionCode": "IN", "region": "india"},
    {"q": "biotech lab tour India", "regionCode": "IN", "region": "india"},
    {"q": "Singapore biomanufacturing", "regionCode": "SG", "region": "apac_rest"},
    {"q": "Japan analytical instruments exhibition", "regionCode": "JP", "region": "apac_rest"},
    {"q": "Saudi Arabia biotechnology laboratory", "regionCode": "AE", "region": "mea"},
    {"q": "UAE genomics laboratory", "regionCode": "AE", "region": "mea"},
    {"q": "South Africa laboratory diagnostics", "regionCode": "ZA", "region": "mea"},
    {"q": "Korea bioprocess CDMO", "regionCode": None, "region": "apac_rest"},
]

# Deterministic pre-filter for practitioner posts, before the model screens.
VOICE_LAB_CONTEXT = [
    "lab", "labs", "laboratory", "instrument", "instruments", "assay",
    "reagent", "reagents", "hplc", "lc-ms", "lcms", "mass spec", "pcr",
    "qpcr", "sequencing", "sequencer", "column", "cell culture",
    "protocol", "experiment", "bench", "pipette", "centrifuge",
    "microscope", "spectrometer", "chromatography", "service engineer",
    "field service", "vendor", "quote", "procurement", "purchasing",
    "consumables", "kit", "kits", "antibody", "bioreactor", "flow cytometry",
    "calibration", "software", "license", "licence", "sales rep", "pi",
    "postdoc", "grad student", "core facility", "sample", "samples",
]
VOICE_OFFTOPIC = [
    "league of legends", "valorant", "fortnite", "minecraft", "genshin",
    "dota", "overwatch", "playstation", "xbox", "nintendo", "nba", "nfl",
    "premier league", "fantasy football", "recipe", "dating", "tinder",
]
VOICE_SCREEN_FLOOR = 0.4            # rule 14

# ---------------------------------------------------------------------------
# 9. Model use and budgets (Part 7)
# ---------------------------------------------------------------------------
# Generic on purpose (rule 21): no company name, no internal priorities.
BUSINESS_DESCRIPTION = (
    "a global supplier of laboratory instruments, reagents, consumables, "
    "bioprocessing equipment and pharma services, reviewing its Asia Pacific, "
    "Middle East and Africa markets"
)
MIN_STORIES_FOR_BRIEF = 3
MIN_POSTS_FOR_VOICE_BRIEF = 3
MAX_BRIEFS = 36
STORIES_PER_BRIEF = 25
VOCAB_SAMPLE = 150                  # headlines sent to vocabulary learning
SCREEN_BATCH = 60                   # posts per screening call
MIN_GAP_SECONDS = 7
MAX_PANEL_STORIES = 60
MAX_PANEL_RIVALS = 12
MAX_PANEL_VOICE = 12

# Collection parallelism (rule 11)
FEED_WORKERS = 8
SEARCH_WORKERS = 6
RIVAL_WORKERS = 5
HTTP_TIMEOUT = 25
