# Recenze: interiérový kit, krok „materiál kitu“ (27. 9. 2026)

Zadání autora (po schválení dávky 3): před dávkou 4 krok „materiál kitu“:
- variace drsnosti;
- broušený kov na konstrukci;
- gumová těsnění;
- špína ve spárách a u soklu;
- jemné mikroškrábance;
- lehký oděr na madlech a u podlahy;
- varianty podlahových desek.

Přepočítat díly dávek 1–3 a změřit jas i výkon před a po.

Kritik: podagent se zadáním `visual-critic` (Fable 5.1), preset snímků `kit_material` (stejné pohledy před a po), listy
v `round1/`–`round3/`.

## Co se změnilo

**Master `M_Ship_Layered`:** nový statický přepínač `SurfaceDetail`. Lodě ho mají vypnutý, kit zapnutý, hlídá to
`test_kit_showroom.py`.
- mikrotextura `T_Ship_Micro` (`generate_detail_textures.py`: broušení, mikroškrábance, jemný šum drsnosti) na UV0 v metrech;
- detailní normála;
- variace grunge a špíny po deskách (`PanelShift`, `PanelDirtVar`);
- oděr hran u podlahy (`FloorWear`) a ploch nahoru (`TopWear`, madla).

**Geometrie kitu (`kit_geo`):**
- čelní plocha každého panelu primárního laku a konstrukce (≥ 15 cm) má vnitřní lem 4 cm;
- obvod a boky panelu nesou okluzi 0,35, master tam dává prach;
- okluze klesá k podlaze jen na svislých plochách, s pásem u soklu;
- UV0 vede podél prvku (krabice, hranoly, trubky), takže broušení jde podél nosníku a sloupku.

**Materiály (`import_kit.build_materials`, `SURFACE`):**
- lak: variace lesku, mikroškrábance, oděr zkosení, šedý prach ve spárách a u soklu;
- konstrukce: broušený kov (dlaždice 15 cm), ×0,75 palety, kov 0,5;
- oranžová: práškový lak s oděrem nahoře;
- guma: vrstvená s prachem místo ploché černé.

**Díly:**
- těsnění poklopu 8 mm;
- gumové lůžko mřížky;
- gumové průchodky trubky a vzduchovodu v portálu C.

**Světla kitu:** ×2,0 místo ×1,8, protože kovovější konstrukce a prach srazily jas chodby z 0,19 na 0,16 (cíl autora: střed rozsahu SC). Emise difuzorů svítidel (`Kit_GlowWarm`) 7 → 3,5.

## Měření (1920×1080, RTX 2060, výchozí kvalita hry: epická, GI vysoká, TSR 75 %)

| | Chodba jas | Křižovatka jas | Portál B jas | Chodba GPU / snímek | Křižovatka GPU / snímek | Hala GPU / snímek |
|---|---|---|---|---|---|---|
| Před (`20260927_193629_kit_material`) | 0,20 | 0,19 | 0,12 | 15,9 / 16,6 ms | 15,4 / 16,0 ms | 13,0 / 14,3 ms |
| Kolo 1 (`20260927_200039`) | 0,19 | 0,18 | 0,12 | 15,6 / 16,3 ms | 14,6 / 15,2 ms | 12,6 / 13,4 ms |
| Kolo 3, světla ×2,0 (`20260927_205537`) | 0,18 | 0,18 | 0,11 | 16,0 / 16,8 ms | 15,0 / 15,8 ms | 13,1 / 14,3 ms |
| Po ověřovacích opravách (`20260928_003957`) | 0,20 | 0,20 | 0,13 | 16,2 / 16,9 ms | 15,5 / 16,4 ms | 13,0 / 14,1 ms |

- B/R 0,72–0,74 (teplé) ve všech kolech.
- Výkon se krokem nezměnil (rozdíly do 0,3 ms jsou šum běhů), mikrovrstva čte jeden vzorek textury (UV0).
- **Pozor:** kolo 2 a první snímky kola 3 vznikly ve střední kvalitě. Grafiku na „střední“ přepnul autor v menu hry 27. 9. ve 20:09 a snímky tehdy braly jeho nastavení (GPU 10,2–10,7 ms, VRAM 2,24 GB, v tabulce proto nejsou). Kritik v kole 2 hodnotil snímky ve střední kvalitě. `Shots.ps1` teď na dobu snímků nastaví výchozí kvalitu a autorův soubor pak vrátí (WORKFLOW dj).

## Kolo 1 – FAIL, 7/5/4/5/5/6/6/5 = 43

Výstup: [round1/critic.md](2026-09-27_kit_material/round1/critic.md), snímky `Saved/Shots/20260927_200039_kit_material`.

