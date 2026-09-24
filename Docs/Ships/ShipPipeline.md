# Loď: Higgsfield → Blender → Unreal

Postup pro první skutečnou loď místo placeholder krychle. Příklad jména lodi: **Example**
(nahraď svým, vždy jedno slovo s velkým písmenem, bez mezer a podtržítek).

Nástroje:
- `Tools/Blender/gamespace_ship_export.py` – Blender addon/skript: kontrola a export FBX.
- `Tools/Blender/tests/test_ship_export_core.py` – testy jeho kontrolní logiky (`python Tools/Blender/tests/test_ship_export_core.py`).

---

## 0. Rozhodnutí předem

| Otázka | Doporučení | Proč |
| --- | --- | --- |
| Velikost lodi | Malá stíhačka **12–16 m** dlouhá | Určuje kameru, přistání, kolize, pocit rychlosti. Změna později = přeladit spoustu čísel (viz kapitola 5). |
| Nanite | **Ano** pro trup | Není potřeba ručně dělat LODy, zvládne 100–300 tis. trojúhelníků. |
| Kokpit/sklo | **Samostatný mesh** `SM_Ship_Example_Canopy` bez Nanite | Nanite nepodporuje průhledné materiály. |
| Pohyblivé části (podvozek, klapky) | **Samostatné statické díly**, pohyb dělá kód | Podvozek (SC-2a): díl `SM_Ship_<Loď>_Gear` s nohami vymodelovanými ve stavu „vysunuto“. Loď ho při zasunutí posune do trupu (`GearStowTravelCm`) a skryje. Klapky zatím ne. |

---

## 1. Adresáře a pojmenování

### Zdrojová data (mimo Content, v gitu přes LFS)

```
ArtSource/
  Ships/
    Example/
      Concept/            obrázky pohledů (front/side/top/3-4), prompt.txt s promptem a nastavením
      Higgsfield/         surové GLB z Higgsfieldu, přesně jak přišly (nikdy needitovat)
      Meshy/<stažení>/    surový export z Meshy (FBX + PBR textury), přesně jak přišel (nikdy needitovat)
      Example_ai_build.json   recept „AI model → loď“ (kapitola 2B)
      Example.blend       výsledek receptu (nebo ručně/procedurálně stavěný model): z něj se exportuje
      Textures/           textury rozbalené z GLB a výstupy bake (PNG)
      Export/             výstup exportního skriptu: *.fbx + Example_manifest.json
```

`.blend`, `.glb`, `.fbx`, `.png` jdou přes Git LFS (`.gitattributes`); zálohy `*.blend1` jsou ignorované.

### Unreal (Content)

```
Content/Ships/
  Audio/                         (už existuje: SW_EngineLoop)
  Shared/
    Materials/                   M_Ship_Master (master materiál), MF_* funkce
    Textures/                    sdílené detaily, decaly, trim sheety
  Example/
    Meshes/                      SM_Ship_Example, SM_Ship_Example_Canopy
    Materials/                   MI_Ship_Example_Hull, MI_Ship_Example_Glass, MI_Ship_Example_Emissive
    Textures/                    T_Ship_Example_Hull_BC, _N, _ORM, _E
    Blueprints/                  BP_Ship_Example (potomek ASpaceshipPawn)
    VFX/                         NS_Ship_Example_EngineTrail
    Audio/                       zvuky specifické pro tuto loď
Content/Characters/              (později player character, stejná logika)
```

### Pojmenování

| Co | Vzor | Příklad |
| --- | --- | --- |
| Hlavní mesh (trup) | `SM_Ship_<Loď>` | `SM_Ship_Example` |
| Další díl | `SM_Ship_<Loď>_<Díl>` | `SM_Ship_Example_Canopy`, `SM_Ship_Example_Gear` |
| LOD (jen bez Nanite) | `SM_Ship_<Loď>[_<Díl>]_LOD<n>` | `SM_Ship_Example_LOD1` |
| Kolize (konvexní) | `UCX_<jméno meshe>_<NN>` | `UCX_SM_Ship_Example_00`, `_01` |
| Kolize box/koule/kapsle | `UBX_` / `USP_` / `UCP_` + totéž | `UBX_SM_Ship_Example_00` |
| Socket | `SOCKET_<Jméno>` (Empty, rodič = mesh) | `SOCKET_Cockpit`, `SOCKET_Engine_L` |
| Materiál (Blender = jméno slotu v UE) | `M_Ship_<Loď>_<Slot>` | `M_Ship_Example_Hull` |
| Instance materiálu (UE) | `MI_Ship_<Loď>_<Slot>` | `MI_Ship_Example_Hull` |
| Textury (UE) | `T_Ship_<Loď>_<Slot>_<mapa>` | `_BC` barva, `_N` normal, `_ORM` AO/Roughness/Metallic, `_E` emissive, `_M` maska |
| Referenční high-poly v Blenderu | `HIGH_<cokoli>` | `HIGH_Example` (skript ignoruje) |
| Blueprint | `BP_Ship_<Loď>` | |
| VFX / zvuk | `NS_…` / `SW_…`, `SC_…` | |

Blender při duplikaci přidává `.001` – skript to hlásí jako chybu, přejmenuj.

### Sockety, se kterými počítá kód

