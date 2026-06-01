import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

# Your authoritative galaxy list, HUMAN numbering (1-based).
GALAXY_NAME_BY_HUMAN_NUMBER = {
    1: "Euclid",
    2: "Hilbert Dimension",
    3: "Calypso",
    4: "Hesperius Dimension",
    5: "Hyades",
    6: "Ickjamatew",
    7: "Budullangr",
    8: "Kikolgallr",
    9: "Eltiensleen",
    10: "Eissentam",
    11: "Elkupalos",
    12: "Aptarkaba",
    13: "Ontiniangp",
    14: "Odiwagiri",
    15: "Ogtialabi",
    16: "Muhacksonto",
    17: "Hitonskyer",
    18: "Rerasmutul",
    19: "Isdoraijung",
    20: "Doctinawyra",
    21: "Loychazinq",
    22: "Zukasizawa",
    23: "Ekwathore",
    24: "Yeberhahne",
    25: "Twerbetek",
    26: "Sivarates",
    27: "Eajerandal",
    28: "Aldukesci",
    29: "Wotyarogii",
    30: "Sudzerbal",
    31: "Maupenzhay",
    32: "Sugueziume",
    33: "Brogoweldian",
    34: "Ehbogdenbu",
    35: "Ijsenufryos",
    36: "Nipikulha",
    37: "Autsurabin",
    38: "Lusontrygiamh",
    39: "Rewmanawa",
    40: "Ethiophodhe",
    41: "Urastrykle",
    42: "Xobeurindj",
    43: "Oniijialdu",
    44: "Wucetosucc",
    45: "Ebyeloof",
    46: "Odyavanta",
    47: "Milekistri",
    48: "Waferganh",
    49: "Agnusopwit",
    50: "Teyaypilny",
    51: "Zalienkosm",
    52: "Ladgudiraf",
    53: "Mushonponte",
    54: "Amsentisz",
    55: "Fladiselm",
    56: "Laanawemb",
    57: "Ilkerloor",
    58: "Davanossi",
    59: "Ploehrliou",
    60: "Corpinyaya",
    61: "Leckandmeram",
    62: "Quulngais",
    63: "Nokokipsechl",
    64: "Rinblodesa",
    65: "Loydporpen",
    66: "Ibtrevskip",
    67: "Elkowaldb",
    68: "Heholhofsko",
    69: "Yebrilowisod",
    70: "Husalvangewi",
    71: "Ovna'uesed",
    72: "Bahibusey",
    73: "Nuybeliaure",
    74: "Doshawchuc",
    75: "Ruckinarkh",
    76: "Thorettac",
    77: "Nuponoparau",
    78: "Moglaschil",
    79: "Uiweupose",
    80: "Nasmilete",
    81: "Ekdaluskin",
    82: "Hakapanasy",
    83: "Dimonimba",
    84: "Cajaccari",
    85: "Olonerovo",
    86: "Umlanswick",
    87: "Henayliszm",
    88: "Utzenmate",
    89: "Umirpaiya",
    90: "Paholiang",
    91: "Iaereznika",
    92: "Yudukagath",
    93: "Boealalosnj",
    94: "Yaevarcko",
    95: "Coellosipp",
    96: "Wayndohalou",
    97: "Smoduraykl",
    98: "Apmaneessu",
    99: "Hicanpaav",
    100: "Akvasanta",
    101: "Tuychelisaor",
    102: "Rivskimbe",
    103: "Daksanquix",
    104: "Kissonlin",
    105: "Aediabiel",
    106: "Ulosaginyik",
    107: "Roclaytonycar",
    108: "Kichiaroa",
    109: "Irceauffey",
    110: "Nudquathsenfe",
    111: "Getaizakaal",
    112: "Hansolmien",
    113: "Bloytisagra",
    114: "Ladsenlay",
    115: "Luyugoslasr",
    116: "Ubredhatk",
    117: "Cidoniana",
    118: "Jasinessa",
    119: "Torweierf",
    120: "Saffneckm",
    121: "Thnistner",
    122: "Dotusingg",
    123: "Luleukous",
    124: "Jelmandan",
    125: "Otimanaso",
    126: "Enjaxusanto",
    127: "Sezviktorew",
    128: "Zikehpm",
    129: "Bephembah",
    130: "Broomerrai",
    131: "Meximicka",
    132: "Venessika",
    133: "Gaiteseling",
    134: "Zosakasiro",
    135: "Drajayanes",
    136: "Ooibekuar",
    137: "Urckiansi",
    138: "Dozivadido",
    139: "Emiekereks",
    140: "Meykinunukur",
    141: "Kimycuristh",
    142: "Roansfien",
    143: "Isgarmeso",
    144: "Daitibeli",
    145: "Gucuttarik",
    146: "Enlaythie",
    147: "Drewweste",
    148: "Akbulkabi",
    149: "Homskiw",
    150: "Zavainlani",
    151: "Jewijkmas",
    152: "Itlhotagra",
    153: "Podalicess",
    154: "Hiviusauer",
    155: "Halsebenk",
    156: "Puikitoac",
    157: "Gaybakuaria",
    158: "Grbodubhe",
    159: "Rycempler",
    160: "Indjalala",
    161: "Fontenikk",
    162: "Pasycihelwhee",
    163: "Ikbaksmit",
    164: "Telicianses",
    165: "Oyleyzhan",
    166: "Uagerosat",
    167: "Impoxectin",
    168: "Twoodmand",
    169: "Hilfsesorbs",
    170: "Ezdaranit",
    171: "Wiensanshe",
    172: "Ewheelonc",
    173: "Litzmantufa",
    174: "Emarmatosi",
    175: "Mufimbomacvi",
    176: "Wongquarum",
    177: "Hapirajua",
    178: "Igbinduina",
    179: "Wepaitvas",
    180: "Sthatigudi",
    181: "Yekathsebehn",
    182: "Ebedeagurst",
    183: "Nolisonia",
    184: "Ulexovitab",
    185: "Iodhinxois",
    186: "Irroswitzs",
    187: "Bifredait",
    188: "Beiraghedwe",
    189: "Yeonatlak",
    190: "Cugnatachh",
    191: "Nozoryenki",
    192: "Ebralduri",
    193: "Evcickcandj",
    194: "Ziybosswin",
    195: "Heperclait",
    196: "Sugiuniam",
    197: "Aaseertush",
    198: "Uglyestemaa",
    199: "Horeroedsh",
    200: "Drundemiso",
    201: "Ityanianat",
    202: "Purneyrine",
    203: "Dokiessmat",
    204: "Nupiacheh",
    205: "Dihewsonj",
    206: "Rudrailhik",
    207: "Tweretnort",
    208: "Snatreetze",
    209: "Iwundaracos",
    210: "Digarlewena",
    211: "Erquagsta",
    212: "Logovoloin",
    213: "Boyaghosganh",
    214: "Kuolungau",
    215: "Pehneldept",
    216: "Yevettiiqidcon",
    217: "Sahliacabru",
    218: "Noggalterpor",
    219: "Chmageaki",
    220: "Veticueca",
    221: "Vittesbursul",
    222: "Nootanore",
    223: "Innebdjerah",
    224: "Kisvarcini",
    225: "Cuzcogipper",
    226: "Pamanhermonsu",
    227: "Brotoghek",
    228: "Mibittara",
    229: "Huruahili",
    230: "Raldwicarn",
    231: "Ezdartlic",
    232: "Badesclema",
    233: "Isenkeyan",
    234: "Iadoitesu",
    235: "Yagrovoisi",
    236: "Ewcomechio",
    237: "Inunnunnoda",
    238: "Dischiutun",
    239: "Yuwarugha",
    240: "Ialmendra",
    241: "Reponudrle",
    242: "Rinjanagrbo",
    243: "Zeziceloh",
    244: "Oeileutasc",
    245: "Zicniijinis",
    246: "Dugnowarilda",
    247: "Neuxoisan",
    248: "Ilmenhorn",
    249: "Rukwatsuku",
    250: "Nepitzaspru",
    251: "Chcehoemig",
    252: "Haffneyrin",
    253: "Uliciawai",
    254: "Tuhgrespod",
    255: "Iousongola",
    256: "Odyalutai",
}

