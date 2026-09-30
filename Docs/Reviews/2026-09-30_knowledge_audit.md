# Kontrola znalostního systému: rozpory, zastaralé odkazy, jeden zdroj pravdy (30. 9. 2026)

Podnět: `Gamespace_AI_Development_Audit_v1.docx` (víc zdrojů pravdy bez hierarchie). Prošly se `CLAUDE.md`, všech
7 skillů, `.claude/agents/visual-critic.md`, `Docs/WORKFLOW.md`, `Docs/HANDOFF.md` (kap. 1–4, 6–13), `README.md`,
`Docs/Ships/ShipPipeline.md`, `Docs/Ships/Fleet.md`, `Docs/AssetPipeline_Modular.md`, `Docs/AssetSources_Free.md`.
Kontrolu dělali tři čtecí podagenti (rozpory, ~540 cest a ~320 křížových odkazů) a oprava šla podle hierarchie
v `CLAUDE.md`: CLAUDE.md > CURRENT.md > skilly > WORKFLOW.md > ARCHITECTURE.md > Reviews > HANDOFF.md.

## Nová struktura

| Soubor | Role |
| --- | --- |
| `CLAUDE.md` | hierarchie autority, pravidla, brány kroku, pravidla paralelní práce, index skillů a dokumentů |
| `Docs/CURRENT.md` (nový) | jediný soubor aktuálního stavu: stav, rozhodnutí autora, známé problémy, další kroky; hook SessionStart ho vkládá do každé session (`.claude/settings.json`, `.claude/hooks/session_start.ps1`) |
| `Docs/ARCHITECTURE.md` (nový) | stabilní rozhodnutí, závěry auditu v1, odložený pevný časový krok |
| skill `visual-review` (nový) | postup kritika a checklisty (dřív třikrát: CLAUDE.md 5b, ship-pipeline 7b, ship-interior) |
| `Docs/Archive/` (nový) | historie přesunutá doslovně ze skillů a WORKFLOW kap. 10 |
| `Docs/HANDOFF.md` | označen jako archiv, obsah beze změny |

`NEXT_SESSION.md` v repozitáři není (ani v historii), nebylo co slučovat. SessionStart hook předtím neexistoval,
vznikl nový.

## Rozpory a jak se vyřešily

| # | Rozpor | Rozhodnutí (vyšší vrstva) | Opraveno v |
| --- | --- | --- | --- |
| C1 | Vzhled „jen v zabalené hře“ / „v PIE“ proti rychlé smyčce `-Editor` (autor 28. 9.) | CLAUDE.md: `-Editor` během kroku, balení na konci, PIE ne | WORKFLOW 9.2 e (jediný popis), unreal-shots-and-look, unreal-scripting, cockpit-displays, ship-interior, README; HANDOFF archiv |
| C2 | Balit po každé změně proti „balí se jen na konci kroku“ | CLAUDE.md | WORKFLOW kap. 1 a 6, unreal-scripting 4, cockpit-displays, ship-interior |
| C3 | Balení mezi koly kritika | CLAUDE.md (kola z `-Editor`) | skill `visual-review` |
| C4 | „Hru nikdy neukončuj“ proti `Package.ps1`, který každý proces `gamespace` ukončí, a „neptej se“ | CLAUDE.md + skutečné chování skriptu | unreal-scripting 4 (jediný popis), WORKFLOW 1, 6, 9.1 a, unreal-shots-and-look |
| C5 | Exteriér lodi z AI modelu proti stavbě z výkresu (od 24. 9.) | ship-pipeline 3b2 + paměť autora | ship-pipeline (pořadí fází, popis, AI recept do `legacy-ai-model.md`), asset-sources, CLAUDE.md, README, banery ShipPipeline.md a AssetPipeline_Modular.md |
| C6 | Paleta: stará „modrá ocel“ a Steadfast 0,33/0,33/0,34 proti paletě kitu | paleta kitu v `kit_rules.json` | ship-pipeline, asset-sources, unreal-shots-and-look, AssetPipeline_Modular |
| C7 | Quaternius jako nosná vrstva proti vlastnímu kitu (od 26. 9.) | ship-interior | asset-sources, ship-interior, AssetPipeline_Modular |
| C8 | „Sedadla z Meshy schválená“ proti vyřazení AI geometrie (25. 9.) | ship-interior | ship-interior, asset-sources, AssetSources_Free |
| C9 | Kit: „nikdy complex-as-simple“ proti kolizi po polygonech průchozí lodi | přechodná výjimka do optimalizace | `kit-design.md`, ship-interior |
| C10 | Blender MCP: „současný komunitní“ proti „výchozí blender-lab“ | blender-lab pro scénu a dokumentaci, stavba jen headless | blender-mcp |
| C11 | Po kroku doplnit HANDOFF kap. 5, 11, 13 | CURRENT.md | CLAUDE.md, WORKFLOW 8, unreal-scripting 5 |
| C12 | „Přečti celý dokument“ (HANDOFF, WORKFLOW) proti „hledej grepem“ | CLAUDE.md | hlavička WORKFLOW, banner HANDOFF |
| C13 | Výchozí grafika „Cinematic“ proti kódu (epická, 75 %, TSR) | kód | README; WORKFLOW kap. 10 v archivu |
| C14 | Podpis commitu „Claude Opus 5“ ve 4 dokumentech, v praxi „Opus 5.5“ | stojí jen v CLAUDE.md | unreal-scripting a WORKFLOW odkazují na CLAUDE.md. **Text v CLAUDE.md jsem neměnil (pravidlo autora), rozhodne autor.** |
| C15 | „Celá sada testů“ nejasná | `Tools/Test.ps1 -All` | CLAUDE.md brána 7 |

