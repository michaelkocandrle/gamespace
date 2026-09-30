# Recenze: exteriér Wayfareru, výchozí stav (30. 9. 2026)

Zadání autora: exteriér Wayfareru ještě nikdy nehodnotil kritik a od přechodu do interiéru se na něj nikdo pořádně
nepodíval. Připravit srovnávací listy (zblízka, chase kamera, zdálky; den, soumrak, vesmír) proti referencím SC,
spustit kritika s laťkou hotové lodi (`"gate": "ship"`). **Nic neopravovat**, jen výchozí skóre a seznam problémů
seřazený podle dopadu. Jedno kolo, bez oprav a bez dalších kol.

## Podklady

- Snímky: `.\Tools\Shots.ps1 -Preset wayfarer_exterior_review -Editor -Width 1920 -Height 1080`, sada
  `Saved/Shots/20260930_232344_wayfarer_exterior_review` (31 snímků, mimo git; listy je obsahují).
- Světlo: den = slunce levelu `space.SunDir -39 45` ve 3 km; soumrak `-52 102` (nízké slunce za lodí vpravo vzadu);
  vesmír 60 km nad Veyrou, nejdřív `-52 85` (protisvětlo), pak slunce levelu. Hledání soumraku a strany na slunci ve
  vesmíru stálo tři zkušební běhy (WORKFLOW 9.2 ex).
- Reference: záběry ze hry SC z lokálních videí (`ArtSource/Reference/Video/sc_pyro_planets`, `sc_engineering_repair`,
  `sc_quantum_travel_tutorial`, `markom_sc_models_look`), obrázky Ship Matrix (`starcitizenreference/ship_matrix/
  small_multirole`) a schválený výkres `ArtSource/Ships/Wayfarer/Design/Wayfarer_exterior.png`.
- Listy a brief: [2026-09-30_wayfarer_exterior/round1](2026-09-30_wayfarer_exterior/round1/brief.md) (22 listů),
  zadání `review_round1.json`, doklady v [evidence](2026-09-30_wayfarer_exterior/evidence/).
- Kritik: agent `general-purpose`, model `fable`, zadání `.claude/agents/visual-critic.md` (typ `visual-critic`
  v session chyběl).

## Kolo 1: výstup kritika

# Verdikt: FAIL

První dojem: Hladká bílá „vlaková“ trubka s nalepenými pruhy, plechově tenkými křídly a dvěma přerostlými ploutvemi –
čistá, ale bez hmoty, mechaniky a světel, které dělají loď ze SC.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 6 | Rozvržení z výkresu sedí (list 1), ale ploutve jsou 2–3× větší než „malá ploutev“ z výkresu, křídla jsou plechy bez tloušťky, podvozkové patky a trysky jsou hrubé bloky. |
| Hierarchie a hustota detailu | 4 | Existuje jen velká vrstva (trup, kabina, gondoly, ploutve); střední vrstva (desky nad rámem, zapuštěné poklopy, mechanika, trubky) chybí a malá vrstva jsou dvě krabičky a bledé nápisy. |
| Materiály | 5 | Dva laky (lesklá bílá, satén tmavá) + oranžová; žádný holý kov, guma ani tmavá mechanika, žádná variace drsnosti, opotřebení jako měkké šmouhy uprostřed panelů místo hran. |
| Decaly | 3 | Nápis WAYFARER je na pravoboku zrcadlený, šablonové značky jsou tak bledé, že nejsou čitelné, nic není shlukované, nýty a čísla panelů prakticky chybí. |
| Světlo | 4 | Trysky za letu nesvítí vůbec a s přídavným tahem jen dvě tečky, poziční světla jsou přepálené barevné skvrny, v protisvětle ve vesmíru loď nemá žádné obrysové světlo. |
| Čitelnost (text, displeje, HUD) | 4 | Jméno čitelné jen z levoboku, z pravoboku zrcadlené; HALCYON FREIGHTWORKS na ploutvi a servisní značky na trupu jsou příliš malé a málo kontrastní. |
| Chyby geometrie | 4 | Zrcadlený decal, roztažená textura na křídle, zbraně jako holé trubky, podvozkové patky a trysky jako placeholdery, panelové čáry se kříží v nahodilých úhlech. |
| Soulad stylu mezi díly | 5 | Trup (bílý, tenké čáry) vs. křídla (holé tmavé plechy s jiným rastrem), záď (krémová) vs. bok (neutrálně bílý), trysky béžové – každý díl má jiný jazyk. |

