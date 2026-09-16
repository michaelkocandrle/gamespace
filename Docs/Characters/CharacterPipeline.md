# Hráčova postava: Higgsfield → Blender → Unreal

Protějšek [Docs/Ships/ShipPipeline.md](../Ships/ShipPipeline.md) pro postavu, která vystoupí
z lodi. Příklad jména: **Explorer**.

Hlavní rozdíl proti lodi: loď je statický mesh, postava je **skeletal mesh** – mesh navázaný na
kostru (skeleton), kterou hýbou animace. Kostra rozhoduje o tom, jaké animace půjdou použít,
proto je to první rozhodnutí, ne poslední.

---

## 0. Doporučení v kostce

1. **Gameplay nejdřív s UE5 Manny/Quinn** (Epic mannequin z Third Person šablony) – výstup
   z lodi, chůze po kulaté planetě, kamera. Umělecká postava přijde až na hotový pohyb.
2. **Postava ve skafandru s helmou.** Obličeje a vlasy jsou u AI generátorů nejslabší místo
   (a vlasy jsou nejdražší na render). Helma to celé obchází a do sci-fi hry sedí.
3. **Cílit na kostru UE5 Mannequin** (varianta B níže). Všechny animace Epicu, Fab
   (Marketplace) a Animation Blueprint z šablony pak fungují bez retargetingu.
4. Higgsfield rig (varianta A) použít jen na rychlou zkoušku vzhledu.

---

## 1. Higgsfield a kostra: co umí a co s tím

**Co Higgsfield umí** (stav 09/2026, přes engine Meshy):
- Z obrázku / 2–4 pohledů / promptu udělá GLB mesh, volitelně s PBR mapami.
- **Umí i rigged výstup:** automaticky napasuje humanoidní kostru a přidá vážení (weights).
  Má knihovnu 678 animací (chůze, běh, skoky, gesta, boj…).
- Doporučuje **A-pózu nebo T-pózu** na vstupu a má parametr výšky postavy (výchozí 1,7 m).
- Auto-rig funguje dobře jen pro humanoidy.

**Problém:** ta kostra je **Meshy kostra, ne UE5 Mannequin**. Jinak se jmenují kosti, jinak jsou
otočené, obvykle chybí twist kosti (předloktí, stehna) a IK kosti, prsty bývají zjednodušené.
Animace pro Manny/Quinn na ní přímo nepoběží. Přesnou podobu kostry je potřeba ověřit na
prvním staženém souboru (Blender: otevřít armaturu, projít jména kostí).

### Varianta A – Higgsfield rig + IK Retargeter (rychlá)

1. Higgsfield: rigged výstup v A-póze, výška 1,8 m, PBR.
2. Blender: import GLB, úklid (jako u lodi, kapitola C), měřítko, orientace, export FBX
   se skeletem (nastavení v kapitole 4).
3. Unreal: import jako Skeletal Mesh **s vlastním novým skeletonem** `SK_Char_Explorer`.
4. **IK Rig** pro tuto kostru (`IK_Char_Explorer`) – Unreal ho umí vygenerovat automaticky
   (Auto Create IK Rig), zkontrolovat řetězce Spine, Neck, Head, Arms, Legs, Fingers.
5. **IK Retargeter** `RTG_Mannequin_To_Explorer` (zdroj `IK_Mannequin`, cíl `IK_Char_Explorer`),
   srovnat retarget pózu (A-póza vs. A-póza).
6. Animace: buď dávkově přeexportovat Manny animace na novou kostru (Export Selected
   Animations v Retargeteru), nebo za běhu v Animation Blueprintu uzlem
   **Retarget Pose From Mesh** (neviditelný Manny hraje animace, postava je kopíruje).

| Plus | Mínus |
| --- | --- |
| Hotovo za hodinu | Dvě kostry, každá nová animace = retarget |
| Nulová práce s vážením | Kvalita závisí na auto-rigu (ramena, kyčle, prsty) |
| Higgsfield animace hned k dispozici | Chybí twist kosti → „cukrkandlové“ předloktí při rotaci |
| | Foot IK, Control Rig a Motion Matching z Epic ukázek se musí přenastavit |

### Varianta B – mesh na kostru UE5 Mannequin (doporučená pro finální postavu)

1. Higgsfield: **bez riggu** (nebo rig v Blenderu smazat), A-póza, výška ~1,8 m.
2. Z Unrealu vyexportovat `SKM_Manny` (nebo `SKM_Quinn`) jako FBX – kostra i referenční tělo
   (Content Browser > pravý klik > Asset Actions > Export). Jednou, uložit do
   `ArtSource/Characters/Shared/Mannequin/`.
