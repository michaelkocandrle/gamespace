# SC Throttle/Flight HUD — vizuální reference pro náš debug HUD

Screenshot z reálného Star Citizen gameplaye (`SC_throttle_hud_reference.png`,
přiložený vedle tohoto dokumentu) ukazuje, jak SC řeší vizuální prezentaci
throttle/letových dat v kokpitu. Náš současný `SpaceDebugHUD` je čistě
textový (řádky typu `SPEED 44 m/s`) — tohle je reference na to, jak by to
mohlo vypadat, až budeme řešit skutečný HUD (naplánováno jako SC-3 v
letovém dokumentu).

## Co dělá ten throttle panel vizuálně dobrým

Z levé strany screenshotu (throttle/G-force panel):

1. **Svislý gauge/pruh místo čísla.** Rychlost není jen text "44 m/s" —
   je to svislý sloupec, kde výška výplně odpovídá aktuální rychlosti
   vůči nastavenému limitu. Číslo (`44M/S`) je pod pruhem jako
   doplněk, ne jako hlavní prvek. Oko čte tvar/výšku rychleji než čísla.
2. **Barevné kódování stavu.** Pruh je zelený/žlutý v normálním rozsahu,
   červený segment dole označuje pravděpodobně minimum/stall zónu.
   Barva nese informaci bez nutnosti číst text.
3. **G-force čítač přímo pod throttle pruhem** (`3.4 G`) — svázaný
   s throttle vizuálně (jsou ve stejném sloupci), protože G-force je
   přímý důsledek toho, co s throttlem/manévrováním děláš.
4. **Malé stavové "spínače" (CPLD, ESP, LOCK vlevo / VTOL, GEAR, GSAF
   vpravo).** Každý je malý label se čtverečkem/indikátorem vedle sebe
   (svítí = aktivní, tmavý = neaktivní). Nejsou to plné textové věty
   ("Coupled: ON") — jsou to husté zkratky, protože pilot je za letu
   čte periferně, ne soustředěně.
5. **Symetrické rozložení kolem středu obrazovky** — throttle/G vlevo,
   VTOL/GEAR/palivo vpravo, zaměřovací kříž uprostřed. Levá/pravá strana
   nese odlišnou kategorii informací (pohyb lodi vs. konfigurace lodi),
   což pomáhá rychlé orientaci — víš, kam se podívat pro daný typ info.
6. **Tenké svítící linky/rámečky** (cyan barva), ne plné panely — HUD
   nezakrývá výhled, jen ho jemně orámuje. Průhlednost/subtilnost je
   klíčová, aby HUD nepůsobil jako vyplácaná tabulka.
7. **Palivový pruh vpravo dole** (`100% REMAINING`) — stejný gauge
   princip jako throttle, konzistentní vizuální jazyk napříč různými
   typy dat (rychlost, palivo, později asi i štíty/health by šly stejně).

## Co z toho je relevantní pro nás TEĎ vs. POZDĚJI

**Teď (debug HUD, co máme):** Náš současný přístup — čistý text řádek
po řádku — je naprosto v pořádku pro debugging fázi, ve které jsme.
Nemá smysl tohle řešit, dokud ladíme SC-1a/SC-1b mechaniky. Přesná
vizuální podoba by se stejně měnila s každou novou přidanou mechanikou.

**Později (SC-3, skutečný HUD):** Až budeme dělat opravdový HUD, tenhle
screenshot je dobrá reference pro:
- Nahradit textové "CPLD: ON/OFF" malými svítícími indikátory vedle
  zkratky (stejný princip pro CPLD, ESP, GSAF, COMSTAB, co už
  máme jako data, jen ne takhle prezentovaná)
- Throttle jako svislý gauge s barevným kódováním místo jen čísla
- G-force čítač vizuálně svázaný s throttle prvkem
- Tenké, průhledné, cyan-tónované linky místo plných UI panelů —
  odpovídá to i naší zvolené vizuální identitě lodi (Star Citizen
  greeble/gunmetal estetika)

## Technická poznámka k implementaci (až přijde na řadu)

Náš současný `SpaceDebugHUD` je `AHUD` s Canvas-based textem (`DrawText`).
Pro tenhle typ vizuálu (gauge pruhy, ikonky, barevné přechody) bude
lepší přejít na **UMG (Unreal Motion Graphics)** widgety místo čistého
Canvas kreslení — UMG má nativní podporu pro progress bary, snazší
stylování a lepší workflow pro tenhle typ "product design" HUD práce.
To je ale rozhodnutí pro SC-3, ne teď.
