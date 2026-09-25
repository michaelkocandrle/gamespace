# Recenze: Wayfarer kokpit (25. 9. 2026)

- Předmět: kokpit po krocích 0–8 (commit 5a2fb3e), zabalená hra.
- Listy a brief: `Docs/Reviews/2026-09-25_wayfarer_cockpit/` (`review.json`, `brief.md`, `sheet_01…09.jpg`).
  Pohled pilota ve dne, v noci a ve vesmíru, kabina z boku a zezadu, moduly, HOTAS, hologram zblízka,
  kabina zvenku.
- Kritik: zadání `visual-critic` v2 (po kalibraci), checklist `cockpit`, Fable 5.1. Spuštěný přes
  read-only agenta se stejným textem zadání, protože nový podagent se načte až po restartu session.
- Kol: 1. Oprava zatím neproběhla: recenze byla součástí zavedení kritika, ne nového vizuálního
  předání. Otevřené body jsou níže jako další krok.

## Kolo 1 – výstup kritika

**Verdikt: FAIL**

První dojem: Působí jako blokový prototyp kokpitu z šedých desek s dobře čitelnými MFD, ale bez hustoty,
materiálů a světla, které dělají kabinu SC.

| Kategorie | Skóre |
|---|---|
| Silueta a tvar | 5 |
| Hierarchie a hustota detailu | 3 |
| Materiály | 4 |
| Decaly | 3 |
| Světlo | 4 |
| Čitelnost (text, displeje, HUD) | 6 |
| Chyby geometrie | 5 |
| Soulad stylu mezi díly | 4 |

Pohled pilota podle kritika: ven asi 55 % obrazu, horizont volný, v ose pohledu nic. Boční sloupky jsou
tmavé klíny, střed mezi MFD je černý blok se dvěma malými displeji, MFD jsou samostatné šikmé desky.

## Výtky a reakce

| # | Výtka (kritik) | Závažnost | Platí? | Stav | Reakce / návrh |
|---|---|---|---|---|---|
| 1 | Noc není noc – obloha i expozice jako ve dne, displeje a hologram nesvítí na okolí | musí | platí | neopraveno | Noční preset jen vypíná slunce, obloha zůstává světlá. Oprava: noční osvětlení scény (sky light, atmosféra) a světla displejů/hologramu výraznější v noci. |
| 2 | Ve vesmíru kabina mizí v černé | musí | platí | neopraveno | Průměrný jas 0,04. Oprava: svítící oranžové linky desky, podsvícená tlačítka, slabý fill kabiny, světlo displejů na desku. |
| 3 | Hologram z oka je bílá šmouha proti obloze, zblízka ve dne změť trojúhelníků | musí | platí | neopraveno | Oprava: nižší jas přes den, čistší (méně decimovaný) mesh, výraznější obrysy/fresnel; přesunout níž, aby nestál proti obloze. |
| 4 | Prázdné plochy (boky desky, zadní štít z holých panelů, desky kolem MFD) | musí | platí | neopraveno | Oprava: panely s hranami a šrouby, mřížky, madla, skříňky na zadním štítu místo holé mřížky panelů. |
| 5 | Ovladače řídké, moduly vypadají položené na povrchu | musí | platí | neopraveno | Moduly mají 3–5 prvků. Oprava: hustší skupiny (řady krytých přepínačů, kolébek, podsvícených tlačítek s popisky), zapustit do desky. |
| 6 | Příhradové „lešenářské“ nosníky, zvenku otevřená díra místo skla | musí | platí | neopraveno | Jde o texturu polstrování vany z kitu Quaternius (vzor X), zvenku čte jako příhradovina. Oprava: jiný povrch vany (plné panely, polstr bez X), sklo s tónem a odrazem. |
| 7 | Plovoucí pedály bez táhel; válec na podlaze bez účelu | musí | zčásti | neopraveno | Pedály mají táhla i čep, ale jsou tenká a tmavá, takže pedál působí volně → zvýraznit mechaniku. „Válec“ je rukojeť páky viděná shora → neplatí. |
| 8 | Sedadlo jako hrudka s „pomačkanou“ normálou | musí | platí | neopraveno | Sedadlo je model z Meshy (Steadfast). Oprava: nové sedadlo s rámem, segmenty polstru, pásy a kolejnicí. |
| 9 | Zvenku chromové trubky rámu a sklo bez odrazu | doporučeno | platí | neopraveno | Lemy obložení (`LinerRim`, saténový kov) prosvítají sklem. Oprava: lemy v grafitu, sklo s tónem a odrazem. |
| 10 | HOTAS: lesklý grip, „jediné tlačítko“; plyn jako hrudka na tyčce | doporučeno | zčásti | neopraveno | Páka má 2 kloboučky, pickle, 2 boční tlačítka a malíčkovou páčku (list 07), tvrzení o jednom tlačítku neplatí. Platí: lesklý materiál gripu bez textury, tenká páka plynu → gumový materiál, pevnější páka s krytem. |
| 11 | Středové displeje (radar, stav) nečitelné | doporučeno | platí | neopraveno | Oprava: zvětšit nebo sloučit obsah na MFD. |
| 12 | HUD má ve dne nízký kontrast | doporučeno | platí | neopraveno | Samostatné téma HUD. Oprava: tmavý obrys prvků nebo adaptivní jas. |
| 13 | Málo decalů v kabině (popisky panelů, šrafy, štítek výrobce) | doporučeno | platí | neopraveno | Štítky mají jen ovladače. Oprava: popisky panelů, šrafy u vstupu, štítek Halcyon Freightworks. |

Shrnutí: 11 výtek platí, 2 jen zčásti, žádná není vynechaná. Body 1–8 jsou kandidáti na další krok
(kokpit v2). Pořadí podle dopadu: 6 a 9 (pohled zvenku), 1–3 (světlo a hologram), 4–5 (hustota
detailu), 7–8 (pedály, sedadlo).
