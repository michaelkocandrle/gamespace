# Seznam záběrů – dávka 2: let a HUD za letu (4. 10. 2026)

Cíl: změřit, jak se v SC letí (zrychlení, rychlosti, otáčení, brzdění) a jak se při tom chová HUD, a doladit podle toho
náš let a HUD. Stačí video (AMD Adrenalin, 1440p, 60 fps); FOV 88°, pohled z kokpitu, HUD zapnutý.

**Loď:** malá jednomístná, nejlépe **Avenger Titan** nebo **Aurora** (nejbližší našemu Wayfareru). Napiš do
`poznamky.txt`, jakou loď jsi měl. Létej ve vesmíru daleko od stanice (žádné zóny, nic v cestě).

**Každý manévr začni z klidu (0 m/s) a mezi manévry 2–3 s nic nedělej.** Ovládání nech ve výchozím nastavení
(coupled, G-Safe, omezovač naplno), pokud u bodu nestojí jinak.

## 08 Přímý let → `captures\08_let\` (jedno video na celou složku stačí)

1. Plný plyn vpřed (W) z nuly, dokud rychlost nepřestane růst (SCM), držet ještě 3 s.
2. Pustit W a nechat loď samu zastavit (coupled brzdí).
3. Znovu na maximum, pak podržet X (vesmírná brzda) do zastavení.
4. Plyn vzad (S) z nuly až na maximum vzad.
5. Úkrok vpravo (D) z nuly až na maximum, pak pustit. Totéž nahoru (mezerník).
6. Plný plyn vpřed s **Boostem** (Shift) z nuly až na maximum.
7. **Afterburner** (plný plyn + jeho klávesa), dokud nedojde, pak ještě 5 s.
8. Přepnout do **NAV** (B), plný plyn z nuly 15 s, pak zpět do SCM a nechat zpomalit.
9. Kolečko myši: omezovač rychlosti dolů na polovinu a zase nahoru, při plném plynu.

## 09 Otáčení → `captures\09_otaceni\`

1. Myš doprava na doraz (zatáčení) a držet, dokud se loď neotočí aspoň 2× dokola.
2. Totéž myší nahoru (klopení), 2 otočky.
3. Náklon (E) držet 2 otočky.
4. Totéž zatáčení s podrženým Shiftem (boost).
5. Plný plyn vpřed a při tom zatáčka na doraz 5 s (jak loď driftuje, co dělá HUD).
6. **Decoupled** (výchozí klávesa V nebo podle nastavení): plný plyn 3 s, pustit, otočit loď o 90° myší a 5 s jen
   letět (setrvačnost), pak zpět coupled.

## 10 HUD za letu → `captures\10_hud\`

Screenshot (Print Screen) ke každému bodu, aby šel přečíst drobný text:

1. HUD v klidu, SCM.
2. HUD při plném plynu na maximu SCM.
3. HUD s boostem a s afterburnerem.
4. HUD v NAV, při zrychlování a na maximu.
5. HUD v decoupled.
6. HUD s rozsvícenými varováními, která najdeš (přetížení, málo paliva…), pokud jdou vyvolat.
7. Volné rozhlížení (podržet tlačítko pro rozhlížení), pohled doleva a doprava.

---

Až to bude ve složkách, napiš. Z videa vystřihnu snímky, změřím časy a rychlosti a pošlu ti tabulku „SC vs. my“.