1. **Broušený kov přepálený do bíla (musí) – opraveno.** Konstrukce ×0,8 → ×0,62, kov 0,5 → 0,6 (v kole 3 ×0,72 / 0,7, viz kolo 2 bod 3).
2. **Bez variace drsnosti a škrábanců (musí) – opraveno.**
   - Lak: grunge 80 cm s rozptylem drsnosti 0,4, mikrošum 0,18, škrábance 0,15.
   - Oděr zkosení: práh 0,35, síla 0,5.
3. **Špína ve spárách a u soklu (musí) – opraveno zčásti.**
   - Špína laku 0,55 → 0,9.
   - Nový záběr `c_plinth_close` se soklem.
   - V kole 2 pořád neviditelná (tmavá na tmavém), v kole 3 šedý prach.
4. **Gumová těsnění (musí) – opraveno.**
   - Poklop: těsnění 8 mm (víko staženo o 4 mm).
   - Mřížka: gumové lůžko na vnitřním okraji rámu.
   - Portál C: gumové průchodky trubky a vzduchovodu.
5. **Mřížka nad černou prázdnotou (musí) – neopraveno, rozhodnutí autora.** Autor 27. 9.: světlo kanálu ztlumit, čitelnost kanálu se doladí při stavbě lodi. Obsah kanálu je (dvě trubky, kabely: `Docs/Reviews/2026-09-27_kit_batch3/evidence/r3_01_channel_contents.jpg`).
6. **Madla bez oděru (musí) – opraveno.** `TopWear` 0,8 → 1,0, nižší práh, oranžová ×0,7, drsnost 0,45.
7. **Tři různé oranžové (doporučeno) – neplatné.** Pruh na stěně (`kit_walls`), madlo poklopu, zábradlí i středová čára jsou jedna instance `MI_Kit_Halcyon_Signal`. Rozdíl dělá světlo a nově oděr.
8. **Protiskluz jako rohož (doporučeno) – neopraveno, rozhodnutí autora.** Protiskluz zůstává (autor 27. 9.).
9. **Světlo bez stínů (doporučeno) – mimo rozsah.** Světla dávek 1–2 jsou schválená.
10. **Nášlapy jiný materiál (doporučeno) – neplatné.** Nášlapy i plošina jsou `Kit_Primary` (sekundární tón). Rozdíl dělá neutrální světlo hran schodů, které si autor vyžádal.
11. **Nečitelný displej (doporučeno) – mimo rozsah.** Obsah displejů a značení patří do dávky 6.
12. **Chybí vrstva pod stropem (doporučeno) – mimo rozsah.** Strop je z dávky 2.

## Kolo 2 – FAIL, 7/5/4/5/6/7/6/6 = 46

Výstup: [round2/critic.md](2026-09-27_kit_material/round2/critic.md), snímky `Saved/Shots/20260927_201846_kit_material`.

1. **Špína ve spárách a u soklu chybí (musí) – opraveno jinak.** Tmavá špína (0,05) na tmavém laku (0,07–0,10) nemá kontrast. Lak dostal šedý prach (0,13 / 0,12 / 0,105), který na grafitu čitelný je.
2. **Broušení v centimetrovém měřítku a na lakovaných dílech (musí) – opraveno.**
   - Pruhy byly na rohovém sloupku (konstrukce, hranol). Ten ještě používal starou projekci, proto na svislém prvku vodorovně.
   - Hranoly a lofty mají teď UV podél nejdelší osy.
   - Broušení konstrukce na dlaždici 15 cm místo 60 cm, síla 0,7.
   - Lakované panely broušení nemají (`Brushed` 0).
3. **Konstrukce se neliší od panelů (musí) – opraveno.**
   - Konstrukce ×0,72, kov 0,7, drsnost 0,5: světlejší a kovová.
   - Lak drsnost 0,42: lesklejší tmavý grafit.
   - Rozdíl 2 EV, jak chtěl kritik, by vrátil přepal z kola 1.
4. **Guma nikde vidět (musí) – opraveno zčásti.** Guma tmavě šedá (0,05, drsnost 0,75) místo téměř černé, aby se odlišila od spáry. Gumové úchopy madel nepřidávám, ruce jdou přímo na lakovanou trubku.
5. **Oděr madel a nášlapů (musí) – opraveno zčásti.**
   - Madla: jemnější grunge (30 cm), oděr každých pár decimetrů, práškový lak 0,5.
   - Nášlapy: protiskluz je trim, který autor nechal beze změny.
6. **Přepálená svítidla (doporučeno) – mimo rozsah.** Emise svítidel se ladila v dávce 2 (7 místo 14) a je schválená.
7. **Mřížka nad prázdnotou (doporučeno) – neopraveno.** Rozhodnutí autora, viz kolo 1 bod 5.
8. **Výstražné pruhy nové (doporučeno) – neopraveno.** Opotřebení decalů patří do dávky 6 (značení).
9. **Volné světlé tečky (doporučeno) – neplatné.** Jsou to šestihranné hlavy šroubů v rozích desek: [evidence/r2_09_dots_are_corner_bolts.jpg](2026-09-27_kit_material/evidence/r2_09_dots_are_corner_bolts.jpg).
10. **Deska B, hřebeny a protiskluz (doporučeno) – neopraveno.** Protiskluz beze změny (autor). Středová čára má oděr (`TopWear`).
11. **Monotónní celek (doporučeno) – zčásti.** Konstrukce se teď odlišuje od panelů. Akcentové bloky jsou věc skladby lodi.