| Socket | K čemu |
| --- | --- |
| `SOCKET_Cockpit` | pozice kamery v kokpitu (dnes napevno `CockpitCamera` 90, 0, 15 cm) |
| `SOCKET_Engine_L`, `SOCKET_Engine_R` (nebo `SOCKET_EngineMain`) | trysky: plamen, zvuk; osa X socketu míří **dozadu ven z trysky** |
| `SOCKET_CameraTarget` (volitelné) | kam se dívá chase kamera, když střed lodi není vizuální těžiště |
| `SOCKET_Gear_Nose`, `SOCKET_Gear_L`, `SOCKET_Gear_R` | podrážky patek podvozku. Když leží přesně na spodku kolizního boxu, je `gear_extension_cm` = 0. Lodi bez dílu `_Gear` na ně kód dá zástupné nohy z válců (SC-2a). Import prefix `SOCKET_` zahodí, kód bere oba tvary. |
| `SOCKET_Exit` (později, s postavou) | kde se po výstupu z lodi objeví hráčova postava; osa X = směr, kterým se dívá |

---

## 2. Pipeline krok za krokem

### A. Koncept (před Higgsfieldem)

1. Vytvoř **2–4 konzistentní pohledy** na tutéž loď: bok, zepředu, shora, 3/4. Neutrální
   pozadí, rovnoměrné světlo, bez motion blur, bez dramatických stínů, celá loď v záběru.
2. Proč: Higgsfield staví mesh jen z toho, co je na obrázcích vidět. Z jednoho obrázku si
   záda a spodek lodi vymyslí (typicky rozteklé nebo prázdné).
3. Ulož do `ArtSource/Ships/Example/Concept/`, prompt a nastavení do `prompt.txt`.

### B. Higgsfield 3D

1. Použij **multi-image to 3D** (2–4 pohledy). Text-to-3D jen na rychlé skici.
2. Nastavení:
   - **Topology: triangle**, **počet trojúhelníků 200–300 tis.** – zdroj detailu (bude to `HIGH_`).
   - **PBR maps: zapnout** (metallic, roughness, normal). Bez nich má textura zapečené
     světlo a stíny a v Unrealu pod naším sluncem vypadá špatně.
   - Volitelně druhý běh **Topology: quad, ~30 tis.** – čistší základ pro herní mesh.
   - Rigging nepoužívat (funguje dobře jen pro humanoidy).
3. Stáhni GLB do `ArtSource/Ships/Example/Higgsfield/` a **neupravuj ho**.
4. Higgsfield má i addon pro Blender (Blender 5.1+), který výsledek vloží rovnou do scény.
   Výsledek je stejný jako přes GLB; GLB si ale stejně ulož jako zálohu zdroje.

### C. Blender: import a úklid

1. Nový soubor, ulož jako `ArtSource/Ships/Example/Example.blend`.
2. **Scene Properties > Units**: Unit System **Metric**, Unit Scale **1.0**, Length **Meters**.
3. **File > Import > glTF 2.0**, vyber GLB. V importu zapni **Merge Vertices**.
4. **File > External Data > Unpack Resources > Write files to current directory** – textury
   z GLB se vybalí vedle .blend; přesuň je do `Textures/`.
5. Outliner: pokud je mesh pod prázdným rodičem, vyber mesh, **Alt+P > Clear and Keep
   Transformation**, prázdného rodiče smaž. Přejmenuj mesh na `HIGH_Example`.
6. **Orientace**: nos lodi do **+X** (červená osa), vršek do **+Z**. Otáčej v Object Mode (R Z 90 …).
7. **Velikost**: N panel > Item > Dimensions > nastav X na cílovou délku (např. 14 m), Y a Z
   se nastaví proporcionálně (uzamkni poměr nebo dopočítej). AI modely přicházejí velké cca 1–2 m.
8. **Ctrl+A > All Transforms** (aplikovat rotaci, měřítko i polohu).
9. Úklid v Edit Mode (vše vybráno, A):
   - **Mesh > Clean Up > Merge by Distance** (0.0001 m)
   - **Mesh > Clean Up > Delete Loose**, **Degenerate Dissolve**
   - **Mesh > Normals > Recalculate Outside** (Shift+N)
   - **Select > Select All by Trait > Non Manifold** – ukáže díry a vnitřní plochy. Vnitřní
     smetí (plochy uvnitř trupu) smaž, díry v místech, která nejsou vidět, můžeš nechat.
10. Symetrie (pokud má být loď souměrná): v Edit Mode **Bisect** v rovině Y = 0, smaž polovinu
    −Y, přidej **Mirror modifier** (osa Y, Clipping). AI výstup nikdy není přesně souměrný.

### D. Herní mesh – vyber jednu cestu

**Cesta 1 – rychlá (Nanite, první iterace, doporučená na začátek)**
1. Duplikuj `HIGH_Example` (Shift+D, Esc), přejmenuj na `SM_Ship_Example`, `HIGH_` skryj.
2. **Decimate modifier**, Collapse, ratio tak, aby v horní liště (Statistics) bylo
   **100–150 tis. trojúhelníků**. Zapni *Symmetry* (osa Y), pokud je loď souměrná.
3. UV a textury z Higgsfieldu zůstávají – nic se nepeče. Apply modifier až před exportem
   (exporter ho aplikuje i sám).

**Cesta 2 – kvalitní (čisté plochy, vlastní UV, bake)**
1. Základ: quad výstup z Higgsfieldu, nebo duplikát `HIGH_` + **Remesh** (Voxel, velikost
   2–4 cm) + **Decimate > Planar** (5–10°) – pro hard-surface lodě dává rovné panely.
   Alternativa: ruční retopo, placený QuadRemesher.
2. Cíl: **30–80 tis. trojúhelníků** (bez Nanite), s Nanite klidně víc.
3. **Hrany a stínování**: pravý klik > **Shade Auto Smooth** (30°) a **Weighted Normal**
   modifier (Keep Sharp). Hard-surface pak nevypadá rozteklý.
