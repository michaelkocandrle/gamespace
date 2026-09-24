# Systém specifikace lodí — šablona podle RSI Ship Matrix

Standardizovaná struktura pro definici parametrů každé lodi v gamespace,
podle kategorií používaných oficiální Star Citizen Ship Matrix
(robertsspaceindustries.com/en/ship-matrix). Cíl: každá loď se definuje stejnou sadou kategorií, ať máme
konzistentní, srovnatelný a rozšiřitelný systém napříč celou flotilou.

Poznámka k IP: přebíráme obecnou STRUKTURU/KATEGORIE specifikace, ne
konkrétní jména lodí, přesné statistiky nebo popisy výrobců z RSI webu.

---

## 1. Identita lodi

| Pole | Popis | Stav u nás |
|---|---|---|
| **Model** | Jméno lodi (např. "Steadfast") | ✅ máme |
| **Manufacturer** | Výrobce/frakce v našem univerzu — zatím nemáme vlastní frakce definované, do budoucna | ⏳ budoucí |
| **Focus** | Role lodi (Interceptor, Freight, Exploration, Multi-role, atd.) | ⏳ zavést teď jako pole |
| **Description** | Krátký lore popis | ⏳ budoucí, kosmetické |
| **Production state** | Interní stav vývoje (placeholder / AI-generated / polished) — vlastní obdoba, ne z RSI | 💡 navrhuji zavést pro sledování stavu asset pipeline |

## 2. Fyzické rozměry

| Pole | Popis | Stav u nás |
|---|---|---|
| **Length / Beam / Height** | Rozměry v metrech | ✅ máme (manifest z exportu) |
| **Size** | Velikostní třída (Snub/Small/Medium/Large...) | ⏳ zavést jako kategorie, hlavně pro budoucí docking/hangár mechaniky |
| **Mass** | Hmotnost — ovlivňuje setrvačnost/manévrovatelnost | ⏳ zatím parametry letu (ThrustAcceleration atd.) řeší efekt hmotnosti nepřímo, formální pole zatím nemáme |
| **Cargo Capacity** | Nákladní prostor (SCU nebo vlastní jednotka) | ⏳ budoucí, až bude ekonomika/těžba |

## 3. Letový výkon — TOHLE UŽ MÁME ROZPRACOVANÉ

| Pole | Popis | Stav u nás |
|---|---|---|
| **SCM Speed** | Standardní bojová rychlost | ✅ máme (`<Loď>_setup.json`, SC-1a) |
| **Afterburner Speed** | Max. rychlost s afterburnerem | ✅ máme (SC-1b) |
| **Pitch/Yaw/Roll Max** | Max. úhlové rychlosti otáčení | ✅ máme (SC-1a rotace se setrvačností) |
| **X/Y/Z-Axis Acceleration** | Zrychlení v jednotlivých osách (hlavní tah, strafe, vertikální) | ✅ máme (samostatné zrychlení pro každý směr, SC-1a) |

**Poznámka:** náš `<Loď>_setup.json` už fakticky pokrývá celou tuhle
sekci. Pro novou loď stačí stejný soubor s jinými hodnotami.

## 4. Posádka

| Pole | Popis | Stav u nás |
|---|---|---|
| **Crew Size** | Počet členů posádky | ✅ implicitně 1 (jednomístná loď); pro multi-crew loď budoucí práce (víc sedadel, přepínání pozic) |

## 5. Avionika a senzory

| Pole | Popis | Stav u nás |
|---|---|---|
| **Avionics** | Obecné elektronické systémy | ⏳ budoucí |
| **Radar** | Detekční dosah/schopnosti | ⏳ budoucí (zmíněno v SC referenčním dokumentu jako SC-3+ téma) |
| **Computers** | Výpočetní kapacita (ovlivňuje kolik systémů běží najednou v SC) | ⏳ pravděpodobně nerelevantní pro náš rozsah, přeskočit |

## 6. Pohon