# Convert human numbering to save numbering
GALAXY_NAME_BY_SAVE_INDEX = {
    human_num - 1: name for human_num, name in GALAXY_NAME_BY_HUMAN_NUMBER.items()
}

# Glyph name mapping keyed by the portal hex digit.
# These are the common glyph names used by the wiki / community tables.
GLYPH_NAME_BY_HEX = {
    "0": "Sunrise",
    "1": "Bird",
    "2": "Face",
    "3": "Diplo",
    "4": "Eclipse",
    "5": "Balloon",
    "6": "Boat",
    "7": "Bug",
    "8": "Dragonfly",
    "9": "Galaxy",
    "A": "Octagon",
    "B": "Fish",
    "C": "Tent",
    "D": "Rocket",
    "E": "Tree",
    "F": "Atlas",
}


def galaxy_name_from_save_index(save_index):
    if isinstance(save_index, int):
        return GALAXY_NAME_BY_SAVE_INDEX.get(save_index, "")
    return ""


def human_number_from_save_index(save_index):
    if isinstance(save_index, int):
        return save_index + 1
    return ""


def load_json_with_backslash_fix(path: Path):
    """
    Load JSON, but repair invalid backslash escapes inside quoted strings if needed.
    This handles malformed exported JSON like:
      "C:\\Temp\\Stuff"  <-- valid
      "C:\Temp\Stuff"    <-- invalid JSON, but some exporters still emit it
    """
    raw = path.read_text(encoding="utf-8")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print("Standard JSON parse failed.")
        print(f"Reason: {e}")
        print("Attempting automatic repair of invalid backslashes inside strings...")

    repaired_chars = []
    in_string = False
    escape = False
    i = 0

    while i < len(raw):
        ch = raw[i]

        if in_string:
            if escape:
                if ch in '"\\/bfnrt':
                    repaired_chars.append("\\")
                    repaired_chars.append(ch)
                elif ch == "u":
                    hex_part = raw[i + 1 : i + 5]
                    if len(hex_part) == 4 and all(
                        c in "0123456789abcdefABCDEF" for c in hex_part
                    ):
                        repaired_chars.append("\\")
                        repaired_chars.append("u")
                    else:
                        repaired_chars.append("\\\\")
                        repaired_chars.append("u")
                else:
                    repaired_chars.append("\\\\")
                    repaired_chars.append(ch)
                escape = False
            else:
                if ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                    repaired_chars.append(ch)
                else:
                    repaired_chars.append(ch)
        else:
            repaired_chars.append(ch)
            if ch == '"':
                in_string = True

        i += 1

    if escape:
        repaired_chars.append("\\\\")

    repaired = "".join(repaired_chars)
    return json.loads(repaired)