4. **UV**: Edit Mode > **Select > Select Sharp Edges** (30°) > **UV > Mark Seam** >
   **UV > Unwrap** (nebo Smart UV Project, Island Margin 0.003) > **UV > Pack Islands**
   (Margin 0.005). Jedna UV mapa `UVMap`, bez překryvů.
5. **Bake** (Render Engine Cycles, GPU): vyber `HIGH_`, pak Ctrl+klik `SM_…` (aktivní),
   Bake panel > **Selected to Active**, **Extrusion** 0.02–0.05 m (nebo cage):
   - **Normal** (Tangent) → `T_Ship_Example_Hull_N.png`, 4096², 16 bit, Non-Color
   - **Diffuse**, jen Color → `_BC.png`, 4096², sRGB
   - **Roughness** → do zeleného kanálu ORM; metallic přes Emit trik → modrý; **AO** → červený
   - Emisivní části (trysky, světla) → vlastní slot `M_Ship_Example_Emissive` nebo `_E` maska

### E. Textury – pravidla

| Mapa | Formát v Blenderu | Unreal nastavení |
| --- | --- | --- |
| `_BC` Base Color | PNG 8 bit, sRGB | Default, sRGB **on** |
| `_N` Normal | PNG 16 bit | Normalmap, **Flip Green Channel on** (Blender i glTF používají OpenGL, Unreal DirectX) |
| `_ORM` (R AO, G Roughness, B Metallic) | PNG 8 bit, Non-Color | Masks (no sRGB), sRGB **off** |
| `_AO` Ambient Occlusion | PNG 8 bit, Non-Color | Masks (no sRGB), sRGB **off** |
| `_E` Emissive | PNG 8 bit | Default, sRGB on |

Tip: GLB „metallicRoughness“ textura má roughness v G a metallic v B – stejné rozložení jako
ORM, jde použít přímo (R je bez AO obvykle bílý).

**Okluze má vlastní mapu, ne červený kanál ORM** (20. 9. 2026). V receptu z AI modelu je R emisní
maska obrazovek (`Tools/Blender/build_ai_ship.py`, `surface_nodes`), takže je na trupu 1 a žádná
okluze v pečených texturách není. Dopeče ji:

```bash
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b   ArtSource/Ships/Example/Example.blend --python Tools/Blender/bake_ship_ao.py -- Example
```

Trvá ~30 s (4096², 16 vzorků, dosah paprsku 0,5 m – tedy spáry a greebly, ne špinavá loď). Peče se
z hotových meshů, ne z originálu: milion trojúhelníků nese všechny prohlubně a originál už v `.blend`
není. V setupu loďi se mapa přidá jako `"ao"` mezi textury a `M_Ship_PBR` ji použije na
`cavity_strength` (ztmavení laku ve spárách), `ao_strength` (výstup Ambient Occlusion) a jako masku
pro `wear_amount` (oddřený lak na exponovaných místech). Bez mapy je parametr bílý a materiál vypadá
jako předtím.

Rozlišení: trup 4096², malé díly 1024–2048². Rozměry vždy mocnina dvou.

### F. LODy

- **S Nanite: žádné LODy**, Unreal je řeší sám.
- **Bez Nanite**: duplikát herního meshe + Decimate: `_LOD1` 50 %, `_LOD2` 25 %, `_LOD3` 10 %
  trojúhelníků. Skript každý LOD exportuje do vlastního FBX; v Unrealu se přidá ve Static Mesh
  Editoru (LOD Settings > LOD Import > Import LOD Level n). Blender neumí FBX „LOD Group“,
  proto samostatné soubory.

### G. Kolize (UCX)

1. **Add > Mesh > Cube**, v Edit Mode tvaruj kolem trupu (jen posun/škálování vrcholů), nebo:
   vyber část herního meshe > Shift+D > P (Separate) > **Mesh > Convex Hull** > Decimate na
   **≤ 32 vrcholů**.
2. Každá kolize musí být **konvexní** (žádné prohlubně). Trup = 1 hull, každé křídlo = 1 hull,
   motory 1–2. Celkem **3–8 hullů**.
3. Pojmenuj `UCX_SM_Ship_Example_00`, `_01`, … Object Properties > Viewport Display >
   **Display As: Wire**, ať neruší.
4. Kolize **nesmí vyčnívat** z viditelného meshe (skript hlásí > 5 % délky).
5. `Ctrl+A > All Transforms` i na kolizích.

### H. Sockety

1. **Add > Empty > Arrows**, přejmenuj `SOCKET_Cockpit`, umísti do hlavy pilota, šipka X dopředu.
2. `SOCKET_Engine_L/R` do ústí trysek, šipka X **dozadu** (směr výtoku).
3. Vyber socket, pak Shift+klik trup (aktivní) > **Ctrl+P > Object (Keep Transform)**.

### I. Pivot (střed otáčení)

1. Po vytvoření kolizí klikni v panelu **Gamespace > Center on collision**: posune geometrii
   všech `SM_`, `UCX_` a socketů tak, že **střed obálky kolizí = počátek světa**. Počátky
   objektů zůstanou v 0, 0, 0.
2. Proč: loď se otáčí kolem počátku a kořenový kolizní box pawnu je na počátku vycentrovaný
   (kapitola 5).

### J. Materiály

