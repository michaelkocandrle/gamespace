# Gamespace – vstupní bod pro Claude Code

Sci-fi vesmírná hra v **Unreal Engine 5.8, C++**. Projekt je v `C:\gamespace\gamespace`, modul
`gamespace`, repozitář `michaelkocandrle/gamespace`, větev `main`.

- **Cíl:** let a interiéry 1:1 se Star Citizen. Hráč letí z vesmíru až na povrch planety, vystoupí a chodí po ní.
- **Lodě:**
  - Wayfarer (Halcyon Freightworks) je malá multirole pro jednoho pilota, nahrazuje odstraněný Vanguard.
    Model v1 létá ve hře (exteriér z Higgsfieldu, dočasný kokpit), další krok interiér. Přehled flotily a dossiery: Ship Matrix
    (`Tools/Design/build_ship_matrix.py`, skill `ship-pipeline` 1b);
  - Steadfast (Halcyon Freightworks) je nákladní loď s interiérem. Její 2D návrh v2 čeká na schválení.
- **Autor** není herní vývojář. Mluví česky a hraje zabalenou hru ve 1080p na RTX 2060 6 GB.

## Jazyk a komunikace

- Odpovídej **česky**. Kód, komentáře a commit messages piš **anglicky**.
- Všechno se mění skriptem nebo kódem, nikdy klikáním v editoru. Když je potřeba akce autora
  (přihlášení, GUI, restart), zastav se a napiš mu přesný postup.
- Neptej se, jestli autorovi běží hra. Prostě balíš; o běžící hře se zmiň, jen když se balení zasekne.

## Pracovní smyčka jednoho kroku

1. **Zadání a reference.**
   - Vizuální vzor je SC (`starcitizenreference/`, autorovy screenshoty).
   - Odchylku, kterou nejde odstranit, pojmenuj.
2. **Malé kroky.** Každý je hotový, otestovaný a commitnutý.
3. **Build** editoru po změně C++ (editor musí být zavřený).
4. **Headless testy**, kterých se změna týká; po větší změně všechny.
5. **Package + Shots.** Každý snímek si **sám prohlédni** (Read na PNG). Autorovi nikdy nepředávej nic, co jsi neviděl.
   - **Žádné spouštění editoru ani PIE kvůli kontrole.** Ověřuje se přes zabalenou hru.
5b. **Vizuální kritik (každé předání vizuální práce, autor 25. 9. 2026).** Podagent `visual-critic`
   (`.claude/agents/`, jen čtení, nejsilnější model) porovná výsledek s referencí. Postup: skill `ship-pipeline` 7b.
   - Listy `python Tools/Review/make_compare_sheet.py <review.json>`: reference vlevo, výsledek vpravo; zblízka, střední, zdálky; den, noc, vesmír.
   - Kritik dostane **jen** `brief.md` a listy: žádný postup, dobu práce, záměry ani vlastní názor.
   - FAIL → oprav body „musí se opravit“ a znovu, nejvýš 3 kola, pak předej i s otevřenými body.
   - Žádnou výtku tiše nevynechat: u každé opraveno / neopraveno a proč; nesouhlas zdůvodni.
   - Neplatnou výtku dolož výřezem ze snímku, výřezy ulož k recenzi (`<téma>/evidence/`).
   - Recenze do `Docs/Reviews/<datum>_<téma>.md` (listy, výstup kritika, reakce na každý bod).
   - Kritik doplňuje automatické kontroly (`test_ship_geometry.py`, testy UE), nenahrazuje je.
   - Co autor vytkne a kritik přehlédl, doplň do zadání kritika a do `Docs/Reviews/calibration.md`.
6. **Dokumentace:**
   - bod do `Docs/HANDOFF.md` kap. 5;
   - nová nástraha do `Docs/WORKFLOW.md` kap. 9;
   - trvalé know-how i do příslušného skillu.
7. **Commit a push.**
8. **Odpověď autorovi česky:**
   - co se změnilo a proč;
   - testy a snímky, které jsi zkontroloval;
   - že je hra v `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe`;
   - přesný testovací scénář (klávesy, kam jít);
   - co musí posoudit jen autor;
   - rizika;
   - u vizuální práce: verdikt a skóre posledního kola kritika, počet kol, výtky s reakcí a odkaz na recenzi.

**Iterace vzhledu vs. předání** (autor, 24. 9. 2026):
- Při iteraci vzhledu (modelování, decaly, materiály, světla) se po každé změně **nebalí** a nepouští celá sada testů:
  - kontrola přes render v Blenderu (Eevee náhled s atlasy), případně snímky z už zabaleného buildu;
  - jen testy, kterých se změna přímo týká (např. `test_ship_import.py`).
