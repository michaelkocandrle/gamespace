# Modulární AI asset pipeline: kdy generovat vcelku, kdy rozkládat na díly

Zjištěno a zapsáno 22. 9. 2026, po srovnání dvou výsledků: exteriér lodi (Ironclad Vanguard)
dopadl dobře, interiér kokpitu ne, i po několika kolech opravování textur a osvětlení. Rozdíl
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
kitbash pilot níže pro Vanguard) — ten pilot ukázal částečně dobré výsledky u
Vanguardu, ale u Steadfast interiéru se ukázalo, že i "vyhrávající" AI díly
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
  viz `WORKFLOW.md` 3.1b; vstupy pro první test: `ArtSource/Ships/Vanguard/Kitbash/UltraShape_input_SwitchPanel.glb`
  a `.../UltraShape/SwitchPanel_three_quarter.png`) — "3D geometry super-resolution": dovybaví
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
základ konzole 46 × 28 cm: `ArtSource/Ships/Vanguard/Kitbash/CentreConsole.blend`, celkem
3 936 trojúhelníků. Zadání dílů (jméno, rozměr, prompt) je v `Tools/Assets/kitbash_parts.json`,
aby se daly generovat kterýmkoliv nástrojem a pak porovnat se stejným měřítkem.

### Co který zdroj dílů umí

| Zdroj | Stav | Poznámka |
| --- | --- | --- |
| **Procedurálně v Blenderu** | **funguje, hotovo** | Přepínací panel (788 tris), mřížka (920), svazek kabelů (816), rám displeje (436). Přesné rozměry, čistá topologie, zadarmo a opakovatelné. Pro malé technické díly je to rychlejší než generovat a pak opravovat. |
| **Meshy** | **funguje** | `Tools/Assets/meshy_generate.py` (text-to-3D v2, preview + volitelný refine, stáhne GLB do `ArtSource/Ships/Vanguard/Kitbash/Meshy/`). Klíč se bere z `MESHY_API_KEY`, nikdy z repozitáře. `--dry-run` vypíše prompty bez volání. |
| **Hyper3D Rodin** (Blender MCP) | **nepoužitelné zadarmo** | Zapíná se `blendermcp_use_hyper3d` + klíč; vestavěný zkušební klíč (`vibecoding`) vrací `API_INSUFFICIENT_FUNDS` – je vyčerpaný. Potřebuje vlastní klíč (hyper3d.ai nebo FAL). |
| **Hunyuan3D** (Blender MCP) | nevyzkoušeno | Vypnuté, chce vlastní klíč. |

### Nástrahy z pilotu

- `bpy.ops.object.join` (a operátory obecně) přes MCP padá na `poll() failed, context is incorrect`.
  Geometrii skládej přímo přes `bmesh` a objekty vytvářej `bpy.data.objects.new` – bez operátorů.
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
