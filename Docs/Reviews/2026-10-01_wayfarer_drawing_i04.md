# Wayfarer – vzorový výkres interiéru I-04 (kajuta), 1. 10. 2026

**Zadání (autor 1. 10., druhá session):** dokončit Wayfarer Design Dossier, bod 4 (interiér) a bod 6 (koncepty), ve
stejném stylu a principu jako výkresy exteriéru E-01 až E-08: jeden zdroj dat, test „výkres = data“, kritik s briefem
pro technické výkresy. Bod 4: půdorys v mřížce kitu s ID dílů, rozvinuté pohledy stěn každé místnosti, plány stropů,
průřezy s kapslí postavy, plán nápisů a decalů, plán světel, rozpisy dveří, nábytku a komponent, účel každého
objektu. **Nejdřív jeden vzorový list interiéru ke schválení stylu**, pak zbytek (bod 4 i bod 6).

**Výsledek:** `ArtSource/Ships/Wayfarer/Design/Drawings/Wayfarer_I04_cabin.png` (A0, 200 dpi; vektorově
`Saved/Drawings/Wayfarer_I04_cabin.pdf`), sidecar `Wayfarer_I04_cabin.json` (ID nakreslená a popsaná po pohledech,
tabulky, otisky dat, kontrola dat). Kreslí `Tools/Design/draw_interior_sheet.py`; test
`Tools/Tests/test_interior_drawing.py` (v `Test.ps1` i CI, bez FBX).

## Jak list vzniká (jeden zdroj dat)

- **Geometrie je postavená loď, ne obdélníky z layoutu:** `fbx_mesh.py` čte binární FBX z LFS v čistém Pythonu, díly
  kitu se kladou přesně jako ve hře (`kit_layout.layout_parts`), interiér a trup lodi z jejich FBX. `mesh_draw.py`
  kreslí vektorově: výplň = odstín materiálu, hrany ohybů a obrysy, malířův algoritmus, řez rovinou tlustou čarou.
- **Prvky a ID z dat** (`interior_model.py`): díly kitu z `interior.kit_modules`, nábytek = díl kitu, který staví
  objekt layoutu, komponenty a dveře z layoutu, světla ze socketů dílů tak, jak je hra rozsvítí (`kit_rooms.py`
  přes ast: násobky, stíny, „jen interiér“, zóna kajuty), vlastní světla lodi z exportu, decaly dílů z FBX
  (poznané podle UV v knihovně), promítané D-INT ze setupu.
- **ID a české účely** v `Design/Wayfarer_interior_design.json` (`ids`, `kit_purpose`, `doors`, `components`,
  `decal_items`, `purposes`, `review_notes`), navázané na data stavby klíčem, který test ověřuje; recept ani layout
  se neměnily (zápis by zneplatnil všechny listy exteriéru, WORKFLOW 9.6 fh). Schéma ID: `CAB-W-L1` stěna levobok
  od zádi, `CAB-B-A/F` přepážky, `CAB-C-n` strop, `CAB-FL-n` podlaha, `CAB-U-…` nábytek, `CAB-M-…` komponenta,
  `DR-…` dveře, světlo/decal = ID dílu + `/` + socket nebo položka.

## Co list ukazuje

Půdorys v řezu 1,20 m s mřížkou kitu 0,3 m, kótami (délka mezi přepážkami 4,79, šířka mezi líci 3,80, dveře, nábytek)
a klíči pohledů 1–4; strop zespodu se světly (Down + Halo jako jeden symbol), žebříkem, potrubím a žebry; rozvinuté
stěny 1–4 s moduly, nábytkem, decaly a světly; řez R1 (x 12,50) s kapslí 0,56 × 1,80 m, průchodem 1,66 m, světlou
výškou 2,30, zónami nad stropem (0,81 m) a pod podlahou (0,63 m) a šířkou trupu; legenda, klíčový plán, tabulky
(díly kitu, účel dílů, nábytek / dveře / komponenty s umístěním, světla po socketech, decaly), souhrn světel
a výkon, kontrola dat, razítko.

## Co list našel v datech (kontrola dat, k rozhodnutí autora)

- **CAB-M-LIFESUP** (podpora života, layout pod lůžkem z −0,55 … −0,05) leží zčásti **mimo trup** (zkosení břicha
  na levoboku) a ve hře není postavená (jen sání v podstavci lůžka a zpětné sání v CAB-W-L1).
- **D-INT-SEC06** (číslo úseku 06): komentář v setupu říká „nad lůžkem, x 13,09“, decal leží v x 14,99 na CAB-W-L5.
- **DR-CAB-HYG:** kit kreslí výstražný pruh a madlo na zadní hraně křídla, ale těsnění u zadní zárubně – jedno je
  opačně (výkres bere směr otevírání k přídi).
- Nábytek z kitu proti layoutu: skříň, buňka, výdejník a lůžko jsou včetně madel a přesahů hlubší (až 233 mm
  u výdejníku se sedátkem) a vyšší (lůžko s policemi 1,72 m proti 0,7 m v layoutu).