- **Před předáním autorovi:** jednou celá sada testů, zabalení hry a finální snímky.
- Změny C++ a herní logiky dál plným postupem (build, testy, balení, snímky).
- V odpovědi uveď zhruba čas práce vs. čas testů, balení a snímků.

**Lodě a interiéry:** nejdřív detailní 2D návrh a až po schválení 3D (skill `ship-pipeline`).
Každý objekt musí mít účel; žádná výplň a žádné kompromisy.

## Příkazy

Build editoru (PowerShell):

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" gamespaceEditor Win64 Development -Project="C:\gamespace\gamespace\gamespace.uproject" -WaitMutex -FromMsBuild
```

Headless Python v UE a testy. Spouštěj **nástrojem PowerShell**; přes bash se rozbije `$PSScriptRoot`.

```powershell
.\Tools\run_editor_python.ps1 Tools\Tests\test_interior.py
```

Balení a snímky (~5 min balení):

```powershell
.\Tools\Package.ps1
.\Tools\Shots.ps1 -Preset <preset> -Package -Width 1920 -Height 1080
```

- Presety jsou v `Tools/Shots/*.json`.
- Snímky se ukládají do `Saved/Shots/...`; s přepínačem `-Keep` i do `Docs/Shots/`.

Blender 5.2 headless (z Git Bash **vždy** s `MSYS_NO_PATHCONV=1`, jinak se přepíšou cesty jako `//Export`):

```bash
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python Tools/Blender/<skript>.py -- <argumenty>
```

2D návrh lodi (výkresy z layout JSON):

```bash
python Tools/Design/draw_ship_design.py ArtSource/Ships/<Loď>/Design/<Loď>_layout.json
```

## Klíčové cesty

| Co | Kde |
| --- | --- |
| C++ | `Source/gamespace/` (SpaceshipPawn, PlayerCharacter, SpaceInterior, SpaceFlightHud, CockpitDisplayComponent, SpaceShotRunner…) |
| UE Python skripty | `Tools/Assets/` (importy), `Tools/Tests/` (headless testy) |
| Blender skripty | `Tools/Blender/` (recepty lodí, `build_steadfast_interior.py`) |
| Snímky | `Tools/Shots.ps1`, `Tools/Shots/*.json`, `Tools/Shots/measure_*.py` |
| Zdroje lodí | `ArtSource/Ships/<Loď>/` (`*_spec.json` ve tvaru Ship Matrix, `*_setup.json`, `Design/`) |
| Reference SC | `starcitizenreference/` (master reference), `Docs/UI/` |
| Zabalená hra | `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe` |
| API klíče (Meshy, Scenario) | `C:\gamespace\secrets\`. **Nikdy do repozitáře.** |

## Git

- Před commitem `git status`. Commituj **vždy** takto; tahle cesta autora se nikdy necommituje:

  ```bash
  git add -A -- . ':!Docs/UI/Screenshot 2026-09-21 150400.png'
  ```

- Commit message je anglicky a končí řádkem `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- `git push origin main` po každém kroku. **Nikdy force push ani přepis historie**: autor má druhý klon v práci.

## Skills (načítají se podle potřeby z `.claude/skills/`)

| Skill | Kdy |
| --- | --- |
| `ship-pipeline` | nová loď: 2D návrh → AI model → Blender recept → import do UE |
| `ship-interior` | interiér lodi (Steadfast): builder, import, materiály, světla, dveře, gravitace, první osoba |
| `blender-mcp` | Blender headless i živý přes MCP, operátory vs. bmesh, nástrahy Blenderu |
| `unreal-scripting` | build, headless Python v UE, testy, balení a cook, nástrahy C++/UHT/Pythonu |
| `unreal-shots-and-look` | snímky ze zabalené hry, měření vzhledu a výkonu, ladění za běhu, nástrahy vykreslování |
| `cockpit-displays` | MFD, HUD, světla a expozice kokpitu |
| `asset-sources` | Meshy, Scenario, Higgsfield, ambientCG, licence a Credits, reference z videa |

## Velké dokumenty (nečti celé, hledej grepem)

- `Docs/HANDOFF.md`: stav projektu, historie hotových bodů (kap. 5), známé problémy.
- `Docs/WORKFLOW.md`: postupy a **úplný seznam nástrah** (kap. 9; formát příznak → příčina → řešení).
- `README.md`: technický popis systémů (anglicky).
- `Docs/Ships/ShipPipeline.md`: pipeline lodi v detailu.
