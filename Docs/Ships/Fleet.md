# Flotila — přehled a plán

Centrální index všech lodí v gamespace. Každá loď má vlastní `Docs/Ships/Fleet.md#<jméno>`
záznam tady (rychlý přehled) a vlastní `ArtSource/Ships/<Jméno>/<Jméno>_spec.json` (plná
specifikace podle `Docs/Ships/ShipSpecification_System.md`).

**Důležité rozlišení dvou typů souborů u každé lodi:**
- **`<Jméno>_spec.json`** — design/identity list (role, rozměry, letové cíle, výzbroj) podle
  RSI Ship Matrix šablony. Vzniká **před** stavbou, řídí, co má loď dělat.
- **`<Jméno>_setup.json`** — skutečný funkční build config, co čte `import_ship.py`
  (`pawn`, `components`, `materials`, `decals`...). Vzniká **až při stavbě** v Blenderu/Unrealu,
  řídí, jak je loď skutečně postavená.

## Výrobci (lore)

Dva fiktivní výrobci pro začátek, ať mají lodě konzistentní identitu bez nutnosti vymýšlet
novou frakci pro každou loď:

- **Kestrel Dynamics** — vojenská/bojová technika. Rychlé, obratné, útočné/průzkumné lodě.
- **Halcyon Freightworks** — průmyslová/civilní technika. Nákladní, těžební, užitkové lodě.

## Přehled flotily

| Loď | Výrobce | Role | Velikost | Posádka | Stav |
| --- | --- | --- | --- | --- | --- |
| *nová malá loď* (jméno zatím není) | *(doplnit do specu)* | Multirole | Small | *(doplnit)* | 📐 2D návrh (nahrazuje první stíhačku, odstraněnou 24. 9. 2026) |
| **Steadfast** | Halcyon Freightworks | Multi-crew Freight/Exploration | Medium | 3 | 🔶 rozjeto (exteriér hrubý tvar z Meshy, koncept interiéru) |
| **Farsight** | Kestrel Dynamics | Long-range Scout/Exploration | Snub | 1 | 📋 naplánováno, nezačato |
| **Delver** | Halcyon Freightworks | Mining/Industrial Utility | Small–Medium | 2 | 📋 naplánováno, nezačato |

## Role a jak se doplňují

Čtyři lodě, čtyři jasně odlišené role — žádná náhodná duplicita:

- **Nová malá multirole loď** — malá a obratná, víc rolí včetně boje; přesné role, náklad a posádku
  určí 2D návrh a spec.
- **Steadfast** — pomalý, odolný, velký náklad, víc posádky. Základna pro delší výpravy.
- **Farsight** — rychlý jako malá stíhačka, ale stavěný na dolet/senzory místo boje. Slabě
  vyzbrojený nebo bezbranný, dlouhý dolet, jedna posádka. Vhodný pro objevování nových
  planet/POI, ne pro boj.
- **Delver** — pomalý jako Steadfast, ale menší a specializovaný na těžbu (těžební laser,
  tažný paprsek), ne na obecný náklad. Dvoučlenná posádka.

Tohle pokrývá čtyři základní herní činnosti (boj, doprava/výpravy, průzkum, těžba) — víc
lodí zatím neplánovat, dokud tyhle čtyři nebudou hotové a otestované. Držíme se zásady
"jeden systém, málo lodí, ale kvalitně", ne honit počet.

## Pořadí práce

1. 📐 Nová malá multirole loď — 2D návrh (první stíhačka byla 24. 9. 2026 odstraněna)
2. 🔶 Steadfast — v procesu (dokončit exteriér → interiér přes kitbash/procedurální detail)
3. Farsight — až po Steadfastu
4. Delver — poslední ze čtyř, protože těžba jako gameplay mechanika ještě není navržená
   (viz `Gamespace_ReferenceLibrary_Plan.md`, téma 4 "Ekonomika, obchod a těžba" — tohle
   téma referenční knihovny by mělo vzniknout dřív, než začneme stavět Delver, ať víme,
   jaké nástroje/mechaniky loď skutečně potřebuje)
