# Wayfarer – výkresy exteriéru E-03 až E-08 (ostatní pohledy a detaily), 1. 10. 2026

**Zadání (autor 1. 10.):** styl E-01 schválen; tabulky na samostatný list (E-02); zbytek bodu 3 dossieru ve stejném
stylu – šest pohledů, materiálové zóny, desky konceptu B + C, funkční prvky, světla, decaly s kontrolou orientace na
obou bocích, detaily 1:10–1:20 (příď s kabinou, gondola s tryskou, rampa, hlavní podvozek, koncový držák zbraně),
kóty. Kit a pilot až podle schválených výkresů. Brief kritika: `2026-10-01_wayfarer_drawing_views/brief.md`.

**Výsledek** (`ArtSource/Ships/Wayfarer/Design/Drawings/`, A0 200 dpi, vektorově `Saved/Drawings/*.pdf`):

| List | Obsah | Měřítko |
|---|---|---|
| E-03 | shora: hřbet, zkosení (desky pásu S, podélník, žebra), křídla s náběžnou hranou a klapkou, gondoly, kabina | 1:30 |
| E-04 | zespodu: břicho, desky pásu K, podvozek, raketnice, břišní pás světel | 1:30 |
| E-05 | zezadu (zadní stěna s rampou, jejím rámem a písty, trysky, zadní nápisy) a zepředu (čelo, kabina, sání) | 1:20 |
| E-06 | levobok: pohled A desky a materiály, pohled B prvky; tabulka kontroly nápisů levé strany | 1:30 |
| E-07 | detaily B příď s kabinou 1:20, C zadní stěna s rampou 1:10, F gondola shora 1:20 (z boku E-01 detail A) | |
| E-08 | detail D hlavní podvozek (z boku a zezadu 1:5 s částmi podle `hs_gear`, zespodu 1:10), E držák zbraně 1:10 s řezem A–A 1:5 | |

Pohledy počítá `Tools/Design/exterior_views.py` z týchž dat jako pravobok; listy skládá
`Tools/Design/draw_exterior_views.py`. Test `test_exterior_drawing.py` (přes 100 kontrol): každý pohled kreslí přesně
prvky, které model v pohledu má, a každý popisuje; každý štítek pohledu v datech má geometrii; detaily popisují své
klíčové díly; nápisy levoboku se čtou nahoru.

## Co nové pohledy našly (opraveno)

- **Sklo kabiny na E-01 bylo z boku o 35 cm níž, než je postavené.** Stavba dělá sklo jen tam, kde je trup uvnitř
  bočního i horního obrysu kabiny; kde je trup širší než horní obrys (x 15,4–17,6), končí sklo výš na rameni.
  Model to teď počítá stejně (spodní hrana 3,115 / 3,023 / 2,641 / 2,320 / 1,999 m proti naměřeným na postavené
  kabině 3,099 / 2,996 / 2,615 / 2,294 / 1,962 m). Těsnění Z-SEAL-CANOPY, pás světel L-HULL-RUN-CANOPY na něm
  a výřezy desek pásu S tím sedí na skutečnou hranu skla (dřív by pás vedl přes lak).
- Výšková značka ležela přes text úrovně (E-01 i E-06): značka je teď na vnějším konci čáry.

## Otázka pro autora

- Schválená změna P-HULL (plášť paint → gunmetal, rám konceptu B + C) udělá **celou střechu a břicho tmavé**:
  desky jsou jen na bocích a zkoseních (pásy K, L, U, S), na střeše jsou jen postavené světlé pláty P-B-04/16/17.
  Na E-03 a E-04 je to vidět. Varianty: (a) nechat (tmavý hřbet jako u průmyslového tahouna), (b) desky i na
  střechu (pás „R“ mezi zkoseními), (c) střecha v laku, gunmetal jen rám a spodek.

## Kola kritika

| Kolo | Verdikt | Skóre | Průměr |
|---|---|---|---|
| 1 | FAIL | 6 / 6 / 7 / 7 / 6 / 6 | 6,3 (2× musí: záblesk ploutve na ose v čelních pohledech; detaily D a E bez obsahu a kót) |
| 2 | PASS | 7 / 7 / 8 / 7 / 7 / 7 | 7,2 (žádné „musí“) |

Plné zprávy: `2026-10-01_wayfarer_drawing_views/round1/critic.md`, `round2/critic.md` (brief kola 2 `brief_round2.md`).