def walk(node):
    """Recursively yield every dict in a nested JSON structure."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def to_unsigned_hex(value: int, digits: int) -> str:
    """
    Convert signed integer to fixed-width uppercase hex using the right-most digits.
    For example:
      -8 with digits=2  -> F8
      -976 with digits=3 -> C30
    """
    mask = (1 << (digits * 4)) - 1
    return f"{value & mask:0{digits}X}"


def build_portal_fields(planet_index, system_index, voxel_x, voxel_y, voxel_z):
    if any(v is None for v in [planet_index, system_index, voxel_x, voxel_y, voxel_z]):
        return {
            "Portal Hex (Grouped)": "",
            "Glyph String (No Spaces)": "",
            "Glyph Digits": "",
            "Glyph Names": "",
        }

    p = f"{planet_index & 0xF:X}"
    sss = f"{system_index & 0xFFF:03X}"
    yy = f"{voxel_y & 0xFF:02X}"
    zzz = f"{voxel_z & 0xFFF:03X}"
    xxx = f"{voxel_x & 0xFFF:03X}"

    compact = f"{p}{sss}{yy}{zzz}{xxx}"
    grouped = f"{p} {sss} {yy} {zzz} {xxx}"
    glyph_digits = " ".join(compact)
    glyph_names = " | ".join(GLYPH_NAME_BY_HEX[d] for d in compact)

    return {
        "Portal Hex (Grouped)": grouped,
        "Glyph String (No Spaces)": compact,
        "Glyph Digits": glyph_digits,
        "Glyph Names": glyph_names,
    }


def decode_packed_galactic_address(value):
    """
    Decode the packed 64-bit GalacticAddress used in PersistentPlayerBases.
    """
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        if text.lower().startswith("0x"):
            value = int(text, 16)
        else:
            value = (
                int(text, 16)
                if all(c in "0123456789abcdefABCDEF" for c in text)
                else int(text)
            )

    return {
        "VoxelX": (value >> 0) & 0xFFF,
        "VoxelZ": (value >> 12) & 0xFFF,
        "VoxelY": (value >> 24) & 0xFF,
        "Unknown": (value >> 32) & 0xFF,
        "SolarSystemIndex": (value >> 40) & 0xFFF,
        "PlanetIndex": (value >> 52) & 0xF,
    }


def signed_from_bits(value, bits):
    sign_bit = 1 << (bits - 1)
    if value & sign_bit:
        return value - (1 << bits)
    return value


def decode_packed_galactic_address_signed(value):
    decoded = decode_packed_galactic_address(value)
    if not decoded:
        return None

    return {
        "VoxelX": signed_from_bits(decoded["VoxelX"], 12),
        "VoxelY": signed_from_bits(decoded["VoxelY"], 8),
        "VoxelZ": signed_from_bits(decoded["VoxelZ"], 12),
        "SolarSystemIndex": decoded["SolarSystemIndex"],
        "PlanetIndex": decoded["PlanetIndex"],
        "Unknown": decoded["Unknown"],
    }


def add_vectors(a, b):
    return [a[i] + b[i] for i in range(3)]


def format_planetary_coordinates_from_world_position(pos):
    """
    Derive No Man's Sky-style planetary coordinates from a world-space position vector.
    Returns values like:
        +21.30, +176.48

    Latitude is derived from Y relative to the planet center.
    Longitude is derived from X/Z around the planet.

    If your in-game longitude reads mirrored on a spot check, the only likely
    adjustment needed is to swap the atan2 argument order or negate longitude.
    """
    if not isinstance(pos, list) or len(pos) != 3:
        return ""

    x, y, z = pos
    radius = math.sqrt((x * x) + (y * y) + (z * z))
    if radius == 0:
        return ""

    latitude = math.degrees(math.asin(y / radius))
    longitude = math.degrees(math.atan2(x, z))

    # Normalize to the same signed style players usually share in-game.
    if longitude > 180:
        longitude -= 360
    elif longitude <= -180:
        longitude += 360

    return f"{latitude:+.2f}, {longitude:+.2f}"


def iter_persistent_player_bases(data):
    """
    Yield PersistentPlayerBases entries from all known save contexts.
    In this save format they live under BaseContext/PlayerStateData and
    ExpeditionContext/PlayerStateData, not at the top level.
    """
    for context_key in ("BaseContext", "ExpeditionContext"):
        context = data.get(context_key, {}) or {}
        player_state = context.get("PlayerStateData", {}) or {}
        for base in player_state.get("PersistentPlayerBases", []) or []:
            if isinstance(base, dict):
                yield base


def build_base_computer_lookup(data):
    """
    Build a lookup keyed by:
      (VoxelX, VoxelY, VoxelZ, SolarSystemIndex, PlanetIndex)

    Each value contains the base computer world position and a formatted
    planetary coordinate string.
    """
    lookup = {}

    for base in iter_persistent_player_bases(data):
        decoded = decode_packed_galactic_address_signed(base.get("GalacticAddress"))
        if not decoded:
            continue

        base_world_pos = base.get("Position")
        if not isinstance(base_world_pos, list) or len(base_world_pos) != 3:
            continue

        computer_world_pos = None
        for obj in base.get("Objects", []) or []:
            if not isinstance(obj, dict):
                continue
            if obj.get("ObjectID") != "^BUILDSAVE":
                continue

            local_pos = obj.get("Position")
            if isinstance(local_pos, list) and len(local_pos) == 3:
                computer_world_pos = add_vectors(base_world_pos, local_pos)
                break

        key = (
            decoded["VoxelX"],
            decoded["VoxelY"],
            decoded["VoxelZ"],
            decoded["SolarSystemIndex"],
            decoded["PlanetIndex"],
        )

        lookup[key] = {
            "computer_world_pos": computer_world_pos,
            "computer_coordinates": format_planetary_coordinates_from_world_position(
                computer_world_pos
            ),
        }

    return lookup


def extract_base_rows(data):
    rows = []
    base_computer_lookup = build_base_computer_lookup(data)

    for node in walk(data):
        if not isinstance(node, dict):
            continue

        if node.get("TeleporterType") != "Base":
            continue

        ua = node.get("UniverseAddress", {}) or {}
        ga = ua.get("GalacticAddress", {}) or {}

        reality_index = ua.get("RealityIndex")
        voxel_x = ga.get("VoxelX")
        voxel_y = ga.get("VoxelY")
        voxel_z = ga.get("VoxelZ")
        system_index = ga.get("SolarSystemIndex")
        planet_index = ga.get("PlanetIndex")

        base_name = str(node.get("Name", "")).strip()

        portal_fields = build_portal_fields(
            planet_index=planet_index,
            system_index=system_index,
            voxel_x=voxel_x,
            voxel_y=voxel_y,
            voxel_z=voxel_z,
        )

        lookup_key = (voxel_x, voxel_y, voxel_z, system_index, planet_index)
        computer_info = base_computer_lookup.get(lookup_key, {})
        computer_coordinates = computer_info.get("computer_coordinates", "")
        teleporter_coordinates = format_planetary_coordinates_from_world_position(
            node.get("Position")
        )

        row = {
            "Base Name": base_name,
            "Galaxy": galaxy_name_from_save_index(reality_index),
            "Galaxy Number (Save)": reality_index,
            "Galaxy Number (Human)": human_number_from_save_index(reality_index),
            "VoxelX": voxel_x,
            "VoxelY": voxel_y,
            "VoxelZ": voxel_z,
            "SystemIndex": system_index,
            "Planet": planet_index,
            "Computer Coordinates": computer_coordinates,
            "Teleporter Coordinates": teleporter_coordinates,
            "IsFavourite": bool(node.get("IsFavourite", False)),
            "IsFeatured": bool(node.get("IsFeatured", False)),
            "System (Coords)": f"({voxel_x}, {voxel_y}, {voxel_z}) | {system_index}",
            "Notes": "",
            **portal_fields,
        }
        rows.append(row)

    return rows


def dedupe_exact_rows(rows):
    seen = set()
    deduped = []

    for row in rows:
        key = (
            row["Base Name"],
            row["Galaxy Number (Save)"],
            row["VoxelX"],
            row["VoxelY"],
            row["VoxelZ"],
            row["SystemIndex"],
            row["Planet"],
            row["IsFavourite"],
            row["IsFeatured"],
        )
        if key not in seen:
            seen.add(key)
            deduped.append(row)
        else:
            print(f"Already seen: {row}")

    return deduped


def annotate_notes(rows):
    name_counts = Counter(row["Base Name"] for row in rows if row["Base Name"])

    for row in rows:
        notes = []
        if row["IsFavourite"]:
            notes.append("Favourite")
        if row["IsFeatured"]:
            notes.append("Featured")
        if row["Base Name"] and name_counts[row["Base Name"]] > 1:
            notes.append("Repeated base name")
        if row["Planet"] == 0:
            notes.append("PlanetIndex 0 (portal will error-correct to planet 1)")
        row["Notes"] = "; ".join(notes)

    return rows


def sort_rows(rows):
    return sorted(
        rows,
        key=lambda r: (
            r["Galaxy Number (Save)"]
            if r["Galaxy Number (Save)"] is not None
            else 999999,
            r["VoxelX"] if r["VoxelX"] is not None else 999999,
            r["VoxelY"] if r["VoxelY"] is not None else 999999,
            r["VoxelZ"] if r["VoxelZ"] is not None else 999999,
            r["SystemIndex"] if r["SystemIndex"] is not None else 999999,
            str(r["Base Name"]).lower(),
            r["Planet"] if r["Planet"] is not None else 999999,
        ),
    )


def write_csv(rows, output_path: Path, fieldnames):
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def build_grouped_rows(rows):
    grouped = []
    for row in rows:
        grouped.append(
            {
                "Galaxy": row["Galaxy"],
                "Galaxy Number (Human)": row["Galaxy Number (Human)"],
                "Galaxy Number (Save)": row["Galaxy Number (Save)"],
                "System (Coords)": row["System (Coords)"],
                "Base Name": row["Base Name"],
                "Planet": row["Planet"],
                "Computer Coordinates": row["Computer Coordinates"],
                "Teleporter Coordinates": row["Teleporter Coordinates"],
                "Portal Hex (Grouped)": row["Portal Hex (Grouped)"],
                "Glyph String (No Spaces)": row["Glyph String (No Spaces)"],
                "Glyph Digits": row["Glyph Digits"],
                "Glyph Names": row["Glyph Names"],
                "Notes": row["Notes"],
            }
        )
    return grouped


def build_duplicate_rows(rows):
    by_name = defaultdict(list)
    for row in rows:
        if row["Base Name"]:
            by_name[row["Base Name"]].append(row)

    duplicate_rows = []
    for base_name, entries in sorted(by_name.items(), key=lambda kv: kv[0].lower()):
        if len(entries) < 2:
            continue

        sorted_entries = sorted(
            entries,
            key=lambda r: (
                r["Galaxy Number (Save)"]
                if r["Galaxy Number (Save)"] is not None
                else 999999,
                r["VoxelX"] if r["VoxelX"] is not None else 999999,
                r["VoxelY"] if r["VoxelY"] is not None else 999999,
                r["VoxelZ"] if r["VoxelZ"] is not None else 999999,
                r["SystemIndex"] if r["SystemIndex"] is not None else 999999,
                r["Planet"] if r["Planet"] is not None else 999999,
            ),
        )

        for idx, entry in enumerate(sorted_entries, start=1):
            duplicate_rows.append(
                {
                    "Base Name": entry["Base Name"],
                    "Occurrence": idx,
                    "Total Occurrences": len(entries),
                    "Galaxy": entry["Galaxy"],
                    "Galaxy Number (Human)": entry["Galaxy Number (Human)"],
                    "Galaxy Number (Save)": entry["Galaxy Number (Save)"],
                    "System (Coords)": entry["System (Coords)"],
                    "Planet": entry["Planet"],
                    "Computer Coordinates": entry["Computer Coordinates"],
                    "Teleporter Coordinates": entry["Teleporter Coordinates"],
                    "Portal Hex (Grouped)": entry["Portal Hex (Grouped)"],
                    "Glyph String (No Spaces)": entry["Glyph String (No Spaces)"],
                    "Glyph Digits": entry["Glyph Digits"],
                    "Glyph Names": entry["Glyph Names"],
                    "Notes": entry["Notes"],
                }
            )

    return duplicate_rows


def write_summary(rows, summary_path: Path):
    total_bases = len(rows)
    by_galaxy = Counter(
        (row["Galaxy Number (Save)"], row["Galaxy"], row["Galaxy Number (Human)"])
        for row in rows
    )
    by_name = Counter(row["Base Name"] for row in rows if row["Base Name"])

    repeated_name_count = sum(1 for _, count in by_name.items() if count > 1)
    favourite_count = sum(1 for row in rows if row["IsFavourite"])
    featured_count = sum(1 for row in rows if row["IsFeatured"])
    planet_zero_count = sum(1 for row in rows if row["Planet"] == 0)

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("No Man's Sky Base Extraction Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total unique teleporter-base rows: {total_bases}\n")
        f.write(f"Bases marked Favourite: {favourite_count}\n")
        f.write(f"Bases marked Featured: {featured_count}\n")
        f.write(f"Distinct repeated base names: {repeated_name_count}\n")
        f.write(f"Bases with PlanetIndex 0: {planet_zero_count}\n\n")

        f.write("Counts by galaxy:\n")
        for save_num, galaxy_name, human_num in sorted(
            by_galaxy.keys(), key=lambda x: x[0] if x[0] is not None else 999999
        ):
            count = by_galaxy[(save_num, galaxy_name, human_num)]
            display_name = galaxy_name if galaxy_name else f"Galaxy {human_num}"
            f.write(
                f"  {display_name} | Human {human_num} | Save {save_num}: {count}\n"
            )

        f.write("\nRepeated base names:\n")
        any_repeats = False
        for base_name, count in sorted(
            by_name.items(), key=lambda kv: (-kv[1], kv[0].lower())
        ):
            if count > 1:
                any_repeats = True
                f.write(f"  {base_name}: {count}\n")
        if not any_repeats:
            f.write("  None\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract No Man's Sky teleporter-base entries from an exported save JSON and generate reports with portal addresses."
    )
    parser.add_argument("input_json", help="Path to the exported save JSON file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="nms_base_reports",
        help="Output directory (default: nms_base_reports)",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    main_csv = output_dir / "nms_bases_master.csv"
    grouped_csv = output_dir / "nms_bases_grouped.csv"
    dupes_csv = output_dir / "nms_bases_duplicate_names.csv"
    summary_txt = output_dir / "nms_bases_summary.txt"

    data = load_json_with_backslash_fix(input_path)

    rows = extract_base_rows(data)
    rows = dedupe_exact_rows(rows)
    rows = annotate_notes(rows)
    rows = sort_rows(rows)

    main_fieldnames = [
        "Base Name",
        "Galaxy",
        "Galaxy Number (Human)",
        "Galaxy Number (Save)",
        "VoxelX",
        "VoxelY",
        "VoxelZ",
        "SystemIndex",
        "Planet",
        "Computer Coordinates",
        "Teleporter Coordinates",
        "System (Coords)",
        "Portal Hex (Grouped)",
        "Glyph String (No Spaces)",
        "Glyph Digits",
        "Glyph Names",
        "Notes",
    ]
    write_csv(rows, main_csv, main_fieldnames)

    grouped_rows = build_grouped_rows(rows)
    grouped_fieldnames = [
        "Galaxy",
        "Galaxy Number (Human)",
        "Galaxy Number (Save)",
        "System (Coords)",
        "Base Name",
        "Planet",
        "Computer Coordinates",
        "Teleporter Coordinates",
        "Portal Hex (Grouped)",
        "Glyph String (No Spaces)",
        "Glyph Digits",
        "Glyph Names",
        "Notes",
    ]
    write_csv(grouped_rows, grouped_csv, grouped_fieldnames)

    duplicate_rows = build_duplicate_rows(rows)
    dupes_fieldnames = [
        "Base Name",
        "Occurrence",
        "Total Occurrences",
        "Galaxy",
        "Galaxy Number (Human)",
        "Galaxy Number (Save)",
        "System (Coords)",
        "Planet",
        "Computer Coordinates",
        "Teleporter Coordinates",
        "Portal Hex (Grouped)",
        "Glyph String (No Spaces)",
        "Glyph Digits",
        "Glyph Names",
        "Notes",
    ]
    write_csv(duplicate_rows, dupes_csv, dupes_fieldnames)

    write_summary(rows, summary_txt)

    repeated_groups = len({r["Base Name"] for r in duplicate_rows})

    print(f"Master CSV written:       {main_csv.resolve()}")
    print(f"Grouped CSV written:      {grouped_csv.resolve()}")
    print(f"Duplicate report written: {dupes_csv.resolve()}")
    print(f"Summary written:          {summary_txt.resolve()}")
    print(f"\nTotal unique teleporter-base rows: {len(rows)}")
    print(f"Repeated base-name groups: {repeated_groups}")


if __name__ == "__main__":
    main()
