# Zkušební úsek chodby – materiálový základ kitu, pilot 1 KF-PORTAL-01, krok 3 (workflow v0.2, 6. 10. 2026)

**Stav:** STOP; autor posoudí 4 listy. Blockout (krok 4) až po schválení.
**Kritik:** nespouštěn (hodnotí až díl v kroku 8); brief s prahem `part` je v `2026-10-06_kit_test_section/brief.md`.

**Předchozí kolo:** tabule vzorků, `2026-10-06_kit_material_board.md`, autor neschválil. Vznikla z toho změna testu
(poučení P26): materiály se posuzují v kontextu a ze stejných úhlů jako kotevní záběry SC.

## Listy (SC vlevo, zkušební úsek vpravo)

Složka `2026-10-06_kit_test_section/`:
- `sheet_00_etalon.jpg` – kotevní záběry;
- `sheet_01` – z oka 1,65 m do hloubky (`ram_portal_1`);
- `sheet_02` – pata pilíře se světlem L1 z ~1,25 m šikmo shora (`ram_portal_2`);
- `sheet_03` – podlaha 35° dolů s lemem (`podlaha_1`);
- `sheet_04` – lak a tmavá třetina z ~0,7 m šikmo (`ram_portal_3`).

Snímky jsou v `shots:20261006_192907_kit_test_section/` (Editor, 2560 × 1440, FOV 90, odrazy varianta c ze hry).

**Zkušební úsek:** `Tools/Kit/kit_factory.py` (`SM_Kit_Test_Portal03W_A`, `SM_Kit_Test_Bay09W_A`), umístění
`import_kit.SHOWROOM["test_section"]`.
- Chodba W: 4 pole po 0,9 m a 3 portály po 1,2 m, konec chodby grafitová stěna.
- Světla jen z listu na každý portál:
  - L1 – 2 body ~7500 K u patek, 2,5 cd;
  - L2 – 2 bodová světla v rozích, 40 cd, 70°;
  - L3 – plošné světlo pod horním členem, 25 cd.
- Bez světla místnosti.

## Změny a zdůvodnění

| Autorova výtka | Změna | Proč |
|---|---|---|
| B1 lak jako papír | Mikro zrnitost 0,06 → 0,018 (−70 %), šmouhy 0,15 → 0,03, drsnost 0,47, jemná variace po panelech (tón 3,5 %, drsnost 0,06) | Satén s měkkým odleskem: v listu 4 je vidět odlesk na stupních rámu, dřív zrno připomínalo papír |
| B2 šrouby na laku | Zkušební úsek nemá na laku žádné šrouby; viditelné šrouby jsou jen na funkčních krytech (krycí destička pásu, poklopy) | Etalon nemá pohledové šrouby na rámech |
| B3 lem | `Kit_Lip` má pevnou barvu (albedo 0,74), metallic 1, drsnost 0,2, bez kartáčování a škrábanců, u všech výrobců stejný (test to hlídá) | Čte se jako světlý leštěný kov kolem desek a rámů (listy 1–3), jako obrys v SC |
| B4 tmavá třetina | Rozdělená na `Kit_Gasket` (guma 0,88, tmavší, jemné zrno, žebra manžety) a `Kit_Graphite` (satén 0,45) | Kontrast drsností: manžeta je matná, grafitové stěny a desky mají měkký lesk |
| B5 škrábance | Jen grafit, síla 0,035 (polovina), jen v pásmu 0,9–1,6 m (`ScratchBandOn` v `M_Kit_Base`) | Na laku, lemu a gumě nejsou; na stěnách jen tam, kde sahají ruce (list 4) |
| B6 podlaha | Protiskluzový vzor z dnešního kitu jako detailní normála v pásech (`T_Kit_Tread_N`, `kit_tread_normal.py`); pásy jen 1,2× světlejší než pole (test ≤ 1,35); vyšlapaná dráha jen přes drsnost (0,62 → 0,4) a o málo světlejší barvu, plynulá; lem desky beze změny | Kolo 2 ukázalo dráhu jako tmavé fleky, protože se maska trhala zrnem; teď je to plynulý pruh s leskem |
| B7 světlo L1 | Barva „foot“ (222, 232, 255) ≈ 7500 K, malý zdroj, jas difuzoru s bloomem | Bílá s modrým nádechem, ne sytě modrá skvrna (listy 2–3) |
| Odrazy kovu | Varianta c v celé hře: C++ `SetInteriorLighting` v interiéru Lumen odrazy do drsnosti 0,32 v ½ rozlišení; venku plné jako dřív | Rozhodnutí autora; RX 9070 1440p +0,6–1,4 ms GPU |

## Kola zkušebního úseku

1. **Příliš tmavé** (průměr 0,10, p10 0,00, B/R 0,71) proti etalonu (0,23–0,28 / 0,13 / 0,96–1,02). Za koncem
   chodby svítil okraj podlahy místnosti jako pruh.
   - Oprava: koncová stěna, světla L2/L3 3–4× silnější a neutrální.
2. **Tóny v rozsahu etalonu** (průměr 0,31–0,35, p10 0,07–0,16, B/R 0,86–0,95), ale vyšlapaná dráha se četla jako
   tmavé fleky.
   - Oprava: plynulá maska, světlejší a hladší.
3. Bez další výtky; stav listů. Tóny: 1 – 0,31 / p50 0,26; 2 – 0,35 / 0,31; 3 – 0,33 / 0,27; 4 – 0,32 / 0,28.

## Proti SC je stále jinak

1. Stěny a podlaha jsou světlejší a šedší než tmavé modrošedé plochy Aurory. Je to grafit Halcyonu pod silným
   světlem, ne chyba materiálu; poměr světlo / tón se doladí v kroku 6 na dílu.
2. Chybí decaly, ražba, šrouby funkčních krytů a perforace stěn: patří k dílu (krok 5), úsek je hrubá geometrie.
3. Patky L1 jsou hrubé pilulky, SC má osmiboký kryt s čočkou (krok 4–5).
4. Etalon v listu 4 (`ram_portal_3`) ukazuje rám v celku, ne zblízka. Lepší kotevní záběr laku zblízka chybí
   (`etalon.md` kap. 4).

## Kontrola P25 (lodě se nezměnily)

- Wayfarer, preset `p25_wayfarer` (sklad, technická chodba, kajuta, kajuta dozadu, kokpit dozadu, uvnitř chodby,
  pohled pilota), 1920 × 1080, `Tools/Review/shot_diff.py`.
- Snímky jsou v `Docs/Shots/p25_wayfarer/20261006_191132` (před) a `.../p25_wayfarer_refl_off/20261006_193005`,
  `.../p25_wayfarer/20261006_193041` (po).

| Srovnání | Průměr rozdílu (0–255) | Změněno > 12 úrovní |
|---|---:|---:|
| šum: před vs. před (2 běhy) | 0,26–2,01 | 0,02–2,32 % |
| před vs. po, odrazy vypnuté | 0,73–2,45 | 0,47–2,93 % |
| před vs. po, varianta c | 0,57–1,27 | 0,03–1,45 % |

- Rozdíly jsou jen na hranách: šum vyhlazování TSR a MegaLights, viz rozdílový obraz kajuty. Plochy materiálů se
  nezměnily.
- Varianta c na Wayfareru téměř nic nemění, protože jeho kovy mají drsnost nad 0,32. Změna je vidět jen na lemech
  kitu a na skle.
