# Architektura: stabilní rozhodnutí

Rozhodnutí, která platí napříč kroky. Aktuální stav je v `Docs/CURRENT.md`, postupy ve skillech, technický popis
systémů v `README.md` (anglicky). **Architekturu neměníme jen proto, že někdo navrhne jiný vzor**; mění se
z konkrétního technického důvodu nebo kvůli měřitelnému přínosu (autor po auditu v1, 30. 9. 2026). Změna
rozhodnutí = úprava tohoto souboru ve stejném commitu, s datem a důvodem.

## 1. Engine a svět

- **UE 5.8, C++ modul `gamespace`.** Logika je v C++; Blueprinty jsou jen datové kontejnery (`BP_Ship_<Loď>`
  s hodnotami ze setupu, `BP_SpaceGameMode`). Žádné widget Blueprinty.
- **Hra pro jednoho hráče.** Žádná replikace; síťová architektura (rebasing, simulace, prediction) se navrhne,
  až bude multiplayer skutečný cíl.
- **Velké souřadnice:** LWC jsou v UE 5 vždy zapnuté (double). `USpaceOriginRebasingSubsystem` posouvá počátek
  k lodi po `RebaseDistanceKm`, aby zůstaly malé hodnoty pro to, co je dál float (vrcholy, GPU částice,
  materiály). Limity: počátek jen do ±21 474 km (int32 cm), Chaos teleportuje těla jedno po druhém.
- **Měřítko:** soustava v řádu stovek km (Veyra poloměr 120 km), přesuny mezi tělesy quantum skokem.
- **Herce najde C++ v buildu podle tagu, nikdy podle labelu** (label v zabalené hře neexistuje).

## 2. Loď a let

- **`ASpaceshipPawn`: vlastní kinematický 6DOF let**, ne fyzikální simulace. Rychlost se integruje v Ticku,
  pohyb sweepuje kořenový box `HullCollision` (ignoruje pawny); postava koliduje s UCX hully meshe `Hull`.
- Tah je zadaný jako **zrychlení po osách** (tak ho uvádí SC Ship Matrix); hmotnost není samostatný parametr.
- Letové hodnoty lodi jsou UPROPERTY pawnu nastavované ze `<Loď>_setup.json` přes `import_ship.py` do
  `BP_Ship_<Loď>`. Jméno takové vlastnosti je rozhraní: přejmenování rozbije setupy, BP a testy.
- **Quantum skok** posouvá loď přímo (`SetActorLocationAndRotation`, bez sweepu). Invarianty: skok povolí jen
  `EvaluateQuantum` (NAV, cíl, minimální vzdálenost, palivo, volná úsečka k bodu příjezdu včetně skořepin
  těles); během skoku se neřídí a cíl je pevný; příjezd na výšku nad povrchem cíle v rychlosti NAV.
- **Odložené rozhodnutí: pevný časový krok simulace letu** (audit v1, 4.3). Dnes let běží v Ticku s
  `DeltaSeconds` (frame-driven). Pevný krok (akumulátor, např. 120 Hz, interpolace prezentace) se zavede před
  multiplayerem, replay/determinismem, nebo když test ukáže výsledek závislý na snímkové frekvenci (stejný
  scénář při 30 a 120 FPS dá jiné přistání nebo kolizi). Hra je zatím pro jednoho hráče, proto ne teď.
- **`ASpaceshipPawn` je rozdělený** (1. 10. 2026, `Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`, rozpis
  souborů v `README.md` „Code layout“): čistá matematika ve `FShipFlightModel`, stav a pravidla v komponentách
  `UShipSystemsComponent`, `UShipQuantumComponent`, `UShipLandingComponent`, `UShipPresentationComponent`,
  `UShipBoardingComponent`, `UShipInputComponent`. Pravidla: tuning UPROPERTY zůstávají na pawnu (override v BP
  a klíče setupu), stav jde do komponent, API pro Python a jiné třídy zůstává na pawnu jako přeposílač, pořadí
  Ticku řídí pawn, komponenty bez vlastního ticku a bez BeginPlay. Nový systém lodi (energie, štíty, zbraně,
  náklad) = nová komponenta podle stejných pravidel, ne další kód v pawnu.
- Komponenty s malým vstupem dostávají tuning jako malé struktury (`FShipQuantumRules`, `FShipLandingRules`…);
  prezentace, nástup a vstup čtou pawn přímo jako jeho `friend` (čtou desítky jeho hodnot a dílů). Kde je to
  možné, dává se přednost strukturám.
- **Jádro letu (IFCS: `UpdateAngularMotion`, `UpdateLinearMotion`, prostředí) zůstává v pawnu**: čte všechny
  systémy, zapisuje rychlost a polohu lodi a je to, co pawn je. Komponenta by jen přesunula kód bez oddělení
  (krok 10 plánu byl volitelný). Vrátit se k tomu s pevným časovým krokem nebo s druhým typem pohybu.
- **Testovací API na pawnu** (`Debug*` UFUNCTION) je záměr: testy řídí let bez vstupu. Těla a konzolové příkazy
  `space.*` jsou v `SpaceshipPawnDebug.cpp`, odděleně od běhového kódu; komponenta by byla jen sbírka přeposílačů.

## 3. Světové dotazy

- **Tělesa:** `ACelestialBody` (planety s terénem, gravitací a atmosférou; `SampleEnvironment`,
  `GetSurfaceFrame`) a `ADistantBody` (kulisy bez gravitace). `ACelestialBody::FindNearest` je jediný vstup pro
  „planeta, u které jsem“.
- Registry místo průchodu světem (`TActorIterator`) se zavádějí jen pro dotazy volané často nebo z více lodí
  (audit v1, 4.2); jednorázové a ladicí příkazy procházejí svět dál.
