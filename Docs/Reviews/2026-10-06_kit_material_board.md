# Tabule materiálů kitu – pilot 1 KF-PORTAL-01, krok 3 (6. 10. 2026)

**Workflow:** v0.1, krok 3: materiálový základ kitu, v pilotu 1 jako sdílený základ.
**Stav:** STOP. Autor posoudí tabuli; blockout (krok 4) až po jeho schválení.
**Kritik:** zatím se nepouštěl. Hodnotí se až díl (krok 8); brief s prahem `part` je připravený v `brief.md`.

## Co vzniklo

**Data:** `ArtSource/Kit/kit_materials.json`.
- **Role trojice:**
  - `Kit_Lacquer` – světlý lak, drsnost 0,5, metallic 0,05, otěr hran 4 mm;
  - `Kit_Lip` – leštěný kov, drsnost 0,25, metallic 1;
  - `Kit_Dark` – guma / grafit, drsnost 0,65;
  - `Kit_AntiSlip` – protiskluzový grafit, drsnost 0,68, vyšlapaná dráha.
- **Palety výrobců:**
  - Halcyon: krémová, gunmetal, grafit, oranžová;
  - Kestrel (jen návrh): světle šedá, modrá.
- **Styl opotřebení:** špína ve spárách, otěr hran 0,9–1,6 m, dráha ±0,25 m od osy.

**Unreal:** master `/Game/Kit/Materials/M_Kit_Base`.
- Je to graf vrstveného masteru lodí jako **vlastní asset kitu** (poučení P25). Navíc má pásmo výšky pro otěr hran
  (`WearBandOn/Lo/Hi`, cm nad podlahou dílu) a vyšlapanou dráhu (`WalkWear`, `WalkHalfCm`).
- Instance `MI_Kit_<Výrobce>_<Role>` pro Halcyon i Kestrel.
- Kód: `ship_materials.build_layered_master(path, kit=True)`, `import_kit.build_factory_materials()`.
- Master lodí se staví stejným kódem jako dřív (`kit=False`). Snímky lodí před a po změně jsem ale nedělal.

**Tabule:** `Tools/Kit/kit_factory.py` (dávka `factory` v `kit_build.py`), umístění `import_kit.SHOWROOM["board"]`.
- Stojí v tmavé místnosti za schodišťovou halou (x 20,2–25,1).
- **Světlo podle etalonu:** teplý zdroj skrytý nad vzorky (pás 3 m, 3500–4000 K), studené body u podlahy, slabá výplň.
- **Vzorky zleva:**
  1. lak se spárami a šrouby;
  2. tmavá třetina (grafit, žebrovaná manžeta, kopací pás);
  3. výsek profilu portálu 1,8 m (tři stupně, leštěné lemy, manžeta);
  4. leštěný kov;
  5. stejný profil v paletě Kestrel;
  6. před nimi chodníková deska 0,9 × 1,2 (lem, vložka −6 mm, pásy, dráha).
- Preset `Tools/Shots/kit_material_board.json`.

**Test:** `Tools/Tests/test_kit_materials.py` hlídá limity drsnosti a metallic, úplnost palet a míru opotřebení
(38 kontrol, PASS). `test_kit_showroom.py` počítá i vzorky tabule (UE, PASS).

## Snímky a listy

- Snímky: `shots:20261006_185810_kit_material_board/` (Editor, 2560 × 1440, varianta odrazů c).
- Listy SC vlevo, tabule vpravo: `2026-10-06_kit_material_board/sheet_00_etalon.jpg` až `sheet_07_*.jpg`.
- Kola tabule:
  1. Podlahová deska nebyla vidět (ležela v jedné rovině s podlahou místnosti) a leštěný lem měl kartáčované šmouhy.
  2. Otěr hran 0,8 / práh 0,35 nebyl vidět. Diagnostický snímek (otěr naplno) ukázal, že maska pásma funguje:
     rozdíl je jen v řádcích nad 0,9 m, pod 0,9 m žádný.
  3. Otěr Halcyonu je zesílený na 1,0 / práh 0,15.
- `measure_look` celkový pohled: průměr 0,17, p50 0,10, p90 0,41, B/R 0,83. Je to v rozsahu SC interiérů
  (0,13–0,23 / 0,08–0,18 / 0,32–0,53 / 0,72–1,05).

## Co je vidět

**Dobré:**
- leštěný lem chodníkové desky čte jako kov a kreslí obrys jako v SC (`sheet_06`);
- krémový lak je proti grafitu čistý dvoutón;
- spáry jsou tmavé, šrouby i manžeta se čtou;
- paleta Kestrel na stejném profilu funguje: jiný výrobce = jen jiná paleta.

**Slabé:**
1. Leštěný kov na svislých plochách v tmavé místnosti působí jako světlý pruh, ne jako zrcadlo. Lumen do drsnosti
   0,32 tu změní obraz jen málo (průměrný rozdíl 1,6 z 255), protože tmavá místnost nemá co odrážet. Lem jako
   leštěný kov potřebuje světla a světlé plochy, do kterých se dívá. Ověří se až ve skutečné chodbě (krok 6).
2. Protiskluzové pásy pod šikmým pohledem svítí do světle béžova (lesk dielektrika při drsnosti 0,68), v SC jsou
   tmavší. Kandidát na úpravu (drsnost 0,75–0,8 nebo tmavší grafit) až po autorově verdiktu.
3. Otěr hran 4 mm je vidět jen zblízka. Ze 2 m je lak skoro čistý, což odpovídá „udržované lodi“, ale potvrdí to
   autor.
4. Tmavá třetina (grafit proti gumě) má malý kontrast, protože obě mají drsnost 0,65 a podobnou barvu.

## Odrazy kovu – varianta c na RX 9070, 1440p, TSR

- Měřeno presetem `wayfarer_reflection_options`, 6. 10. 2026, Editor, 2560 × 1440, výchozí kvalita her
  (epic, TSR 75 %).
- Jeden běh: poučení P12 chce tři. Čísla jsou orientační.

| Pohled (Wayfarer) | b: kov bez Lumenu | c: kov + Lumen do 0,32, ½ rozlišení | rozdíl |
|---|---:|---:|---:|
| kajuta zblízka | 7,05 ms | 8,42 ms | +1,37 |
| sklad zblízka | 7,59 ms | 8,17 ms | +0,58 |
| technická chodba dozadu | 7,65 ms | 8,84 ms | +1,19 |
| sklad, náklad | 7,62 ms | 8,38 ms | +0,76 |

- **Shrnutí:** +0,6 až +1,4 ms GPU, průměr +1,0 ms, celkem 8–9 ms GPU na snímek. Do 16,7 ms (60 fps) zbývá
  velká rezerva.
- Dnešní stav: v C++ `SetInteriorLighting` jsou v interiéru Lumen odrazy vypnuté (`Allow 0`). Zapnutí varianty c
  je rozhodnutí autora; doporučuji ji.
- Frame čas v Editoru (17–20 ms) je limitovaný procesorem v režimu Editor, ne GPU.