Sloty na meshi pojmenuj `M_Ship_<Loď>_<Povrch>` (`_HullPaint`, `_Glass`, `_Emissive`, ...). Jméno
slotu se přenese do Unrealu. Materiály v Unrealu vytvoří import podle
`ArtSource/Ships/<Loď>/<Loď>_setup.json` (viz L3): instance `MI_Ship_<Loď>_*` ze dvou sdílených
masterů `/Game/Ships/Shared/Materials/M_Ship_Hull` (neprůhledný, Nanite; BaseColor, Metallic,
Roughness, EmissiveColor × EmissiveStrength) a `M_Ship_Glass` (průhledný, oboustranný; BaseColor,
Opacity, Roughness).

### K. Kontrola a export

1. Nainstaluj addon: **Edit > Preferences > Add-ons > Install from Disk** >
   `Tools/Blender/gamespace_ship_export.py` a zaškrtni ho. (Nebo otevři soubor v Text
   Editoru a **Run Script**.)
2. N panel > záložka **Gamespace**:
   - **Export folder**: `//Export` (= `ArtSource/Ships/Example/Export`)
   - **Validate ship** – výsledek v dolní liště a celý v Text Editoru, text `gamespace_ship_report`.
     ERROR musí být 0; WARN si přečti.
   - **Export FBX for Unreal** – při ERRORech export odmítne.
3. Z příkazové řádky (bez UI):
   ```
   blender -b ArtSource/Ships/Example/Example.blend --python Tools/Blender/gamespace_ship_export.py -- --out "//Export" --validate-only
   blender -b ArtSource/Ships/Example/Example.blend --python Tools/Blender/gamespace_ship_export.py -- --out "//Export"
   ```
4. Výstup: `SM_Ship_Example.fbx` (mesh + UCX + sockety), `SM_Ship_Example_Canopy.fbx`,
   případně `_LODn.fbx`, a `Example_manifest.json` (rozměry, počty, pozice socketů v cm pro
   Unreal, doporučené hodnoty pro pawn).

Co skript kontroluje: jednotky scény, jména, aplikované transformace, zrcadlení, počty
trojúhelníků, UV, prázdné/špatně pojmenované materiály, non-manifold a loose geometrii,
konvexnost a počet vrcholů kolizí, návaznost LODů, rodiče socketů, orientaci (nos +X), měřítko
(4–80 m), pivot, kolize vyčnívající z meshe.

Exportní nastavení (napevno ve skriptu): Selected Objects, Mesh + Empty, Apply Modifiers,
Smoothing **Face**, Tangent Space, Triangulate, Apply Unit, Apply Scalings **All Local**, Forward **−Z**,
Up **Y**, bez leaf bones a animací.

Export si manifest po zápisu přečte zpátky a zkontroluje ho (viz L1); chybný manifest =
export hlásí chybu.

### L. Import do Unrealu (až bude editor volný)

**L1. Kontrola manifestu – kdykoli, bez Blenderu i bez Unrealu:**
```
python Tools/Blender/gamespace_ship_export.py --check-manifest ArtSource/Ships/Example/Export/Example_manifest.json
python Tools/Assets/import_ship.py ArtSource/Ships/Example/Export/Example_manifest.json
```
První příkaz ověří strukturu, typy, rozsahy a vnitřní konzistenci (verze, všechna pole
`suggested_pawn_settings`, převod cm/osy, existence FBX souborů vedle manifestu, rozumná
velikost lodi). Druhý navíc vypíše přesný plán importu (co se kam naimportuje a jaké hodnoty
se nastaví do `BP_Ship_Example`) a nic nezmění.

**L2. Automatický import – editor zavřený:**
```
$env:GAMESPACE_SHIP_MANIFEST = "C:\gamespace\gamespace\ArtSource\Ships\Example\Export\Example_manifest.json"
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py
```
`Tools/Assets/import_ship.py`:
1. zkontroluje manifest (chyba = konec, nic se neimportuje),
2. naimportuje LOD0 FBX s nastavením z tabulky níže (Nanite zapne jen pro neprůhledné díly),
3. ověří velikost (při stokrát menší lodi zkusí jednou Convert Scene Unit), otočení, počet
   kolizních hullů, sloty materiálů a sockety (polohu a měřítko srovná podle manifestu),
4. vytvoří/aktualizuje `BP_Ship_Example` (potomek `ASpaceshipPawn`) s hodnotami ze
   `suggested_pawn_settings` (tabulka v kapitole 5), sklo přidá jako komponentu pod `Hull`,
5. nastaví `Planet_Veyra` (warm-up dosah, minimální kolizní poloměr) a vytvoří
   `/Game/Blueprints/BP_SpaceGameMode`, který v TestSpace spawnuje novou loď
   (vypnout: `$env:GAMESPACE_SHIP_APPLY_PLANET = "0"`, `$env:GAMESPACE_SHIP_SET_GAME_MODE = "0"`),
6. zapíše `Example_import_report.json` vedle manifestu (co se opravilo, co je ruční krok).

Ověřeno na první stíhačce (09/2026, odstraněna 24. 9. 2026). Kontrola po importu v čerstvém editoru:
`.\Tools\run_editor_python.ps1 Tools\Tests\test_ship_import.py` (testuje loď z
`Tools/Tests/ship_under_test.py`; dokud je `SHIP = None`, vypíše SKIP). Zjištění z prvního běhu:
sockety přicházejí z FBX s měřítkem 100 (skript je srovná na 1) a pole `Sockets` je v UE 5.8 pro
Python chráněné (skript používá `find_socket`). Blender z Git Bash spouštějte s
`MSYS_NO_PATHCONV=1`, jinak se `//Export` přepíše na `/Export`.

Ruční import (kdyby skript selhal) – FBX do `Content/Ships/Example/Meshes/`:

| Volba | Hodnota |
| --- | --- |
| Skeletal Mesh | off |
| Build Nanite | **on** pro trup, **off** pro `_Canopy` |
| Generate Missing Collision | **off** (použijí se UCX) |
| Combine Meshes | on (jeden mesh na soubor) |
| Transform Vertex to Absolute | on (pivot = počátek z Blenderu) |
| Import Uniform Scale | 1.0 |
| Convert Scene | on, Force Front X Axis **off** |
| Convert Scene Unit | off |
| Normal Import Method | Import Normals and Tangents |
| Import Materials / Textures | off (textury importovat zvlášť s nastavením z E.) |

**L3. Ruční doladění: `ArtSource/Ships/<Loď>/<Loď>_setup.json`** (nepovinné, v gitu).
Import ho načte po manifestu, takže jeho hodnoty vyhrávají:
- `materials`: jméno instance → `master` (`hull`/`glass`), `slots` (jména slotů z Blenderu),
  volitelně `meshes` (jen na těchto meshích; např. sklo trupu neprůhledné, kokpit průhledný),
  `base_color`, `metallic`, `roughness`, `emissive_color`, `emissive_strength`, `opacity`.
  Každý slot musí mít materiál (hlídá `test_import_ship_plan.py`).
- `pawn`: vlastnosti `ASpaceshipPawn` v snake_case (`pitch_rate`, `thrust_acceleration`,
  `engine_min_pitch`, `hide_hull_in_cockpit`, ...).
- `components`: komponenta → vlastnosti (`camera_boom.target_arm_length`,
  `chase_camera.field_of_view`, `cockpit_camera.relative_location`, ...). Vektory jako `[x, y, z]`.
- Klíče začínající `_` jsou poznámky.

Po úpravě stačí znovu spustit import (L2); FBX se naimportují znovu, ale nic ručního se neztratí,
protože všechno je v souborech.

**Ověření po prvním importu** (jednou; pak víme, že nastavení sedí):
1. Static Mesh Editor > Details > **Approx Size** = `expected_ue_size_cm` z manifestu.
   Stokrát menší → reimport se zapnutým Convert Scene Unit.
2. Nos lodi míří po **červené ose X** v editoru.
3. **Show > Simple Collision**: UCX hully sedí na trupu.
4. **Socket Manager**: sockety jsou, `SOCKET_Cockpit` na pozici `location_ue_cm` z manifestu
   a s měřítkem 1.
5. Nanite: Show > Nanite Visualization > Triangles.

---

## 2B. AI model → hratelná loď (Meshy, Higgsfield): opakovatelný recept

Poprvé použito 18. 9. 2026 na první stíhačce (Meshy, 3,36 mil. trojúhelníků; odstraněna 24. 9. 2026). Postup
je stejný pro každou další loď: **nic se nedělá ručně v Blenderu**, celou přestavbu popisuje jeden
soubor `ArtSource/Ships/<Loď>/<Loď>_ai_build.json` a skript `Tools/Blender/build_ai_ship.py` ji
z originálu kdykoli zopakuje (3 minuty). Když něco nesedí, upraví se čísla v receptu a spustí se znovu.

### Co AI modely typicky dělají a proč recept vypadá takhle

| Vlastnost AI exportu | Důsledek | Co s tím recept dělá |
| --- | --- | --- |
| Jeden souvislý mesh, miliony trojúhelníků | Nejde oddělit díly podle objektů | Díly (podvozek) se vyřežou **oblastmi** (boxy v metrech) |
| Orientace a měřítko náhodné (Meshy: příď −X, 1,9 m) | Import do UE by byl otočený a maličký | `orient`: otočení kolem Z a délka lodi v metrech |
| UV atlas z tisíců malých ostrůvků | Decimace je slepí → trojúhelníky přes půl textury, fleky | **Nové UV** na decimovaném meshi a **přepečení** textur |
| Normal mapa skoro prázdná, detail je v geometrii | Decimovaný mesh na kovu leskne fleky | Normal mapa se **zapeče z originálu** (Cycles, selected to active) |
| Podvozek srostlý s trupem | Nejde zasunout | Vyříznout do dílu `_Gear` (kód ho pak posouvá do trupu) |
| Kabina bez interiéru | Zevnitř UE odřízne všechny stěny (jsou jednostranné) | Oko kokpitu těsně nad předním okrajem kabiny |

### Postup

1. **Surový export** ulož do `ArtSource/Ships/<Loď>/Meshy/<název stažení>/` (FBX + textury), nic v něm neměň.
2. **Změř model** (orientace, rozměry, kde je příď, kabina, motory, podvozek). Nejrychleji: spusť recept
   s prázdnými `parts` / `collision` / `sockets` a `--no-save`; vypíše rozměry po otočení a zmenšení.
   Pro detailnější míry (výšky břicha, středy trysek) se osvědčily histogramy vrcholů v Blenderu
   (skripty v historii session 18. 9. 2026; hledá se hustá plocha = trup, řídké body = podvozek).
