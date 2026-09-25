# Modulární AI asset pipeline: kdy generovat vcelku, kdy rozkládat na díly

Zjištěno a zapsáno 22. 9. 2026, po srovnání dvou výsledků: exteriér první stíhačky (Meshy;
odstraněna 24. 9. 2026) dopadl dobře, interiér kokpitu ne, i po několika kolech opravování textur a osvětlení. Rozdíl
není v úsilí ani v promptu — je v tom, **co přesně se po AI chtělo vygenerovat najednou**.

## Pravidlo

Než se cokoliv pošle do Meshy/Tripo, rozhodni:

- **Jednoduchý tvar** (jedna dominantní konvexní silueta, málo odlišných funkčních prvků —
  trup lodi, tělo postavy, jeden prop) → generovat přímo, jako doteď (hero obrázek → multi-view
  → Meshy). Tohle AI zvládá dobře, protože nemusí domýšlet skrytou vnitřní strukturu ani
  udržet čitelnost mnoha odlišných prvků najednou.
- **Komplexní kompozice** (víc odlišných funkčních dílů poskládaných dohromady — kokpit
  interiér, řídicí místnost, cokoliv s "čitelným" detailem jako displeje/přístroje/ovladače)
  → **rozložit na díly**, ne generovat vcelku. Tohle je přesně ten případ, kde current-gen
  image-to-3D nástroje (Meshy, Tripo) selhávají — jak geometrie, tak čitelnost detailu.

## Postup u komplexní kompozice