- Světla: 42 na 18,5 m² = 2,27 /m² (pravidlo kitu pro obytné 1,2–1,8 /m²) – většinu tvoří lišty stěn.
- Šířka trupu v řezu 4,67 m (s deskami a lištami) proti 4,60 v obrysu layoutu (kritik, ověřovací kolo).

## Kola kritika (brief `2026-10-01_wayfarer_drawing_i04/brief.md`, kategorie jako u E-01)

| Kolo | Verdikt | Skóre (čitelnost / úplnost / data / konvence / stavebnost / srozumitelnost) | Průměr |
|---|---|---|---|
| 1 | PASS | 7 / 8 / 7 / 6 / 7 / 8 | 7,2 (žádné „musí“) |
| ověření | 14 z 15 opraveno | 7 / 9 / 8 / 7 / 8 / 8 | 7,8 |

Plné zprávy: `round1/critic.md`, `verify/critic.md` (brief `brief_verify.md`).

### Kolo 1 → reakce (všechny body opravené kromě 9, to je otázka pro autora)
1. Uříznutý stav DR-TEC-CAB: sloupec stavu širší, 3 řádky.
2. Navržená křídla DR-TEC-CAB: modře čárkovaně v zasunuté poloze v půdorysu i v pohledu 4; v datech návrhu
   `open`, `side` (po líci ze strany chodby: líc 3 cm + přepážka 4 cm kapsu neunesou), výška 2,05.
3. Kóty: půdorys (furniture a délka podél obou boků, šířka a dveře u obou čel, dveře buňky), řez (šířka mezi líci
   obložení, šířka trupu). Řetězec slučuje body blíž než 15 mm (skříň a buňka se dotýkají).
4. D-INT-SEC06: účel podle polohy z dat; rozpor s komentářem setupu v kontrole dat (`review_notes`).
5. Vzorec intenzity se skládá z dat (`SOCKET_SCALE`, zóna místnosti, `SHIP_LIGHT_SCALE`) s příkladem Wash 12L.
6. Rozpis nábytku má umístění (střed zadní hrany, na podlaze, čelem k …).
7. Nábytek před čelní stěnou v pohledech 2 a 4: šedé štítky „před stěnou“ a (po ověření) světlejší výplň.
8. Strop: štítky kabelového žebříku, potrubí, žeber a římsy (konstanty `kit_batch2.services` přes ast).
9. Měřítko a formát (1:20 na A0, nebo 1:10 / A1): **rozhodne autor** při schválení stylu.
Drobnosti: text „pod podlahou“ vedle odkazu; štítky modulů na bílém poli; zalomené buňky tabulek; „pod podlahou
nemodelováno: jen trup“ v řezu; legenda doplněná o materiály lodi, trup v řezu, cd a MegaLights; výškové úrovně u
každého pohledu; mřížka tmavší plnou čarou.

### Ověřovací kolo → opravy po něm (levné, bez dalšího kola)
- CAB-W-R1 přeškrtnutý odkazy: štítky modulů na širším bílém poli, odkazy se o ně přeruší.
- Kóty pod odkazy nábytku: odkaz nábytku v půdorysu míří do třetiny jeho délky, ne do středu.
- Splývající odkazy: žebřík a potrubí ve stropě v jiných x, strop a podlaha v řezu v jiných y.
- „DR-TEC-CAB 2 křídla“.
- Nábytek před čelní stěnou světlejší výplní (`mesh_draw.draw(fade=...)`), položka v legendě.
- Decaly dílů kitu: výplň jen z geometrie (vidět jen tam, kde nic nestojí před nimi), přes ně čárkovaný rámeček
  polohy; legenda to říká.

### Neopraveno (vědomě)
- Výška otvorů dveří jako kóta: v datech stavby není (jen v kódu kitu, `DOOR_H`); křídla DR-TEC-CAB nesou výšku
  v datech návrhu, otvory zatím ne.
- Základní cd dílů kitu na listu nejsou (jsou v manifestu); tabulka má výsledné hodnoty a vzorec s příkladem.
- Mřížka 0,3 m zaniká v celkovém náhledu (na zoomu je čitelná).

## Otázky pro autora
1. **Styl** listu interiéru (vzor pro I-01 až I-09).
2. **Měřítko a formát** listu místnosti: 1:20 na A0 (jako teď), 1:10 na A0, nebo 1:20 na A1.
3. Dveře: **DR-TEC-CAB** dvoukřídlé posuvné po líci ze strany chodby (návrh); DR-CAB-CPT bez křídla; DR-HLD-TEC
   posuvné do kapsy přepážky k pravoboku (návrh, list nákladu).
4. **Podpora života** pod lůžkem leží zčásti mimo trup – posunout do osy lodi, zmenšit, nebo jinam?
5. Číslo úseku 06: nad lůžko (x 13,09, jak říká komentář), nebo nechat na CAB-W-L5?
