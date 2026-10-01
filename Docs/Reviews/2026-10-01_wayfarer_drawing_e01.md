# Wayfarer – vzorový technický výkres E-01 (exteriér, pravobok), 1. 10. 2026

**Zadání (autor 1. 10.):** dossier body 3, 4 a 6 jako detailní profesionální výkresy z týchž dat, ze kterých se loď
staví; každý díl, decal a světlo s ID shodným s daty, test souladu, nepostavené prvky odlišené jako návrh. Nejdřív
jeden vzorový list (exteriér pravobok s deskami podle konceptu B + C, materiály, funkční prvky, světla a decaly) ke
schválení stylu; kritik s briefem pro technické výkresy (`2026-10-01_wayfarer_drawing_e01/brief.md`).

**Výsledek:** `ArtSource/Ships/Wayfarer/Design/Drawings/Wayfarer_E01_starboard.png` (A0, 200 dpi, 9362 × 6622 px;
vektorově `Saved/Drawings/Wayfarer_E01_starboard.pdf`), seznam nakreslených ID `Wayfarer_E01_starboard.json`.
Kreslí `Tools/Design/draw_exterior_sheet.py` z modelu `Tools/Design/exterior_model.py`; data stavby s ID
(`assign_exterior_ids.py`: 230 prvků v receptu a setupu), data návrhu `Design/Wayfarer_exterior_design.json`;
test `Tools/Tests/test_exterior_drawing.py` (66 kontrol, v `Test.ps1` i CI).

## Kola kritika (brief: čitelnost, úplnost, soulad s daty, konvence, návrh povrchu, srozumitelnost)

| Kolo | Verdikt | Skóre | Průměr |
|---|---|---|---|
| 1 | PASS | 6 / 8 / 8 / 6 / 7 / 7 | 7,0 |
| 2 | FAIL | 6 / 8 / 8 / 7 / 5 / 7 | 6,8 (1× musí: desky zakrývají postavené prvky) |
| 3 | PASS | 7 / 8 / 8 / 7 / 6 / 8 | 7,3 |

Plné zprávy: `round1/critic.md`, `round2/critic.md`, `round3/critic.md`.

### Kolo 1 → reakce
- Písmo: ID desek 2,4 mm na bílé podložce, odkazy 2,5 mm, staničení 2,2 mm, tabulky 2,5 mm se zalamováním.
- L05–L07 pod raketnicí: ID se kreslí jen tam, kam se vejde (pól nedostupnosti), jinak odkazem.
- Křížení odkazů: jedna řada, kde se vejde, sloučení odkazů na stejné místo; od kola 3 lomené odkazy přes sběrnici.
- Stará poloha Z-B-03 červeně čárkovaně se šipkou; tabulka změn má sloupec „postaveno → návrh“.
- F-RCS-09: model počítá, kam paprsek z boku dopadne (nejbližší díl) – blok leží na gondole, v kontrole dat.
- Česky: účely postavených prvků v datech návrhu (`purpose`), test hlídá, že žádný nechybí.
- Razítko: Kreslil / Kontroloval / Schválil, List 1/1, jednotky, revize.
- Detail A: řetězová kóta gondoly a prstenců, úroveň špičky ploutve; řez R1 deska na rámu 1:5.
- Zbytkové desky: pravidlo minimální šířky 0,25 m (S04, U07, U11 odpadly, rám je vidět).
- Drobnosti: vzorek Δ v legendě, obdélníkový odkaz na detail A v pohledech A i B, metrová osa v A, vzor čísla
  panelu (D-R-PANEL-NUMBERS) na desce L10, logo D-LOGO-R přesunuto zpoza gondoly (změna), přesné hodnoty pásů.

### Kolo 2 → reakce
- **Musí:** desky 30–40 mm by zakryly postavené prvky na plášti. `panels.cut_hardware` vyřízne v deskách místo pro
  každý díl na boku trupu (okraj 40 mm; kontrola dat vypisuje každý výřez), světelné pásy jdou na rám (L-HULL-RUN-LOW
  na spodní podélník, L-HULL-RUN-CANOPY na těsnění kabiny). Test: žádný díl pod deskou bez výřezu.
- Tmavý nápis na tmavém rámu: D-H-59 světlým inkoustem (`xstl_inspect`); test „nápis × podklad“.
- Kontrola dat: jedna věta na ID, částečně skryté prvky s procentem, levobok (D-*-L čtou nahoru) uveden.
- Úroveň „+3,30 střecha kabiny, špička ploutve“, kóta „4,90 (zem … střecha kabiny)“, řez R2 těžký plát se šrouby,
  šrouby i u XK-PLATE (Ø 20 po 300 mm – doplněno do kitu), revize bez skóre kritika, D-HAZARDEXHAUST-R „gondola“.

### Kolo 3 → opravy po posledním kole (levné, bez dalšího kola kritika)
- Pruh Z-B-03 na spodní hraně desek pásu U pod nápisem (v pásu L by ho zakryl kořen křídla).
- Kořen křídla F-WING vyříznutý z desek a žeber: pás L v polích 03–10 je jen pod křídlem, rám je vidět.
- Vůle 40 mm mezi deskami a podélníky (pásy K, L, U, S upravené).
- D-H-57 GND POINT o 0,4 m dozadu (zvětšený blok F-RCS-02 by ho zakryl); test „nápis pod dílem“.
- Částečně skryté díly mají zakrytou část čárkovaně; tabulka F má umístění celých dílů.

### Neopraveno (vědomě, k rozhodnutí nebo na další listy)
- **Velikost písma pro tisk:** písmo má 2,5 mm (velikost fontu), výška verzálek je tedy ≈ 1,8 mm. Na monitoru se
  zoomem je list čitelný; pro tisk A0 podle ISO 3098 (verzálky 2,5 mm) by se tabulky musely přesunout na vlastní
  list. **Rozhodne autor při schválení stylu.**
- Šachta a dvířka hlavního podvozku na zkosení (pás K): geometrii má `hs_gear`; vyřeší list zespodu (E-03).
- Boční shluky pravidla D-R-PANEL-MARKS se na listu nekreslí (pravidla jsou jen v tabulce); shluk u přídě se
  překrývá s blokem F-RCS-01 – vyřeší se s kitem (návrh ruší boční rozsev D-R-COVERAGE, PANEL-MARKS zatím ne).
- Desky K a rám mají stejný materiál (gunmetal), rozliší je modrý obrys a šrouby; stínová hrana až s dalšími listy.
- Příčný řez trupem s pásy K/L/U/S (návrh kritika) patří na list řezů.

## Co návrh na listu mění proti postavené lodi (k posouzení autorem)
8 RCS podle specifikace (9 bloků navíc pryč, 4 bloky větší XK-RCS, nový pár na hřbetu gondol); plášť trupu
gunmetal, na něm desky P-S ve 4 pásech mezi žebry a podélníky; dvě zapuštěné šachty s mřížkou místo lepených mřížek;
oranžový pruh po celém boku; ploutve v sekundárním laku; záblesky na ploutvích a křídlech, přistávací a pracovní
světlo; hydraulika rampy; přesunuté logo, konektor a čtyři nápisy, které z boku dopadaly na gondolu, křídlo nebo
zbraň.
