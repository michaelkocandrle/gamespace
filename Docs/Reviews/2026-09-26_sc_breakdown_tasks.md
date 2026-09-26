# Úkoly z rozboru lodí SC (26. 9. 2026)

Rozbor: `starcitizenreference/ShipDetailing_VideoNotes.md` (Markom3D: C2 Hercules, Argo MOLE). Tři systémové
úkoly z něj plus audit zdrojů. Podle zadání autora bez kritika, stačí snímky před a po:
`2026-09-26_sc_breakdown_tasks/`.

## 1. Světla u svítidel (desítky malých světel)

- `Tools/Blender/hs_fixture_lights.py`, recept `interior.fixture_lights`. Pro každý ostrov svítícího
  materiálu (`int_light` teplé lampy, `int_glow` modré lišty, `int_accent_glow` oranžové linky):
  - změří délku ostrovu (hlavní osa) a každých 0,9 m postaví bodové světlo (dosah 1,6 m, bez stínu, specular 0,2);
  - světlo odsadí na otevřenou stranu (paprsky do interiéru), nejvýš 12 cm od montážní plochy.
- Wayfarer: **88 nových světel** (38 lamp, 37 modrých lišt, 13 oranžových linek), celkem 129 místo 41. C2 má
  ~790 světel, v přepočtu na plochu jsme teď ve stejném řádu.
- Světla dostanou jména `fix_N`. `ASpaceshipPawn::UpdateViewCollection` je zapíná, jen když je kamera uvnitř
  lodi: v kokpitu (vlastní kamery pawnu) nebo v obálce interiéru (chodící postava, volná kamera snímků).
  - Zvenku by bez stínů svítila přes trup a jejich objemy by pokryly celou loď na obrazovce.
  - Blízký chase záběr bez vypínání stál až 12 ms.
- Výkon z oka pilota (`stat gpu`, 3 km): 13,73 → **14,87 ms (+1,1 ms)**, z toho `Lights` 1,25 → 2,26 ms.
  Snímky exteriéru mají stejné FPS jako předtím (66–70).
- Listy `01`–`04`: podél podlahy a stropu nákladového prostoru jsou modré a teplé ostrůvky světla, schody
  do kokpitu jsou osvětlené.

## 2. Velké karty špíny

- Atlas `Tools/Assets/generate_grime_textures.py` → `ArtSource/Ships/Shared/Decals/Grime/` (2048 px,
  2 × 2, procedurální, bez cizí licence). Buňky:
  - `streaks` – stékání;
  - `soot` – saze za tryskou;
  - `smear` – šmouhy;
  - `rim` – nános u hrany s kapkami.

  Zdrojová hrana je nahoře, ostatní tři hrany mizí do ztracena.
- Master `M_Ship_MeshDecalGrime`: jen barva a drsnost, bez normály, takže detail panelů pod kartou zůstane.
  Neprůhlednost = alfa × krytí vertex colour × `DecalOpacity` (0,8).
- Pravidlo `decals.grime` v `hs_decals.py` (`Placer.card`): paprsek jako u položek, pak mřížka 8 cm
  promítnutá na povrch podél normály (karta obtéká gondolu). Buňky mimo povrch vypadnou a jejich okolí dostane
  alfu 0 (měkký okraj). `up` = odkud špína přichází.
- Wayfarer: **22 karet**:
  - saze na zádi gondol;
  - stékání na ploutvích a křídlech;
  - šmouhy u kořene křídla, nad nákladovým prostorem a na přídi gondol;
  - nános u podvozku.
- Listy `05`–`07`. Z chase kamery je efekt jemný, stejně jako v SC.

## 3. Variace drsnosti a opotřebení

- Lak trupu: `EdgeWear` 0,8 → **0,15** (SC nemá otřené hrany). Nový parametr `ClearCoatRoughVariation` 0,12:
  lesk clear coatu se mění s grunge a ve špíně zmatní, šmouhy jsou vidět v odrazech.
- Interiér (stěny, panely, podlaha, lišty, grafit desky, rámy): `GrungeTileCm` 180 → **45**,
  `RoughVariation` **0,35**. Skvrny 180 cm na plochách velikosti kokpitu nebyly vidět (kritik: „grafit bez
  mikrostruktury“).

## 4. Audit zdrojů

Tabulka v `starcitizenreference/ShipDetailing_VideoNotes.md`, kapitola 8. Vyřešeno bez cizích assetů:
- textury špíny jsou procedurální;
- variace drsnosti používá existující grunge texturu v jiném měřítku;
- světla jsou kód.

Zbývá:
- tištěné rámečky skupin a oblouky stupnic v atlasu;
- emisní štítky;
- trim sheet interiéru (krok 3, kit);
- lokální volumetrická mlha (ověřit cenu).

Kandidáti CC0 pro jemnější škrábance: ambientCG Scratches / Smudges.
