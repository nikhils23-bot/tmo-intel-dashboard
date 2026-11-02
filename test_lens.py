"""
test_lens.py: regression cases for lens.py.

Run by hand before every release:   python test_lens.py
The app never imports this file.
"""

import sys

import config
import lens

BUILD = "2026-10-31.b1"

# ---------------------------------------------------------------------------
# Relevance: (title, source, kind, expected_keep)
# ---------------------------------------------------------------------------
RELEVANCE = [
    # Should keep
    ("Samsung Biologics breaks ground on fifth plant in Incheon", "Reuters", "search", True),
    ("Agilent launches new LC-MS system for biopharma QC labs", "GenomeWeb", "search", True),
    ("Illumina cuts guidance as China export controls bite", "Fierce Biotech", "search", True),
    ("India unveils BioE3 policy to boost biomanufacturing", "Economic Times", "search", True),
    ("NIH indirect cost cap hits university labs as research funding cuts deepen", "STAT", "search", True),
    ("Cytiva expands single-use bioreactor capacity in Singapore", "BioProcess International", "search", True),
    ("Waters Corporation reports Q3 revenue growth in chromatography", "Reuters", "search", True),
    ("WuXi AppTec sells US operations amid BIOSECURE Act pressure", "Endpoints News", "search", True),
    ("Saudi Arabia opens national genome centre with new sequencing capacity", "Zawya", "general", True),
    ("Merck KGaA to acquire Bio-Techne in $11.3 billion deal", "Reuters", "search", True),
    ("Thermo Fisher opens bioprocessing design centre in Hyderabad", "Express Pharma", "search", True),
    ("China volume-based procurement squeezes immunoassay prices", "360Dx", "search", True),
    ("Syngene wins biologics manufacturing agreement with US pharma", "Pharmabiz", "search", True),
    ("Mindray expands IVD manufacturing in Türkiye", "Daily Sabah", "general", True),
    ("Sartorius warns of slower bioprocessing demand recovery", "Reuters", "search", True),
    ("Tariffs on lab instruments raise costs for Indian CROs", "Mint", "search", True),
    ("Oxford Nanopore launches new long-read sequencer", "GenomeWeb", "specialist", True),
    ("Researchers develop new assay for sepsis", "360Dx", "specialist", True),
    ("Qiagen completes acquisition of Parse Biosciences", "GenomeWeb", "search", True),
    ("Lonza commissions new fill-finish site", "Contract Pharma", "specialist", True),
    ("Korean CDMO wins tech transfer for biosimilar", "Korea Biomedical Review", "specialist", True),
    ("Africa CDC pushes local vaccine manufacturing", "Health Policy Watch", "specialist", True),
    ("Avantor restructuring includes job cuts at lab supply unit", "BioPharma Dive", "search", True),
    ("FDA issues warning letter to Indian API plant after inspection", "Fierce Pharma", "search", True),
    ("Siemens Healthineers launches immunoassay analyser in Asia", "MedTech Dive", "search", True),
    # Should reject
    ("Vanguard Group raises stake in Agilent Technologies", "MarketBeat", "search", False),
    ("Mass Spectrometry Market Size to Reach $9 Billion by 2032, CAGR 7%", "openPR", "search", False),
    ("Top 10 best stocks to buy in life sciences", "Motley Fool", "search", False),
    ("Bruker shares jump after analyst price target hike", "Investing.com", "search", False),
    ("How to become a lab technician: salary and career advice", "Indeed", "search", False),
    ("Wastewater surveillance finds virus in coastal waters", "Local News", "search", False),
    ("Michael Jordan opens restaurant in Dubai", "Gulf News", "general", False),
    ("Weight loss tips: home remedies that work", "Health Site", "search", False),
    ("Lewis Hamilton wins in Abu Dhabi", "BBC", "search", False),
    ("Roast turkey recipe for Thanksgiving", "Food Blog", "search", False),
    ("Danaher stock forecast: buy rating from analysts", "Zacks", "search", False),
    ("Webinar: improving lab culture", "Labmate Online", "specialist", False),
    ("City council approves new park", "Local News", "general", False),
    ("Award-winning chef opens bistro", "Arabian Business", "general", False),
    ("Bitcoin price surges past record", "CNBC", "search", False),
]

