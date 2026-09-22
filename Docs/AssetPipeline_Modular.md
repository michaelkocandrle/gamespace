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

1. **Rozděl na logické díly** podle funkce a geometrické složitosti:
   - Základní tvar/rám (velký, jednoduchý) — může jít přímo z multi-view generování
   - Malé detailní kousky (knoflík, displej rám, ventilace, kabeláž, šroubky) — **každý
     samostatně**, jako vlastní jednoduchý objekt. Tohle je přesně ta kategorie, kde je AI
     nejspolehlivější (jednoduchá silueta, čitelná plocha materiálu).
2. **Sesaď (kitbash) díly na základní tvar** přes Blender MCP s živou vizuální kontrolou
   (nainstalováno 19. 9. 2026, postup v `WORKFLOW.md` kapitola 3). Tohle je krok, který
   předtím chyběl úplně — zkoušelo se generovat rovnou hotovou kompozici.
3. Zbytek pipeline (decimate, UV, rebake, export, import) beze změny podle
   `Docs/Ships/ShipPipeline.md`.

## Nástroje k vyzkoušení pro geometrický detail (ne jen texturu)

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
