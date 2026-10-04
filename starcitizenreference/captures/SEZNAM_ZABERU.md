# Seznam záběrů ze Star Citizenu – dávka 1: od spuštění po první vzlet

Pro autora (4. 10. 2026). Záběry jsou jen vzor: z hry nic nevytahujeme (soubory, modely, zvuky).

## Jak fotit

- **Rozlišení 2560 × 1440, celá obrazovka**, HUD a UI zapnuté, pokud u bodu není napsáno jinak.
- **FOV v SC nastav na 88°** (Nastavení → Grafika / Kamera), stejně jako náš kokpit, a nech ho tak u všech záběrů.
- **Stačí video** (AMD Adrenalin, 4. 10. 2026): snímky si z něj vystřihnu sám (`Tools/Reference/fetch_video.py
  <soubor> <název>`). Adrenalin: rozlišení „In-game“ (1440p), 60 fps, **bitrate aspoň 50 Mbps**, kodek HEVC nebo AV1.
  Na každé obrazovce s textem (menu, nastavení, MFD) **zastav na 1–2 s bez pohybu myši**, ať je snímek ostrý.
  Jedno delší video na celou složku je v pořádku; v `poznamky.txt` stačí hrubé časy (např. „1:20 nastavení zvuku“).
- **Screenshot** (Print Screen, `StarCitizen\LIVE\screenshots`) dělej jen u drobného textu, který chci číst
  (klávesy, popisky MFD): video ho rozmaže kompresí.
- **Kam:** `starcitizenreference\captures\<složka>\`. Soubor pojmenuj číslem bodu, např. `01_03.png` nebo `03_02.mp4`.
  Když bod nejde splnit, napiš ke složce do `poznamky.txt` proč (stačí jedna věta).
- Značky: **[S]** screenshot, **[V]** krátké video, **[S+V]** obojí.

## 01 Spuštění a hlavní menu → `captures\01_menu\`

1. [V] Spuštění hry od prvního loga po hlavní menu (intro klidně přeskoč klávesou, jen ať je vidět, co jde).
2. [S] Hlavní menu celé, bez najetí myší na položku.
3. [S] Hlavní menu s myší na jedné položce (zvýraznění).
4. [V] Přechod mezi položkami menu (5–10 s pohybu myší, kliknutí do podmenu a zpět).
5. [S] Výběr režimu (Universe / Arena Commander / Star Marine…), pokud je to samostatná obrazovka.
6. [S] Dialog „Ukončit hru“ nebo jiné potvrzovací okno.

## 02 Nastavení – všechny karty → `captures\02_nastaveni\`

U každé karty **[S] celou obrazovku**; když se karta posouvá, **víc screenshotů po sobě** (02_03a, 02_03b…).

1. Grafika (Graphics).
2. Zobrazení / Display (rozlišení, okno, FOV, HDR).
3. Zvuk (Audio).
4. Ovládání a citlivost (Control / Mouse / Joystick).
5. Klávesy (Keybindings): **přehled kategorií** a hlavně **Lodě – let, podvozek, quantum, power**, každá podkategorie
   jeden screenshot.
6. Kamera / Head tracking / Comfort (pohupování hlavy, motion blur, FOV).
7. HUD a rozhraní (barva HUD, velikost, průhlednost, jazyk).
8. Game / Advanced (všechno ostatní, co tam je).
9. [S] Jedna rozbalená roletka (dropdown) a jeden posuvník během tažení: jak vypadají ovládací prvky.
10. [S] Dialog „Uložit / Zahodit změny“, pokud se objeví.

## 03 Načítání a výběr místa → `captures\03_nacitani\`

1. [S] Výběr místa startu (planeta, stanice, město) celý.
2. [S] Detail jedné vybrané lokace (popis, ikony).
3. [S+V] Načítací obrazovka (loading screen): celá a 10 s videa (animace, ukazatel průběhu, tipy).
4. [S] Případná obrazovka „Připojování / Connecting“.

## 04 První minuty – probuzení a postava → `captures\04_start\`

1. [V] Probuzení v posteli nebo spawn: prvních 20–30 s, jak se zobrazí kamera a HUD.
2. [S] Pohled z očí v pokoji ve stoje (HUD pěšky: co je na obrazovce).
3. [S] Interakce: podržet F, aby byl vidět **interakční režim s nabídkou** (na dveřích nebo terminálu).
4. [S] Zaměřovací bod / kurzor při pohledu na předmět bez interakce.
5. [S] **mobiGlas** (F1): úvodní obrazovka a každá aplikace jeden screenshot (mapa, inventář, úkoly…).
6. [S] Inventář (I nebo Tab, podle verze).
7. [S] Pauza / Esc menu ve hře.
8. [V] Chůze chodbou 15 s (rychlost, pohupování kamery), pak 10 s sprint.

## 05 Cesta k lodi → `captures\05_hangar\`

1. [S+V] Terminál pro přivolání lodi (ASOP / Fleet Manager): úvodní obrazovka, výběr lodi, potvrzení.
2. [S] Výtah: ovládací panel s patry.
3. [S] Hangár s lodí: celek, z místa, kde vystoupíš z výtahu.
4. [V] Obejití lodi dokola 30 s (měřítko lodi proti postavě).
5. [S+V] Nástup: přiblížení k rampě nebo dveřím, interakce, otevření.
6. [V] Cesta z rampy na sedadlo pilota 20–30 s.
7. [S+V] Sednutí do sedadla: animace a první pohled z kokpitu.

## 06 Kokpit před letem → `captures\06_kokpit\`

1. [S] Pohled pilota rovně, **lodní systémy vypnuté** (tma).
2. [V] **Zapnutí lodi** (power on / flight ready, klávesa R nebo podržet): celé, jak se rozsvěcují displeje a HUD.
3. [S] Pohled pilota rovně, **vše zapnuté** (HUD + displeje).
4. [S] Pohled doleva a doprava (Alt + myš nebo Z), každý jeden screenshot.
5. [S] **Každá obrazovka MFD zblízka**: přiblížit pohled (Z / hold) na každý displej, projít všechny jeho stránky.
6. [S] Interakční režim v kokpitu (podržet F): co jde na desce ovládat.
7. [S] HUD zblízka: levá polovina, střed, pravá polovina (můžeš i přiblížit).

## 07 Vzlet → `captures\07_vzlet\`

1. [S+V] Žádost o odlet (ATC): jak se žádá a co se zobrazí (hláška, otevírání hangáru).
2. [V] Vzlet od zapnutých motorů po zasunutí podvozku: **z kokpitu**, 30–60 s.
3. [V] Totéž **z pohledu třetí osoby** (F4), 30 s.
4. [S] HUD hned po vzletu s vysunutým podvozkem (co ukazuje GEAR, rychlost, omezení).
5. [S] HUD po zasunutí podvozku (rozdíl proti bodu 4).
6. [V] Výlet z hangáru nebo z města do otevřeného prostoru 30 s (hlášení na HUD, zóny).

---

**Další dávky** pošlu podle toho, na čem budeme dělat: let a HUD (SC-1 až SC-6), přistání na planetě, quantum,
interiér lodi a chůze, výstup na planetu, mapa (starmap). Když tě během focení něco zaujme, vyfoť to taky
do `captures\99_navic\` s jednou větou v `poznamky.txt`.
