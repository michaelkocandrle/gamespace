# KF-PORTAL-01 – list rev. D a blockout (krok 4), 6. 10. 2026

**Stav:** STOP. Autor posoudí listy blockoutu. Krok 5 (detail) až po schválení.
**Kritik:** nespouštěn (hodnotí díl v kroku 8).

## List rev. D (jen bota L1 a manžeta; zbytek rev. C schválen)

`ArtSource/Kit/Design/KF-PORTAL-01.png`; změněné výřezy jsou `_01_pohled`, `_02_rez`, `_03_profil` (manžeta),
`_04_podlaha` a `_05_napojeni` (detail boty).

1. **Bota L1** je světlá, v laku rámu, s leštěnou hranou 12 mm nahoře.
   - Světlo je záře uvnitř osmibokého kalichu (110 / 90 mm, hloubka 30 mm) s **jemným rozptylem na podlahu**:
     svítící dno a slabé bodové světlo 0,6 cd s dosahem 0,5 m. Žádný reflektor, žádné ostré elipsy, ~7500 K.
   - V úzké chodbě N je bota 120 mm místo 170 mm, aby průchod zůstal 0,96 m (minimum kitu 0,9).
2. **Manžeta:** žebra 4 mm po 9 mm, výška 2 mm, a guma o tón světlejší (0,04 místo 0,016). Uprostřed rámu už není
   tmavý proužek.

## Krok 4 – blockout

Díl má vlastního stavitele `Tools/Kit/kit_portal.py`, který staví z dat listu.
- **Díly:** `SM_Kit_Portal_Frame03W_A`, `..03N_A` (portál, boty, horní světla, práh v síti lemu) a
  `SM_Kit_Floor_Walk09W_A`, `..09N_A` (chodník, rohové trojúhelníky, boční desky ve W, síť lemu).
- **Světla jsou sockety dílu**, takže v lodi svítí stejně (`kit_rooms`):
  - `Light_Cup` – bod v kalichu;
  - `Light_Corner` – široký kužel dolů;
  - `Light_Strip` – plošné světlo pod horním členem.
- **Zkušební úsek** (`import_kit.SHOWROOM["test_section"]`) je teď z blockoutu dílu. Kolem je jen plášť
  `SM_Kit_Test_Shell09W_A` (stěny, strop, kopací pás). Konec uzavírá 4. portál.
- **Varianta N** nemá zkušební úsek v UE: je vyrenderovaná v Blenderu z oka (`sheet_06_varianta_N_blender.jpg`,
  `Tools/Kit/render_part_eye.py`).
- **Blockout neobsahuje:** decaly, ražbu, karty špíny, otěr hran (zkosení) ani detail kalichu a boty. To je krok 5.

## Opar a zvednutá černá jen v interiérech

- **Post-process interiéru** (`Tools/Assets/interior_post.py`, hodnoty v `kit_rules.json` `interior_post`):
  kontrast 0,90, posun stínů +0,018, sytost 0,95. Je to „závoj“ místo globální tónové křivky.
- **V lodi:** krabice přes všechny místnosti z `Design/<Loď>_layout.json` jako komponenta lodi
  (`kit_rooms.add_interior_post`), takže se pohybuje s lodí. Ve Wayfareru x 1,0–19,4, y ±1,9, z −0,2–3,5.
- **Ve zkušebním úseku:** ohraničený `PostProcessVolume` přes místnost.
- **Nástraha:** krabice s `NoCollision` nedělala nic. Řešením je `QueryOnly` s odpovědí `Ignore` na všechny kanály
  (WORKFLOW 9.2).

**Kontrola P25** (`Tools/Review/shot_diff.py`):

| Srovnání | Průměr rozdílu (0–255) | Výsledek |
|---|---:|---|
| exteriér: šum dvou běhů před | 0,51 / 1,74 / 1,45 | – |
| exteriér před vs. po (kokpit do vesmíru, chase nad horizontem a planetou) | 0,43 / 1,81 / 1,42 | **beze změny**, vesmír a planety stejné |
| interiér Wayfareru před vs. po | 9–20 | změna je záměr: tmavé plochy klesly z 26–77 % na 0–16 %, ve skladu z 64 % na 9 % |

- **Riziko:** krabice zahrnuje kokpit, takže závoj leží i na výhledu z kabiny ven (obloha za sklem je o něco
  šedší). Fyzikálně to odpovídá oparu v kabině. Kdyby to vadilo, kokpit se z krabice vynechá.
- HUD se nemění: kreslí se až po post-processu.

## Jas – SC / rev. C / rev. D (blockout)

Měřeno `measure_look.py`. Rev. C = `shots:20261006_200718_kit_test_section`; rev. D = blockout s post-processem
interiéru, `shots:20261006_203857_kit_test_section`.

| Úhel | | průměr | p10 | medián | p90 | tmavé | světlé |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 z oka do hloubky | SC | 0,24 | 0,13 | 0,22 | 0,37 | 1 % | 4 % |
| | rev. C | 0,19 | 0,03 | 0,14 | 0,49 | 26 % | 11 % |
| | **rev. D** | 0,27 | **0,13** | 0,21 | 0,51 | **1 %** | 12 % |
| 2 pata pilíře | SC | 0,28 | 0,14 | 0,26 | 0,42 | 1 % | 7 % |
| | rev. C | 0,25 | 0,06 | 0,22 | 0,42 | 12 % | 8 % |
| | **rev. D** | 0,31 | **0,19** | 0,28 | 0,45 | **1 %** | 10 % |
| 3 podlaha 35° | SC | 0,28 | 0,19 | 0,25 | 0,40 | 0 % | 6 % |
| | rev. C | 0,23 | 0,06 | 0,17 | 0,44 | 17 % | 8 % |
| | **rev. D** | 0,29 | **0,15** | 0,23 | 0,45 | **0 %** | 10 % |
| 4 lak a tmavá třetina | SC | 0,23 | 0,13 | 0,19 | 0,37 | 1 % | 6 % |
| | rev. C | 0,21 | 0,06 | 0,16 | 0,55 | 25 % | 11 % |
| | **rev. D** | 0,26 | **0,15** | 0,21 | 0,54 | **2 %** | 12 % |

- **Tmavé plochy a p10** jsou teď na úrovni SC.
- **Zbývá:** světlých ploch je 10–12 % proti 4–7 % v SC a p90 je o 0,05–0,17 vyšší. Krémový rám je pořád
  nejjasnější plocha; jeho tón autor nechce měnit. Kandidát pro krok 5–6: menší L2 nebo L3 na koruně.

## Listy

Složka `2026-10-06_kf_portal_01_blockout/`:
- `sheet_00_etalon.jpg` a `sheet_01` až `sheet_04` – SC vlevo, blockout vpravo, stejné úhly, FOV 90;
- `sheet_05_oko_list_vs_hra.jpg` – pohled z oka v listu vedle blockoutu ve hře (návrh z retrospektivy);
- `sheet_06_varianta_N_blender.jpg` – varianta N z oka (Blender, jen tvary).

U `sheet_05`: list kreslí nekonečnou chodbu ořezanou na 4:3, ve hře jsou 4 portály a stěna zkušební místnosti.
Rytmus portálů, proporce rámu a poloha bot a světel souhlasí.
