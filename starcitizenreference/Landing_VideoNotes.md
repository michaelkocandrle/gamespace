# Přistání v SC 4.x – poznámky z videa (4. 10. 2026)

Zdroj: „Star Citizen – How to Land Safely and Smoothly (New Player's Guide)“, YouTube `P4FHuCqTcWw`, 1440p, 174 s.
Stažené lokálně: `python Tools/Reference/fetch_video.py <url> sc_landing_guide --every 3 --subs`
(`ArtSource/Reference/Video/sc_landing_guide/`, mimo git). Přistání v hangáru stanice, ne na terénu planety.

## Průběh (časy)

| Čas | Co se děje |
|---|---|
| 0:57–1:30 | přiblížení, toast „Hangar Request Completed“ nahoře uprostřed, značka přiděleného hangáru |
| 1:33–1:39 | vjezd do tunelu hangáru, podvozek ještě nahoře (červená ikona s „!“) |
| 1:42–1:57 | podvozek dole, rychlost omezená na 29 m/s |
| 2:09–2:24 | visení nad plošinou a klesání krátkými ťuky Ctrl; vpravo dole R-ALT a VSI |
| 2:33 | přistáno, motory vypnuté (I) |

## HUD při přistání

- **Ikona podvozku** u horního konce pásu rychlosti: nahoře červená s vykřičníkem, dole symbol nohy se šipkou,
  po přistání s vypnutými motory jiný oranžový symbol.
- **R-ALT / VSI** vpravo dole pod G (např. „R-ALT 8m“, „VSI -3m/s“). R-ALT po dosednutí ukazuje 4 m: měří se od bodu
  lodi, ne od patek.
- Páska kurzu, žebřík sklonu a zaměřovač beze změny; značka cíle (hangár) modře.
- **Nic dalšího:** žádný kruh na zemi, žádný obrys patek, žádný text „LANDED“ ani důvod odmítnutí. SC přistává
  fyzicky; varování v rámečku má jen quantum (TOO CLOSE pod SPOOLING/CALIBRATING/READY).
- Hlášení: tmavý rámeček s azurovým textem vpravo (ARMISTICE ZONE), toast nahoře uprostřed.

## Co říká autor videa (vlastními slovy)

- Zpomalit omezovačem (Alt + kolečko), B z NAV do SCM brzdí.
- Do 10 km Alt+N žádost o přistání, pak značka přidělené plošiny; jinak přes MFD Comms.
- N podvozek (omezí rychlost na 29 m/s), nad plošinou krátce Ctrl dolů, I motory, podržet Y vstát.

## Co z toho bereme

- Máme: GEAR (kontrolka a řádek), PREC (omezení rychlosti), R-ALT a VSI.
- **Odchylka:** stavový rámeček přistání (TOUCHDOWN / LANDED / důvod odmítnutí), protože naše přistání má pravidla
  (sklon, trup na zemi, rychlost, náklon) a hráč musí vědět, proč loď nepřistává. Styl podle rámečku stavu quantum.
- Později (mimo SC-3): žádost o přistání a přidělená plošina (až budou stanice), ikona podvozku u pásu rychlosti.