Průměr: 4,4 (práh: hotová loď – všechny kategorie aspoň 7 a žádný bod „musí se opravit“)

### Rozdíly proti referenci (zkráceně; plné znění s místy na listech: [round1/critic.md](2026-09-30_wayfarer_exterior/round1/critic.md))

1. Zrcadlený nápis WAYFARER na pravoboku – musí se opravit.
2. Trysky bez hloubky a bez záře (béžová miska s kuželem, za letu nesvítí, s přídavným tahem dvě tečky) – musí se
   opravit.
3. Ploutve násobně větší než na výkresu – musí se opravit.
4. Křídla jsou plechy bez tloušťky a bez nádrží – musí se opravit.
5. Zbraně S3 jako holé trubky – musí se opravit.
6. Detail trupu jsou čáry na hladkém povrchu, spáry se kříží v nahodilých úhlech, chybí střední vrstva – musí se
   opravit.
7. Přepálená poziční světla (ve dne barevné skvrny na křídle) – musí se opravit.
8. Podvozek jako placeholder (bílá krabice, černý kvádr s lištami, bez šachty a dveří) – musí se opravit.
9. Záď: plochá přepážka bez rámu rampy, pantů, pístů a zadních světel – musí se opravit.
10. Roztažená textura na křídle – doporučeno.
11. Šablonové nápisy nečitelné a rozházené – doporučeno.
12. Materiály bez variace drsnosti a bez hranového opotřebení, žádný holý kov ani guma – doporučeno.
13. Čelo gondoly je plochý kryt s lampou – doporučeno.
14. V protisvětle loď nemá obrysová světla – doporučeno.
15. Bílý pás pod spodní hranou trupu vypadá jako artefakt – doporučeno.
16. Oranžově svítící šachta v gondole působí jako pec – doporučeno.
17. Trup čte jako vagon (pravidelné příčné prstence) – doporučeno.
18. Dva různé odstíny bílé – doporučeno.
19. Výchozí chase kamera příliš blízko – doporučeno.

Checklist podle kritika: vrstvený tvar se střední vrstvou ne, detail jako tvar nebo decal s hloubkou ne, materiály jen
dva laky a oranžová, decaly zrcadlené a bledé, světla přepálená a trysky tmavé, silueta podle výkresu jen v rozvržení.

## Reakce na body (ověřeno na snímcích v plném rozlišení; nic se neopravuje)

| Bod | Platí? | Poznámka |
|---|---|---|
| 1 zrcadlený nápis | **ano, a víc** | Vpravo je zrcadlené i `HF-0417`, ne jen WAYFARER (kritik psal opak): [r1_p01](2026-09-30_wayfarer_exterior/evidence/r1_p01_starboard_both_mirrored.jpg). Nejsou to mesh decaly z hs (ty hlídá `test_ship_geometry.py`), ale promítané decaly UE `Name_R` a `Reg_R` ve `Wayfarer_setup.json` (rotace `0, 90, -90`, `flip_u 1`); žádný test je nekontroluje. |
| 2 trysky | ano | Recept `NozzleGlow` je plochý svítící disk na dně šachty; snímek 24 s přídavným tahem: jen světlé disky, žádný plamen. |
| 3 ploutve | **ne vůči výkresu** | Ploutev je 2,0 m vysoká a 0,7 m nad hřbetem přesně podle výkresu (recept x 0,2–3,7, z 2,0–4,05): [r1_p03](2026-09-30_wayfarer_exterior/evidence/r1_p03_fin_per_drawing.jpg). Kritik špatně odečetl zmenšený výkres. Že působí velká a tmavá, je otázka návrhu, ne odchylka. |
| 4 křídla | zčásti | Tloušťka 0,4 m je podle výkresu a nádrže jsou uvnitř křídla (bez vyboulení). Platí, že shora je křídlo plochá deska se dvěma obdélníky bez hloubky a bez náběžné hrany. |
| 5 zbraně | ano | Recept `Guns`: tři válce (tělo r 0,18 m, hlaveň r 0,055 m, ústí). |
| 6 detail trupu | ano | Spáry jsou pásy `panel_lines` bez znatelné hloubky; ve dne vypadají jako kresba. Hlavní systémový problém. |
| 7 poziční světla | ano | Snímky 06, 07, 15: červená a zelená skvrna na křídle i ve dne. |
| 8 podvozek | ano | Snímek 08: krabicová noha, deska s lištami, bez šachty a dveří. |
| 9 záď | ano | Snímek 09: rovná stěna, rampa bez rámu a pantů, bez zadních světel. |
| 10 textura křídla | ano | Snímek 06: vodorovné šmouhy v pravém horním poli křídla. |
| 11 šablony | ano | Šedé nápisy na bílé (NO STEP, B07) jsou ve 1080p na hranici čitelnosti. |
| 12 materiály | ano | Jeden bílý lak bez variace drsnosti, opotřebení na plochách místo hran. |
| 13 čelo gondoly | ano | Hladký kryt s lampou. |
| 14 obrysová světla | ano | Snímky 18 a 20: v protisvětle svítí jen kabina. |
| 15 bílý pás | ano | Světelné lišty trupu (`LightStrip`) ve dne čtou jako šum nebo škrábance. |
| 16 šachta gondoly | ano | Servisní šachta svítí oranžově i ve dne. |
| 17 vagon | ano | Pravidelné prstence po celé délce; řeší se spolu s bodem 6. |
| 18 dva odstíny bílé | neprokázáno | Ve stejném snímku (09) mají záď a boky stejný odstín; béžové jsou jen svítící disky trysek (bod 2). |
| 19 chase kamera | ano, mimo mesh | Výchozí vzdálenost chase kamery; prezentace lodi, ne model. |

