# Gamespace – vstupní bod pro Claude Code

## Hierarchie autority (při rozporu platí vyšší)

1. **`CLAUDE.md`** – pravidla spolupráce a brány workflow (tento soubor).
2. **`Docs/CURRENT.md`** – aktuální stav, rozhodnutí autora, známé problémy, další kroky (hook SessionStart ho
   vloží do každé nové session).
3. **Skilly** (`.claude/skills/`) – postupy, příkazy a nástrahy podle domény.
4. **`Docs/WORKFLOW.md`** – podrobný postup a úplný seznam nástrah (kap. 9).
5. **`Docs/ARCHITECTURE.md`** – stabilní architektonická rozhodnutí.
6. **`Docs/Reviews/`** – evidence rozhodnutí a iterací.
7. **`Docs/HANDOFF.md`** – archiv historie do 30. 9. 2026; nikdy ne zdroj aktuálního stavu.

Designová reference hry je `starcitizenreference/` (master reference). Rozpor nižšího dokumentu s vyšším oprav
v nižším ve stejném kroku.

## Projekt

Sci-fi vesmírná hra v **Unreal Engine 5.8, C++**, modul `gamespace`, repozitář `michaelkocandrle/gamespace`,
větev `main`, hlavní checkout `C:\gamespace\gamespace`. Cíl: let a interiéry 1:1 se Star Citizen, z vesmíru
až na povrch planety a pěšky po ní. Lodě a stav: `Docs/CURRENT.md`.
**Autor** není herní vývojář. Mluví česky a hraje zabalenou hru ve 1080p na RTX 2060 6 GB.

## Pravidla

- Odpovídej **česky**. Kód, komentáře a commit messages piš **anglicky**.
- Všechno se mění skriptem nebo kódem, nikdy klikáním v editoru nebo v Blenderu. Když je potřeba akce autora
  (přihlášení, GUI, restart), zastav se a napiš mu přesný postup.
- Neptej se, jestli autorovi běží hra. Prostě balíš; o běžící hře se zmiň, jen když se balení zasekne.
- **Lodě a interiéry:** nejdřív detailní 2D návrh a spec, 3D až po schválení (skill `ship-pipeline`). Každý
  objekt má účel; žádná výplň a žádné kompromisy.
- Architekturu neměň jen proto, že existuje jiný vzor; jen z konkrétního technického důvodu nebo kvůli
  měřitelnému přínosu (`Docs/ARCHITECTURE.md`).