# ---------------------------------------------------------------------------
# Region routing: (title, home, expected_regions, expected_origins or None)
# ---------------------------------------------------------------------------
REGIONS = [
    # Roll-up behaviour
    ("Shanghai biotech raises funds for new lab", None, ["apac", "china"], None),
    ("Indian CDMO expands in Hyderabad", None, ["apac", "india"], None),
    ("Japanese firm builds plant in Kobe", None, ["apac", "apac_rest"], None),
    ("Saudi Arabia launches biotech strategy", None, ["mea"], None),
    ("New lab opens in Nairobi", None, ["mea"], None),
    # APAC-wide, no country
    ("Demand for sequencing grows across Asia Pacific", None, ["apac"], None),
    ("APAC diagnostics market shifts", None, ["apac"], None),
    # ASEAN goes to the leaf, not just the roll-up
    ("ASEAN regulators align on IVD rules", None, ["apac", "apac_rest"], None),
    ("Southeast Asia CDMO capacity grows", None, ["apac", "apac_rest"], None),
    # Two APAC leaves: roll-up, no World
    ("China and India compete for CDMO work", None, ["apac", "china", "india"], None),
    # APAC + MEA: both, no World
    ("Lab expansion in India and Saudi Arabia", None, ["apac", "india", "mea"], None),
    ("Distributor deal covers Singapore and the UAE", None, ["apac", "apac_rest", "mea"], None),
    # APMEA-wide term
    ("Company names new APMEA head", None, ["apac", "mea"], None),
    # Explicit global marker adds World
    ("Indian diagnostics firm announces worldwide launch", None, ["global", "apac", "india"], None),
    ("Kit available worldwide from Singapore plant", None, ["global", "apac", "apac_rest"], None),
    # No APMEA market -> World, with origin chip
    ("NIH funding cut hits Boston labs", None, ["global"], ["US"]),
    ("US tariffs on lab equipment take effect", None, ["global"], ["US"]),
    ("European IVDR deadline looms", None, ["global"], ["Europe"]),
    ("Swiss CDMO opens plant in Basel", None, ["global"], ["Europe"]),
    ("Brazil approves new diagnostics rule", None, ["global"], ["LatAm"]),
    ("Sequencing costs keep falling", None, ["global"], []),
    # US + APMEA: APMEA wins, World only with marker
    ("US firm opens plant in Singapore", None, ["apac", "apac_rest"], ["US"]),
    # Publication home region fallback (rule 2)
    ("Firm opens new plant", "india", ["apac", "india"], None),
    ("Firm opens new plant", "apac", ["apac"], None),
    ("Firm opens new plant", "mea", ["mea"], None),
    ("Firm opens new plant", None, ["global"], None),
    # Named region beats the publication home region
    ("Firm opens new plant in Japan", "india", ["apac", "apac_rest"], None),
    ("Firm opens new plant in Dubai", "apac", ["mea"], None),
    # Home fallback ignores outside-region mentions only for APMEA naming
    ("Zydus gets USFDA nod for generic", "india", ["apac", "india"], None),
    # Word boundaries (rule 1)
    ("Bioreactor capacity expansion announced", None, ["global"], None),
    ("Firm boosts capacity at Texas site", None, ["global"], ["US"]),
    ("Indiana lab opens", None, ["global"], None),
    ("New woman-led lab venture", None, ["global"], None),
    # Region-name traps (Part 4e)
    ("MEA spokesperson comments on trade talks", None, ["global"], None),
    ("Ministry of External Affairs (MEA) briefing on visas", None, ["global"], None),
    ("Guinea pig model used in vaccine study", None, ["global"], None),
    ("Fine china sales rise", None, ["global"], None),
    ("Bone china and fine china exports", None, ["global"], None),
    ("China approves new assay", None, ["apac", "china"], None),
    ("Thanksgiving turkey prices", None, ["global"], []),
    ("Turkey's pharma exports rise", None, ["mea"], None),
    ("Türkiye builds vaccine plant", None, ["mea"], None),
    ("Michael Jordan invests in startup", None, ["global"], None),
    ("Jordan opens pharmaceutical plant in Amman", None, ["mea"], None),
    ("Gulf of Mexico storm hits Texas plants", None, ["global"], None),
    ("Gulf states invest in genomics", None, ["mea"], None),
    ("North Korea tests missile", None, ["global"], None),
    ("South Korea biotech grows", None, ["apac", "apac_rest"], None),
    ("WuXi Biologics opens Irish plant", None, ["global"], ["Europe"]),
    ("Plant opens in Wuxi city", None, ["apac", "china"], None),
    ("Papua New Guinea health lab", None, ["apac", "apac_rest"], None),
    ("West Asia conflict hits shipping", None, ["mea"], None),
    ("Latin American lab market", None, ["global"], ["LatAm"]),
    ("Researchers in the UK publish study", None, ["global"], ["Europe"]),
]