| Pole | Popis | Stav u nás |
|---|---|---|
| **Fuel Tanks** | Palivo pro hlavní pohon | ✅ máme koncept (afterburner má vlastní nádrž, SC-1b) |
| **Quantum Drives** | Pohon pro dálkové cestování | ⏳ budoucí (Quantum Travel je naplánovaný v `StarCitizen_FlightSystem_Reference.md`, zatím máme jen dočasný Cruise J jako náhradu) |
| **Jump Modules** | Meziseystémové skoky | ⏳ vzdálená budoucnost, nemáme víc systémů |
| **Quantum Fuel Tanks** | Palivo specificky pro QT drive | ⏳ budoucí, spolu s Quantum Travel |

## 7. Trysky

| Pole | Popis | Stav u nás |
|---|---|---|
| **Main Thrusters** | Hlavní pohon vpřed | ✅ máme |
| **Maneuvering Thrusters** | Manévrovací trysky (strafe/rotace/boost) | ✅ máme, včetně rozdílu Boost (manévrovací) vs Afterburner (hlavní), SC-1b |

## 8. Energetické systémy

| Pole | Popis | Stav u nás |
|---|---|---|
| **Power Plants** | Zdroj energie lodi | ⏳ budoucí — přímo odpovídá Power Triangle konceptu z letového referenčního dokumentu |
| **Coolers** | Chlazení (souvisí s HEAT systémem, co už máme u atmosférického vstupu!) | 🔶 částečně — máme HEAT při rychlém vstupu do atmosféry, ale ne jako spravovatelný systém s vlastním komponentem |
| **Shield Generators** | Štíty | ⏳ budoucí, závisí na bojovém systému |

## 9. Výzbroj

| Pole | Popis | Stav u nás |
|---|---|---|
| **Weapons** | Zbraně na pevných úchytech | ⏳ budoucí (plánováno jako téma 5 v referenční knihovně) |
| **Turrets** | Otočné věže (relevantní hlavně pro multi-crew lodě) | ⏳ budoucí |
| **Missiles** | Raketové zbraně | ⏳ budoucí |
| **Utility Items** | Ostatní vybavení (scanner, tractor beam, atd.) | ⏳ budoucí |

---

## Navrhovaná JSON struktura pro budoucí lodě

Na základě týhle šablony navrhuji rozšířit formát `*_setup.json` (co už
používáme pro lodě) o identity/rozměrové pole, zatímco letová
sekce zůstává v podstatě stejná jako teď:

```json
{
  "identity": {
    "model": "Example",
    "manufacturer": "",
    "focus": "Interceptor",
    "size_class": "Snub",
    "production_state": "ai_generated_v1"
  },
  "dimensions": {
    "length_m": 14.0,
    "beam_m": 11.4,
    "height_m": 6.2,
    "mass_kg": null,
    "cargo_capacity": 0
  },
  "flight": {
    "scm_speed_ms": 210,
    "afterburner_speed_ms": 420,
    "pitch_max_deg_s": 100,
    "yaw_max_deg_s": 75,
    "roll_max_deg_s": 150,
    "acceleration": {
      "main_ms2": 4000,
      "retro_ms2": null,
      "strafe_ms2": null,
      "vertical_ms2": null
    }
  },
  "crew": {
    "crew_size": 1
  },
  "propulsion": {
    "main_fuel_capacity": null,
    "afterburner_fuel_seconds": 8,
    "quantum_drive": null
  },
  "systems": {
    "power_plant": null,
    "cooler": null,
    "shield_generator": null
  },
  "weaponry": {
    "weapons": [],
    "turrets": [],
    "missiles": [],
    "utility_items": []
  }
}
```

Pole s `null` jsou budoucí — necháváme je ve struktuře přítomné, ať je
jasné, kam bude časem přibývat data, ale nevyplňujeme je, dokud
nebudeme mít odpovídající systém implementovaný (zbraně, štíty,
quantum travel, atd.).

## Doporučení pro Claude Code prompty

Až budeme zadávat novou loď (nebo rozšiřovat existující), odkazovat na
tenhle dokument a žádat, aby nové `*_setup.json` soubory následovaly
tuhle strukturu — i pro pole, která zatím nejsou funkční (necháme je
jako `null`/prázdná pro budoucí rozšíření, ne úplně vynechaná).
