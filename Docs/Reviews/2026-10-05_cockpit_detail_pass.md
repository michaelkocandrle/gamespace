# Kokpit a předměty na úroveň SC (5. 10. 2026, večerní blok)

Zadání autora: zvuky působí levně, motory mají mít vlastní přepínač, MFD jsou přepálené, kokpit je z plastových levných tvarů (křeslo, střední displeje, nápisy), hasicí přístroj je levný. Měřítkem je strop chodby.

## Hotové (commity)

| Commit | Co |
| --- | --- |
| `d7360739` | MFD lehčí (Saira Medium, slabší záře), neaktivní záložky čitelné, kamera o 9 cm dozadu, pryč nápisy FLIGHT / SYSTEMS / C21 / C22 |
| `53e098ad` | motory jako samostatný systém (U napájení, I motory, start 3 s), přepínač ENGINES na MFD CONFIGURATION, zvuky ElevenLabs Sound Effects 2 (napájení, holo, motory, přepínač) |
| `28a6911c` | křeslo v3 (skořepina U, prošívané polstrování, bočnice, pětibodový postroj, spona, konstrukce, plynová vzpěra, kolejnice), přepínač ENG s červenou krytkou na levé konzoli (klikací), pryč šablonové nápisy v kokpitu |
| `4a2e0ab7` | střední displeje RADAR / SELF STATUS jako holo obraz nad lištou emitoru |
| `6f8b6caf` | boční konzole: čalouněná opěrka předloktí, sokl, lem, žebra, žaluziová mřížka |
| (poslední) | hasicí přístroj: soustružená láhev s ramenem, ventil, manometr, pojistka s plombou, rukojeť a spoušť, hadice s tryskou v klipu, zadní deska se šrouby, kolébka, pásky se západkami |

Snímky (lokálně):
- `shots:20261005_183949_cockpit_audit`, `shots:20261005_191320_cockpit_audit` (kokpit);
- `shots:20261005_193019_extinguisher` (hasicí přístroj);
- `shots:20261005_182132_ship_power` (motory).

## Kritik

V tomto bloku jsem kritika nepouštěl, protože šlo o průběžné úpravy. Kolo kritika patří k předání holo MFD v3 a kokpitu jako celku.

## Zbývá (pořadí)

1. **Holo MFD:** stránky THRUSTERS / NAVIGATION / CONTACTS / SELF ve stylu SC, pruh kontrolek pravého MFD, barevný lem. Pak kritik.
2. **Dveře:** holografický dotykový panel vedle dveří (otevírá se v režimu interakce), detail křídla.
3. **Detail dalších předmětů a celé lodi na úroveň stropu chodby:**
   - skafandr;
   - podlaha a stěny kokpitu (deska nad nohama, zadní stěna);
   - kajuta, nákladový prostor.
4. **Rampa:** samostatný díl s pantem a animací (Pisces do 3 s, klid ~20°).
5. **Zvuky:** ElevenLabs zní realisticky, ale posoudit je musí autor. Případně přegenerovat (prompty v `ArtSource/Audio/ElevenLabs/README.md`).
