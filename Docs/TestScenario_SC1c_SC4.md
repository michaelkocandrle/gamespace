# Testovací scénář: SC-1c (HUD) + SC-4 (Quantum Drive)

Cíl: ověřit vlastním hraním vše, co Claude Code označil jako
"neověřeno autorem" v HANDOFF kapitole 11. Spusť `.\Tools\Play.ps1`
(zabalená hra z `C:\gamespace\Builds`).

## Část 1 — SC-1c HUD (obecná kontrola)

1. **Rozmístění a čitelnost:** ve vesmíru i v atmosféře zkontroluj,
   jestli throttle pruh, G-metr, indikátory (CPLD/GSAF/COMSTAB/BOOST/
   SCM-NAV) jsou čitelné na světlém pozadí (proti planetě/mlhovině),
   ne jen na černém vesmíru.
2. **Jiné rozlišení:** pokud hraješ na jiném rozlišení než 1600×900,
   zkontroluj, jestli HUD nesedí divně (moc blízko/daleko od středu).
3. **Kokpit kamera (C):** zkontroluj novou pozici — sedí ti to vizuálně
   i pocitově při zatáčení?

## Část 2 — SC-4 Quantum Drive (celé neověřené)

1. **Aktivace:** přepni do NAV (B), namiř na vzdálený cíl/planetu.
2. **Spool a kalibrace:** stiskni a drž tlačítko pro quantum skok.
   - Sleduj HUD stavy: SPOOLING → READY → (držení ~0.6s) → skok
   - Sedí ti časování (spool 6s, kalibrace 2.5s)? Necítí se to moc
     dlouhé/krátké?
3. **TOO CLOSE stav:** zkus aktivovat skok s překážkou blízko před
   sebou (asteroid/jiný objekt) — mělo by to odmítnout s hláškou.
4. **Vizuál skoku:**
   - První okamžik (zelený záblesk) — působí to dobře?
   - Tunel s mlhou za letu — hustota/barva sedí?
   - Zkus i pohled z kokpitu a zvenku (chase) během skoku
5. **Příjezd a chlazení:** po doletu sleduj chlazení (cooldown) —
   funguje blokace opětovného skoku správně?
6. **Palivo:** sleduj, jestli quantum palivo ubývá rozumně a jestli je
   na HUD čitelné.

## Co konkrétně hodnotit (subjektivní, jen ty to můžeš posoudit)

- Cítí se přechod SCM→NAV→quantum skok jako plynulá, uspokojivá
  sekvence, nebo něco trhá/nesedí?
- Je tunel při skoku vizuálně přesvědčivý, nebo příliš řídký/hustý?
- Je časování (kolik sekund co trvá) frustrující, nebo OK?
- Radar (pokud narazíš na jiný objekt v dosahu 5 km) — zobrazuje
  kontakt srozumitelně?

## Po testu

Napiš Claude Code, co z tohoto sedí a co ne — buď konkrétní u čísel
(časování, vzdálenosti), ne jen "líbí/nelíbí".
