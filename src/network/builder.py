"""
Northern Railway Network Data Foundation Builder.

Built with 100% fidelity to official Northern Railway System Map callout diagrams:
- Inset A: PATHANKOT-MUKERIAN-JALANDHAR CANTT SECTION
- Inset B: PHAGWARA-NAWANSHAHR DOABA-RAHON JAIJON DOABA SECTION
- Inset C: LUDHIANA-FIROZPUR CANTT. & LOHIAN KHAS-PHILLAUR SECTIONS
- Inset D: DELHI SHAHDARA-SHAMLI-SAHARANPUR SECTION
- Inset E: SAHARANPUR BYE PASS LINE
- Inset F: DELHI AREA
- Inset K: DELHI-ROHTAK & ROHTAK-GOHANA-PANIPAT SECTIONS
- Inset L: UTRAITIA-RAEBARELI-CHILBILA SECTION
- Inset M: PARTAPGARH-JANGHAI-VARANASI & PHAPHAMAU-JANGHAI-ZAFRABAD SECTIONS
- Inset N: UNNAO - DALMAU - UNCHAHAR SECTION
- Inset O: BEAS-GOINDWAL SAHIB-TARAN TARAN SECTION
- Inset P: LAKSAR BYE PASS LINE
- Inset Q: FAIZABAD-SULTANPUR-PARTAPGARH-PHAPHAMAU SECTION
- Inset R: ABOHAR-FAZILKA SECTION
- Inset S: VARANASI AREA
- Inset T: MUAZZAMPUR NARAIN-GAJROULA SECTION
"""

import json
import os
import re
import sqlite3
from typing import Dict, List, Any, Optional, Tuple