3. **Napiš recept** `<Loď>_ai_build.json` (vzor zatím není – první recept zůstal v gitové historii; všechny souřadnice jsou metry
   v Blenderu po otočení: +X příď, +Y levý bok, +Z nahoru):
   - `source_fbx`, `textures` (base_color, normal, roughness, metallic ze surového exportu);
   - `orient`: `rotate_z_deg`, `length_m` (malá stíhačka 12–16 m);
   - `parts.Gear.regions`: boxy, ve kterých leží celé nohy **pod úrovní břicha** (pahýly nad řezem zůstanou
     jako úchyty); díry v trupu po řezu se zacelí samy;
   - `decimate`: cíl trojúhelníků (trup 150–250 tis.) a `importance` pravidla (vršky, příď, kabina
     důležité; spodek a vnitřek trysek ne). Faktor držet nízko (1), vysoký dělal artefakty;
   - `rebake`: kam uložit `T_Ship_<Loď>_BC/ORM/N.png` a velikost (4K barva a normála, 2K ORM);
     Pozor: 4K na celou 14m loď jsou ~3 mm na pixel, takže zblízka je paint měkký vždy. Detail zblízka
     nedělá větší textura, ale **detailní vrstva materiálu** (`M_Ship_PBR`, dlaždicová mikro-normála a
     opotřebení triplanárně v prostoru lodi; `Tools/Assets/generate_detail_textures.py`, parametry
     `detail_*` v `<Loď>_setup.json`). Trup může mít i 1 mil. trojúhelníků místo 200 tis.
     (Nanite si vybere, co kreslí; cena je velikost FBX a čas pečení, ne snímkování);
   - `emissive`: středy trysek (y, z), poloměr a x, za kterým jsou; ty plochy dostanou slot
     `M_Ship_<Loď>_Emissive` a hra je rozsvítí podle tahu;
   - `collision`: boxy oblastí, z každé vznikne jeden konvexní `UCX_` hull (max 26 vrcholů). Trup
     rozděl tam, kde se zužuje, každý motor zvlášť, kabinu zvlášť (budoucí interiér), každou nohu zvlášť;
   - `sockets`: `Cockpit`, `CameraTarget`, `Exit` (vedle kabiny na zemi), `Engine_*` (kolik motorů má
     model, osa X ven z trysky: `rotate_z_deg: 180`), `Gear_*` jako `bottom_of` dílu podvozku (spodek patky).
4. **Spusť recept:**
   `blender -b --python Tools\Blender\build_ai_ship.py -- ArtSource\Ships\<Loď>\<Loď>_ai_build.json`
   Výpis ukáže počty trojúhelníků, hustotu na důležitých a nedůležitých plochách, hully a sockety.
5. **Zkontroluj vzhled v Blenderu** proti originálu ze stejných úhlů (kabina zblízka, spodek, 3/4).
   Fleky na kovu = problém normál/UV, rozmazané textury = moc malé textury nebo UV okraj.
6. **Kokpit:** `cockpit_view_survey.py` s `sweep:X0:X1:Z0:Z1` v rozsahu kabiny, pak konkrétní oči. Počítá
   s tím, že UE odvrácené stěny nekreslí; bez interiéru je zevnitř kabiny vidět jen okolí, proto oko
   těsně nad předním okrajem kabiny. Zapiš ho do `sockets.Cockpit` i do `<Loď>_setup.json`
   (`components.cockpit_camera.relative_location`, cm, Y s opačným znaménkem).
7. **Export:** `gamespace_ship_export.py -- --out "//Export"` na výsledném `.blend`. Staré FBX dílů, které nový
   model nemá, smaž z `Export/`.
8. **`<Loď>_setup.json`:** materiály `master: "pbr"` s `textures` a trysky `master: "hull"` s emisí; letové
   hodnoty se nemění; přepočítat jen, co závisí na geometrii (kamera, oko, `gear_stow_travel_cm` = výška
   nejdelší nohy pod břichem, `gear_extension_cm` 0, když patky leží na spodku kolizního boxu).
9. **Import:** `import_ship.py`. Když má nový model jiné materiálové sloty, starý mesh smaže a naimportuje
   načisto; odstraní komponenty a assety staré lodi, na které už nic neodkazuje (Canopy, staré MI).
   Pak `build_main_menu.py` (loď na úvodní obrazovce se skládá z dílů v manifestu, bez podvozku)
   a ještě jednou `import_ship.py` (uklidí, co držela úvodní obrazovka).
10. **Interiér kokpitu** (volitelně, druhý AI export): sekce `interior` v receptu (zdroj, `rotate_z_deg`,
    `fit` s mezemi hledání a výškou rukojetí stick-ů `stick_grip`). Nejdřív postav loď bez interiéru, pak
    `blender -b <Loď>_Meshy.blend --python Tools\Blender\fit_ship_interior.py -- <recept>`: vypíše
    nejlepší usazení a oko. Zapiš `interior.placement`, `sockets.Cockpit` a oko do setupu, postav znovu.
    K interiéru patří `lining` (výstelka trupu kolem kokpitu, jinak je zevnitř vidět skrz loď),
    `canopy_clear` (plochy canopy mířící do kabiny) a v setupu `cockpit_light_*` (trup kabinu stíní) a
    `placeholder_cockpit: false`. Zkontroluj pohled z oka v Blenderu s backface cullingem (jako UE) a pak
    `Shots.ps1 -Preset cockpit`. Rámování oka podle SC reference: `fit.dash_below_eye_deg` [7, 13]
    a `eye_behind_stick_m` tak, aby displeje vyšly ~15–24° pod okem (první stíhačka: 0,65 m).
    **Displeje** (`interior.displays`): AI malované obrazovky nejdou přečíst. Změř každou obrazovku v
    otočeném, neškálovaném modelu (střed, `u` = doprava po obrazovce, `v` = nahoru, `rect` [u0, u1, v0, v1]
    v metrech – nejlíp ortho renderem kolmo na obrazovku s mřížkou). Build plochy za ní vyřízne a dá
    plochý quad se slotem `M_Ship_<Loď>_Screens` (UV: obrazovka i z n dostane i-tou n-tinu textury).
    V setupu materiál s `"master": "screen"` (unlit `M_Ship_Screen`); hra do slotu kreslí displeje
    (`UCockpitDisplayComponent`, první slot končící na `_Screens`). Před každou obrazovkou build dá socket
    `Display_<jméno>`; hra na něj pověsí plošné světlo (displeje svítí do kokpitu).
    `canopy_frame` (box): vnitřek rámu canopy, jak ho vidí oko, dostane tmavý slot `M_Ship_<Loď>_CanopyFrame`.