### Kolo 1 → reakce
- **Musí:** záblesk ploutve L-STROBE-FIN kreslen na ose – kotva prvku se dvěma kopiemi byla těžiště mezi nimi; teď
  ukazuje na jednu kopii (špička ploutve y 3,81). Totéž hlídá kotva v čelních pohledech (prvky na ose ukazují na
  pravou polovinu, aby se odkazy nesbíhaly do jedné svislice).
- **Musí:** detaily D a E přesunuty na nový list E-08 s obsahem: hlavní podvozek z boku a zezadu v 1:5 s 15
  číslovanými částmi tak, jak je staví `hs_gear.leg` (třmen, čep, válec tlumiče, ucpávka, píst, nůžky, objímka,
  vzpěra, hydraulika, dvířka s výstražným pruhem, kotník, patka, podrážka, žebra; za dvířky čárkovaně), zespodu
  v 1:10 s nápisy u šachty (D-H-27, D-H-52), kóty (patka 1,20 × 0,80 × 0,15, noha 0,40, výšky) a seznam částí;
  držák zbraně shora v 1:10 s řetězovou kótou objímek (D-H-47 ve výřezu) a řez A–A 1:5: zbraň Ø 0,36 leží osou
  0,15 m za koncem křídla a zasahuje do něj 3 cm, objímky Ø 0,42 ji drží na konci křídla. Detaily na E-07 mají kóty
  (kabina, spára a rám rampy, rozteč pístů).
- Záďový kryt: P-B-01 a Z-B-02 se kreslí přes střechu jen tam, kde střecha převyšuje 2,2 m; šikmá hrana je
  vrstevnice 2,2 m na klesající zádi – vysvětleno poznámkou na E-03.
- Odstraněné díly: červený čárkovaný obrys bez výplně a malý křížek v rohu (nový díl na témže místě je čitelný);
  svislé odkazy od sebe nejméně 1,5 mm.
- Hřbet: poznámka na E-03 a otázka pro autora (nechat tmavý, desky i na hřbet, nebo hřbet v laku).
- Legenda: poznámky na E-05/E-06/E-07/E-08 odkazují na E-01, E-03/E-04 ji opakují.
- **Rám rampy F-RAMP-FRAME** doplněn do dat návrhu (U z profilu podélníku XK-LONGERON kolem spáry D-T-05, nese
  závěsy a písty) a kreslen zezadu a v detailu C.
- Skryté desky (P-S-K04 nad podvozkem, desky za křídlem na levoboku) mají tečkovaný odkaz; popisky desek bez „+“.
- Drobnosti: kóta délky pod číslicemi měřítka, obě čela v 1:20, detail F „Gondola shora“, velké nápisy jejich
  obsahem („výstraha rampy“), logo D-LOGO-L na levoboku v nové poloze (model nepoužil změnu polohy u levobočních
  kopií – opraveno, stará poloha čárkovaně).

### Kolo 2 → opravy po posledním kole (levné, bez dalšího kola kritika)
- Zbraň v půdorysu (E-03, E-04, detail E) podle válců stavby: tělo Ø 0,36, hlaveň Ø 0,11, ústí Ø 0,16 (dřív kužel
  z obrysu layoutu).
- Detail D: části za dvířky nohy (třmen, čep, válec, vzpěra, hydraulika) čárkovaně přes dvířka.
- Zepředu příďové bloky RCS (F-RCS-01/02 Δ jako profil z boku nosu, F-RCS-03/04 × odstraněné); obecně funkční prvky
  u přídě a zádi v čelních pohledech.
- Podvozek zespodu jako pryžová podrážka patky (MZ-RUBBER v legendě), detail „zespodu: patka a nápisy u nohy“.
- Detail B: řádek, co měří kóty; řez A–A: přesah zbraně 0,03 m i objímky 0,06 m do konce křídla.
- Odstraněné desky (P-B ×) mají křížek v rohu jako ostatní odstraněné díly.

### Neopraveno (vědomě)
- Svazky odkazů u gondoly (E-03) a u F-GRILLE-01 (E-06 B): hustota dat v tom místě; řešení je další výřez, až to
  bude potřeba (E-01 detail A ukazuje gondolu, E-07 F shora).
- F-FIN Δ z boku: výplň ploutve s náběžnou hranou a jádrem (tmavé díly receptu) jako na E-01; zezadu je vidět jen
  box v laku 2. Sjednotit při stavbě kitu ploutve.
- E-05 bez legendy (odkaz na E-01), E-06 bez celkové délkové kóty (je na E-01 a E-03).
- D-H-34/D-H-35 přes D-HAZARDRAMP na zadní stěně: věc dat receptu, opraví se s kitem zadní stěny.
- Hřbet: otázka pro autora (výše).