## Zastaralý stav a odkazy (opraveno)

- Stav Wayfareru („model v1, dočasný kokpit, další krok interiér“) v CLAUDE.md, Fleet.md → `CURRENT.md`.
  `Wayfarer_spec.json` má dál `_status: "design_v1_approved, model_v1_flying"`: je to datový vstup dossieru, nechal
  jsem ho; aktualizuje se s dalším krokem lodi (dossier se pak publikuje znovu).
- „Loď pod testem `SHIP = None`“ v unreal-scripting, WORKFLOW 2.2 a 5, README (2×) a „žádná loď nemá živé displeje“
  v cockpit-displays → `SHIP = "Wayfarer"`, `MENU_SHIP = "Wayfarer"`.
- Ovládání v README: F vstane z křesla / sedne / ven po rampě, U ukázka kitu, I Steadfast.
- Banner „návrh ke schválení, do schválení se nic nestaví“ u designového jazyka kitu (dávky 1–4 už stojí).
- `ship-pipeline`: seznam speců bez Wayfareru; příkazy s pevnou cestou `C:\gamespace\gamespace` (ve worktree
  špatně) → cesty z kořene repozitáře; `<Loď>_Meshy.blend` → `<Loď>_HS_Game.blend`.
- `ShipPipeline.md`: rozbitý řádek (`\r`, `\t` z cesty `.\Tools\run_editor_python.ps1`), neexistující `M_Ship_Master`.
- Křížové odkazy: `unreal-shots-and-look` „HANDOFF ~ř. 1370“, WORKFLOW 6.1 uvnitř kap. 7 (nadpis přesunut),
  „nástraha 9.2h“ → 9.6 cy, „Viz 9.4a níže“ → WORKFLOW 9.4 a, „WORKFLOW bod 14“ → skill.
- Pevná cesta k UE v dokumentaci → `Tools/UERoot.ps1` / `Tools/Build.ps1` (krok 1).

## Zdvojené postupy (sjednoceno)

Pravidla gitu, brány kroku a odpověď autorovi jen v `CLAUDE.md`; postup kritika jen ve `visual-review`; popis
nezabaleného projektu jen ve WORKFLOW 9.2 e; seznam testů jen v unreal-scripting 3; úplný seznam presetů jsou
soubory `Tools/Shots/*.json` s `_comment` (tabulky ve skillech uvádějí jen opakovaně používané).

## Neopraveno (vědomě)

- `Docs/HANDOFF.md` obsahově (Vanguard v kap. 1, 6, 8, 11, dvakrát bod 33): archiv, jen banner.
- `Docs/Ships/ShipPipeline.md` a `Docs/AssetPipeline_Modular.md` popisují starší AI cestu; dostaly banner, text zůstal.
- Duplicitní tabulky konzolových příkazů `space.*` (unreal-shots-and-look, ship-interior, WORKFLOW 6.1 a 11.1) a
  receptu displejů AI lodi (WORKFLOW 2.1, `legacy-ai-model.md`, `blender-mcp/reference.md`): různé výřezy pro různé
  úlohy, bez rozporu.
- Nepopsané presety (`kit_perf_*`, `night_views`, `compare_*` …): popisuje je jejich `_comment`.
- `SyntaxWarning` v docstringách šesti skriptů `Tools/Assets` (zapsáno v `CURRENT.md`).

## Kontext načítaný do session (řádky, stav po krocích 1–6)

| Co | Před (44c26cc) | Po | Změna |
| --- | --- | --- | --- |
| `CLAUDE.md` (vždy) | 158 | 111 | −47 |
| `Docs/CURRENT.md` (vždy, nově přes hook) | – | 73 | +73 |
| **Vždy načtené celkem** | **158** | **184** | **+26** (místo dřívějšího čtení HANDOFF podle potřeby) |
| `ship-interior/SKILL.md` | 968 | 237 | −731 |
| `ship-pipeline/SKILL.md` | 822 | 539 | −283 |
| `blender-mcp/SKILL.md` | 258 | 162 | −96 |
| `unreal-shots-and-look/SKILL.md` | 256 | 257 | +1 |
| `asset-sources/SKILL.md` | 225 | 227 | +2 |
| `unreal-scripting/SKILL.md` | 210 | 211 | +1 (test runner a registr +, git a odpověď −) |
| `cockpit-displays/SKILL.md` | 203 | 202 | −1 |
| `visual-review/SKILL.md` (nový) | – | 90 | +90 |
| **Těla skillů celkem** (načtou se při použití skillu) | **2 942** | **1 925** | **−1 017 (−35 %)** |
| **CLAUDE.md + skilly** | **3 100** | **2 036** | **−1 064 (−34 %)** |
| Referenční soubory skillů (jen když úloha potřebuje) | – | 539 | `kit-design.md` 270, `legacy-ai-model.md` 117, `steadfast-legacy.md` 95, `blender-mcp/reference.md` 57 |

Doslovně přesunuto do archivu: `Docs/Archive/skills/ship-interior_2026-09-30.md`, `ship-pipeline_2026-09-30.md`,
`blender-mcp_2026-09-30.md`, `Docs/Archive/workflow-kap10_2026-09-19.md`. Nic se nesmazalo.