11. **Testy a snímky:** všechny `Tools\Tests`, pak `Tools\Shots.ps1 -Preset ship_views -Package`, `cockpit`,
    `landing`. Vzdálenost chase kamery se ladí bez balení přes `chase_zoom` v dočasném scénáři.

---

## 3. Checklist modelu lodi

**Rozměry a orientace**
- [ ] Reálná velikost v metrech (stíhačka 12–16 m), Unit Scale 1.0
- [ ] Nos **+X**, vršek **+Z**, souměrná podle roviny Y = 0 (pokud má být)
- [ ] Všechny transformace aplikované (rotace 0, měřítko 1, žádné záporné měřítko)
- [ ] Pivot = střed obálky kolizí (**Center on collision**)

**Geometrie**
- [ ] Trup s Nanite: 100–300 tis. trojúhelníků; bez Nanite ≤ 80 tis. + LOD1–3
- [ ] Žádné vnitřní plochy, loose vrcholy, degenerované plochy; normály ven
- [ ] Sklo kokpitu jako samostatný mesh `_Canopy` (bez Nanite)
- [ ] Spodek lodi: nejnižší bod = místo, kde loď stojí na zemi (podvozek nebo plochý spodek)

**UV a materiály**
- [ ] Jedna UV mapa bez překryvů
- [ ] 2–4 materiálové sloty `M_Ship_<Loď>_<Slot>`, žádný prázdný
- [ ] Textury bez zapečeného osvětlení a stínů (PBR z Higgsfieldu nebo vlastní bake)
- [ ] Normal mapa: v Unrealu Flip Green Channel

**Kolize**
- [ ] 3–8 hullů `UCX_SM_Ship_<Loď>_NN`, každý konvexní, ≤ 32 vrcholů
- [ ] Nevyčnívají z meshe, pokrývají trup, křídla, motory

**Sockety**
- [ ] `SOCKET_Cockpit` (X dopředu), `SOCKET_Engine_*` (X dozadu), rodič = trup

**Export**
- [ ] Validate: 0 ERROR, WARN přečtené
- [ ] FBX + manifest v `Export/`, `.blend` a GLB commitnuté (LFS)

---

## 4. Specifika AI modelů (na co si dát pozor)

- **Měřítko a osy**: GLB je Y-up a v nahodilé velikosti (Blender importér převede na Z-up,
  velikost ne). Vždy krok C6–C8.
- **Zapečené světlo** v base color: loď pak vypadá dobře jen z jednoho úhlu. PBR mapy zapnout.
- **Záda/spodek si AI vymýšlí**: více pohledů, spodek kontrolovat zvlášť (na spodek se
  bude při přistání dívat hodně často).
- **Roztečené hrany** hard-surface: Cesta 2 (Remesh + Planar decimate + Weighted Normal),
  nebo alespoň Auto Smooth.
- **Jeden slitý mesh**: kokpit, trysky, zbraně jsou součástí trupu. Pro sklo a emisivní trysky
  je oddělit (Edit Mode, vybrat, **P > Selection**).
- **Fragmentované UV atlasy**: pro další úpravy textur ve 2D nepoužitelné; když chceš texturu
  ručně upravovat, Cesta 2 s vlastním UV.
- **Hustá triangulace s dlouhými tenkými trojúhelníky**: dělá artefakty stínování; Decimate
  (Collapse) to zlepší.
- **Licence**: ověř si podmínky Higgsfieldu (a použitých modelů Meshy/Tripo) pro komerční
  použití vygenerovaných assetů, než loď půjde do vydané hry.

---

## 5. Přechod z krychle na skutečnou loď (SpaceshipPawn)

Stav dnes (`Source/gamespace/SpaceshipPawn.cpp`):
- **Root = `HullCollision`** – `UBoxComponent` 100 × 50 × 17,5 cm (půlrozměry), profil `Pawn`.
  **Jediná kolize lodi.**
- `Hull` = krychle škálovaná (2, 1, 0,35), `NoCollision`, jen vizuál.
- Pohyb: `AddActorWorldOffset` se sweepem – **sweep testuje jen root komponentu** (to byl
  kořen dřívějšího bugu s proletem planetou, když root byl SceneComponent).
- Přistání (`SweepHull`) sweepuje `HullCollision->GetCollisionShape()` – tvar root boxu.

### Doporučený postup (varianta A, nejdřív)

1. **Root zůstane jednoduchý tvar** (box, případně kapsle) – je to „fyzikální pravda“ lodi.
   Sweep jednoho boxu je rychlý, stabilní a přistání s ním už funguje.
2. Velikost boxu podle manifestu: `suggested_pawn_settings.HullCollision_BoxExtent_cm`
   (= půlka obálky UCX hullů). Kompromis:
   - box přes celé rozpětí křídel → loď nikdy neprojde vizuálně křídlem skrz skálu, ale
     narazí „vzduchem“ vedle trupu;
   - box jen kolem trupu → křídla občas zajedou do terénu/asteroidu.
   Pro začátek **celé rozpětí**.
3. `Hull` → `SM_Ship_Example`, **NoCollision**, **měřítko 1** (smazat
   `SetRelativeScale3D(2, 1, 0.35)`), relativní poloha 0, pokud pivot sedí (krok I).
