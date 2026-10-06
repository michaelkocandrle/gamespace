# KF-PORTAL-01 – rev. F, krok 7 (výkon) a krok 8 (kritik proti etalonu), 6. 10. 2026

**Stav:** STOP. Kritik po 3 kolech **FAIL** (5,3 / 5,3 / 5,2; práh pilotu: všech šest rozměrů ≥ 7). Krok 9
(autorovo oko ve hře) čeká na autora.

Listy: `2026-10-06_kf_portal_01_critic/`:
- `sheet_00` etalon;
- `sheet_01`–`04` čtyři úhly etalonu;
- `sheet_05` bota;
- `sheet_06` práh;
- `sheet_07` A/B špíny;
- `sheet_08` showroom 3/4;
- `sheet_09`–`11` výřezy k výtkám.

Výřezy jsou v `evidence/`.

## Rev. F (úpravy autora 1–5)

1. **Bota L1 zblízka.**
   - Kalich má grafitový plášť 1,5 mm. První kolo s lakovanými stěnami četlo jako bílé okénko.
   - Viditelná hloubka je 35 mm (N 30). Při 60 mm nebylo dno z oka vidět, takže z dálky chyběl jasný bod. Tělo boty
     zůstává 60/45 kvůli zkosení v půdorysu.
   - Světlo u dna má 0,012 cd a dosah 12 cm. Stěny mají přechod od zdroje do tmy.
   - Zdroj je kapka Ø18, která stojí 9 mm nad dnem.
   - Otvor má leštěný rámeček 6 mm. Na stěnách boty je drážka 30 mm pod vrchem.
   - Z dálky zůstává malý jasný bod (`sheet_02`).
2. **Rozptyl na podlahu:** druhé světlo, bodové, bez stínů.
   - Nakonec 0,35 cd, kužel 100°, dosah 0,45 m.
   - Je skloněné o 45° ven, aby nesvítilo do kalichu.
   - Skvrna je měkká, bez ostré elipsy. Kritik ji v kole 2 hodnotil jako příliš plošnou na prahu, proto se zmenšila.
3. **L3:** horní člen visí 40 mm pod stropem a lišta leží na jeho horní ploše, svítí nahoru do kazety.
   - Kazeta je světlý lak; grafitová světlo pohltila.
   - Clonky 25 mm podél hran členu z kazety dělají žlab. Zdroj z oka vidět není (`evidence/k1_b1_l3.jpg`), ale
     nasvícená kazeta se pořád čte jako zářící linka (kritik, body 1 / 5 / 3).
   - Úsek je teď tmavší než etalon: úhel 1 má medián 0,14 proti SC 0,22. L3 zvednuté z 8 na 24 cd pomohlo jen málo,
     nepřímé světlo odráží do chodby málo. **Otevřené, rozhodne autor:** buď přímá složka dolů skrytá za hranou
     členu, nebo víc světla od jiných dílů (strop, stěna).
4. **Šrouby destičky:** tmavé byly dvě kvůli odrazu (leštěný kov zrcadlil místnost). Všechny 4 jsou teď saténový grafit
   a stejné (`sheet_06`).
5. **Špína Halcyonu:** alfa 0,8, jen na místech vzniku:
   - šmouha u paty boty (posunutá 45 mm před čelo, předtím horní řada karty ležela pod botou a karta se vytratila);
   - žlab u soklu;
   - rohy prahu.

   A/B podle P5 (`sheet_07`): karty vyp proti normálu mění 1,1–1,9 % pixelů u boty a 0,35 % na prahu. Kitová
   špína je světlý matný prach (rozhodnutí z ladění Wayfareru), takže ve světelné skvrně působí jako opar.

## Krok 7 – výkon světel (1440p, zabalená hra, 3 běhy, `kit_portal_perf`)

| Stav | GPU ms (průměr, n = 9) | rozptyl | snímek ms |
|---|---:|---:|---:|
| osvětlení interiéru | 6,36 | 0,04 | 7,50 |
| osvětlení letu (`space.InteriorLighting 0`) | 6,85 | 0,03 | 7,97 |
| světla dílu vypnutá | 5,31 | 0,10 | 6,46 |

Světla 4 portálů (16 L1, 8 L2, 4 L3) stojí asi 1,05 ms. Žádný skok, cíl 16,6 ms je daleko. Neoptimalizováno.

## Krok 8 – kritik (Opus, gate „part“, pilot)

| Rozměr | K1 | K2 | K3 |
|---|---:|---:|---:|
| Tvar a hierarchie | 6 | 6 | 5 |
| Materiály | 6 | 5 | 5 |
| Světlo | 5 | 6 | 6 |
| Decaly a značení | 5 | 5 | 5 |
| Špína a opotřebení | 4 | 4 | 5 |
| Funkce a stavy | 6 | 6 | 5 |
| **Průměr** | 5,3 | 5,3 | 5,2 |