3. Blender: importovat Manny FBX a Higgsfield mesh, **napasovat mesh na Manny kostru**
   (ne naopak – kostra se nesmí měnit): posun/škálování meshe, Proportional Editing, případně
   úprava A-pózy meshe podle kostry.
4. Mesh vybrat, pak armaturu > **Ctrl+P > With Automatic Weights**.
5. **Weight Paint** úpravy: podpaží, rozkrok, ramena, prsty, helma přilepená 100 % na `head`,
   pevné části skafandru (batoh) 100 % na `spine_05`.
6. Test v Blenderu: Pose Mode, ohnout lokty, kolena, předklon, otočit hlavu.
7. Export FBX jen mesh + armatura (kapitola 4) a import do Unrealu se skeletonem
   **`SK_Mannequin`** (existující asset) – žádný nový skeleton.

| Plus | Mínus |
| --- | --- |
| Všechny UE5 animace, ABP, Control Rig, foot IK, Motion Matching fungují hned | Ruční práce s vážením (půl dne až dva dny) |
| Jedna kostra pro všechny postavy (Explorer, NPC) | Proporce postavy musí zhruba sedět na Manny |
| Retarget jen pro cizí animace (Higgsfield, Mixamo) | |

Placená zkratka pro B: Blender addon **Auto-Rig Pro** má export s kostrou kompatibilní s UE
Mannequin. Alternativa k celé cestě: **MetaHuman** (v Unrealu nativní, s riggem i obličejem),
ale je to jiný styl a těžší na výkon – spíš pro NPC ve stanicích než pro hráče ve skafandru.

---

## 2. Rozhodnutí

**Rozhodnuto (L6):** third-person kamera jako výchozí (FP přepínač později) a UE5 Manny jako
placeholder. Implementace: `APlayerCharacter` (README, sekce PlayerCharacter).

### 2.1 Kamera po výstupu z lodi: first-person, nebo third-person?

| | First-person | Third-person |
| --- | --- | --- |
| Pocit | Imerze, měřítko planety a lodi působí větší | Vidíš svou postavu a skafandr |
| Umělecká práce | Stačí ruce (a zbraň/nástroj) z pohledu hráče; celé tělo jen pro stíny/odraz | Celé tělo a animace musí být pěkné, každá chyba je vidět |
| Animace | Méně, jiné (FP ruce), ale kamera nesmí houpat → nevolnost | Standardní locomotion z UE5 šablony funguje hned |
| Terén (svahy medián 15°) | Foot IK skoro není vidět | Bez foot IK nohy lítají nad/pod terénem – nutné |
| Nízká gravitace (6 m/s²) | Skok vypadá dobře i bez animace | Dlouhé skoky potřebují loop animaci ve vzduchu |
| Kontinuita s lodí | Kokpitový pohled → FP pěšky je plynulý přechod | Chase kamera lodi → TP pěšky je plynulý přechod |
| Kolize kamery s terénem | Žádná | Spring arm (máme vyzkoušené u lodi) |

**Můj návrh:** **third-person jako výchozí**, FP přepínač později (jako u lodi klávesa C).
Důvody: investujeme do postavy a TP ji ukazuje; UE5 šablona Third Person dá funkční základ
za pár minut; spring arm s kolizí máme odladěný. FP ruce jsou separátní asset, který se dá
přidat, až bude jasné, že je chceme.

### 2.2 Animační sada pro první verzi

**V1 (doporučeno – pohyb po planetě):**
- `Idle`, `Walk`, `Run` → 1D Blend Space podle rychlosti (`BS_Char_Locomotion`)
- `Jump_Start`, `Fall_Loop`, `Land` (fall loop je kvůli nízké gravitaci důležitý)
- **Foot IK na svahu** (Control Rig nebo IK uzly v ABP) – bez něj to na Veyře nepůjde
- Výstup z lodi / nástup: ve V1 stmívačka + přemístění, žádná animace
- Vše existuje v UE5 Third Person šabloně (a v Epic **Game Animation Sample**)

**V2 (nástroj):** skener / multitool v ruce – horní polovina těla přes Layered Blend per Bone,
míření (Aim Offset), socket `hand_r` pro nástroj.

**V3 (zbraň):** až bude jasné, jestli hra má boj. Kostru i sockety (`hand_r`, `weapon_r`)
připravit už teď, animace ne.

**Nepřidávat na začátek:** obličejové animace (helma), prsty mimo základní úchop, plavání,
lezení, motion matching (až bude locomotion odladěná na kulaté planetě).

### 2.3 Co musí vyřešit kód, ne art (kvůli tomu gameplay s Manny nejdřív)