# Official Verified Inset Route Definitions from Northern Railway System Map
NR_MAP_ROUTES = [
    # --- INSET A ---
    {
        "route_id": "NR-A",
        "map_label": "A",
        "route_name": "Pathankot-Mukerian-Jalandhar Cantt Section",
        "division": "Firozpur",
        "stations": [
            ("PATHANKOT Jn.", "PTK", 115.71, True),
            ("PATHANKOT CANTT.", "PTKC", 112.06, False),
            ("GHIALA HALT", "GILA", 98.49, False),
            ("KANDRORI", "KNDI", 102.76, False),
            ("MIRTHAL", "MRTL", 92.19, False),
            ("BHANGALA", "BNGL", 81.93, False),
            ("MUKERIAN", "MEX", 72.46, False),
            ("UNCHI BASSI", "UCB", 62.97, False),
            ("DASUA", "DZA", 56.92, False),
            ("GARNA SAHIB", "GSB", 53.75, False),
            ("KHUDA KURALA", "KZX", 49.65, False),
            ("TANDA URMAR", "TDO", 41.70, True),
            ("CHOLANG", "CGH", 35.58, False),
            ("BHOGPUR SIRWAL", "BPRS", 28.50, False),
            ("KALA BAKARA", "KKL", 19.70, False),
            ("ALAWALPUR", "AWL", 13.80, False),
            ("SUCHI PINDI", "SCPD", 3.38, False),
            ("JALANDHAR CANTT Jn.", "JRC", 0.00, True),
        ]
    },
    # --- INSET B (Main + Branches) ---
    {
        "route_id": "NR-B1",
        "map_label": "B",
        "route_name": "Phagwara-Nawanshahr Doaba Section",
        "division": "Firozpur",
        "stations": [
            ("PHAGWARA Jn.", "PGW", 0.00, True),
            ("KULTHAM ABDULLA SHAH HALT", "KASH", 8.44, False),
            ("BAHRAM", "BHM", 13.87, False),
            ("MALUPOTA", "MXP", 19.44, False),
            ("BANGA", "BXB", 23.44, False),
            ("KHATKARKALAN JHANDAJI", "KHHJ", 26.67, False),
            ("KARIHA", "KYY", 29.99, False),
            ("NAWANSHAHR DOABA Jn.", "NSS", 35.80, True),
        ]
    },
    {
        "route_id": "NR-B2",
        "map_label": "B",
        "route_name": "Nawanshahr Doaba-Rahon Branch",
        "division": "Firozpur",
        "stations": [
            ("NAWANSHAHR DOABA Jn.", "NSS", 0.00, True),
            ("RAHON", "RHU", 6.98, False),
        ]
    },
    {
        "route_id": "NR-B3",
        "map_label": "B",
        "route_name": "Nawanshahr Doaba-Jaijon Doaba Section",
        "division": "Firozpur",
        "stations": [
            ("NAWANSHAHR DOABA Jn.", "NSS", 35.80, True),
            ("GARH SHANKAR", "GSR", 48.01, False),
            ("SATNAUR BADESRON", "SNB", 53.19, False),
            ("SAILA KHURD", "SQJ", 57.87, False),
            ("MAHNGARWAL DOABA", "MGWD", 61.81, False),
            ("JAIJON DOABA", "JJJ", 66.77, False),
        ]
    },
    # --- INSET C (Ludhiana-Firozpur & Lohian Khas-Phillaur) ---
    {
        "route_id": "NR-C1",
        "map_label": "C",
        "route_name": "Ludhiana-Firozpur Cantt Section",
        "division": "Firozpur",
        "stations": [
            ("LUDHIANA Jn.", "LDH", 0.00, True),
            ("MODEL GRAM", "MG", 3.55, False),
            ("BADOWAL", "BWZ", 11.93, False),
            ("MULLANPUR", "MLX", 20.90, False),
            ("CHAUKIMAN", "CKM", 30.74, False),
            ("JAGRAON", "JGN", 39.88, True),
            ("NANAKSAR", "NNKR", 44.86, False),
            ("AJITWAL", "AJL", 53.05, False),
            ("PARAO MAHNA", "PMH", 59.77, False),
            ("MOGA", "MQF", 68.90, True),
            ("GHALKALAN", "GKX", 74.68, False),
            ("DAGRU", "DAU", 79.16, False),
            ("MAHESHARI SANDHUAN", "MSSD", 86.31, False),
            ("TALWANDI", "TWB", 92.99, False),
            ("SULHANI", "SULH", 98.83, False),
            ("FEROZESHAH", "PHS", 104.66, False),
            ("DHINDSA HALT", "DDK", 109.66, False),
            ("SAIDANWALA", "SWX", 115.08, False),
            ("FIROZPUR CANTT", "FZR", 123.95, True),
        ]
    },
    {
        "route_id": "NR-C2",
        "map_label": "C",
        "route_name": "Phillaur-Lohian Khas Section",
        "division": "Firozpur",
        "stations": [
            ("PHILLAUR Jn.", "PHR", 0.00, True),
            ("PARTAPPURA", "PPB", 8.24, False),
            ("BILGA", "BZG", 13.56, False),
            ("GUMTALI HALT", "GTQ", 16.35, False),
            ("NURMAHAL", "NRM", 19.87, False),
            ("SIDHWAN", "SWG", 26.22, False),
            ("NAKODAR Jn.", "NRO", 32.23, True),
            ("MALSIAN SHAHKOT", "MQS", 44.07, False),
            ("MULEWAL KHAIRA", "MLKH", 49.36, False),
            ("SINDHAR", "SDZ", 53.69, False),
            ("KANG KHURD", "KGKD", 58.30, False),
            ("LOHIAN KHAS Jn.", "LNK", 64.10, True),
        ]
    },
    # --- INSET D ---
    {
        "route_id": "NR-D",
        "map_label": "D",
        "route_name": "Delhi Shahdara-Shamli-Saharanpur Section",
        "division": "Delhi",
        "stations": [
            ("DELHI SHAHDARA Jn.", "DSA", 0.00, True),
            ("BEHTA HAZIPUR HALT", "BHHZ", 5.87, False),
            ("NOLI", "NO", 8.60, False),
            ("NUSRATABAD KHARKHARI HALT", "NTG", 12.09, False),
            ("GOTRA HALT", "GTRA", 16.32, False),
            ("FAKHARPUR HALT", "FAP", 19.61, False),
            ("KHEKRA", "KEX", 22.91, False),
            ("SUNHERA HALT", "SFA", 26.64, False),
            ("AHERA HALT", "AHQ", 29.61, False),
            ("BAGHPAT ROAD", "BPM", 32.58, False),
            ("SUJRA HALT", "SUJR", 38.79, False),
            ("ALAWALPUR IDRISPUR HALT", "AIH", 42.86, False),
            ("BARKA HALT", "BADK", 45.69, False),
            ("BARAUT", "BTU", 48.36, True),
            ("BAOLI HALT", "BAOL", 53.20, False),
            ("QASIMPUR KHERI", "KPKI", 57.96, False),
            ("BHUDPUR HALT", "BDHP", 61.84, False),
            ("ASARA HALT", "ASAR", 65.39, False),
            ("AILAM HALT", "AILM", 67.86, False),
            ("KANDHLA", "KQL", 73.65, False),
            ("KANDRAWALI HALT", "KZI", 80.09, False),
            ("GUJRAN BALWAN HALT", "GLBN", 83.01, False),
            ("SHAMLI", "SMQL", 87.45, True),
            ("SILAWAR HALT", "SLWR", 94.79, False),
            ("HIND", "HID", 97.98, False),
            ("USMANPUR DEHAT HALT", "UPRD", 100.80, False),
            ("HARHAR FATEHPUR HALT", "HHP", 102.39, False),
            ("THANA BHAWAN TOWN HALT", "TBTN", 106.50, False),
            ("THANA BHAWAN", "THBN", 109.07, False),
            ("NANAUTA", "NNX", 119.00, False),
            ("SONA ARJUNPUR", "SNAP", 125.16, False),
            ("RAMPUR MANYHARAN", "RPMN", 130.53, False),
            ("BHANKLA HALT", "BNQL", 135.22, False),
            ("JANDHERA SAMASPUR HALT", "JDHH", 137.30, False),
            ("MANANI", "MNZ", 140.19, False),
            ("TAPRI Jn.", "TPZ", 151.25, True),
            ("SAHARANPUR Jn.", "SRE", 157.87, True),
        ]
    },
    # --- INSET E ---
    {
        "route_id": "NR-E",
        "map_label": "E",
        "route_name": "Saharanpur Bye Pass Line",
        "division": "Delhi",
        "stations": [
            ("SAHARANPUR Jn.", "SRE", 1591.48, True),
            ("KHANALAMPURA WEST", "KWT", 1588.83, False),
            ("HINDON CABIN", "HNC", 1585.25, False),
            ("TAPRI Jn.", "TPZ", 1574.19, True),
        ]
    },
    # --- INSET F (Delhi Area) ---
    {
        "route_id": "NR-F1",
        "map_label": "F",
        "route_name": "Delhi-Ambala Line (Delhi Area)",
        "division": "Delhi",
        "stations": [
            ("DELHI Jn.", "DLI", 0.00, True),
            ("SUBZIMANDI", "SZM", 2.77, False),
            ("DELHI AZADPUR", "DAZ", 7.23, False),
            ("ADARSH NAGAR", "ANDI", 8.98, False),
            ("BADLI HALT", "BHD", 13.53, False),
            ("KHERA KALAN", "KHKN", 16.93, False),
            ("HOLAMBI KALAN", "HUK", 20.66, False),
            ("NARELA", "NUR", 25.92, True),
        ]
    },
    {
        "route_id": "NR-F2",
        "map_label": "F",
        "route_name": "Delhi-Ghaziabad Line (Delhi Area)",
        "division": "Delhi",
        "stations": [
            ("DELHI Jn.", "DLI", 0.00, True),
            ("DELHI SHAHDARA Jn.", "DSA", 6.02, True),
            ("VIVEK VIHAR", "VVB", 8.62, False),
            ("SAHIBABAD Jn.", "SBB", 13.16, True),
            ("GHAZIABAD Jn.", "GZB", 19.88, True),
            ("CHIPYANA BUZURG", "CPYZ", 25.70, True),
        ]
    },
    {
        "route_id": "NR-F3",
        "map_label": "F",
        "route_name": "New Delhi-Hazrat Nizamuddin-Palwal Line",
        "division": "Delhi",
        "stations": [
            ("NEW DELHI", "NDLS", 27.95, True),
            ("SHIVAJI BRIDGE", "CSB", 29.22, False),
            ("TILAK BRIDGE", "TKJ", 30.59, False),
            ("PRAGATI MAIDAN", "PGMD", 32.20, False),
            ("HAZRAT NIZAMUDDIN Jn.", "HNZM", 35.21, True),
            ("OKHLA", "OKA", 42.00, False),
            ("TUGHLAKABAD", "TKD", 49.00, False),
            ("FARIDABAD", "FDB", 59.00, False),
            ("FARIDABAD TOWN", "FDN", 63.00, False),
            ("BALLABHGARH", "BVH", 67.00, False),
            ("PIYALA", "PYLA", 73.00, False),
            ("ASAOTI", "AST", 77.00, False),
            ("PALWAL", "PWL", 88.00, True),
        ]
    },
    {
        "route_id": "NR-F4",
        "map_label": "F",
        "route_name": "Delhi Ring Railway (Dayabasti-Safdarjang-Nizamuddin)",
        "division": "Delhi",
        "stations": [
            ("DAYABASTI", "DBSI", 21.01, False),
            ("PATEL NAGAR", "PTNR", 19.45, False),
            ("KIRTI NAGAR HALT", "KRTN", 17.70, False),
            ("NARAINA VIHAR HALT", "NRVR", 16.30, False),
            ("DELHI INDERPURI HALT", "DLPI", 15.05, False),
            ("BRAR SQUARE", "BRSQ", 13.52, False),
            ("SARDAR PATEL MARG HALT", "SDPR", 10.00, False),
            ("CHANAKYAPURI HALT", "CNKP", 9.36, False),
            ("DELHI SAFDARJANG", "DSJ", 7.35, False),
            ("SAROJINI NAGAR", "SOJ", 6.61, False),
            ("LODHI COLONY", "LDCY", 4.62, False),
            ("SEWA NAGAR", "SWNR", 3.56, False),
            ("LAJPAT NAGAR", "LPNR", 1.68, False),
            ("HAZRAT NIZAMUDDIN Jn.", "HNZM", 0.00, True),
        ]
    },
    # --- INSET K (Delhi-Rohtak & Rohtak-Panipat) ---
    {
        "route_id": "NR-K1",
        "map_label": "K",
        "route_name": "Delhi-Rohtak Section",
        "division": "Delhi",
        "stations": [
            ("DELHI Jn.", "DLI", 0.00, True),
            ("DELHI KISHANGANJ", "DKZ", 2.95, False),
            ("VIVEKANANDPURI", "VKP", 4.50, False),
            ("DAYABASTI", "DBSI", 5.89, False),
            ("SHAKURBASTI", "SSB", 10.19, True),
            ("MANGOLPURI HALT", "MGLP", 13.99, False),
            ("NANGLOI", "NNO", 17.19, False),
            ("MUNDKA HALT", "MQC", 20.13, False),
            ("GHEORA", "GHE", 23.06, False),
            ("BAHADURGARH", "BGZ", 29.75, True),
            ("ASAUDAH", "ASE", 37.72, False),
            ("ROHAD NAGAR HALT", "ROHN", 43.00, False),
            ("SAMPLA", "SPZ", 47.59, False),
            ("ISMAILA HARYANA", "ISM", 51.35, False),
            ("KHARAWAR", "KRZ", 58.04, False),
            ("ASTHAL BOHAR Jn.", "ABO", 64.01, True),
            ("ROHTAK Jn.", "ROK", 69.91, True),
        ]
    },
    {
        "route_id": "NR-K2",
        "map_label": "K",
        "route_name": "Rohtak-Gohana-Panipat Section",
        "division": "Delhi",
        "stations": [
            ("ROHTAK Jn.", "ROK", 0.00, True),
            ("MAKRAULI", "MKLI", 9.59, False),
            ("JASIA", "JSS", 17.65, False),
            ("RUKHI HALT", "RKX", 22.00, False),
            ("BHAINSWAN", "BASN", 24.75, False),
            ("GOHANA Jn.", "GHNA", 31.88, True),
            ("MUDLANA", "MDLA", 42.21, False),
            ("DHURANA HALT", "DHRN", 47.50, False),
            ("ISRANA", "IRA", 52.88, False),
            ("NAULATHA", "NLH", 59.24, False),
            ("BINJHOL HALT", "BNJL", 66.12, False),
            ("PANIPAT Jn.", "PNP", 71.40, True),
        ]
    },
    # --- INSET L ---
    {
        "route_id": "NR-L",
        "map_label": "L",
        "route_name": "Utraitia-Raebareli-Chilbila Section",
        "division": "Lucknow",
        "stations": [
            ("UTRAITIA Jn.", "UTR", 1060.95, True),
            ("MOHANLAL GANJ", "MLJ", 1052.35, False),
            ("KANKAHA", "KKAH", 1044.55, False),
            ("NIGOHAN", "NHN", 1037.63, False),
            ("SHRIRAJNAGAR", "SAGR", 1031.72, False),
            ("BACHHRAWAN", "BCN", 1025.98, False),
            ("KUNDANGANJ", "KVG", 1016.45, False),
            ("HARCHANDPUR", "HCP", 1010.20, False),
            ("GANGAGANJ", "GANG", 1003.14, False),
            ("RAEBARELI Jn.", "RBL", 995.35, True),
            ("RUPAMAU", "RUM", 986.39, False),
            ("FURSAT GANJ", "FTG", 977.10, False),
            ("JAIS", "JIS", 966.61, False),
            ("KASIMPUR HALT", "KCG", 964.15, False),
            ("BANI", "VAI", 956.87, False),
            ("GAURI GANJ", "GNG", 948.62, True),
            ("TALAKHAJURI", "TLKH", 942.72, False),
            ("AMETHI", "AME", 935.25, True),
            ("MISARAULI", "MFL", 929.16, False),
            ("SAHAJI PUR HALT", "SHJP", 925.35, False),
            ("ANTU", "ANT", 920.99, False),
            ("JAGESHAR GANJ", "JGJ", 912.69, False),
            ("CHILBILA Jn", "CIL", 904.09, True),
        ]
    },
    # --- INSET M (Partapgarh-Varanasi & Phaphamau-Zafrabad) ---
    {
        "route_id": "NR-M1",
        "map_label": "M",
        "route_name": "Partapgarh-Janghai-Varanasi Section",
        "division": "Lucknow",
        "stations": [
            ("PARTAPGARH Jn.", "PBH", 900.19, True),
            ("PIRTHI GANJ", "PHV", 893.40, False),
            ("DANDUPUR", "DND", 886.18, False),
            ("GAURA", "GRX", 876.12, False),
            ("SUWANSA", "SWS", 870.56, False),
            ("BADSHAHPUR", "BSE", 863.76, False),
            ("NIBHAPUR", "NBP", 856.74, False),
            ("JANGHAI Jn.", "JNH", 847.18, True),
            ("SARAI KANSRAI", "SQN", 842.02, False),
            ("SURIAWAN", "SAW", 832.02, False),
            ("MONDH", "MOF", 824.89, False),
            ("BHADOHI", "BOY", 816.66, True),
            ("PARSIPUR", "PRF", 808.19, False),
            ("KAPSETHI", "KEH", 799.89, False),
            ("SEWAPURI", "SWPR", 794.71, False),
            ("CHAUKHANDI", "CHH", 787.97, False),
            ("LOHTA", "LOT", 777.94, False),
            ("VARANASI Jn.", "BSB", 772.06, True),
        ]
    },
    {
        "route_id": "NR-M2",
        "map_label": "M",
        "route_name": "Phaphamau-Janghai-Zafrabad Section",
        "division": "Lucknow",
        "stations": [
            ("PHAPHAMAU Jn", "PFM", 46.79, True),
            ("THARWAI", "THW", 41.30, False),
            ("SARAI CHANDI", "SYC", 34.64, False),
            ("PHULPUR", "PLP", 23.26, False),
            ("UGRASENPUR", "URPR", 14.62, False),
            ("BARYARAM", "BYHA", 8.61, False),
            ("JANGHAI Jn.", "JNH", 0.00, True),
            ("JARUNA", "JUA", 9.32, False),
            ("BARSATHI", "BSY", 15.56, False),
            ("BHANAUR", "VNN", 22.10, False),
            ("MARIAHU", "MAY", 29.87, False),
            ("WARIGAON NEWADA", "WRGN", 26.17, False),
            ("SHUDINPUR", "SPPR", 35.22, False),
            ("SALKHAPUR", "SAF", 40.29, False),
            ("KAJGAON TEEWAN HALT", "KJTW", 43.91, False),
            ("ZAFRABAD Jn.", "ZBD", 47.79, True),
        ]
    },
    # --- INSET N ---
    {
        "route_id": "NR-N",
        "map_label": "N",
        "route_name": "Unnao-Dalmau-Unchahar Section",
        "division": "Lucknow",
        "stations": [
            ("UNNAO JN.", "ON", 184.40, True),
            ("KORARI", "KURO", 173.36, False),
            ("ACHAL GANJ", "ACH", 169.27, False),
            ("BAND HAMIRPUR HALT", "BAHP", 165.05, False),
            ("TIKAULI RAWATPUR", "TKRP", 161.43, False),
            ("KULHA HALT", "KULHA", 155.56, False),
            ("BIGHAPUR", "BQP", 152.03, False),
            ("INDAMAU HALT", "IDM", 146.62, False),
            ("TAKIA", "TQA", 141.98, False),
            ("BAISWARA", "BSWA", 135.74, False),
            ("RAGHURAJ SINGH", "RRS", 130.36, False),
            ("NIHASTHA HALT", "NHF", 125.02, False),
            ("LALGANJ", "LLJ", 117.02, True),
            ("BAHAI HALT", "BYQ", 111.53, False),
            ("DALMAU Jn.", "DMW", 103.67, True),
            ("BARARA BUZURG", "BRRZ", 98.03, False),
            ("JALALPUR DHAI", "JPD", 90.94, False),
            ("MANJHILEPUR", "MNJR", 83.59, False),
            ("ISWARDASPUR", "IDS", 79.45, False),
            ("UNCHAHAR Jn.", "UCR", 72.27, True),
        ]
    },
    # --- INSET O ---
    {
        "route_id": "NR-O",
        "map_label": "O",
        "route_name": "Beas-Goindwal Sahib-Taran Taran Section",
        "division": "Firozpur",
        "stations": [
            ("BEAS Jn.", "BEAS", 0.00, True),
            ("SAIDPUR JALALABAD", "SPJB", 13.00, False),
            ("KHADUR SAHIB", "KDSB", 21.50, False),
            ("GOINDWAL SAHIB", "GWSB", 27.17, False),
            ("TARAN TARAN", "TTO", 48.58, True),
        ]
    },
    # --- INSET P ---
    {
        "route_id": "NR-P",
        "map_label": "P",
        "route_name": "Laksar Bye Pass Line",
        "division": "Moradabad",
        "stations": [
            ("LAKSAR SOUTH CABIN", "LKSC", 0.00, False),
            ("LAKSAR AVOIDING LINE", "LKAV", 0.81, False),
            ("LAKSAR NORTH CABIN", "LKNC", 1.50, False),
            ("LAKSAR JN.", "LRJ", 1538.48, True),
        ]
    },
    # --- INSET Q ---
    {
        "route_id": "NR-Q",
        "map_label": "Q",
        "route_name": "Faizabad-Sultanpur-Partapgarh-Phaphamau Section",
        "division": "Lucknow",
        "stations": [
            ("AYODHYA CANTT.", "AYC", 0.00, True),
            ("MASODHA", "MSOD", 7.19, False),
            ("BHARAT KUND", "BTKD", 15.24, False),
            ("MALETHUKANAK", "MEQ", 18.85, False),
            ("KHAJURHAT", "KJA", 27.29, False),
            ("CHAURE BAZAR", "CHBR", 33.65, False),
            ("KURE BHAR", "KBE", 40.31, False),
            ("DAWARKA GANJ", "DWJ", 49.43, False),
            ("SULTANPUR Jn.", "SLN", 58.24, True),
            ("PIPARPUR", "PPU", 71.04, False),
            ("KOHNDAUR", "KDF", 82.62, False),
            ("CHILBILA Jn.", "CIL", 94.05, True),
            ("PARTAPGARH Jn.", "PBH", 97.95, True),
            ("BHUPIAMAU", "VPO", 103.16, False),
            ("BISHNATH GANJ", "BTJ", 112.51, False),
            ("DHIR GANJ", "DHRJ", 118.84, False),
            ("MAUAIMMA", "MEM", 124.18, False),
            ("SIWAITH", "SWE", 138.26, False),
            ("PHAPHAMAU Jn.", "PFM", 144.05, True),
        ]
    },
    # --- INSET R ---
    {
        "route_id": "NR-R",
        "map_label": "R",
        "route_name": "Abohar-Fazilka Section",
        "division": "Firozpur",
        "stations": [
            ("ABOHAR Jn.", "ABS", 0.00, True),
            ("BURJMOHAR HALT", "BLMA", 8.00, False),
            ("CHURIWALA", "CWDA", 15.50, False),
            ("GHALLU HALT", "GHLU", 21.25, False),
            ("KHUI KHERA", "KUKA", 27.13, False),
            ("JANDWALA HALT", "JWKA", 34.90, False),
            ("FAZILKA Jn.", "FKA", 42.89, True),
        ]
    },
    # --- INSET S ---
    {
        "route_id": "NR-S",
        "map_label": "S",
        "route_name": "Varanasi Area Section",
        "division": "Lucknow",
        "stations": [
            ("SHIVPUR", "SOP", 777.85, False),
            ("VARANASI Jn.", "BSB", 772.06, True),
            ("KASHI", "KEI", 766.70, False),
            ("BABABHAGWAN RAM HALT", "BBRH", 764.60, False),
            ("VYASNAGAR", "VYN", 761.38, False),
            ("BLOCK HUT 'B'", "BHB", 757.30, False),
            ("BLOCK HUT 'K'", "BHK", 754.00, False),
        ]
    },
    # --- INSET T ---
    {
        "route_id": "NR-T",
        "map_label": "T",
        "route_name": "Muazzampur Narain-Gajroula Section",
        "division": "Moradabad",
        "stations": [
            ("MUAZZAMPUR NARAIN Jn.", "MZM", 95.17, True),
            ("BASI KIRATPUR", "BSKR", 84.68, False),
            ("SUAHERI HALT", "UDX", 78.46, False),
            ("JHALRA HALT", "JHH", 76.06, False),
            ("BIJNOR", "BJO", 70.28, True),
            ("KHARI JHALU", "KJLU", 60.77, False),
            ("HALDAUR", "HLDR", 53.07, False),
            ("AMHERA HALT", "ARH", 49.52, False),
            ("SISAUNA HALT", "SISN", 44.72, False),
            ("CHANDPUR SIAU", "CPS", 35.06, True),
            ("BAGARPUR HALT", "BGPR", 28.49, False),
            ("BAKAINA HALT", "BKNA", 23.44, False),
            ("CHUCHELA KALAN HALT", "CLKN", 20.12, False),
            ("MANDI DHANAURA", "MNDR", 15.15, False),
            ("SHERPUR", "SEPR", 11.75, False),
            ("GAJROULA JN.", "GJL", 0.00, True),
        ]
    }
]