# ---------------------------------------------------------------------------
# Segment routing: (title, source_hint, must_include, must_exclude)
# ---------------------------------------------------------------------------
SEGMENTS = [
    ("New single-use bioreactor launched", "", ["bioprocess"], ["genomics"]),
    ("Long-read sequencing platform unveiled", "", ["genomics"], ["bioprocess"]),
    ("Orbitrap mass spectrometer for proteomics", "", ["instruments"], []),
    ("Immunoassay analyser cleared by FDA", "", ["diagnostics"], []),
    ("CDMO signs clinical supply deal", "", ["services"], []),
    ("Agilent posts Q3 growth", "", ["all"], ["bioprocess", "genomics", "instruments", "diagnostics", "services"]),
    ("Company reports earnings", "Contract Pharma", ["all"], []),
    ("Cryo-EM facility opens", "", ["instruments"], []),
    ("qPCR kit for infectious disease testing", "", ["genomics", "diagnostics"], []),
    ("Fill-finish capacity for GLP-1 drugs", "", ["bioprocess"], []),
    ("Lab automation and liquid handling robots", "", ["services"], []),
    ("Spatial transcriptomics study", "", ["genomics"], []),
    ("Clinical laboratory consolidation", "", ["diagnostics"], []),
    ("Chromatography resin shortage", "", ["bioprocess", "instruments"], []),
    ("Viral vector manufacturing expansion", "", ["bioprocess"], []),
]

# ---------------------------------------------------------------------------
# Name ambiguity on competitors: (title, expected_competitors)
# ---------------------------------------------------------------------------
AMBIGUITY = [
    ("Waters Corporation launches new UPLC", ["Waters"]),
    ("Waters posts strong quarter", ["Waters"]),
    ("Floodwaters hit coastal waters", []),
    ("Maxine Waters questions regulators", []),
    ("Abbott launches glucose sensor", ["Abbott"]),
    ("Greg Abbott signs Texas bill", []),
    ("Charles River Laboratories cuts jobs", ["Charles River"]),
    ("Rowing on the Charles River", []),
    ("Illumina launches sequencer", ["Illumina"]),
    ("Illuminating the path to growth", []),
    ("10x Genomics sues rival", ["10x Genomics"]),
    ("10x growth for startup", []),
    ("Element Biosciences raises funds", ["Element Biosciences"]),
    ("A key element of strategy", []),
    ("Pall Corporation filters", ["Pall"]),
    ("A pall hung over the market", []),
    ("Hamilton Company robotics", ["Hamilton"]),
    ("Hamilton musical tickets", []),
    ("ICON plc wins trial contract", ["ICON"]),
    ("An iconic design", []),
    ("Revvity results", ["Revvity"]),
    ("PerkinElmer launches analyser", ["Revvity"]),
    ("Merck KGaA results", ["Merck KGaA / MilliporeSigma"]),
    ("Merck & Co drug approval", []),
    ("WuXi AppTec and WuXi Biologics update", ["WuXi AppTec", "WuXi Biologics"]),
    ("BD Biosciences flow cytometer", ["Waters"]),
    ("Thermometer sales rise", []),
    ("Oxford Nanopore sequencing", ["Oxford Nanopore"]),
    ("Nanopore technology paper", []),
]

