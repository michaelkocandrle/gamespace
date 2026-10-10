# Wayfarer – exteriér r3 (techniky SC z rozboru), 10. 10. 2026

Práh `ship` (všechny kategorie aspoň 7). Kritik Opus 5.5, 3 kola. Listy:
`2026-10-10_wayfarer_exterior_r3/` (kolo 1), `…_r3_k2/` (kolo 2), `…_r3_k3/` (kolo 3); zadání `*.json` vedle.

Krok: techniky 1, 3–12 z `ArtSource/Reference/Video/sc_ext_notes/SC_exterior_techniques.md` (lem křídel, zaoblení,
odstupňované plechy, zapuštěné pásy, rám trysek, tepelné mřížky, zbraně, podvozek, značení, hex povlak), oprava směru
tětivy křídel, Lumen ShortRangeAO 0.

## Skóre

| Kategorie | K1 | K2 | K3 |
|---|---|---|---|
| Silueta a tvar | 8 | 7 | 7 |
| Hierarchie a hustota detailu | 6 | 6 | 6 |
| Materiály | 6 | 5 | 5 |
| Decaly | 6 | 6 | 6 |
| Světlo | 6 | 6 | 6 |
| Čitelnost | 7 | 7 | 7 |
| Chyby geometrie | 6 | 5 | 6 |
| Soulad stylu | 7 | 6 | 7 |
| **Průměr** | **6,5** | **6,0** | **6,25** |

Minulá recenze (9. 10., r2): 5,9. Verdikt po 3 kolech **FAIL**, předáno s otevřenými body.

## Reakce – kolo 1

1. Zrcadlený NO STEP na pravém křídle – **neplatné jako zrcadlení** (výřez ze snímku 15: písmena vzhůru nohama v
   obráceném pořadí = otočení o 180°), přesto srovnáno: `rot_mirror` v `hs_decals` (kolo 2).
2. Šmouhy na laku – **opraveno**: karty špíny `decals.grime` vypnuté (autor 8. 10.: nové díly), Accent bez opotřebení.
3. Podvozek kvádr – **částečně**: hadice, manžeta kotníku, výstražný pruh (kolo 1), gumový lem, žebra, oka a druhý
   aktuátor (kolo 2); kritik stále chce kloubovou nohu s rameny (otevřené).
4. Trysky bez žáru při tahu – **neplatné**: na snímku 24 jsou jádra oranžová; plamen za tryskou hra nemá (efekty, mimo krok).
5. Přepálený pás – **opraveno**: emise 1,2, jádro 3 cm v drážce 1,5 cm.
6. Plochá křídla – **opraveno částečně**: poklopy, šrouby, šablona (decaly), 3 vystouplé desky na křídlo (geometrie).
7. Černý otvor u přídě – **opraveno**: senzor G-SN-01 na desce (`on_plate`), prázdný výřez pryč.
8.–13. Doporučené: hex příliš velký (buňka je 17 cm, ne 30–40 cm; ponecháno), vzpěra ploutve, drobné šablony, poziční
   světla zdálky, satén laku – **neopraveno** (zapsáno níže).

## Reakce – kolo 2

1. Zrcadlený nápis – viz výše (otočení), srovnáno.
2. Hřbet jako odhalená kostra v protisvětle – **artefakt snímků**: po skoku do 60 km chyběl hlavní mesh trupu na všech
   stojících vesmírných snímcích, dokud se loď nepohnula; recenzní sada má zahřívací let (`space_warmup`), kolo 3 už
   trup celý.
3. Podvozek – viz výše. 4. Střední vrstva – desky na křídle (geometrie). 5. Pás – užší jádro, hlubší drážka.
6.–11. Doporučené – neopraveno.

## Kolo 3 – otevřené body

- **Musí se opravit (otevřené):** (1) střední vrstva skutečné geometrie na velkých plochách boku, zádě a křídla (2–3
  prvky na plochu > 1,5 m²); (2) variace drsnosti po panelech, světlejší gunmetal s kovovým odleskem, čitelnější hex;
  (3) přistálá loď na svahu (známý problém – snímek 11 chce rovné místo, `space.FlatSpot`); (4) podvozek jako kloubová
  noha (ramena, chromová pístnice, štítek).
- **Doporučené:** segmentace pásů po spárách, shluky malých šablon u poklopů a menší NO STEP (8–10 cm), vnitřek
  trysek (lopatky, tepelně zbarvené hrdlo), nekotvený oranžový díl u L14, tmavá příď světlejší.
- **Podklady:** reference SC na listech jsou z velké části jeden záběr Aurory; pro další kolo doplnit cílené záběry
  autora (chase, soumrak, vesmír, trysky, podvozek).

## Po kole 3 (bez nového kola kritika)

- Bod 2 (materiál): lak satén – čirý lak 0,5 / 0,12 s variací 0,3 mezi panely (byl 1,0 / 0,05, „plast“), tmavá
  livrej 0,09 (byla 0,05), kavita detailní textury 0,25 (rytá mřížka působila nakresleně). Snímky
  `shots:20261010_212123_wayfarer_ext_step`.