Stav po L6: gravitace po kouli, kamera v gravitačním rámci, výstup/nástup a foot IK proti
viditelnému terénu jsou hotové. Šablonový ABP a Control Rig foot IK se **nepoužívají**
(počítají s gravitací po světové −Z); pózu skládá nativní `UPlayerCharacterAnimInstance`.
Vlastní postava na kostře `SK_Mannequin` (varianta B) proto dostane animace i IK bez úprav.
Jemnější kolize kolem chodce zatím není potřeba: foot IK pokryje rozdíl (max ~25 cm).

- **Gravitace po kouli:** `UCharacterMovementComponent` od UE 5.4 umí vlastní směr gravitace
  (`SetGravityDirection`). Každý tick ho nastavit na −Up z `ACelestialBody::FindNearest`.
  Na 25 km planetě se „dolů“ změní o 2,3° na každý kilometr chůze. Chování v UE 5.8
  ověřit (kamera a ovládání musí také počítat s lokální vertikálou).
- **Kolize terénu je na postavu hrubá:** kolizní buňky mají při pomalém pohybu ~2,4 m
  (dlaždice 77 m / 32 buněk), viditelný terén 33 cm. Loď to snese, noha postavy ne – bude
  levitovat nebo se bořit o desítky cm. Potřeba: jemnější kolizní dlaždice kolem postavy
  (menší `CollisionMinTileSizeM` / víc `CollisionTileQuads`, jen v okolí pěšáka).
- **Výstup z lodi:** `SOCKET_Exit` na lodi, spawn postavy, `Possess`, loď zůstane `Landed`.
- **Origin rebasing:** postava i loď jsou actory, posun počátku je řeší stejně jako dnes.
- **Planeta sleduje „player pawn“:** kolizní dlaždice se staví kolem posednutého pawnu, takže
  po výstupu budou kolem postavy – loď opuštěná daleko od hráče ztratí kolize pod sebou.
  Až se bude odcházet daleko, loď musí zůstat stát i bez kolize (je `Landed`, fyziku nemá).

---

## 3. Adresáře a pojmenování

### Zdrojová data

```
ArtSource/
  Characters/
    Shared/
      Mannequin/            SKM_Manny.fbx exportovaný z Unrealu (kostra pro variantu B)
    Explorer/
      Concept/              pohledy (A-póza zepředu, z boku, zezadu), prompt.txt
      Higgsfield/           surové GLB (needitovat)
      Explorer.blend
      Textures/
      Export/               SKM_Char_Explorer.fbx (+ manifest, až bude exportní skript)
```

### Unreal

```
Content/Characters/
  Mannequins/                        Epic obsah z Third Person šablony (SK_Mannequin, SKM_Manny, ABP, animace)
                                     – nepřejmenovávat, jiné Epic balíčky počítají s touto cestou
  Shared/
    Animations/
      Locomotion/                    AS_Char_Idle, AS_Char_Walk_Fwd, AS_Char_Run_Fwd, BS_Char_Locomotion
      Traversal/                     AS_Char_Jump_Start, AS_Char_Fall_Loop, AS_Char_Land
    AnimBlueprints/                  ABP_Char_Base (společný pro všechny postavy na SK_Mannequin)
    Rigs/                            IK_Char_Explorer, RTG_Mannequin_To_Explorer, CR_Char_FootIK
    Materials/                       M_Char_Master, MF_Char_*
  Explorer/
    Meshes/                          SKM_Char_Explorer, PHYS_Char_Explorer
                                     (SK_Char_Explorer jen ve variantě A – vlastní skeleton)
    Materials/                       MI_Char_Explorer_Suit, _Helmet, _Visor
    Textures/                        T_Char_Explorer_Suit_BC, _N, _ORM, _E
    Animations/                      AS_/AM_ jen specifické pro tuto postavu
    Blueprints/                      BP_Char_Explorer
    Audio/                           kroky, dýchání v helmě
```

### Pojmenování

| Co | Vzor | Příklad |
| --- | --- | --- |
| Skeletal mesh | `SKM_Char_<Postava>` | `SKM_Char_Explorer` |
| Skeleton | `SK_<Jméno>` | `SK_Mannequin` (sdílený), `SK_Char_Explorer` (varianta A) |
| Physics asset | `PHYS_Char_<Postava>` | ragdoll, kolize kostí |
| Samostatné díly (helma, batoh) | `SKM_Char_<Postava>_<Díl>` | `SKM_Char_Explorer_Helmet` |
| Animace | `AS_Char_<Akce>[_<Směr>]` | `AS_Char_Run_Fwd` |
| Montáž | `AM_Char_<Akce>` | `AM_Char_ExitShip` |
| Blend space | `BS_Char_<Co>` | `BS_Char_Locomotion` |
| Animation Blueprint | `ABP_Char_<Co>` | `ABP_Char_Base` |
| IK Rig / Retargeter / Control Rig | `IK_…`, `RTG_<Z>_To_<Na>`, `CR_…` | `RTG_Mannequin_To_Explorer` |
| Materiály, textury | jako u lodi, `Char` místo `Ship` | `MI_Char_Explorer_Suit`, `T_Char_Explorer_Suit_N` |
| Blueprint postavy | `BP_Char_<Postava>` | `BP_Char_Explorer` |
| Sockety na kostře (v UE) | bez prefixu, u kosti | `hand_r_Tool`, `head_Lamp` |

