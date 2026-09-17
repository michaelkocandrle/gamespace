# Gamespace — plán referenční knihovny

Přehled tematických celků, které postupně rozebereme do samostatných
referenčních dokumentů (stejným způsobem jako "Star Citizen pilotovací
systém" a "Vesmír a okolní prostředí"). Pořadí je navržené podle toho,
co na sebe logicky navazuje a co už máme rozjeté v enginu — ne nutně
podle důležitosti.

## Hotovo
1. ✅ **Pilotovací systém** (`StarCitizen_FlightSystem_Reference.md`) —
   IFCS, coupled/decoupled, flight modes, boost/afterburner, power
   triangle, quantum travel, VTOL/landing.
2. ✅ **Vesmír a okolní prostředí** (`SpaceEnvironment_Reference.md`) —
   škála vesmíru, POI typy (asteroidy, vraky, mlhoviny), procedurální
   vs. ručně dělaný obsah, environmentální hazardy.

## Navrhované pořadí dalších témat

3. **Planetární prostředí a biomy** — logicky navazuje na to, co jsme
   právě postavili (quad-sphere terén, L3 atmosférický vstup). Téma:
   jak Elite/NMS/Starfield řeší biomy, vegetaci, počasí, POI na
   povrchu planety, denní/noční cyklus, planetární rozmanitost.

4. **Ekonomika, obchod a těžba** — jádro "co budeš ve hře dělat" smyčky.
   Téma: obchodní systémy, cenotvorba, těžba surovin (ruční vs.
   automatizovaná), craftění, jak to řeší ED (trading/mining) vs.
   NMS (crafting/base building) vs. SC (kariéry).

5. **Lodní systémy — zbraně, štíty, poškození** — navazuje na Power
   Triangle z prvního dokumentu. Téma: typy zbraní (energetické vs.
   balistické), štíty a jejich regenerace, poškození po komponentách,
   loadout systém.

6. **Postava, EVA a pohyb na nohou** — navazuje na to, co jsme udělali
   u player charactera (L6). Téma: inventář, nástroje, skafandr/kyslík
   management, EVA (chůze v beztížném stavu mimo loď), interakce
   s prostředím.

7. **Mise a NPC/AI chování** — jak generovat/strukturovat úkoly,
   chování NPC lodí (obchodníci, piráti, hlídky), reputace/frakce.

8. **UI/HUD a navigace** — star mapa, scanning/sensor systém, radar,
   jak prezentovat informace hráči napříč všemi předchozími systémy
   (shrnující téma, dává smysl až budeme vědět, co všechno má HUD
   zobrazovat).

## Vynechané/odložené nadobro
- **Multiplayer/sociální systémy** — mimo scope sólo projektu, pokud
  se to nezmění, tohle téma neotvíráme.

---

Postup: u každého tématu udělám stejně hloubkový research jako
u prvních dvou (web research → strukturovaný dokument → sekce
"Shrnutí" s doporučeným pořadím implementace a vazbou na současný
stav enginu). Po dokončení všech témat (nebo kdykoliv mezitím) můžeme
sednout a naplánovat konkrétní implementační roadmapu napříč všemi
dokumenty najednou.
