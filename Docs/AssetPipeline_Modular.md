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
- **UltraShape 1.0** (scenario.com, open-source) — "3D geometry super-resolution": dovybaví
  hrubý mesh o skutečné povrchové detaily (až 8 mil. trojúhelníků na výstupu, čeká ho tedy
  stejný decimate krok jako ostatní AI modely). Podle popisu cílí primárně na organické tvary,
  u hard-surface sci-fi dílů neověřeno — vyzkoušet na konkrétním kusu, ne rovnou nasadit plošně.

## Kdy tohle použít příště

- Interiér kokpitu (aktuální otevřený problém) — kandidát č. 1 na přepracování tímhle
  postupem místo dalšího ladění jednoho monolitického AI modelu.
- Jakákoliv budoucí "obydlená" scéna (druhá loď s kabinou, stanice, interiér budovy).
- NE pro samotné lodě/postavy zvenku — tam dosavadní přímý postup funguje dobře.