---

## 4. Checklist modelu postavy

**Póza, rozměry, orientace**
- [ ] A-póza (paže ~45° dolů), dlaně dolů, prsty rovně, nohy mírně od sebe
- [ ] Výška 1,75–1,85 m (Manny ~1,8 m); chodidla na Z = 0, počátek mezi chodidly
- [ ] Blender: postava **kouká do −Y** (pohled Numpad 1 ukazuje obličej) – v Unrealu pak kouká
      do +Y jako Manny, a Blueprint postavy má mesh otočený o −90° (stejně jako šablona)
- [ ] Unit Scale 1.0, aplikované transformace na meshi i armatuře

**Geometrie a materiály**
- [ ] 30–60 tis. trojúhelníků celkem (bez Nanite; Nanite pro skeletal mesh nepočítat)
- [ ] Helma a batoh mohou být součástí meshe (pevně na `head` / `spine_05`), vizor zvlášť (průhledný materiál)
- [ ] Zavřená geometrie v kloubech (lokty, kolena, ramena) – dost hran na ohyb
- [ ] 2–4 materiály: Suit, Helmet, Visor (průhledný), případně Emissive
- [ ] Textury bez zapečeného světla; skafandr 4096², helma 2048²

**Rig (varianta B)**
- [ ] Kostra = nezměněná `SK_Mannequin` (jména, hierarchie, klidová póza)
- [ ] Max. 4 kosti na vrchol, váhy normalizované
- [ ] Žádné nové kosti (doplňky jako batoh = váha 100 % na existující kost)
- [ ] Test ohybů v Pose Mode bez propadů a trhlin

**Export FBX (Blender) – ověřit při prvním exportu**
- [ ] Vybrat mesh + armaturu, Object Types: Armature + Mesh
- [ ] Armature: **Add Leaf Bones off**, Only Deform Bones on
- [ ] Apply Scalings **FBX Units Scale** (u kostry se jinak kostem přidá měřítko 100)
- [ ] Bez animací (Bake Animation off) – animace jdou zvlášť
- [ ] Objekt armatury pojmenovat `Armature`: exporter ho pak nepřidá jako navíc kořenovou kost
      a kořenem zůstane kost `root`

**Import (Unreal)**
- [ ] Skeletal Mesh, Skeleton = `SK_Mannequin` (varianta B)
- [ ] Import Morph Targets off, Import Animations off, Create Physics Asset on
- [ ] Po importu: přehrát `AS_Char_Run_Fwd` na novém meshi v Animation Preview, zkontrolovat
      ramena, kyčle, prsty, jestli nic nepropadá

---

## 5. Specifika AI postav

- **Obličej a vlasy** – nejslabší místo, proto helma.
- **Póza**: AI občas vrátí postavu v „přirozené“ póze s pokrčenými končetinami – rig i
  retarget pak dělají chyby. Vstupní obrázky v A-póze, výsledek zkontrolovat.
- **Symetrie**: skafandr má být souměrný, AI výstup není – u meshe před riggingem srovnat
  (Bisect + Mirror jako u lodi) a teprve pak vážit.
- **Slepené prsty a prsty v rukavicích** – pro skafandr v pořádku (rukavice), stačí úchop.
- **Tloušťka kolem kloubů**: AI mesh má v kloubech málo hran → ohyb loktu „láme“ rukáv.
  Přidat edge loopy (Loop Cut) kolem loktů, kolen, ramen, kyčlí před vážením.
- **Rozlišení textur**: GLB textury bývají 2K; pro TP kameru na blízko stačí, pro FP ruce ne.
- **Licence** generovaných assetů pro komerční použití – ověřit (stejně jako u lodi).

---

## 6. Co ještě neexistuje (další kroky)

- Exportní addon pro postavy (analogie `gamespace_ship_export.py`: kontrola kostry proti
  `SK_Mannequin`, výšky, pózy, vah, export FBX + manifest).
- Importní skript (analogie `Tools/Assets/import_ship.py`) pro skeletal mesh s přiřazením
  `SK_Mannequin`, physics assetem a `BP_Char_Explorer`.
- Gameplay: pawn postavy s gravitací po kouli, výstup z lodi, jemnější kolize terénu kolem pěšáka.
