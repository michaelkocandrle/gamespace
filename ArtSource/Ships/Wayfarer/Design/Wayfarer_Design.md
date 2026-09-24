# Wayfarer – návrh lodi v1 (schválen 24. 9. 2026)

**Halcyon Freightworks Wayfarer**, malá multirole loď pro jednoho pilota. Nahrazuje Vanguard jako
hráčova loď. Stav: **návrh v1 schválen autorem 24. 9. 2026 se všemi navrženými výchozími odpověďmi (kap. 6); další krok je 3D model.** Přehled a dossier: `python Tools/Design/build_ship_matrix.py`.

Soubory:

| Co | Kde |
| --- | --- |
| Specifikace ve tvaru Ship Matrix | `../Wayfarer_spec.json` |
| Jediný zdroj pravdy (místnosti, objekty, dveře, obrysy exteriéru) | `Wayfarer_layout.json` |
| Výkresy (generované, nikdy ručně) | `Wayfarer_exterior.png`, `Wayfarer_deck_main.png`, `Wayfarer_cutaway.png` |
| Siluety pro koncepty a pro kontrolu 3D modelu | `guides/Wayfarer_mask_*.png`, `guides/guide_*.png` |
| Koncepty z Higgsfieldu a prompty | `../Concept/` (`prompt.txt`) |
| Referenční lodě ze Ship Matrix | `starcitizenreference/ship_matrix/small_multirole.md` |

## 1. Vize

První vlastní domov hráče ve vesmíru. Do lodi se **vchází po zadní rampě** ze země, projde se
nákladem, kolem komponent, kajutou až do prosklené kabiny a **usedne se do křesla zezadu**. Je to
malá loď, ale všechno v ní dává smysl: náklad na obchod, lůžko na odhlášení, skříň na skafandr,
komponenty, které jde vyměnit, a dost zbraní na obranu.

## 2. Parametry (Ship Matrix) proti referencím

Referenční sada: 8 lodí ze Ship Matrix ve stavu *flight-ready*, třída malá multirole / starter
(Avenger Titan, Mustang Alpha, Aurora MR, 100i, Cutter, C8X Pisces, Nomad, Syulen). Staženo skriptem
`Tools/Design/fetch_ship_matrix.py`.

| Hodnota | Wayfarer | medián referencí | rozsah referencí | poznámka |
| --- | --- | --- | --- | --- |
| Délka | 21,5 m | 19,5 m | 16–25 m | o 2 m delší kvůli průchozímu interiéru |
| Šířka | 14,7 m | 15,5 m | 8,75–28 m | krátká křídla, zbraně na koncích |
| Výška | 5,6 m | 7,25 m | 4,5–16 m | nízká, s podvozkem venku |
| Hmotnost | 52 t | 47 t | 25–216 t | |
| Náklad | 8 SCU | 4 SCU | 2–24 SCU | jako Avenger Titan |
| Posádka | 1 | 1 | 1 | jedno lůžko |
| SCM / AB | 225 / 1 200 m/s | 224 / 1 197 m/s | 180–262 / 1 010–1 425 | |
| Pitch / yaw / roll | 55 / 48 / 150 °/s | 56 / 49,5 / 143,5 °/s | | |

Komponenty (všechny S1, jako u referencí): reaktor, 2 chladiče, generátor štítů, kvantový pohon,
podpora života, radar a počítač. Zbraně: 2× S3 na koncích křídel, 2 raketnice S2 pod křídly.
Rozměry měří kreslicí skript přímo z obrysů (`SHIP_SHEETS`) a musí se rovnat specifikaci.

## 3. Uspořádání (jedna paluba, podlaha 0 m, strop 2,3 m)

Od zádě k přídi (x v metrech od zádě):

1. **Zadní rampa** (x 0–1): sklápí se na zem pod úhlem 22°. Ovládá ji pilot z levé konzole nebo
   hráč z mobiGlasu. **Žádná klávesnice u dveří.**
2. **Nákladový prostor** (x 1–8,2): mřížka 4 × 2 SCU u pravoboku, podél levoboku volná ulička
   1,25 m. U rampy hydraulika a držák ručního tažného paprsku. Pod podlahou kvantový pohon a nádrž
   kvantového paliva.
3. **Technická chodba** (x 8,2–10,4): po stranách přístupné komponenty jako v SC, mezi nimi 2,1 m
   průchodu. Vlevo reaktor a chladič, vpravo generátor štítů a chladič.
