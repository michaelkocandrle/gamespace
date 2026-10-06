# KF-PORTAL-01 – list rev. E, krok 5 (detail) a krok 6 (UE a zkušební úsek), 6. 10. 2026

**Stav:** STOP. Autor posoudí listy. Krok 7 (výkon) a 8 (kritik) až po schválení.

## Rev. E (úpravy tvaru po blockoutu)

1. **Čela stupňů rámu jsou zkosená pod 45°** místo svislých 90°, takže chytají světlo shora.
   - Profil: plošky 25 / 24 mm, krátké svislé paty 15 / 6 / 12 mm, nášlapy 5–6 mm.
   - Leštěná je zkosená hrana koruny 18 × 18 mm: jedna světlá linka.
   - Rám se teď staví tažením profilu po obrysu průřezu (`kit_portal.loft`), jeden tvar bez spár.
   - Ověřeno z oka na W (listy 1, 5) i na N (`sheet_06`, Blender).
2. **Bota L1:**
   - nižší, W 150 mm a N 120 mm;
   - osmiboká i v půdorysu (svislé hrany zkosené 50 mm, v N 40);
   - plochá bez stříšky, leštěná horní hrana 12 mm;
   - kalich je osmiboká jamka 70 mm, hluboká 60 mm (N 45), s **tmavým dnem**, zdrojem Ø14 a slabým světlem
     0,05 cd u dna, takže svítí stěny jamky s přechodem k okraji.
   - Kola kalichu: 1 – světlé dno 15 mm od světla 0,6 cd = plochý bílý osmiúhelník; 2 – tmavé dno, 0,3 cd, pořád
     přepálené; 3 – 0,05 cd u dna: stěny stínované, zdroj je bod.
   - **Otevřené:** rozptyl na podlahu je teď skoro neznatelný; zesílení vrátí přepal stěn. Návrh: druhé, širší
     světlo mířící jen na podlahu (rozhodne autor).
   - **Otevřené:** L3 (skrytá lišta) ztratila v rev. E drážku na římse stupně 2. Ve zkušebním úseku svítí jen jako
     plošné světlo pod horním členem; nové místo drážky se navrhne s horním členem.

## Krok 5 – detail

Etalonová karta (štítky 3 cm, krycí destička pásu se 4 šrouby, drážky pásu, žlab u soklu) a styl Halcyon:
- **Štítky:** číslo rámu B03 jako mesh decal na plošce základny každého pilíře, svisle, výška písma asi 3 cm. Jsou
  na obou čelech modulu, takže je vidět z obou směrů chodby. Na laku nejsou žádné šrouby.
- **Práh** pod portálem slouží jako pás:
  - 5 příčných drážek;
  - krycí destička 400 × 150 mm se 4 leštěnými šrouby (funkční kryt);
  - odznak výrobce v reliéfu, grafit s leštěnými lištami (bílý lak četl jako samolepka);
  - pole v síti leštěného lemu.
- **Žlab u soklu:** okrajový pás se 3 podélnými drážkami (v portálu i v podlahovém modulu).
- **Opotřebení podle stylu Halcyon:**
  - špína ve spárách přes drsnost (materiál);
  - otěr hran 5–6 mm jen na nášlapech ve výšce 0,9–1,6 m (maska v `M_Kit_Base`);
  - vyšlapaná dráha přes drsnost;
  - karty špíny `rim` u paty boty a podél žlabu. Karty `smear` v rozích prahu se nepoložily: v úzkém místě mezi
    drážkami a lemem nenašly plochu, zůstávají otevřené.

**Oprava mimo díl:** karty špíny (`Tools/Blender/hs_decals.py` `card_at`) skládaly buňky v pořadí, ve kterém každá
plocha mířila proti normále. Kontrola přeložených buněk je pak zahodila všechny a od jejího zavedení (3. 10.) se
**žádná karta špíny nepoložila**. Pořadí je opravené (WORKFLOW 9.6). Až se znovu postaví dávky kitu a trup Wayfareru,
karty se jim vrátí. To je viditelná změna: při přestavbě udělat P25.

## Krok 6 – UE, pevné pohledy a A/B

