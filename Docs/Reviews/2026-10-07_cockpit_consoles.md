# Kokpit: konzole, křeslo, plyn – 7. 10. 2026

Otevřené body kritika z `2026-10-06_cockpit_critic.md` (holé horní plochy konzolí, oranžová lišta za holo MFD,
popruhy křesla). Autor 7. 10.: kopírujeme úroveň SC, ne rozměry. Práh `step`. Generátory `Tools/Blender/hs_interior.py`
(`obj_console`), `Tools/Blender/hs_cockpit.py` (`console_head`, `hazard_band`, `control_module`, `pilot_seat_v3`,
`hotas_throttle`); materiály `Wayfarer_hs.json` + `Wayfarer_setup.json`. Snímky `cockpit_audit` (nové záběry 09/10
hlavy konzolí) a `mfd_pages`.

## Co se změnilo

- **Konzole:** horní deska a kryty modulů v novém středně šedém saténovém kovu `int_housing` (dřív téměř černá);
  tělo v teplém grafitu místo trim pruhu kitu (ten se ze sedadla četl jako zmačkaná fólie). Hlava konzole: jemná
  perforovaná mřížka reproduktoru (24 × 14 otvorů), velké červené nouzové tlačítko na vlastním soklíku pod
  sklopeným červeným krytem s panty, štítek EMERG O2 / ALARM, oranžové šrafy na čele. Vedle HOTAS banka 2 × 2
  kolébek s popisky (PWR, ENG, EXT LT, BATT / SHLD, COOL, WPN, SYSTEMS).
- **Světlo:** lišta na čele konzolí jako difuzor v tmavém žlábku se saténovými lemy (`int_glow_soft`, 2,6 místo 8);
  oranžový pás u parapetu zúžen z 8,6 cm na 1,4cm linku v kanálku.
- **Křeslo:** popruhy 6 mm se zkosenými hranami, vyhlazené po dráze, se světlým prošitím; přezky jako kovové rámečky
  s příčkou; středové pole sedáku a opěradla z perforované kůže (`int_leather_perf`, normála perforace kitu);
  boční valy s dvojitým prošitím; saténová lišta se šrouby po stranách skořepiny; kůže matná (0,7).
- **Plyn:** prstové žebrování, opěrka dlaně, saténový pás pod víčkem, červené tlačítko s lícnicemi, kolébka na boku.
- **Satén `int_trim`:** drsnost 0,42 (mimo rozsah trasovaných odrazů interiéru) a jemný grunge.

## Kolo 1 – FAIL 5,75

Skóre: silueta 6, hierarchie 5, materiály 6, decaly 5, světlo 5, čitelnost 7, geometrie 6, styl 6.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | List 4 neukazuje hlavu konzole (musí) | Opraveno: nové záběry `09_left_console_head`, `10_right_console_head`. |
| 2 | Prázdné horní desky (musí) | Opraveno: banka kolébek vedle HOTAS, větší hlava konzole. |
| 3 | Mřížka a tlačítko malé, kryt zakrývá (musí) | Opraveno: hlava 22 × 30 cm, tlačítko ∅ 5 cm na soklíku, kryt sklopený dozadu. |
| 4 | Přepálené pásky na bocích (musí) | Opraveno: difuzor v žlábku, emise 2,6. |
| 5 | Křeslo bez detailu (musí) | Opraveno: perforace, prošití, lišty skořepiny. |
| 6 | Studený nádech (doporučeno) | Neopraveno: studiové světlo snímků (displeje, lišty); materiál těl je teplý grafit. |
| 7 | Plyn placeholder (doporučeno) | Opraveno v kole 2. |
| 8 | Málo decalů, bez opotřebení (doporučeno) | Částečně: štítky modulů; systémová vrstva opotřebení kokpitu je další krok. |
| 9 | Nečitelné popisky panelů (doporučeno) | Částečně: popisky nových modulů 0,5 místo 0,42. |
| 10 | Příčka rámu skla (doporučeno) | Neopraveno: tvar kanopy je schválený výkres (C-01). |

## Kolo 2 – FAIL 6,5 (dva body „musí“)

Skóre: 7 / 6 / 6 / 6 / 7 / 6 / 7 / 7.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Kryt tlačítka jen drátěný rámeček (musí) | Opraveno: plná červená deska krytu s lemem, hranou pro prst a panty. |
| 2 | Štítek „EMERG UZ“ nečitelný (musí) | Opraveno: horní okraj zakrýval lem soklíku – štítek níž, měřítko 1,0. |
| 3 | Hlavice plynu (doporučeno) | Opraveno: žebrování, opěrka dlaně, tlačítko, kolébka. |
| 4 | Prázdná čela konzolí (doporučeno) | Neopraveno: na čele jsou žebra, větrací mřížka a lišta; další krok. |
| 5 | Bez opotřebení (doporučeno) | Neopraveno (systémové, další krok). |
| 6 | Řídká mřížka (doporučeno) | Opraveno: 24 × 14 otvorů ∅ 2,6 mm. |
| 7 | Prázdné plochy desek (doporučeno) | Částečně. |
| 8 | Postroj bez logiky (doporučeno) | Neplatné: ramenní pásy vedou do centrální přezky pod záběrem (sedák mimo list). |
| 9 | Kolík u kniplu (doporučeno) | Neopraveno: je to páčka trimu kniplu (`hotas_stick`), drobnost. |
| 10 | Pohled pilota dolů (doporučeno) | Neopraveno: záběry z oka zůstávají; konzole jsou v `cockpit_audit`. |

## Kolo 3 – PASS 6,5

Skóre: silueta 7, hierarchie 6, materiály 6, decaly 6, světlo 6, čitelnost 7, geometrie 7, styl 7. Žádný bod „musí“.
Doporučení na další krok: drobná vrstva detailu na volných plochách hlavy konzole (šablony, čísla panelů), opotřebení
hran a špína ve spárách kokpitu, křeslo – popruhy jinou hodnotou, kovová kostra; lišta na čele ještě jasná; žlutý
štítek EMERG O2 proti oranžovým akcentům.

Finální snímky ze zabalené hry: `shots:20261007_101154_cockpit_audit`, `shots:20261007_101301_mfd_pages`.

## Vedlejší opravy

- `hs_decals.card_at`: buňka karty špíny překroucená na ostrém ohybu trupu (kořen křídla) měla zrcadlenou texturu,
  ač mířila po normále – `test_ship_geometry` shodil přestavbu (`mirrored_decals`); nově stejný test (T × B) · N.
- `test_kit_showroom`: materiál lodi smí mít `SurfaceDetail`, když ho setup zapíná (perforovaná kůže).
- `test_exterior_drawing`: rada k přegenerování rozvrhu kitu uvádí `--region` (výchozí je pilot, soubor je ship).
- Známé: náhodné decaly trupu jednou mezi dvěma přestavbami poskočily (`test_kit_decals`); další přestavba prošla.
- CI na GitHubu padalo od 6. 10. v `test_interior_drawing`: model četl sockety z FBX, v CI je to jen ukazatel LFS;
  nově z manifestu exportu (`interior_model`).
