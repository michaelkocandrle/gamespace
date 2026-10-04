# SC 4.10 – autorovy záznamy hraní (4. 10. 2026)

Tři záznamy z autorova PC (AMD Adrenalin, 2560 × 1440, 60 fps), celkem ~22 min; videa ve
`starcitizenreference/captures/Star Citizen/` (mimo git), snímky po 3 s v `ArtSource/Reference/Video/sc_own_02..04/`
(`Tools/Reference/fetch_video.py <soubor> <název> --every 3`). Rozbor udělali tři podagenti, tady je souhrn vlastními slovy.

| Záznam | Délka | Obsah |
|---|---|---|
| sc_own_02 | 4:10 | probuzení v EZ Hab (Port Tressler), sklad a inventář, chodba, výtah, lobby, klinika, lékárna |
| sc_own_03 | 6:32 | hangárový blok: terminály Fleet Manager, Storage Access, Freight Manager; vyzvednutí lodi (C8 Pisces), rampa, sedadla, zapnutí lodi |
| sc_own_04 | 11:15 | Aurora Mk II: nástup, interiér, inženýrský terminál, studený start, ATC a vrata, vesmír, quantum, atmosféra microTechu, přistání ve sněhu, výstup |

## Rozhraní hráče (pěšky i v lodi)

- **Výzvy u předmětů**: malý popisek s klávesou přímo u věci („USE [F]“, „SIT [F]“, „OPEN [F]“), i svisle u hrany dveří;
  „INTERACT (OFFSCREEN)“ pro věc mimo střed pohledu. Neplatná akce: červená ikona a „NO APPROPRIATE ITEM“.
- **Režim interakce** (podržet F): kurzor myši, klikání na fyzická tlačítka a obrazovky ve světě; po najetí plovoucí
  popisek (POWER ON, OPEN EXTERIOR, CYCLE CONFIGURATION). Panely dveří, výtahu i terminály se ovládají jen takhle.
- **Seznam kláves vpravo dole**: „AKCE [klávesa]“ podle situace (pěšky, sedadlo, pilot vypnutý / zapnutý, vznášení,
  quantum); hráč nepotřebuje manuál.
- **Hlášení**: tmavá pilulka nahoře uprostřed (Hangar Request Completed, připojení ke kanálu lodi), tutoriálové karty
  vpravo (titulek azurově, 2–4 řádky; RADAR PING ANGLE, QUANTUM SPOOLING / CALIBRATION / CANCEL, PLAYER TEMPERATURE),
  zóny (Entering / Leaving Armistice Zone).
- **Helma / visor**: kompasová páska nahoře, čísla sklonu na krajích, holografická 3D mapka interiéru vlevo nahoře
  (s názvy místností; ve výtahu „RADAR UNAVAILABLE“), úkol vpravo nahoře, značka cíle se vzdáleností v km.
- **Životní hodnoty vlevo dole**: zdraví, kyslík, tlak (hPa), teplota (19 °C uvnitř, −22 °C venku), hydratace a výživa
  (klesají ~1 % za minutu). Sada se mění podle prostředí.
- Barva visoru se v pilotním sedadle mění z azurové na zelenou. Globální chat stále na obrazovce (MMO, pro nás ne).

## Loď

- **Studený start**: loď je po nastoupení tmavá, MFD černé; POWER (U) nebo fyzické tlačítko PWR, MFD a HUD naběhnou
  za několik sekund. Pak THRUSTERS, REQUEST TAKEOFF (L-Alt+N).
- **MFD**: fyzické naklopené obrazovky na ramenou; sloupec tlačítek = zároveň kontrolky (QTM RADR PROX HIT MISL VTOL GEAR
  GSAF / PWR WPN THR SHLD COOL CPLD ESP LOCK; PROX červeně při hrozící srážce, GEAR a GSAF jantarově). Nad MFD plovoucí
  pruhy s rychlostí, G, AB, vodíkem, návnadami. Stránky: SELF STATUS, TARGET, CONFIGURATION (přepínače letu: coupled,
  cruise, kompenzace gravitace, auto slowdown, G-Safe, ESP, proximity assist, omezovač, světla), COMMUNICATIONS,
  DIAGNOSTICS (opravy), POWER MANAGEMENT (signatury EM/IR/CS), WEAPON CONFIG, QT (palivo, vzdálenost).
- **Inženýrský terminál**: rentgenový 3D model lodi s komponenty (relé, pojistky, propojení), rozdělení energie
  (pipy, teploty, chladiče), předvolby (uložit, použít, smazat s potvrzením, max 10), poruchy (vypnuté chladiče →
  COOLER FAILURE, podpora života offline).
- **Pilot může vstát za letu**, loď drží polohu. Varování uprostřed červeně (COLLISION ALERT, PREDICTED ANTI-G
  RESISTANCE, NO POWER). Radarový kruh na zemi před nosem.
- **Nástup**: panel na trupu (OPEN / HATCH), vyklápěcí schůdky, kulatý průlez, irisová přechodová komora, vnitřní
  dveře s tlačítkem PUSH; rampa Pisces s panelem RAMP ACCESS. Sedadla pro cestující (SIT / GET UP / EXIT).
- **Quantum**: cíl nosem, NO POWER → spool (zelený pruh) → kalibrace (zelené oblouky kolem cíle) → READY.
- **Přistání**: výška v km, podvozek N, AUTOLAND N, oblak sněhu pod tryskami.

## Stanice a hangár

- Kajuta EZ Hab: probuzení v posteli (EXIT Y), sklopné stolky, terminál skladu (otisk prstu, TOUCH TO START), dveře
  s dotykovým panelem. Pokládání předmětů s průhledným náhledem.
- Výtah: panel venku ukazuje, kde výtah je; uvnitř seznam pater; jízda ~6–9 s.
- Hangárové terminály: špinavé oranžové kiosky s hardwarem pod obrazovkou (kontrolky zelená / červená). Fleet Manager
  (seznam lodí, pronájem s odpočtem, Retrieve, Store), Freight Manager (sklad ↔ výtah v SCU, přesun trvá, místnost
  zčervená). Loď se objeví na plošině v jámě, okraj jámy jistí holografická bariéra CAUTION.
- ATC: jedna klávesa, potvrzení hlášením, obří vrata se otevírají 6–9 s.
- Prostředí: hodně značení a nápisů (MIND STEP, KEEP CLEAR, loga značek), každá oblast jiná teplota světla, opar,
  prach, NPC při práci.

## Co máme a co ne (zkráceně)

Máme: let SC-1 až SC-4 (IFCS, boost, AB, HUD, podvozek, VTOL, quantum s kalibrací), MFD a radar, chůzi lodí, menu a
nastavení ve stylu SC. Chybí hlavně: výzvy u předmětů a režim interakce, seznam kláves, hlášení a tutoriály, studený
start a fyzická tlačítka kokpitu, MFD stránky CONFIGURATION a kontrolky, visor pěšky (kompas, životní hodnoty),
systémy lodi (energie, chlazení, inženýrský terminál), stanice, hangár, ATC, inventář, přežití, NPC.