- API klíče jsou v `C:\gamespace\secrets\`. **Nikdy do repozitáře.**

## Brány workflow jednoho kroku

1. **Zadání a reference.** Vzor je SC (`starcitizenreference/`, autorovy screenshoty); odchylku, kterou nejde
   odstranit, pojmenuj.
2. **Malé kroky.** Každý je hotový, otestovaný a commitnutý.
3. **Build** editoru po změně C++ (`.\Tools\Build.ps1`, editor zavřený).
4. **Testy**, kterých se změna týká; po větší změně všechny (`.\Tools\Test.ps1`, s `-UE` i testy v UE).
5. **Snímky.** Každý snímek si **sám prohlédni** (Read na PNG). Autorovi nikdy nepředávej nic, co jsi neviděl.
   - Během kroku rychlá smyčka bez balení: `.\Tools\Shots.ps1 -Preset <x> -Editor` (autor 28. 9. 2026).
   - Hra se balí jen na konci kroku: `.\Tools\Shots.ps1 -Preset <x> -Package` pro finální snímky a předání.
   - Žádné spouštění editoru s UI ani PIE kvůli kontrole.
6. **Vizuální kritik** u každého předání vizuální práce (autor 25. 9. 2026): skill `visual-review`. Nejvýš
   3 kola; žádnou výtku tiše nevynechat; recenze do `Docs/Reviews/<datum>_<téma>.md`.
7. **Iterace vzhledu vs. předání** (autor 24. 9. 2026): při ladění vzhledu se po každé změně nebalí a nepouští
   celá sada testů (Blender Eevee náhled nebo `-Editor`, jen dotčené testy). Před předáním jednou celá sada
   testů (`.\Tools\Test.ps1 -All`), balení a finální snímky. Změny C++ a herní logiky plným postupem.
8. **Dokumentace:** stav do `Docs/CURRENT.md` (hotové, známé problémy, další kroky); nová nástraha do
   `Docs/WORKFLOW.md` kap. 9; trvalé know-how do příslušného skillu; architektonické rozhodnutí do
   `Docs/ARCHITECTURE.md`. Historie patří do commitu a recenze, ne do skillu.
9. **Commit a push.**
10. **Odpověď autorovi česky:** co se změnilo a proč; testy a snímky, které jsi zkontroloval; že je hra
    v `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe`; přesný testovací scénář (klávesy, kam jít); co musí
    posoudit jen autor; rizika; u vizuální práce verdikt a skóre posledního kola kritika, počet kol, výtky
    s reakcí a odkaz na recenzi; zhruba čas práce vs. čas testů, balení a snímků.

## Paralelní práce (druhá session)

- Druhá session pracuje v **samostatném git worktree** na vlastní větvi, ne v hlavním checkoutu.
- Bez Unreal editoru, balení hry, Blenderu a snímků. Co potřebuje těžký zdroj, zapíše a nechá hlavní session.
- Každý krok commitne zvlášť. Slučování do `main` a push dělá **hlavní session**.

## Příkazy (PowerShell; bash rozbije `$PSScriptRoot`)

```powershell
.\Tools\Build.ps1                                   # build editoru (engine: GAMESPACE_UE_ROOT, Tools/UERoot.ps1)
.\Tools\Test.ps1                                    # offline testy + compileall; -UE, -Blender, -All, -Filter *x*
.\Tools\run_editor_python.ps1 Tools\Tests\test_interior.py
.\Tools\Shots.ps1 -Preset <preset> -Editor -Width 1920 -Height 1080   # snímky během kroku (~2 min)
.\Tools\Package.ps1                                 # balení na konci kroku (~5 min)
.\Tools\Shots.ps1 -Preset <preset> -Package -Width 1920 -Height 1080
```

Presety jsou v `Tools/Shots/*.json`; snímky v `Saved/Shots/...`, s `-Keep` i v `Docs/Shots/`.
Blender 5.2 headless z Git Bash **vždy** s `MSYS_NO_PATHCONV=1` (skill `blender-mcp`); 2D návrh lodi
`python Tools/Design/draw_ship_design.py ArtSource/Ships/<Loď>/Design/<Loď>_layout.json`.

## Git

- Před commitem `git status`. Commituj **vždy** takto; tahle cesta autora se nikdy necommituje:
  `git add -A -- . ':!Docs/UI/Screenshot 2026-09-21 150400.png'`
- Commit message je anglicky a končí řádkem `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- `git push origin main` po každém kroku (hlavní session). **Nikdy force push ani přepis historie**: autor má
  druhý klon v práci.

## Skilly (načítají se podle úkolu)

| Skill | Kdy |
| --- | --- |
| `ship-pipeline` | nová loď: Ship Matrix, 2D návrh, exteriér z výkresu (hs), decaly, export, import do UE |
| `ship-interior` | interiér lodi: interiérový kit, místnosti z kitu v lodi, průchozí loď, světla, materiály |
| `visual-review` | vizuální kritik: srovnávací listy, brief, kola, checklisty, kalibrace |
| `cockpit-displays` | MFD, HUD, světla a expozice kokpitu |
| `unreal-scripting` | build, headless Python v UE, testy, balení a cook, nástrahy C++/UHT/Pythonu |
| `unreal-shots-and-look` | snímky, měření vzhledu a výkonu, ladění za běhu, nástrahy vykreslování |
| `blender-mcp` | Blender headless i živý přes MCP, operátory vs. bmesh, nástrahy Blenderu |
| `asset-sources` | zdroje a licence assetů, Meshy, Scenario, Higgsfield, reference z videa |

## Dokumenty (velké nečti celé, hledej grepem)

- `Docs/CURRENT.md` (stav), `Docs/ARCHITECTURE.md` (rozhodnutí), `Docs/WORKFLOW.md` (postup, kap. 9 nástrahy
  ve formátu příznak → příčina → řešení), `README.md` (technický popis systémů, ovládání; anglicky).
- `Docs/Ships/ShipPipeline.md` (pipeline lodi v detailu), `Docs/Reviews/` (recenze, `calibration.md`),
  `Docs/Archive/` (historie přesunutá ze skillů), `Docs/HANDOFF.md` (archiv).
- Kód `Source/gamespace/`; skripty `Tools/` (`Assets` importy v UE, `Tests`, `Blender`, `Kit`, `Design`,
  `Review`, `Shots`); zdroje lodí `ArtSource/Ships/<Loď>/`; zabalená hra
  `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe`.