Skóre se přes kola hýbe jen o bod. Podle pravidla „systémové, ne lokální“ zbývající výtky nevyřeší díl sám:
- lak s jednou drsností;
- podlaha a lem;
- míra značení a špíny.

To jsou rozhodnutí materiálové desky a autora.

### Kolo 1

1. **L3 holé pruhy.** Platí, i když zdroj vidět není: svítí kazeta 4 cm od něj. Opraveno clonkami 25 mm (žlab) →
   v K2/K3 zůstává zářící linka.
2. **Kalich jako vypouklé okénko.** Neplatí: kalich je zapuštěný 35 mm (`evidence/k1_b2_kalich.jpg`). Zdroj u dna
   ale opravdu nebyl vidět → kapka Ø18 (K2/K3).
3. **Bota holý hranol.** Nesouhlas: autor chtěl hladkou botu s jednou drážkou nebo polem; drážka je.
4. **Špína není vidět.** Částečně platí: karta u boty se vytrácela → posunuta a změněna na šmouhu. Světlý prach je
   záměr.
5. **Chybí hierarchie značení.** Rozsah kroku 5 schválil autor; štítek B03 je (`evidence/k1_b5_stitek.jpg`).
6. **Lak bez odlesku, lem.** Neopraveno: systémová věc materiálové desky (drsnost laku), viz závěr.
7. **Podlahová pole bez lemu.** Neplatí: síť lemu 18 mm je (`evidence/k1_b7_lem.jpg`). V hloubce chodby slabne
   (K3 bod 7).
8. **Holé stěny.** Mimo díl (stěna zkušební místnosti).
9. **Tmavé zářezy na pilíři.** Spára 4 mm mezi pilířem a stěnou podle profilu. Světlý bod v ní je soused za spárou.
   Neopraveno, zapsáno.

### Kolo 2

1. **Kalich bez zdroje.** Opraveno (kapka Ø18, 9 mm nad dnem).
2. **Jedna drsnost laku.** Neopraveno (systémové).
3. **Podlaha bez tmavé třetiny.** Neopraveno: podlaha je z materiálové desky kroku 3 (schválená); otázka pro autora.
4. **Špína.** Viz K1/4.
5. **L3 pruh.** Viz K1/1.
6. **Odznak jako placeholder, B03 nízký kontrast.** Platí. Odznak „||“ je zástupný, chybí logo Halcyonu (návrh do
   dalšího kroku).
7. **Přechod pilíř–bota.** Platí jako doporučení. Límec u paty pilíře se navrhne s listem.
8. **Rozptyl příliš plošný.** Opraveno: 0,5 → 0,35 cd, 0,6 → 0,45 m.
9. **Rám plošně osvětlený.** Neopraveno: v úseku svítí jen L2 a nepřímé L3.
10. **Holé plochy pilíře.** Viz K3/1.

### Kolo 3 (poslední)

1. **Holé lakované plochy pilíře a koruny, chybí třetí vrstva.** Platí proti etalonu. Je to tvarová změna listu
   (zapuštěná pole se šrouby): rozhodne autor, rev. G.
2. **Zdroj v kalichu jako přepálená ploška.** Částečně platí. Jádro kapky je ostré; matný difuzor nebo slabší emise
   jsou levná oprava pro rev. G.
3. **L3 linka.** Viz výše. Otevřené: přímá složka nebo vyšší clonka.
4. **Špína jako opar ve světelné skvrně.** Platí: světlý prach ve skvrně L1 vypadá jako bloom. Návrh: u boty tmavá
   karta (ne prach) mimo skvrnu.
5. **Značení bez hierarchie, placeholderový reliéf.** Platí (viz K2/6).
6. **Jednotná drsnost.** Systémové (M_Kit_Base: šum drsnosti ±0,05, lesklejší fazety).
7. **Lem podlahy slabý.** Doporučeno, systémové (drsnost lemu).
8. **Podlaha není grafitová.** Doporučeno. Barvu podlahy schválil autor u desky. Otázka pro autora.
9. **Bota bez stavu.** Doporučeno. Světelné stavy (nouzový jantar) patří do kroku „funkce a stavy“.

## Jas – SC / rev. E / rev. F (`shots:20261006_224145_kit_test_section`)

| Úhel | SC průměr / medián | rev. E | rev. F |
|---|---|---|---|
| 1 do hloubky | 0,24 / 0,22 | 0,23 / 0,20 | 0,19 / 0,14 |
| 2 pata pilíře | 0,28 / 0,26 | 0,29 / 0,25 | 0,28 / 0,26 |
| 3 podlaha | 0,28 / 0,25 | 0,28 / 0,22 | 0,26 / 0,20 |
| 4 lak zblízka | 0,23 / 0,19 | 0,24 / 0,21 | 0,18 / 0,16 |

Úhly 1 a 4 ztratily přímé světlo L3 (rev. E svítila plošně dolů).
