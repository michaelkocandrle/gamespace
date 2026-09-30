# Registry místo průchodů světem: tělesa (zavedeno) a lodě a cíle (návrh), 30. 9. 2026

Podnět: technický audit v1, 4.2 („TActorIterator v několika runtime cestách; při růstu počtu lodí, NPC, planet a POI
opakovaná práce“). Rozhodnutí autora: převést nejčastěji volané dotazy na tělesa a radar, obecný registr lodí a cílů
jen navrhnout, zatím ho nezavádět plošně.

## Co se dnes prochází (Source/gamespace)

`TActorIterator<T>` v UE 5 bere objekty třídy T (a podtříd) z hashe UObjectů a filtruje je podle světa; cena roste
s počtem herců té třídy v paměti. `TActorIterator<AActor>` projde všechny herce.

| Místo | Dotaz | Jak často | Stav |
| --- | --- | --- | --- |
| `ACelestialBody::FindNearest` (volá pawn lodi, postava, `ASkyDome`, origin rebasing) | nejbližší planeta | každý snímek, 3–4 volající | **registr těles** |
| `SpaceshipQuantum::Gather` (`ASpaceshipPawn::UpdateQuantumTarget`, `EvaluateQuantum`) | všechna tělesa (planety + kulisy) | každý snímek v NAV, 2× | **registr těles** |
| `USpaceCockpitDisplays::MakeRadarContacts` | tělesa + pawny + static meshe s kolizí v dosahu | 5×/s na kokpit | **tělesa z registru; objekty jen `TActorIterator<APawn>` a `<AStaticMeshActor>` místo všech herců** |
| `SpaceDebugHUD::DescribeNearestBody` | nejbližší planeta | každý snímek se zapnutým textovým HUD | **přes `FindNearest`** |
| `APlayerCharacter::FindBoardableShip` (F, výzva v HUD) | přistálé lodě v dosahu | každý snímek pěšky (výzva) | zůstává; kandidát registru lodí |
| `ASpaceGravityVolume::FindAt` (`APlayerCharacter::UpdateGravity`) | gravitační objem v bodě | každý snímek pěšky | zůstává; kandidát (objemů je pár) |
| `SpaceshipPawn.cpp` 64–169, `SpaceShipLightTuning`, `SpacePostTuning`, `SpaceInteriorTuning`, `SpaceShotRunner`, `CockpitDisplayComponent` (`space.MfdPage`) | konzolové a ladicí příkazy | na příkaz | zůstává (jednorázové) |
| `ASkyDome::BeginPlay`, `ASpaceshipPawn::BeginPlay` (slunce, sky light), `SpacePlayerController` (kamera menu) | jednou při startu | jednou | zůstává |

Přínos dnes: tělesa jsou tři až čtyři, takže u dotazů na tělesa se ušetří hlavně práce úměrná všem ostatním
hercům (radar procházel všechny herce levelu včetně interiérů a světel) a vzniklo jedno místo, které ví, jaká tělesa
svět má. Měřitelné to bude až s více tělesy, loděmi a POI; změřit se dá `stat SpaceCockpit` (radar) a Insights.

## `USpaceCelestialRegistrySubsystem` (zavedeno)

- `UWorldSubsystem` (světy Game, PIE a Editor; headless testy spawnují tělesa v editorovém světě).
- Tělesa se přihlásí v `PostRegisterAllComponents` a odhlásí v `PostUnregisterAllComponents` (`ACelestialBody`,
  `ADistantBody`): pokryje spawn, načtení levelu, streaming i editor. První dotaz jednou projde svět kvůli tělesům,
  která se zaregistrovala dřív, než subsystém vznikl. Záznamy jsou slabé ukazatele; zničené těleso vypadne.
- API: `ForEachCelestialBody`, `ForEachDistantBody`, `FindNearestCelestialBody`; pro testy statická
  `DebugCountRegisteredBodies(WorldContext, bDistant)`.
- Světy bez subsystémů (náhledy v editoru) mají záložní průchod světem, chování je stejné.
- `ACelestialBody::FindNearest` vzorkuje prostředí jen, když o něj volající požádá (rebasing a ladicí HUD chtějí
  jen těleso).
- Test `Tools/Tests/test_celestial_registry.py` (headless UE): tělesa TestSpace v registru, spawn a zničení tělesa,
  radar vidí každé viditelné těleso. Stávající `test_cockpit_displays.py` (radar), `test_quantum_sc4.py`
  (cíl, OBSTRUCTED), `test_planet_l3.py` (prostředí, gravitace) a `test_character_l6.py` hlídají, že se chování
  nezměnilo.

## Obecný registr lodí a cílů (návrh, zatím nezavádět)

**Kdy:** až bude víc lodí nebo NPC v jednom světě, zbraně s cílením, stanice nebo POI, nebo až profil ukáže radar či
`FindBoardableShip` v rozpočtu snímku. Do té doby je průchod dvou tříd levný a jednodušší.

**Návrh:**
- `USpaceTargetRegistrySubsystem : UWorldSubsystem` se stejným životním cyklem jako registr těles
  (Post(Un)RegisterAllComponents, jednorázový seed, slabé ukazatele).
- Kdo se přihlásí: `ASpaceshipPawn` a `APlayerCharacter` samy; statické cíle (vraky, stanice, asteroidy, POI)
  komponentou `USpaceTargetComponent` (kategorie, jméno pro HUD, poloměr), kterou přidá import nebo scéna. Radar pak
  přestane hádat cíle z „static mesh s kolizí“ a interiérové kulisy se na něm neobjeví omylem.
- Záznam: slabý ukazatel na herce + kategorie (`Ship`, `Character`, `Station`, `Wreck`, `Asteroid`, `Poi`) + poloměr.
  Polohy se neukládají: origin rebasing posouvá herce a uložená poloha by zastarala.
- Dotazy: `ForEachInRadius(Location, RadiusCm, Categories, Visit)`, `FindNearest(Location, Categories, Filter)`.
  Nejdřív lineárně (desítky záznamů); prostorovou mřížku nebo oktalový strom až při stovkách, bez změny API.
- Převést: `MakeRadarContacts` (objekty), `FindBoardableShip`, ladicí příkazy nad loděmi. `ASpaceGravityVolume::FindAt`
  může dostat vlastní malý seznam stejným vzorem.
- Rizika: pořadí přihlášení při načtení levelu (řeší seed), herci ve streamovaných levelech (řeší registrace
  s komponentami), multiplayer (registr je lokální, pro klienta stačí).