1. **Meshy dělá jen hrubou obálku/objem** — celkový tvar kabiny, sklon dashboardu,
   silueta sedadel. Z dálky/na celek to Meshy zvládá slušně (je to pořád "jeden
   velký tvar" z pohledu pravidla výše).
2. **Veškerý funkční/technický detail je procedurální, NE AI-generovaný kus po
   kuse.** Tlačítka, přepínače, rámy displejů, panely s pravidelným rozestupem —
   tohle dělá Claude Code přímo v Blenderu (bmesh, přesné primitivy), ne Meshy/
   Tripo, a to ani po jednotlivých malých dílech. Důvod, zjištěno na Steadfast
   interiéru 23. 9. 2026: i malé samostatně generované AI kusy (viz kitbash pilot
   níže) nemají strojovou přesnost — hrany nejsou rovné, rozestupy nejsou
   pravidelné, vypadá to jako "organická aproximace" tlačítka, ne vyrobená
   součástka. Lidské oko tohle u technických předmětů okamžitě pozná jako špatně.
   Procedurální přístup navíc stojí nula kreditů a je neomezeně opakovatelný.
3. **Sesaď** obojí (obálka + procedurální detail) přes Blender MCP s živou
   vizuální kontrolou (postup v `WORKFLOW.md` kapitola 3).
4. Zbytek pipeline (decimate/retopologie, UV, rebake, export, import) beze
   změny podle `Docs/Ships/ShipPipeline.md`.

Tohle nahrazuje dřívější plán "kitbash z malých AI-generovaných dílů" (viz sekce
kitbash pilot níže na první stíhačce) — ten pilot ukázal částečně dobré výsledky u
stíhačky, ale u Steadfast interiéru se ukázalo, že i "vyhrávající" AI díly
nemají dost geometrickou přesnost na blízký pohled hráče v kokpitu. Kitbash
pilot zůstává jako cenný záznam SROVNÁNÍ (kdy AI vyhrává na "designu", kdy
prohrává na přesnosti), ne jako doporučený finální postup.

## Zdroje geometrie — tři rovnocenné cesty

Vedle "generovat v Meshy" a "postavit procedurálně v Blenderu" existuje ještě třetí
legitimní cesta, kterou stojí za to zvážit u každého nového kusu, ne jen jako výjimku:

- **Koupený/stažený hotový model** s komerční licencí (Fab, Sketchfab, CGTrader, TurboSquid,
  itch.io). Profesionálně vymodelovaná geometrie má přesně to, co AI generování postrádá —
  čisté strojové hrany, promyšlené UV, žádný organický šum. Restylizace na náš vizuální
  jazyk (gunmetal + oranžové akcenty, Kestrel Dynamics/Halcyon Freightworks paleta) jde
  přes stejnou Meshy Retexture funkci, co už používáme, nebo ručně v materiálových nodech.
  **Kontrola licence PŘED stažením je povinná** — CC0, royalty-free komerční nebo CC-BY
  (s atribucí v creditech) jsou v pořádku; "personal use only", "non-commercial" a
  "editorial use only" NE, bez ohledu na to, že se to tváří jako "free asset".
- Zbytek pipeline (import do Blenderu, kolize, sockety, Nanite rozhodnutí, export) je
  stejný bez ohledu na to, odkud geometrie pochází — `ShipPipeline.md` na tom nic nemění.

Volba mezi třemi cestami podle situace:
- Velký jednoduchý tvar, kde chceme rychlý první průchod → Meshy multi-view
- Malý přesný technický díl (knoflík, panel, displej rám) → procedurálně v Blenderu
- Kdykoliv existuje kvalitní hotový model odpovídající stylu → koupený/stažený base,
  restylizovaný



- **Meshy Retexture** (text prompt, bez nových referenčních obrázků) — upgraduje
  materiál/texturu existující geometrie. Použitelné a ověřené, nemění tvar.
- **UltraShape 1.0** (scenario.com, předplatné od 23. 9. 2026; chce referenční obrázek *i* hrubý mesh,
  viz `WORKFLOW.md` 3.1b; vstupy prvního testu, přepínací panel, byly smazány s první stíhačkou
  24. 9. 2026) — "3D geometry super-resolution": dovybaví
  hrubý mesh o skutečné povrchové detaily (až 8 mil. trojúhelníků na výstupu, čeká ho tedy
  stejný decimate krok jako ostatní AI modely). Podle popisu cílí primárně na organické tvary,
  u hard-surface sci-fi dílů neověřeno — vyzkoušet na konkrétním kusu, ne rovnou nasadit plošně.

## Kdy tohle použít příště

- Interiér kokpitu (aktuální otevřený problém) — kandidát č. 1 na přepracování tímhle
  postupem místo dalšího ladění jednoho monolitického AI modelu.
- Jakákoliv budoucí "obydlená" scéna (druhá loď s kabinou, stanice, interiér budovy).
- NE pro samotné lodě/postavy zvenku — tam dosavadní přímý postup funguje dobře.

## Pilot na středové konzoli kokpitu (23. 9. 2026)

První reálné použití postupu. Čtyři díly ve skutečném měřítku kokpitu, sesazené na klínový
základ konzole 46 × 28 cm (první stíhačka), celkem 3 936 trojúhelníků. Zadání dílů (jméno, rozměr,
prompt) bylo v JSON spec, aby se daly generovat kterýmkoliv nástrojem a pak porovnat se stejným
měřítkem. Soubory pilotu byly smazány s první stíhačkou 24. 9. 2026 (historie v gitu); vzor spec pro
další loď je `ArtSource/Ships/Steadfast/Kitbash/meshy_parts.json`.

### Co který zdroj dílů umí

| Zdroj | Stav | Poznámka |
| --- | --- | --- |
| **Procedurálně v Blenderu** | **funguje, hotovo** | Přepínací panel (788 tris), mřížka (920), svazek kabelů (816), rám displeje (436). Přesné rozměry, čistá topologie, zadarmo a opakovatelné. Pro malé technické díly je to rychlejší než generovat a pak opravovat. |
| **Meshy** | **funguje** | `Tools/Assets/meshy_generate.py` (text-to-3D v2, preview + volitelný refine, `--spec <parts.json> --out <složka>`, stáhne GLB, např. do `ArtSource/Ships/<Loď>/Kitbash/Meshy/`). Klíč se bere z `MESHY_API_KEY`, nikdy z repozitáře. `--dry-run` vypíše prompty bez volání. |
| **Hyper3D Rodin** (Blender MCP) | **nepoužitelné zadarmo** | Zapíná se `blendermcp_use_hyper3d` + klíč; vestavěný zkušební klíč (`vibecoding`) vrací `API_INSUFFICIENT_FUNDS` – je vyčerpaný. Potřebuje vlastní klíč (hyper3d.ai nebo FAL). |
| **Hunyuan3D** (Blender MCP) | nevyzkoušeno | Vypnuté, chce vlastní klíč. |

### Nástrahy z pilotu

- Operátory (`object.join`, `modifier_apply`, `mesh.bevel`…) přes MCP spouštěj helperem
  `Tools/Blender/mcp/ops_context.py` (od 24. 9. 2026; dřív padaly na `poll() failed`). Čistou
  geometrii jde dál skládat i přes `bmesh` a `bpy.data.objects.new`.
- `get_viewport_screenshot` je u dílů velikosti 10 cm k ničemu (v okně jsou to tři pixely a
  nastavení `region_3d` se na snímku neprojeví). Spolehlivé je **renderovat přes kameru do souboru**
  (Workbench, `bpy.ops.render.render(write_still=True)`) a ten soubor si přečíst.

### Srovnání obou zdrojů na stejném zadání (23. 9. 2026)

Meshy text-to-3D, preview (bez refine): **20 kreditů a asi minuta na díl**, 2 300–3 000 trojúhelníků
proti 440–920 u procedurálních. Renders: `Saved/Kitbash/compare_all.png` (díly) a
`compare_consoles.png` (obě konzole vedle sebe).

| Díl | Meshy | Procedurálně | Kdo vyhrál |
| --- | --- | --- | --- |
| Přepínací panel | zaoblený rám, kolébkové přepínače, šrouby v rozích | čisté, ale generické válečky | **Meshy** (lepší „design“) |
| Ventilační mřížka | hluboký rám s lamelami | placatější, ale přesná | **Meshy** o kousek |
| Svazek kabelů | **selhal** – chuchvalec jako chobotnice, nepoužitelné | přesně to, co má být | **procedurálně** |
| Rám displeje | rám, zapuštěné sklo, clona | holý rámeček | **Meshy** |

**Pravidlo z toho:** AI je dobrá na **„panelové“ díly** – plochá deska s ovladači, kde jde o design
a čitelnost. Na **tenké protáhlé struktury** (kabely, trubky, madla) selhává a procedurální skript
je rychlejší i přesnější. Povrch z AI je navíc zvlněný a rozměry nesedí na zadání (Meshy vrací
normalizovaný model, měřítko si musí srovnat import podle `size_cm`).

### Geometrické rozlišení u Meshy vs. UltraShape (23. 9. 2026)

UltraShape na Scenariu je zamčený za tarifem Pro (`accessRestrictions` 50, účet má `cu-basic`,
běh vrací 403 `ModelAccessRestrictedError`; Pro stojí od 45 $/měsíc). Než za to platit, zkusilo se,
kam došahne Meshy, když se mu řekne o geometrii: `--hi` v `Tools/Assets/meshy_generate.py` posílá
`geometry_resolution: "4k"` a `target_polycount: 30000`.

| Verze | Trojúhelníky | Povrch |
| --- | --- | --- |
| Procedurálně | 788 | ostré, ale holé |
| Meshy standard (3 000) | 2 928 | zvlněná deska, měkké detaily |
| **Meshy 4k (`--hi`)** | **28 624** | rovná deska, ostré šrouby, čitelné kolébkové přepínače, vystouplý štítek |

Stálo to 25 kreditů místo 20. Srovnání: `Saved/Kitbash/compare_resolution.png`. Závěr: na hrubý
povrchový detail u panelových dílů stačí Meshy ve 4k a předplatné Pro kvůli UltraShape zatím nemá
opodstatnění; vstupy pro UltraShape jsou ve Scenariu nahrané, takže případný test bude na jedno
zapnutí tarifu.

### Co umí Scenario v základním tarifu (23. 9. 2026)

Účet `cu-basic` vidí 161 modelů; `accessRestrictions` 0 znamená dostupné, 50 je Pro (tam sedí
UltraShape). Kroky, které jsme dosud dělali ručně, jsou dostupné jako modely:

| Model | K čemu | Nahrazuje |
| --- | --- | --- |
| `model_tencent-smarttopology` (Hunyuan Polygen 1.5) | AI retopologie hustého GLB na čistou geometrii, `polygonType` triangle/quad, `faceLevel` | `decimate` v `build_ai_ship.py` |
| `model_tencent-uv-unwrapping` | automatické UV do 30 000 ploch | ruční UV před `rebake` |
| `model_hunyuan-3d-part` | rozdělení meshe na díly (dobré na hard-surface) | krok `split` |
| `model_tripo-v3-0-texturing` | PBR textury na hotový mesh z promptu nebo obrázku | doplněk k `rebake` |
| `model_tripo-v3-1-image-to-3d` (Tripo 3.1) | obrázek → 3D, `smartLowPoly`, `quad`, `generateParts`, PBR | placené Meshy |
| `model_hunyuan-3d-v2-1` | obrázek → 3D, `targetFaceNum` | placené Meshy |

Klient: `Tools/Assets/scenario_mcp.py` (`tools`, `upload`, `run`, `get`). Upload jde přes MCP
server (dokončovací krok vícedílného uploadu není v REST dokumentaci), spouštění a stahování přes
REST `POST /v1/generate/custom/<modelId>` a `GET /v1/jobs/<id>`.

Ceny prvních běhů: retopologie hustého panelu 113 CU, Tripo 3.1 s texturou 75 CU.

### AI retopologie místo decimace (23. 9. 2026, první ostrý běh)

Hustý panel z Meshy 4k prošel přes `model_tencent-smarttopology` (Hunyuan Polygen 1.5,
`polygonType` triangle, `faceLevel` medium):

| | Trojúhelníky | Vrcholy | Soubor |
| --- | --- | --- | --- |
| Meshy 4k (vstup) | 28 624 | 26 143 | 1,0 MB |
| **Polygen retopologie** | **3 131** | 1 611 | 56,8 kB |

Devítinásobné zmenšení a deska, šrouby, přepínače i štítek zůstaly čitelné (`Saved/Kitbash/compare_retopo.png`).
Běh stál 113 CU a trval ~20 minut; průběh přitom hlásí 10 % a pak skočí rovnou na hotovo, takže
podle `progress` se nedá poznat, jestli úloha žije — kouká se na `updatedAt`.

Praktický závěr pro `build_ai_ship.py`: krok `decimate` (Blender) může nahradit Polygen, protože
drží ostré hrany hard-surface dílů líp než decimace podle chyby.

### Tripo 3.1 na stejném dílu: neúspěch (23. 9. 2026)

Stejný referenční obrázek (šedý clay render panelu), `geometryQuality: detailed`, `smartLowPoly`,
PBR, `faceLimit` 20 000 → 21 302 trojúhelníků, ale **model je rozbitý**: díry v desce, přepínače
chybí, textura přepálená do bílé (`Saved/Kitbash/tripo_textured.png`). 75 CU.

Dvě vysvětlení, obě se dají příště otestovat:
- vstup byl **šedý clay render bez barvy a bez kontextu**; image-to-3D čeká spíš barevný koncept
  s materiálem a osvětlením (Meshy dostal textový popis, ne tenhle obrázek),
- `smartLowPoly` zjednodušuje geometrii už při generování a u malých technických prvků ji zřejmě
  smete.

Zatím tedy platí: **geometrii generovat v Meshy ve 4k**, a Scenario používat na kroky za tím
(retopologie, UV, dělení na díly, textury). Než Tripo zavrhnout, stojí za zkoušku barevný koncept
jako vstup a `smartLowPoly` vypnuté.

## Exteriér: hard-surface místo AI skenu (24. 9. 2026, pilot na gondole první stíhačky)

Pravidlo „AI dělá obálku, detail je procedurální“ platí i pro exteriér.

**Proč:** trup z Meshy má 92 % hran pod 36° (WORKFLOW kap. 10, bod 4). Je to organický sken a
nemá rovné panely. Bevel ani vážené normály na něm nic nezmění a na úroveň SC se z něj nedostaneme.

### Postup

1. **AI model je jen objemová reference.**
   - Meshy / Higgsfield trup se nepoužije jako herní mesh.
   - Změří se na něm osy, poloměry a délky: `silhouette_compare.py` masky ve světových souřadnicích,
     střed a profil z masek.
   - Může sloužit i jako cíl pro shrinkwrap volných ploch.
   - Nic z jeho trojúhelníků se nepřebírá.
2. **Loď se staví po dílech:** nos, trup, křídla, gondoly motorů, podvozek. Každý díl má vlastní JSON
   recept v `ArtSource/Ships/<Loď>/HardSurface/<díl>.json` a builder skript v `Tools/Blender/hs_*.py`.
   - Rotační díly (gondola, nádrž, věž, tryska): `Tools/Blender/hs_build_part.py`. Profil (x, r)
     má skoky jako dvojice bodů se stejným x.
   - Ploché a skořepinové díly (nos, trup, křídla): další builder stejného typu (zatím není). Plochy
     z polygonů a průřezů, shrinkwrap na AI objem.
3. **Skutečná hard-surface geometrie:**
   - panely jako samostatné skořepiny s tloušťkou a mezerou 8 mm nad tmavou nosnou konstrukcí, takže
     spára je skutečná, ne namalovaná;
   - pásy, příruby a drážky jako plné prstence se schody mezi sekcemi;
   - sání a tryska modelované (kanál, náboj, loukotě, prstenec);
   - na všem `Bevel` (limit úhel 30°, 6 mm, 3 segmenty, harden normals) a `WeightedNormal` (keep sharp);
     ostré hrany jsou označené podle úhlu.
4. **Greebly jako znovupoužitelný kit.**
   - Kolekce `HS_Kit` je vyloučená z view layeru, obsahuje vent, hatch, hatch_large, sensor, strip a bolt.
   - Geometry nodes skupina `HS_KitInstancer` je instancuje na mračno bodů s atributy `kit_index`
     a `rot` (Euler).
   - Kam co patří, říká recept (`greebles`, `bolt_rings`), takže je to opakovatelné a upravitelné bez
     klikání.
5. **Kontrola:**
   - `hs_render_views.py`: tři pravoúhlé pohledy a 3/4, Workbench s kavitou a obrysy, stejně pro
     dnešní Meshy díl (výřez) i pro nový díl;
   - `silhouette_compare.py`: IoU proti výřezu AI objemu;
   - list vedle sebe a detail zblízka.

### Pilot: horní levá gondola první stíhačky (recept a soubory smazány s lodí 24. 9. 2026, historie v gitu)

- **Postavení:** 37 objektů, ~91 tis. trojúhelníků bez instancí kitu, 123 bodů kitu, build ~15 s
  headless.
- **Shoda siluety s Meshy gondolou** (výřez s válcem r 1,24 m, bez pylonu), průměr IoU:
  - **0,854** – první verze, poloměry z maximální vzdálenosti vrcholů, což započítává i výstupky;
  - **0,894** – druhá verze, osa a poloměry dopočítané z masek (střed y 4,49, z 1,92; tělo r 1,12).
    Po pohledech: zepředu 0,878, z boku 0,906, shora 0,898.
  - Zbylý rozdíl (~9 % „navíc“) dělají hlavně greebly a pásy nad obrysem. Meshy má na obrysu
    zaoblené a zdeformované tvary, rovné panely je nekopírují 1:1. To je záměr.
- **Vzhled:** rovné panely, skutečné spáry, čisté zkosení, čitelné sání s nábojem a loukotěmi. Meshy je
  vedle toho hrbolatý sken se zubatými okraji.
- **Známé nedostatky pilotu:**
  - díly kitu jsou rovné, takže velké víko (1,1 × 0,7 m) na válci r 1,12 odstává na krajích asi o 5 cm.
    Řešení: ohýbat instance podle povrchu (GN raycast / deform), nebo zakřivené varianty dílů;
  - chybí pylon a napojení na křídlo;
  - chybí UV a materiálové zóny;
  - díl ještě nešel do Unrealu.
- **Loď byla 24. 9. 2026 celá odstraněna;** postup platí pro další lodě.

## Wayfarer v2: kit jako struktura interiéru (25. 9. 2026)

Interiér Wayfareru v1 z procedurálních boxů autor odmítl. Pilot v2 staví chodbu z kitu Quaternius:
`Tools/Blender/hs_interior_kit.py` vkládá díly s jejich UV do lodního receptu (part `InteriorKit`), trim
textury jsou přetónované `Tools/Assets/tone_kit_textures.py` a v UE běží na `M_Ship_PBR` (vzorkuje v prostoru
lodi, na letící lodi se nic neposouvá, na rozdíl od světového triplanaru `M_KitTrim` Steadfastu). Procedurálně
jen přesné díly (portály, trubky, skříňky, ovladače v kokpitu), značení jako decaly.

## Kde brát hotové díly interiéru (průzkum 23. 9. 2026)

Průzkum volně dostupných zdrojů pro třetí cestu („koupený/stažený base“), seřazeno podle toho,
jak draho vyjde licence:

| Zdroj | Licence | Co tam je | Poznámka |
| --- | --- | --- | --- |
| **Quaternius** ([packs](https://quaternius.com/packs/)) | **CC0**, bez atribuce | modulární sci-fi interiéry: Modular Sci-Fi MegaKit (270+ dílů), Ultimate Modular Sci-Fi (46), Sci-Fi Essentials Kit | FBX/OBJ/glTF/Blend; stahuje se přes itch.io, přímý odkaz na webu není |
| **Poly Haven** | CC0 | fotoskeny reálných věcí: sudy, bedny, nářadí, svěráky, ventily (521 modelů, z toho ~177 průmyslových) | **ne sci-fi**; dobré na nákladový prostor a dílnu Steadfastu, ne na kokpit. Už máme `fetch_polyhaven.py` |
| **ambientCG** | CC0 | materiály, ne modely | zapsáno ve `WORKFLOW.md` bod 14 |
| **Sketchfab** | většinou **CC-BY** (CC0 u sci-fi prakticky nula) | panely, terminály, konzole, dveře, sedačky, bedny v rozumné hustotě (350–8 000 ploch) | **vyžaduje uvedení autora** → `Docs/Credits.md`; stahování chce přihlášení/token |
| Fab, CGTrader, TurboSquid | placené i free s různými licencemi | kvalitní hotové kity | licenci číst kus po kuse |

Konkrétní kandidáti ze Sketchfabu (71 kusů s licencí, autorem, počtem ploch a odkazem) jsou
v `ArtSource/Ships/Steadfast/Kitbash/free_asset_survey.json`. Dotazy: sci-fi control panel,
sci-fi console, spaceship cockpit interior, vent grille, cockpit seat, door panel, crate,
modular pipes. Filtrováno na stažitelné, 300–60 000 ploch.

**Pořadí, v jakém to zkoušet u Steadfastu:** nejdřív Quaternius (CC0, žádné závazky, modulární
grid), pak Sketchfab kusy pro věci, co v kitu chybí (a zapsat autora do `Docs/Credits.md`),
a procedurálně dodělat technický detail, který má být přesný (tlačítka, přepínače, rámy).

## Paleta gamespace a restylizace staženého kitu (23. 9. 2026)

Do téhle chvíle byla paleta popsaná jen slovy („gunmetal + oranžové akcenty“). Čísla, lineární RGB:

| | Hodnota | Kde |
| --- | --- | --- |
| **Gunmetal** (trup, stěny, podlahy) | `0.35, 0.42, 0.55` jako násobek po odbarvení (zesvětlení ×0,8, metallic ×0,4) | modrá ocel; platí jen se **studeným světlem** (pracovní světla 7000 K) – pod teplým světlem vyjde stříbrně (měřeno 23. 9. 2026, HANDOFF bod 59; původně 0.62/0.65/0.70) |
| **Oranžová** (akcenty, pásy, západky) | `0.85, 0.34, 0.06` | Halcyon Freightworks |

Restylizaci dělá `Tools/Blender/recolour_kit.py`: texturu kitu odbarví, zesvětlí a přetónuje do
gunmetalu (kresba panelů a špína zůstanou), červené akcenty v base colouru přebarví na oranžovou
a **emisivní mapu kitu použije jako oranžové svítící pásy**. To poslední je u Quaternius MegaKitu
to podstatné — jeho díly mají akcent výhradně v emisivní mapě, v base colouru žádný barevný pruh
není, takže bez toho vyjde všechno jednolitě šedé.

Ověřeno na nákladovém prostoru Steadfastu 8 × 6 m se stropem 2 m: **16 806 trojúhelníků** i s
bednami, sudy, potrubím a ventilací (`Saved/Kitbash/steadfast_cargobay.png`).