4. Mesh nepřiřazovat přes `ConstructorHelpers` napevno v C++; dát ho do `BP_Ship_Example`
   (potomek `ASpaceshipPawn`) a ten nastavit jako `DefaultPawnClass` – další lodě pak bez
   zásahu do C++.

### Varianta B (později): kolize = UCX hully meshe

- Root by byl `UStaticMeshComponent` s UCX. Sweep s více konvexními tvary Unreal umí, ale
  je dražší a na hranách mezi hully se může zasekávat.
- **Nutné změny v kódu**: `SweepHull` a sonda přistání používají `GetCollisionShape()` (u meshe
  vrací jen obalový box) → přepsat na `ComponentSweepMulti`; `HullCollision` typ a všechny
  odkazy na něj.
- Až bude potřeba přesný zásah (střely, AI), stačí nechat root box a na meshi zapnout
  `QueryOnly` na vlastním kanálu pro zásahy – pohyb se tím nemění.

### Čísla, která se změní s velikostí lodi (placeholder 2 × 1 × 0,35 m → ~14 × 10 × 3 m)

Přesné vzorce jsou na jediném místě: `suggest_pawn_settings()` v
`Tools/Blender/gamespace_ship_export.py`. Export je zapíše do manifestu a `import_ship.py` je
nastaví do `BP_Ship_<Loď>` – nic se nepřepočítává ručně. Tabulka ukazuje orientační hodnoty.

| Kde | Dnes | Pro ~14 m loď | Poznámka |
| --- | --- | --- | --- |
| `HullCollision` BoxExtent | 100, 50, 17,5 | z manifestu (~700, 500, 150) | |
| `CameraBoom->TargetArmLength` | 900 | ~2500 (1.8 × délka) | manifest: `CameraBoom_TargetArmLength_cm`; při hraní bylo moc daleko, v praxi ~0,8 × délka (v `_setup.json`) |
| `CameraBoom->SocketOffset.Z` | 200 | ~300–400 | kamera kousek nad lodí |
| `CameraBoom->ProbeSize` | 25 | 25–50 | |
| `CameraBoom->CameraLagMaxDistance` | 1500 | ~3000 | |
| `CockpitCamera` poloha | 90, 0, 15 | ze `SOCKET_Cockpit` | oko pilota: **před opěrkou sedačky**, ~15 cm pod sklem, nad palubní deskou; ověřit řezy a paprsky v Blenderu (`cockpit_view_survey.py`). Oko za opěrkou má celý výhled zakrytý |
| `LandingFootprintRadiusCm` | 150 | ~500 | půlka menšího rozměru |
| `LandingMaxGapCm` | 60 | ~100 | |
| `GroundContactToleranceCm` | 10 | 10–20 | |
| Planeta `CollisionWarmupReachM` | 15 | ≥ 0,75 × délka (~11–15) | manifest |
| Planeta `CollisionMinRadiusM` | 60 | 60–100 | musí být ≫ délka lodi |
| `HeatShakeCm` | 14 | ~30 | větší kamera = větší třes |
| Zrychlení/rychlosti | 40 m/s², 120 m/s | beze změny, ale **pocit** se změní | 14m loď při 120 m/s působí pomaleji |

### Kolize lodi pro postavu

Kořenový box (`HullCollision`) obaluje celou loď včetně vzduchu pod křídly, a proto **ignoruje
pawny**. Postava naráží do UCX hullů meshe (`Hull` má query-only kolizi proti Pawn, Camera a
Visibility). Z toho plyne pro model:
- UCX hully mají kopírovat tvar tak, aby se kolem lodi dalo chodit (pod křídly nechat volno, pokud
  tam má jít vejít).
- `SOCKET_Exit` musí být mimo UCX hully s rezervou aspoň na kapsli postavy (poloměr 42 cm, výška
  1,92 m), ideálně ~80 cm volno. Když je obsazený, hra zkouší místa vpravo, vlevo, za a před lodí.

### Další pasti

- **Vizuál nesmí být pod spodkem root boxu**: přistání usadí box na zem. Co mesh má pod boxem
  (podvozek, ploutve), zajede do terénu. Spodek boxu = nejnižší bod, na kterém loď stojí.
- **Pivot mimo střed boxu**: pokud box není na počátku, loď se při otáčení „kývá“ kolem
  špatného bodu a přistávací zarovnání vypadá divně. Proto krok I.
- **Měřítko komponent**: root i mesh musí mít scale 1. Škálovaný root škáluje kamery a
  zvuk (proto je dnes škálovaný jen `Hull`).
- **Kokpit**: dnes se v kokpitu trup schová (`SetOwnerNoSee`). S Nanite ověřit, že to funguje;
  skutečný interiér kokpitu = samostatný mesh viditelný jen pro vlastníka (`OnlyOwnerSee`).
- **Chase kamera a vlastní loď**: kamera sweepuje kanálem Camera; mesh s `NoCollision` ji
  neblokuje. Kdyby mesh dostal kolizi, kamera by se „lepila“ do vlastní lodi.
- **Near clip** (10 cm) je v pořádku; kokpitová kamera ale nesmí být uvnitř geometrie skla.
- **Průhledné sklo nemá Nanite** a řadí se s ostatní průhledností (atmosféra oblohy je
  neprůhledná, takže zatím bez problémů).
- **Trysky**: emisivní materiál + později Niagara na `SOCKET_Engine_*`; zvuk
  `EngineAudio` přesunout na socket (dnes nespatializovaný, takže nevadí).
- **Origin rebasing**: nic nového – loď je jeden actor, jeho komponenty se posouvají s ním.
`.\Tools
un_editor_python.ps1 Tools\Tests	est_ship_import.py`. Zjištění z prvního běhu:
