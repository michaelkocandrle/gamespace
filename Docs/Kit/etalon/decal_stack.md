# Vrstvy decalů – rozbor etalonu (autor 6. 10. 2026)

Záběry: `sc/decal_aurora_bay.jpg` (pohled dveřmi do technického koutu) a `sc/decal_aurora_corridor.jpg` (chodba ke
kokpitu). Autor ke svému dílu: „plastové, holé zdi bez decalů". Kouzlo SC jsou různé textury navrstvené na sebe pro
pocit plnosti a na nich detaily; nestačí jednoduché nápisy (EXIT).

## Co je na záběrech, vrstva po vrstvě

**0. Tónový rozsah (předpoklad všeho).** Jas v zobrazení (sRGB), změřeno na záběrech:

| Plocha | Jas |
|---|---|
| střední šedé panely stěn | 0,24–0,31 |
| rámy | 0,23–0,24 |
| tmavé perforované vložky | 0,14 |
| světlé vnitřky skříněk | 0,73 |

Stěna je **středně šedá, ne černá**; tmavé jsou jen vložky. Naše stěny měly 0,10–0,15 (grafit 0,06), takže se
žádná vrstva nemohla ukázat.

**1. Podklad.**
- Saténový lak s jemnou proměnou lesku a skvrnami.
- Každý panel má malinko jiný odstín.
- Hrany chytají světlou linku.

**2. Tvarové vrstvy, vnořené 2–3×.**
- Panel → zkosený rám (osmibok, rohy 45°) → zapuštěné pole → vložka (perforace, mřížka, deska s logem).
- Každá úroveň má vlastní lem a stín v koutě.
- Kryt „COMPONENT BAY" jsou čtyři vnořené osmiboké úrovně.

**3. Střední detaily** (hustota 15–30 prvků na m²):
- řady drážek a slotů (malé obdélníkové výřezy po 3–6 kusech, i podél rámů);
- šrouby v rozích každého pole;
- lamely a mřížky nad skříňkami;
- spáry panelů;
- perforované tmavé vložky (jemná pravidelná síť);
- madla a západky;
- malé obdélníkové stavové LED;
- kabelové kanály.

