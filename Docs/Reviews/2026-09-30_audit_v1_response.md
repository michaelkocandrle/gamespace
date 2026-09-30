# Reakce na externí audity v1 (30. 9. 2026)

Audity: `Gamespace_Audit_v1.docx` (kód a technika) a `Gamespace_AI_Development_Audit_v1.docx`
(vývojový systém s AI), oba v této složce. Zpracovala druhá session ve worktree `audit-v1-followup`
(bez editoru, balení, Blenderu a snímků).

Princip (autor, podle auditu): architekturu neměníme jen proto, že audit navrhuje jiný vzor. Měníme ji
z konkrétního technického důvodu nebo kvůli měřitelnému přínosu. Přijatá architektonická rozhodnutí
jsou v `Docs/ARCHITECTURE.md`.

## Audit kódu a techniky

| Nález auditu | Reakce | Stav |
| --- | --- | --- |
| P0: ~137 trackovaných `.pyc` / `__pycache__` | **Neplatí.** `git ls-files` = 0 souborů a `git log --all --diff-filter=A` = 0: v historii nikdy nebyly. Audit je nejspíš napočítal po vlastním `compileall`, který je vytvoří vedle skriptů. `.gitignore` je ignoruje. `Tools/Test.ps1` teď píše bytecode do `%TEMP%\gamespace_pycache` (`PYTHONPYCACHEPREFIX`). | nic se nemaže |
| P0: test `test_setup_file_overrides_manifest_in_order` padá na Linuxu | Platí. Test předával `C:/art/...`, na Linuxu relativní cestu, a `setup_path` volá `os.path.abspath`. Test teď staví absolutní cestu pro OS, na kterém běží (`os.path.abspath(os.sep)`). Ověřeno na Windows a v simulaci modelu cest POSIX (stará podoba dala `<cwd>/C:/art/...`). | hotovo |
| P0/P1: pevná cesta k UE 5.8 | Platí. `Tools/UERoot.ps1` je jediné místo: `$env:GAMESPACE_UE_ROOT`, jinak `C:\Program Files\Epic Games\UE_5.8`. Berou ji `Package.ps1`, `Play.ps1`, `Shots.ps1`, `run_editor_python.ps1`, nový `Build.ps1` i `install_mannequin_pack.py` (čte řádek `$default`). | hotovo |
| P0: jeden příkaz na testy | `Tools/Test.ps1`: offline (compileall + 5 testů bez UE a Blenderu) s jednotným souhrnem, `-Blender`, `-UE`, `-All`, `-Filter`. Při tom nalezeno: `run_editor_python.ps1` hlásil `RESULT: OK` i po `SUMMARY FAILED` (testy logují verdikt přes `unreal.log`) a `test_decal_orientation.py` vracel vždy exit 0. Obojí opraveno. | hotovo |

Vedlejší nález: `compileall` hlásí `SyntaxWarning: invalid escape sequence '\T'` v docstringách šesti
skriptů v `Tools/Assets` (`.\Tools\run_editor_python.ps1 ...` v obyčejném `"""`). Dnes jen varování;
v budoucím Pythonu chyba. Oprava je `r"""`, zatím neprovedena (mimo rozsah).

## Audit vývojového systému s AI

| Nález auditu | Reakce | Stav |
| --- | --- | --- |
| Víc zdrojů pravdy bez hierarchie | Hierarchie autority na začátku `CLAUDE.md`; `Docs/CURRENT.md` jako jediný aktuální stav (hook SessionStart), `Docs/ARCHITECTURE.md`, `Docs/HANDOFF.md` archiv. Rozpory a opravy: `2026-09-30_knowledge_audit.md`. | hotovo |
| Skilly přerůstají roli (historie, jednorázové stavy) | Historie doslovně do `Docs/Archive/skills/`, stabilní reference do souborů vedle skillu (načtou se jen při potřebě). Těla skillů 2 942 → 1 921 řádků. | hotovo |
| CLAUDE.md nezvětšovat | 158 → 111 řádků: pravidla, brány, hierarchie, index. | hotovo |
| Kritik: „nejméně 5 rozdílů“ tlačí na drobnosti | viz krok 3 (kalibrace v `calibration.md`) | krok 3 |
| Nevytvářet desítky mikro-skillů | Přibyl jediný skill `visual-review` (postup kritika byl třikrát). | – |