Zkušební úsek: snímky `shots:20261006_212542_kit_test_section`, 2560 × 1440, FOV 90.
- 4 úhly etalonu;
- pevné pohledy showroomu pro rám: A osa ze 2 m, B 3/4 z 1,2 m, C detail z 0,5 m, D = úhel 1;
- 4 detaily: štítek, práh, kalich, otěr.

**A/B podle P5** (`shots:20261006_212218_kit_portal_ab`, za běhu `space.Kit` / `space.KitColor`):

| Snímek | Změna proti normálu | Závěr |
|---|---|---|
| otěr hran vyp | průměr 4,6, změněno 5,6 % pixelů | otěr je vidět, jen na nášlapech v pásmu ruky |
| otěr hran naplno | 1,3 / 0,03 % | normál je prakticky „naplno“ (práh 0,15) |
| decaly a špína černé / bílé / vyp (práh) | 1,3–1,4 | na prahu karty nejsou (`smear` se nepoložily) |
| decaly a špína černé / bílé / vyp (bota) | 1,0–1,1, změněno 0,3–0,5 % | karta `rim` u paty boty je, ale slabá |

**Návrh:** karty špíny zesílit (alfa 0,55 → 1,0) a položit `smear` v prahu mimo drážky. Před tím autorovo slovo
k míře špíny Halcyonu.

## Jas – SC / blockout / detail

Detail = `shots:20261006_212542`, blockout = `shots:20261006_203857`.

| Úhel | | průměr | p10 | medián | p90 | tmavé | světlé |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 z oka do hloubky | SC | 0,24 | 0,13 | 0,22 | 0,37 | 1 % | 4 % |
| | blockout | 0,27 | 0,13 | 0,21 | 0,51 | 1 % | 12 % |
| | **detail** | **0,23** | 0,11 | **0,20** | **0,43** | 1 % | **9 %** |
| 2 pata pilíře | SC | 0,28 | 0,14 | 0,26 | 0,42 | 1 % | 7 % |
| | blockout | 0,31 | 0,19 | 0,28 | 0,45 | 1 % | 10 % |
| | **detail** | **0,29** | 0,17 | **0,25** | **0,42** | 1 % | **8 %** |
| 3 podlaha 35° | SC | 0,28 | 0,19 | 0,25 | 0,40 | 0 % | 6 % |
| | blockout | 0,29 | 0,15 | 0,23 | 0,45 | 0 % | 10 % |
| | **detail** | **0,28** | 0,15 | **0,22** | **0,43** | 0 % | **8 %** |
| 4 lak a tmavá třetina | SC | 0,23 | 0,13 | 0,19 | 0,37 | 1 % | 6 % |
| | blockout | 0,26 | 0,15 | 0,21 | 0,54 | 2 % | 12 % |
| | **detail** | **0,24** | 0,14 | **0,21** | **0,43** | 2 % | **8 %** |

- Pevné pohledy showroomu A / B / C: průměr 0,25 / 0,24 / 0,29, světlé 9 / 11 / 17 % (C je detail laku zblízka).
- Rev. E (plošky místo svislých čel) stáhla p90 a světlé plochy k etalonu: p90 0,42–0,43 proti SC 0,37–0,42,
  světlé 8–9 % proti 4–7 %.

## Závoj interiéru – kokpit vynechán

Krabice závoje teď pokrývá Wayfarer jen v x 1,0–15,2 (sklad, technická chodba, kajuta); kokpit je venku.

| Pohled (P25) | Průměr rozdílu proti stavu před závojem |
|---|---:|
| kokpit dozadu | 0,54 (šum) |
| pohled pilota | 1,16 (šum) |
| sklad / chodba / kajuta | 17–20 (závoj, záměr) |

## Listy

Složka `2026-10-06_kf_portal_01_detail/`:
- `sheet_00`–`04` – etalon a 4 úhly, SC vlevo, díl vpravo;
- `sheet_05` – pohled z oka list vs. hra;
- `sheet_06` – varianta N;
- `sheet_07` – štítek a práh;
- `sheet_08` – bota a kalich;
- `sheet_09` – A/B otěru a decalů.