- **`USpaceCelestialRegistrySubsystem`** (30. 9. 2026): seznam těles světa (`ACelestialBody`, `ADistantBody`).
  Tělesa se přihlašují s registrací komponent (spawn, level, streaming, editor), zničené vypadnou (slabé ukazatele).
  Čtou z něj `FindNearest`, quantum (cíl, překážky) a radar. Ve světech bez subsystémů záložní průchod.
- **Registr lodí a cílů** je jen návrh (`Docs/Reviews/2026-09-30_registry_design.md`): zavést, až bude víc lodí,
  NPC, stanic nebo POI, nebo až profil ukáže radar či hledání lodě v rozpočtu snímku. Radar zatím prochází jen
  pawny a static mesh herce.

## 4. Obsah a assety

- **Každý asset vzniká skriptem** (`Tools/Assets`, `Tools/Blender`, `Tools/Kit`); zdroj pravdy jsou skripty
  a JSON recepty v gitu, nikdy ruční úprava v editoru nebo v `.blend`.
- **Vrstvy dat lodi:** `<Loď>_spec.json` (návrh ve tvaru RSI Ship Matrix, kód ho nečte) →
  `Design/<Loď>_layout.json` (jediný zdroj pravdy místností, objektů a obrysů exteriéru) →
  `HardSurface/<Loď>_hs.json` (recept stavby) → `Export/<Loď>_manifest.json` (výstup exportéru) →
  `<Loď>_setup.json` (konfigurace v UE, vyhrává nad manifestem).
- **Exteriér lodi se staví přesně z výkresu** (`hs_build_ship`, od 24. 9. 2026). AI generátory jen jako
  reference stylu, ne jako geometrie lodi.
- **Interiérový kit** je vlastní; čísla (mřížka, průřezy, rozpočty, palety) jsou jen v `ArtSource/Kit/kit_rules.json`.
- **Interiér bez Nanite** (tenké díly mizely, stíny MegaLights chtějí přesnou geometrii, mesh u kamery rozmazává
  TSR); sklo, hologramy a decaly jsou vlastní díly bez Nanite.
- **Světlo interiéru:** MegaLights jen s kamerou uvnitř lodi (autor 27. 9. 2026), odrazy Lumenu v interiéru varianta c: do drsnosti 0,32 v polovičním rozlišení (autor 6. 10. 2026); závoj interiéru (kontrast, zvednutá černá) jako PostProcessComponent v krabici místností, komponenta lodi – nikdy globální tónová křivka (autor 6. 10. 2026, `interior_post.py`); světla
  jen pro interiér nesou tag a v letu nesvítí.
- **Assety načítané z C++ podle cesty** musí být v `DirectoriesToAlwaysCook`; `Package.ps1` klíčové kontroluje.
  Odloženo (audit v1, P2): Asset Manager a Primary Data Assets, až knihovna assetů poroste (víc lodí, delší cook).

## 5. UI

- Letový HUD a MFD jsou UMG strom stavěný v C++ (`USpaceFlightHud`, `USpaceCockpitDisplays`). Displeje kokpitu
  se kreslí do render targetu přes trvalé okno `FWidgetRenderer`; stav 5 Hz, kreslení 60 Hz.
- Menu je ve Slate (bez UMG assetů). Písma jako TTF stagované jako UFS.

## 6. Nástroje a testy

- **Testy:** headless UE testy (`Tools/Tests`, commandlet s Pythonem) a offline Python testy (`Tools/*/tests`,
  statické kontroly). Jeden příkaz `Tools/Test.ps1` s jednotným souhrnem.
- **CI:** GitHub Actions spouští `Tools/Test.ps1` bez `-UE` (compileall a offline testy, Linux, bez LFS). Build UE
  a testy v UE v CI nejsou: chtěly by Windows runner s enginem a LFS obsahem (audit v1, P1/P2; rozhodnutí autora).
- **Vizuální ověření:** `USpaceShotRunner` podle JSON scénářů v zabalené hře nebo v rychlé smyčce `-Editor`;
  nezávislý vizuální kritik (skill `visual-review`). Kritik doplňuje automatické kontroly, nenahrazuje je.
- **Cesta k enginu** je na jediném místě: `Tools/UERoot.ps1` (`GAMESPACE_UE_ROOT`, jinak výchozí instalace).

## 7. Závěry auditu v1 (30. 9. 2026)

Podrobná reakce bod po bodu: `Docs/Reviews/2026-09-30_audit_v1_response.md`.

| Nález | Rozhodnutí |
| --- | --- |
| Pevná cesta k UE, chybí jeden testovací příkaz, test závislý na OS | přijato, hotovo |
| Trackované `.pyc` | neplatí (v historii nikdy nebyly) |
| Víc zdrojů pravdy v dokumentaci | přijato: hierarchie v `CLAUDE.md`, `CURRENT.md`, tento soubor, HANDOFF archiv |
| Rozdělit `ASpaceshipPawn`, oddělit testovací API | hotovo 1. 10. 2026 (kroky 1–9 plánu); jádro letu zůstává v pawnu (kap. 2) |
| Registry místo průchodů světem | přijato pro časté dotazy: `USpaceCelestialRegistrySubsystem` (tělesa, radar); obecný registr lodí a cílů zatím jen návrh |
| Pevný časový krok letu | odloženo (kap. 2) |
| Asset Manager, prostorové dotazy, síťová architektura | odloženo, až je vyvolá růst světa nebo multiplayer |
| `SpaceUserSettings`: const metoda s migrací přes `const_cast` | zapsáno; opravit při nejbližší změně nastavení. Rekurze migrace na čisté instalaci (bez `GameUserSettings.ini`) opravena 1. 10. 2026 |
| CI | přijato jen offline testy a compileall; build UE v CI ne |