**4. Informační vrstva.** Malá, tón v tónu, žádné velké nápisy.
- Pásky s textem: tmavý proužek, drobné bílé písmo a šipky („WEAPON RACK ▸", „PERSONAL STORAGE",
  „FIRE EXTINGUISHER UNIT" u spodní hrany).
- Šedé šrafy //// na hranách sloupků (výstražný pruh tón v tónu).
- Malé ikony: červený čtvereček hasicího přístroje, oranžová „PUSH" s rukou.
- Logo výrobce na krytu a rohové značky └ ┘.

**5. Opotřebení.** Jemné, jen na hranách a v koutech: světlé odřené hrany, lehká špína v koutech, stékance pod
lamelami.

## Pravidla pro díly továrny (od teď)

1. **Tóny:**
   - stěny a panely jsou středně šedé (jas v obraze 0,22–0,32);
   - tmavá třetina (vložky, perforace, guma) kolem 0,12–0,15;
   - světlé akcenty (lak, lem, vnitřky) 0,6–0,75.
2. **Žádná plocha nad ~0,3 m bez vnoření.** Každé pole má rám, zapuštění a vložku nebo detail.
3. **Hustota:** aspoň 15 prvků vrstvy 3–4 na m² stěny ve výšce oka. Ve stropu a u podlahy může být méně, ale ne
   nula.
4. **Informace:** pásky s textem, šrafy a ikony malé a tón v tónu. Barevné (červená, oranžová) jen jako bod u
   funkce.
5. **Opotřebení** podle stylu výrobce, jen kde vzniká (hrany, kouty, pod lamelami).
6. **Kontrola:** snímek z oka a výřez 1:1. Kritik i autor posuzují **hustotu vrstev**, ne jen přítomnost decalů.

## Stav v1 (6. 10., zkušební úsek)

Snímky v1 nahradila v2.

**Stěna úseku je postavená jako modul s vrstvami** (`Tools/Kit/kit_factory.py`, `wall_module`):
- **tóny:** nové role `Kit_Panel` (středně šedá 0,19) a `Kit_Perforated` (tmavá perforace, `kit_perf_normal.py`);
- **tvar:** spodní větrací pás (rám → perforace), hlavní pole (rám → zapuštění → u levé stěny krycí deska s lemem
  a logem);
- **detaily:** řady slotů, pásky s textem na tmavém proužku, LED, poklop a zásuvka se štítkem, šrouby v rozích,
  šrafy;
- **šikmina:** perforované panely v rámu s příčkou;
- **strop:** sloty a mřížka.

Levá a pravá strana se liší.

**Lak a grafit:** skvrny 0,03 → 0,22 a 0,05 → 0,30, proměna drsnosti 0,05 → 0,16.

**Otevřené:**
- Šikminy a strop jsou v šeru: úsek svítí jen světly portálu.
- Hustota je pořád pod SC.
- Plochy rámu portálu jsou úzké (24–25 mm), takže se na ně řady výřezů jako v SC nevejdou bez rozšíření profilu.
- Logo Halcyonu chybí.

## Stav v2 (6. 10., autor „pokračuj tím")

Snímky: `stack_v2_eye.jpg`, `stack_v2_wall_34.jpg` a `stack_v2_detail.jpg`.

- **Stropní svítidlo v každém modulu:** zapuštěný rám, opálový difuzor s mřížkou, plošné světlo dolů 2 cd. Jas je
  teď u etalonu: medián 0,21–0,24, SC 0,19–0,22. Při 6 cd byl průměr 0,35, při 3 cd 0,30.
- **Druhá řada drobností:** západky, červené servisní značky, pásky GND POINT a EXT PWR, rohové značky, HF-CL 07.
- **Rám portálu rev. G:** manžeta 80 → 40 mm, lakované pásy podhledu 24 → 44 mm. Po celém obvodu (pilíře, šikminy,
  horní člen) mají řady malých výřezů po 12 cm.

## Inženýrský terminál a průchodnost (7. 10.)

Autor: „přesně stejný MFD řídící panel jako na referencích, kompletně stejnou kvalitu".

Snímky: `terminal_corridor.jpg`, `terminal_config.jpg`, `terminal_3dview.jpg` a `terminal_housing.jpg`.

- **Pouzdro:** díl `SM_Kit_Terminal_Eng07W_A` (`kit_factory.terminal_housing`).
  - Světlý zaoblený rám 0,70 × 0,43 m, tmavý stupeň a leštěná hrana kolem skla.
  - Výstupek nahoře, vlevo kulatý ovladač a žebrovaný posuvník, šroub v rohu.
  - Slabé světlo obrazovky na okolí.
- **Obrazovka:** `ASpaceEngineeringTerminal` / `USpaceEngineeringScreen` (C++).
  - **Hlavička:** ARMOR, HULL, COOLING SYSTEM, LIFE SUPPORT a HYDROGEN FUEL; NAV/SCM, oznámení, zvonek, zavřít.
  - **Záložky:** 3D VIEW, CONFIG, PRESETS.
  - **CONFIG:**
    - výkonová deska: zdroje → systémy (zbraně, trysky, štíty, kvantový pohon jen v NAV, podpora života, radar) →
      2 chladiče;
    - pipy, teplotní lišty, značky H a klávesy s ikonami;
    - jantarový rám úprav s EDIT / NEWPRESET_n, CLEAR ALL, SAVE a SAVE AND APPLY.
  - **3D VIEW:** drátový model chodby s komponentami (relé, elektrárna, chladiče, podpora života), propojeními,
    filtry a kartou vybrané komponenty.
  - **PRESETS:** uložené konfigurace s APPLY.
- **Ovládání:** podržet F (režim interakce) a kliknout přesně na prvek. Konzole pro snímky: `space.EngTab`,
  `space.EngClick`, `space.EngSave`, `space.EngNav`.
- **Hodnoty:** model energie je terminálu vlastní. Hra zatím nemá zbraně, štíty ani teplotu; hlavičky ARMOR, HULL a
  FUEL ukazují 100 %.
- **Průchodnost:** portál měl jednu kolizní krabici přes celou světlost a stěny úseku žádnou. Teď mají kolizi práh,
  pilíře, boty, šikminy, horní člen a stěny.

## Ladění terminálu a servisní stěna (7. 10.)

Snímky: `terminal_housing.jpg`, `terminal_3dview.jpg`, `bay_end_wall.jpg` a `bay_close.jpg`.

**Terminál:**
- **Záložky** se kreslí nad panelem. Předtím jim panel zakryl pravou půlku i text. Jsou to zkosené výstupky
  s textem a ikonou.
- **Rám** je ve vrstvách:
  - montážní deska se šrouby a stínovou spárou;
  - zapuštěná obvodová spára, sestup do tmavé vnitřní stěny, leštěná hrana kolem hlubšího skla;
  - dvoubarevný horní výstupek se spárou, sloty a LED;
  - tlačítko ve věnci s vroubkovaným prstencem, posuvník v drážce;
  - šrouby, větrací sloty, LED a ID.

  Rohy jsou bez zkosení na každém segmentu: radiální rýhy působily plastově.
- **Paleta** je vzorkovaná ze SC a převedená ze sRGB do lineárních barev.
- **3D VIEW** je rentgen interiéru zevnitř chodby, oříznutý na plochu panelu.

**Servisní stěna** (`SM_Kit_Bay_Service10W_A`, podle `sc/decal_aurora_bay.jpg`) stojí na čelní stěně vlevo,
terminál vpravo:
- skříň hasicího přístroje: niša s červeně svítící zadní stěnou, přístroj s ventilem, pákou, hadicí a tryskou
  v držáku, pod ní dvířka;
- dvě skříňky s teple osvětleným krémovým vnitřkem a leštěným lemem;
- kryt COMPONENT BAY: 4 vnořené osmiboké úrovně, HALCYON FREIGHTWORKS, SERVICE ACCESS a štítek COOLER S1;
- žaluzie, šrouby, šrafy a šablony.

Nové role jsou `Kit_Red` (červený lak) a `Kit_GlowRed`.