# Thermo traps: the subject terms must not fire on these.
SUBJECT_TRAPS = [
    ("Thermometer recall", False),
    ("Thermal imaging camera", False),
    ("Thermo Fisher Scientific opens plant", True),
    ("Invitrogen antibodies", True),
    ("PPD skin test for tuberculosis", False),
    ("PPD wins clinical trial contract", True),
]

# ---------------------------------------------------------------------------
# Practitioner-post pre-filter: (title, body, expected_keep)
# ---------------------------------------------------------------------------
VOICE = [
    ("Our Agilent service contract response time is awful", "Waited 3 weeks for a field service engineer", True),
    ("HPLC column pricing went up again", "Consumables keep getting pricier", True),
    ("Thermo rep keeps pushing a new quote", "Procurement says no", True),
    ("Waters League of Legends team wins", "Great match for the team", False),
    ("Illumina in Valorant tournament", "gaming clip", False),
    ("My PI wants me to calibrate the spectrometer daily", "", True),
    ("Best pizza recipe", "dinner ideas", False),
    ("Fortnite update", "new skins", False),
    ("Is the software license for the mass spec worth it?", "", True),
    ("Random thoughts about life", "nothing in particular", False),
]


def _run():
    failures, total = [], 0

    for title, source, kind, expect in RELEVANCE:
        total += 1
        pts, why = lens.score(title, "", source)
        got = lens.keep(pts, kind)
        if got != expect:
            failures.append(f"RELEVANCE  {title!r} [{kind}] score={pts} why={why} expected keep={expect}")

    for title, home, expect, origins in REGIONS:
        total += 1
        got, got_origins = lens.route_regions(title, "", home)
        ok = got == expect and (origins is None or got_origins == sorted(origins))
        if not ok:
            failures.append(f"REGION     {title!r} home={home} got={got} {got_origins} expected={expect} {origins}")

    for title, hint, must, must_not in SEGMENTS:
        total += 1
        got = lens.route_segments(title, "", hint)
        if not all(m in got for m in must) or any(m in got for m in must_not):
            failures.append(f"SEGMENT    {title!r} got={got} must={must} must_not={must_not}")

    for title, expect in AMBIGUITY:
        total += 1
        got = lens.competitors_named(title)
        if sorted(got) != sorted(expect):
            failures.append(f"AMBIGUITY  {title!r} got={got} expected={expect}")

    for title, expect in SUBJECT_TRAPS:
        total += 1
        got = bool(lens.hits(title.lower(), config.SUBJECT_TERMS))
        if got != expect:
            failures.append(f"SUBJECT    {title!r} got={got} expected={expect}")

    for title, body, expect in VOICE:
        total += 1
        got, reason = lens.voice_prefilter(title, body)
        if got != expect:
            failures.append(f"VOICE      {title!r} got={got} ({reason}) expected={expect}")

    # Structural checks
    total += 1
    if [r["key"] for r in config.REGIONS][0] != "global":
        failures.append("STRUCTURE  'global' must be the first region")
    total += 1
    if config.SEGMENTS[0]["key"] != "all":
        failures.append("STRUCTURE  'all' must be the first segment")
    total += 1
    if len({c["name"] for c in config.COMPETITORS}) != len(config.COMPETITORS):
        failures.append("STRUCTURE  duplicate competitor names")
    total += 1
    if any(c["star"] and not c.get("query") for c in config.COMPETITORS):
        failures.append("STRUCTURE  a starred competitor has no query")
    total += 1
    if lens.normalise_title("Agilent launches LC-MS - GenomeWeb") != "agilent launches lc ms":
        failures.append("STRUCTURE  normalise_title did not strip the publisher")

    for f in failures:
        print("FAIL", f)
    print(f"\n{total - len(failures)} / {total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