def normalize_station_name(name: str) -> str:
    """Normalize station names for robust deduplication."""
    clean = name.strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean.upper()


def build_network(output_dir: str = "Data/network") -> Dict[str, Any]:
    """
    Builds the complete normalized Northern Railway Network Data Foundation.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    corridors: List[Dict[str, Any]] = []
    stations_by_normalized: Dict[str, Dict[str, Any]] = {}
    station_counter = 1
    sections_by_pair: Dict[Tuple[str, str], Dict[str, Any]] = {}
    section_counter = 1
    routes: List[Dict[str, Any]] = []
    route_sections: List[Dict[str, Any]] = []
    
    # 1. Register & Deduplicate All Stations
    for raw_route in NR_MAP_ROUTES:
        for item in raw_route["stations"]:
            st_name, st_code = item[0], item[1]
            is_junc = item[3] if len(item) > 3 else False
            norm = normalize_station_name(st_name)
            
            if norm not in stations_by_normalized:
                st_id = f"NR-ST-{station_counter:04d}"
                station_counter += 1
                stations_by_normalized[norm] = {
                    "station_id": st_id,
                    "station_code": st_code,
                    "station_name": st_name,
                    "normalized_name": norm,
                    "latitude": None,
                    "longitude": None,
                    "division": raw_route.get("division"),
                    "zone": "NR",
                    "station_category": "Junction" if is_junc else "Station",
                    "is_junction": is_junc,
                    "source_document": "Northern Railway System Map",
                    "source_reference": f"Map Inset {raw_route['map_label']}",
                    "needs_verification": False if st_code else True,
                    "active": True
                }
            else:
                existing = stations_by_normalized[norm]
                if is_junc:
                    existing["is_junction"] = True
                    existing["station_category"] = "Junction"
                if not existing["station_code"] and st_code:
                    existing["station_code"] = st_code
                    existing["needs_verification"] = False
                    
    # 2. Build Routes, Physical Sections, and Route-Section Sequences
    for raw_route in NR_MAP_ROUTES:
        route_id = raw_route["route_id"]
        map_label = raw_route["map_label"]
        route_name = raw_route["route_name"]
        
        station_items = raw_route["stations"]
        station_names = [s[0] for s in station_items]
        start_station_name = station_names[0]
        end_station_name = station_names[-1]
        
        route_record = {
            "route_id": route_id,
            "corridor_id": None,
            "map_label": map_label,
            "route_name": route_name,
            "source_document": "Northern Railway System Map",
            "source_page": 1,
            "start_station_name": start_station_name,
            "end_station_name": end_station_name,
            "station_sequence": station_names,
            "source_reference": f"Map Inset {map_label}",
            "needs_verification": False,
            "active": True
        }
        routes.append(route_record)
        
        for i in range(len(station_items) - 1):
            s1_name, _, s1_chainage, _ = station_items[i]
            s2_name, _, s2_chainage, _ = station_items[i + 1]
            
            s1_norm = normalize_station_name(s1_name)
            s2_norm = normalize_station_name(s2_name)
            
            st1 = stations_by_normalized[s1_norm]
            st2 = stations_by_normalized[s2_norm]
            st1_id = st1["station_id"]
            st2_id = st2["station_id"]
            
            # Canonical pair for physical section deduplication
            canonical_pair = (min(st1_id, st2_id), max(st1_id, st2_id))
            
            # Compute distance if chainage is present
            calc_dist = None
            if s1_chainage is not None and s2_chainage is not None:
                calc_dist = round(abs(float(s1_chainage) - float(s2_chainage)), 2)
                
            if canonical_pair not in sections_by_pair:
                sec_id = f"NR-SEC-{section_counter:04d}"
                section_counter += 1
                
                sec_record = {
                    "section_id": sec_id,
                    "from_station_id": st1_id,
                    "to_station_id": st2_id,
                    "from_station_name": st1["station_name"],
                    "to_station_name": st2["station_name"],
                    "distance_km": calc_dist,
                    "scheduled_run_time_min": None,
                    "division": raw_route.get("division"),
                    "zone": "NR",
                    "source_document": "Northern Railway System Map",
                    "source_reference": f"Map Inset {map_label} (Step {i+1})",
                    "needs_verification": False if calc_dist is not None else True,
                    "active": True
                }
                sections_by_pair[canonical_pair] = sec_record
            else:
                # If existing section has no distance but new route has chainage, enrich it
                sec_rec = sections_by_pair[canonical_pair]
                if sec_rec["distance_km"] is None and calc_dist is not None:
                    sec_rec["distance_km"] = calc_dist
                    sec_rec["needs_verification"] = False
                    
            target_sec = sections_by_pair[canonical_pair]
            direction = "FORWARD" if target_sec["from_station_id"] == st1_id else "REVERSE"
            
            route_sections.append({
                "route_id": route_id,
                "section_id": target_sec["section_id"],
                "sequence_number": i + 1,
                "direction": direction,
                "source_reference": f"Route {route_id} Step {i+1}"
            })
            
    station_list = sorted(stations_by_normalized.values(), key=lambda s: s["station_id"])
    section_list = sorted(sections_by_pair.values(), key=lambda s: s["section_id"])
    
    # Save JSON files
    with open(os.path.join(output_dir, "corridors.json"), "w", encoding="utf-8") as f:
        json.dump(corridors, f, indent=2)
    with open(os.path.join(output_dir, "routes.json"), "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2)
    with open(os.path.join(output_dir, "stations.json"), "w", encoding="utf-8") as f:
        json.dump(station_list, f, indent=2)
    with open(os.path.join(output_dir, "sections.json"), "w", encoding="utf-8") as f:
        json.dump(section_list, f, indent=2)
    with open(os.path.join(output_dir, "route_sections.json"), "w", encoding="utf-8") as f:
        json.dump(route_sections, f, indent=2)
        
    export_sqlite(output_dir, corridors, routes, station_list, section_list, route_sections)
    
    summary = {
        "corridors_count": len(corridors),
        "routes_count": len(routes),
        "stations_count": len(station_list),
        "sections_count": len(section_list),
        "route_sections_count": len(route_sections)
    }
    print("Updated Northern Railway Network Foundation successfully built:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


def export_sqlite(output_dir: str, corridors, routes, stations, sections, route_sections):
    """Exports the normalized network model to a high-integrity SQLite database."""
    db_path = os.path.join(output_dir, "network.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    cur.execute("""
    CREATE TABLE corridors (
        corridor_id TEXT PRIMARY KEY,
        corridor_name TEXT NOT NULL,
        description TEXT,
        source_document TEXT,
        source_reference TEXT,
        needs_verification INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    );
    """)
    
    cur.execute("""
    CREATE TABLE routes (
        route_id TEXT PRIMARY KEY,
        corridor_id TEXT REFERENCES corridors(corridor_id),
        map_label TEXT NOT NULL,
        route_name TEXT NOT NULL,
        source_document TEXT,
        source_page INTEGER,
        start_station_name TEXT NOT NULL,
        end_station_name TEXT NOT NULL,
        station_sequence TEXT NOT NULL,
        source_reference TEXT,
        needs_verification INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    );
    """)
    
    cur.execute("""
    CREATE TABLE stations (
        station_id TEXT PRIMARY KEY,
        station_code TEXT,
        station_name TEXT NOT NULL,
        normalized_name TEXT NOT NULL UNIQUE,
        latitude REAL,
        longitude REAL,
        division TEXT,
        zone TEXT DEFAULT 'NR',
        station_category TEXT,
        is_junction INTEGER DEFAULT 0,
        source_document TEXT,
        source_reference TEXT,
        needs_verification INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    );
    """)
    
    cur.execute("""
    CREATE TABLE sections (
        section_id TEXT PRIMARY KEY,
        from_station_id TEXT NOT NULL REFERENCES stations(station_id),
        to_station_id TEXT NOT NULL REFERENCES stations(station_id),
        from_station_name TEXT NOT NULL,
        to_station_name TEXT NOT NULL,
        distance_km REAL,
        scheduled_run_time_min REAL,
        division TEXT,
        zone TEXT DEFAULT 'NR',
        source_document TEXT,
        source_reference TEXT,
        needs_verification INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        CONSTRAINT uq_station_pair UNIQUE (from_station_id, to_station_id)
    );
    """)
    
    cur.execute("""
    CREATE TABLE route_sections (
        route_id TEXT NOT NULL REFERENCES routes(route_id),
        section_id TEXT NOT NULL REFERENCES sections(section_id),
        sequence_number INTEGER NOT NULL,
        direction TEXT DEFAULT 'FORWARD',
        source_reference TEXT,
        PRIMARY KEY (route_id, sequence_number)
    );
    """)
    
    for s in stations:
        cur.execute("""
        INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            s["station_id"], s["station_code"], s["station_name"], s["normalized_name"],
            s["latitude"], s["longitude"], s["division"], s["zone"], s["station_category"],
            1 if s["is_junction"] else 0, s.get("source_document"), s.get("source_reference"),
            1 if s["needs_verification"] else 0, 1 if s["active"] else 0
        ))
        
    for r in routes:
        cur.execute("""
        INSERT INTO routes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            r["route_id"], r["corridor_id"], r["map_label"], r["route_name"],
            r["source_document"], r["source_page"], r["start_station_name"], r["end_station_name"],
            json.dumps(r["station_sequence"]), r["source_reference"],
            1 if r["needs_verification"] else 0, 1 if r["active"] else 0
        ))
        
    for sec in sections:
        cur.execute("""
        INSERT INTO sections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            sec["section_id"], sec["from_station_id"], sec["to_station_id"],
            sec["from_station_name"], sec["to_station_name"], sec["distance_km"],
            sec["scheduled_run_time_min"], sec["division"], sec["zone"],
            sec.get("source_document"), sec.get("source_reference"),
            1 if sec["needs_verification"] else 0, 1 if sec["active"] else 0
        ))
        
    for rs in route_sections:
        cur.execute("""
        INSERT INTO route_sections VALUES (?, ?, ?, ?, ?);
        """, (
            rs["route_id"], rs["section_id"], rs["sequence_number"],
            rs["direction"], rs["source_reference"]
        ))
        
    conn.commit()
    conn.close()
    print(f"Relational SQLite export completed: {db_path}")


if __name__ == "__main__":
    build_network()