## Kolo 3 – FAIL, 7/5/4/5/5/6/7/6 = 45 (poslední počítané)

Výstup: [round3/critic.md](2026-09-27_kit_material/round3/critic.md), snímky `Saved/Shots/20260927_205537_kit_material` (výchozí kvalita).

1. **Panely jednolitý lak bez variace (musí) – neopraveno, otevřený bod.**
   - Variace lesku je (grunge 80 cm, drsnost ±0,2), stejně tak škrábance a oděr zkosení. Na listu z 1,6 m se nečtou.
   - Když se variace zesílí, čte se jako skvrny uprostřed desek (ověření, bod 3).
2. **Přepálená svítidla (musí) – opraveno zčásti, ověřeno zčásti.**
   - Emise difuzorů `Kit_GlowWarm` 7 → 3,5 (světla samotná beze změny): lamely jsou čitelné.
   - Jádro je dál bílé a svítidla nemají rámeček. Rámeček je geometrie dávky 2.
3. **Špína uprostřed desek, ne ve spárách (musí) – nevyřešeno (ověření).**
   - Grunge v ploše 0,3 → 0,15, prach v lemu silnější (okluze 0,2, prach 0,15).
   - Lem z barev vrcholů dává jen jemný světlejší okraj desky.
   - Systémové řešení: pruhy špíny jako mesh decaly podél spár a soklu (karty špíny z `hs_decals` Wayfareru).
4. **Portál: chybí broušený kov, svorky, guma (musí) – zčásti.**
   - Trubka a trámy jsou konstrukce s broušením (dlaždice 15 cm), příruby se šrouby i gumové průchodky (kolo 2) na portálu jsou.
   - Ze střední vzdálenosti se to nečte.
5. **Konstrukce stejný tón jako panely (musí) – opraveno zčásti, ověřeno zčásti.**
   - Konstrukce ×0,75, kov 0,5 (difuzní jas asi 2× panel).
   - Vpředu čte, v hloubce chodby splývá.
6. **Madla bez oděru, jiná oranžová (musí / doporučeno) – zčásti.**
   - Oděr nahoře (`TopWear`) je vidět na plném rozlišení (ohyb madla, madlo poklopu).
   - „Jiná oranžová“ neplatí: je to jedna instance `MI_Kit_Halcyon_Signal` (kolo 1 bod 7).
7. **Mřížka nad černem (doporučeno) – neopraveno.** Rozhodnutí autora (kolo 1 bod 5).
8. **Poklop: těsnění a madlo (doporučeno) – neopraveno.**
   - Těsnění je 8 mm gumy.
   - Madlo (oranžová tyč v prohlubni) je podle zadání autora z 27. 9.
9. **Roztřepený odraz na desce B (doporučeno) – neopraveno.** Protiskluzový trim zůstává beze změny (autor).
10. **Výstražný pruh bez oděru (doporučeno) – neopraveno.** Dávka 6.
11. **Lišty na každém žebru (doporučeno) – mimo rozsah.** Schválená světla.
12. **Popisek O2 / N2 (doporučeno) – neopraveno.** Dávka 6.

## Ověřovací kolo (body 1, 2, 3 kola 3) – ZČÁSTI

Výstup: [verify/critic.md](2026-09-27_kit_material/verify/critic.md), snímky `Saved/Shots/20260928_003957_kit_material`.

- Svítidla zčásti, konstrukce zčásti, špína ve spárách nevyřešena. Podrobnosti v bodech kola 3 výše.

## Otevřené body pro autora

- **Materiály mají u kritika dál 4 z 10 ve všech třech kolech.**
  - Jemná variace povrchu (lesk, škrábance, broušení, prach v lemu desek) je na snímcích v plném rozlišení.
  - Z 1,6 m a na zmenšeném listu se nečte. Zesílená se čte jako skvrny.
  - Kritik chce výraznější špínu a opotřebení, než říká art direction „lakované panely SC téměř čisté“.
  - Systémový krok: karty špíny (mesh decaly) podél spár, soklu a kolem kování.
- **Konstrukce proti panelům:** v hloubce chodby splývají. Další krok: jiný charakter povrchu konstrukce (matnější lak s hranou), ne jen světlejší tón.
- **Svítidla:** bílé jádro bez rámečku (geometrie svítidel dávky 2).
- **Kanál pod mřížkou, protiskluz, značení:** podle rozhodnutí autora později.
