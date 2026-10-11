# MFD – rozbor stránek, FLIGHT klávesy (11. 10. 2026)

Zadání: autor 10. 10. „MFD kompletně analyzovat a vyladit“; pokračování po úpravě FLIGHT (commit bb52dc7c).

## Rozbor stránek (snímky `mfd_pages`, pohled z křesla)

- FLIGHT: 6 kláves ve 3 řádcích (34 px, mezera 5 px) – záře obrysu (4 px na stranu) je slepila, poslední řádek
  seděl na názvu stránky; G MAX narážel do BST. **Opraveno:** 2 řádky po 3 (128 × 38, mezery 20 px), klávesa režimu
  přes celou mřížku, sloupec G 150 px + 16 px odstup.
- THRUSTERS, NAVIGATION, CONFIG, STATUS, CONTACTS, SELF STATUS: bez přetečení a překryvu.
- Pohled přiblížení (Z) displeje ořízne, k rozboru se nehodí (náhradní preset zahozen).
- Pozn.: displej je 880 px široký (holo MFD v3), ne 560; skill opraven.

## Kritik (1 kolo, Opus, gate step) – PASS 6,9

Rozvržení 7 / čitelnost 7 / hierarchie 6,5 / konzistence 7; must-fix žádné.

| Výtka (should-fix) | Reakce |
| --- | --- |
| BOOST blízko „LIMIT 100%“ (~20 px) | odloženo do dalšího ladění MFD (posun mřížky o 12 px) |
| SCM širší než mřížka | ne: šířka = mřížka (3 × 128 + 2 × 20 = 424), rozšiřuje ji záře obrysu |
| popisky těsně v klávesách | odloženo; písmo 26 je minimum rozpočtu čitelnosti, řešení = širší klávesy |
| „4.6“ G přes oblouk prstence | starší stav, odloženo |
| název stránky dvakrát (záložka + spodní lišta) | záměr podle SC 4.x (holo MFD v3), všechny stránky stejně |

shots: `shots:20261011_170355_mfd_pages/` (zabalená hra), `flight_before_after.png`.