4. **Kajuta** (x 10,4–15,2): lůžko u levoboku (pod ním podpora života), vpravo skříň na skafandr
   a zbraň, hygienická buňka a výdejník jídla a vody.
5. **Kokpit** (x 15,2–19,4, podlaha o schod výš): křeslo uprostřed, levá a pravá konzole
   s fyzickými přepínači, přístrojová deska se třemi MFD a HUD. Pod podlahou avionika.

### Pohyb hráče

- Nástup: ze země po rampě → uličkou podél nákladu → technická chodba → kajuta → schod → za křeslo
  → animace usednutí. Celá cesta je rovná, bez slepých uliček.
- Šířky: dveře 1,0–1,1 m, ulička 1,25 m (kapsle postavy má průměr 0,84 m).
- Výstup ze sedadla zpět za křeslo; z lodi jen rampou (zatím bez nouzového výstupu kabinou).

## 4. Designový jazyk

**Exteriér:** dlouhý trup s tlakovým prostorem, vpředu vyvýšená prosklená kabina. Krátká šípová
křídla nesou nádrže vodíku a na koncích zbraně. Dvě motorové gondoly jsou u kořene křídel a na každé
je malá ploutev. Halcyon Freightworks je „pracovní“ značka: teplá lomená bílá a gunmetal, oranžové
pruhy (`0.85, 0.34, 0.06`), servisní poklopy a nápisy, lehké opotřebení hran. Styl SC, ale vlastní
tvar: podobnost s konkrétní lodí SC nechceme.

**Interiér:** teplá architektura osvětlená lištami, tmavý základ, studené hologramové UI jen
v kokpitu (art direction ze skillu `asset-sources`). Komponenty za mřížemi s popisky ve stylu decalů,
ať je jasné, co je co.

## 5. Jak návrh vznikl (postup, opakovatelný pro každou loď)

1. **Reference:** `fetch_ship_matrix.py` stáhl celou Ship Matrix (255 lodí) a pro zvolenou třídu
   vytvořil tabulku, medián a obrázky (`starcitizenreference/ship_matrix/small_multirole.*`).
   Obrázky CIG jsou jen ke studiu, **nikdy nejdou do AI generátoru**.
2. **Čísla:** specifikace vychází z mediánu a odchylky jsou vysvětlené (tabulka v kap. 2).
3. **Layout JSON:** místnosti, objekty s účelem, dveře a obrysy exteriéru ve třech pohledech.
4. **Výkresy:** `python Tools/Design/draw_ship_design.py ArtSource/Ships/Wayfarer/Design/Wayfarer_layout.json`
   nakreslí exteriér, palubu a řez a uloží masky siluet.
5. **Kontrola konzistence výkresu:** `silhouette_compare.py views` na maskách. Bok, shora a zepředu
   k sobě sedí (uzávěr 0,0 %, symetrie 0,99, rozměry proti spec do 0,3 %).
6. **Koncepty:** vodítka z masek (`silhouette_compare.py guide`) → Higgsfield (Nano Banana Pro).
   Nejdřív bok ve dvou stylových variantách, lepší z nich je stylový vzor pro pohledy shora,
   zepředu a 3/4. Každý pohled se měří proti masce a prohlíží se.
7. **Schválení autorem** → teprve pak 3D (multi-image to 3D nebo stavba po dílech, kontrola
   siluety proti týmž maskám).

## 6. Rozhodnutí autora (24. 9. 2026: „schvaluju všechno“)

Platí navržené výchozí odpovědi: Wayfarer od Halcyon Freightworks, styl A, 8 SCU a 21,5 m, hygienická buňka ano, výstup jen rampou, zbraně 2× S3 + 2 raketnice S2. Před 3D: rozpětí bere se z výkresu (koncept shora je o 8 % širší), gondoly bez lopatek ventilátoru.

Původní otázky:

1. **Jméno a výrobce:** Wayfarer od Halcyon Freightworks (stejná značka jako Steadfast, rodinný
   vzhled)? Nebo jiné jméno či vlastní značka?
2. **Vzhled:** která stylová varianta boku (A čistší bílá, B hrubší béžová) a sedí koncepty?
3. **Náklad 8 SCU** za cenu delší lodi (21,5 m), nebo menší 4 SCU a kratší loď kolem 19 m?
4. **Hygienická buňka** v tak malé lodi (reference ji většinou nemají), nebo místo ní větší skříň
   či místo na zbraně?
5. **Nouzový výstup** otevřením kabiny, nebo jen rampa?
6. **Zbraně:** 2× S3 + rakety stačí, nebo přidat bradovou zbraň S2 pod nos?