**Co kritik nezmínil (vlastní kontrola snímků):**

- Přistání na svahu (snímek 11): trup přistálé lodi leží v terénu, podvozek není vidět. Je to přistávání na nerovném
  terénu (herní logika, CURRENT: loď stojí na kořenovém boxu), ne model exteriéru.
- Denní světlo levelu je ploché: slunce `-39 45` dává jen měkké stíny, trup nemá odlesky ani tvrdý stín jako
  reference. Ubírá materiálům na všech denních listech; je to nastavení scény, ne lodi.

## Seznam podle dopadu (pro rozhodnutí autora)

Pořadí podle toho, jak moc problém ovlivňuje dojem z lodi; cena je hrubý odhad práce.

| # | Problém (body kritika) | Kde je vidět | Cena |
|---|---|---|---|
| 1 | Chybí střední vrstva detailu: spáry jako kresba, žádné desky nad rámem, zapuštěné poklopy, trubky; trup jako vagon (6, 17) | každý pohled | velká (návrh rozvržení panelů + hs recept) |
| 2 | Zrcadlené nápisy WAYFARER a HF-0417 na pravoboku (1) | celý pravobok | malá (`Name_R`, `Reg_R` ve `Wayfarer_setup.json` + test) |
| 3 | Trysky: plochý béžový disk, žádná hloubka ani plamen (2) | chase kamera zezadu, pořád | střední (geometrie trysky + emise podle tahu + VFX) |
| 4 | Materiály: jeden lak bez variace drsnosti, opotřebení mimo hrany, chybí holý kov a guma (12) | všechny pohledy zblízka | střední (maska hran, drsnost, materiálové zóny) |
| 5 | Světla lodi: přepálená poziční světla, chybí obrysová a strobe, lišty ve dne jako šum, šachta jako pec (7, 14, 15, 16) | den i noc | malá až střední |
| 6 | Záď a rampa bez rámu, pantů, pístů a světel (9) | při každém vstupu do lodi | střední |
| 7 | Podvozek jako placeholder (8) | přistálá loď, pěšky | střední |
| 8 | Křídla shora ploché desky, šmouhy textury (4, 10) | chase kamera, shora | střední |
| 9 | Zbraně jako holé válce (5) | chase kamera, zblízka | malá až střední |
| 10 | Šablonové nápisy bledé a rozházené (11) | zblízka | malá |
| 11 | Čelo gondoly bez sání a struktury (13) | zepředu | malá |
| 12 | Chase kamera blízko (19) | výchozí pohled | malá (parametr kamery) |
| 13 | Mimo model lodi: trup v terénu při přistání na svahu; ploché denní světlo levelu | přistání, den | podle rozsahu |

Neplatné nebo neprokázané: ploutve (bod 3, jsou podle výkresu), dva odstíny bílé (bod 18).

Řádky 1, 4 a 5 jsou systémové (skill `visual-review`: hierarchii detailu, materiály a světlo drží systémové věci, ne
lokální opravy). Řádky 2, 10 a 12 jsou levné a dají se udělat bez dalšího kola kritika.
