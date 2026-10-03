# Wayfarer – boky revize F, 3. 10. 2026

Navazuje na `2026-10-03_wayfarer_ship_kit.md` (kit celé lodi, kritik kolo 3 FAIL 6,0: boky a příď tmavší než výkres
a koncept B). Autor 3. 10. schválil čtyři úpravy dat výkresu a pak výkresy revize F (výřezy E vs F v této složce:
`01_nose_E_vs_F.png`, `02_mid_E_vs_F.png`, `03_aft_E_vs_F.png`).

## Co se změnilo (data `Wayfarer_exterior_design.json`, model `exterior_model.py`)
1. Kýlový pás K v primárním laku (dřív gunmetal); gunmetal zůstal na břiše, rámu a v kanálech.
2. Kanál mezi pásy L a U ~0,10 m (dřív ~0,35 m): horní hrana L z v 0,43 na 0,497; U beze změny (oranžový pruh, jméno
   a registrace na svých deskách). Světelné pásky L-HULL-RUN-LOW a L-HULL-RUN-CANOPY vedou středem kanálu (v 0,511)
   jako lomená čára `z: [[x, z], ...]` (`exterior_model.side_strip_pts`, `hs_lights._strip_z`).
3. Žebra FR-RIB po celé výšce jen na hlavních přepážkách 1,4 / 8,2 / 10,4 / 15,2 (`full`); na ostatních příčkách
   od FR-LONG-HI výš (`v_other` 0,77–1,0). Pod tím se desky stýkají spárou 2 × 15 mm (`panels.seam_gap`).
4. Příď: K14 jedna deska 16,7–20,3, L14 a U14 jedna deska 16,7 až k bloku RCS (`merge`, pás s rozsahem `x`), před
   RCS jedna deska P-S-N15 přes výšku L a U (nový pás N). Dřív pole 15 a 16 rozřezal RCS a kabina na pruhy
   a lichoběžníky (model z rozříznuté desky bral jen největší kus).
- Řezy R1/R2 na E-01 na přepážce 15,2; razítko vypisuje revize D až F.

## Stavba
- Trup 453 k trojúhelníků (dřív 455 k, strop 700 k). Dvě přestavby: v první ležel přední pásek
  L-HULL-RUN-CANOPY na staré pevné výšce z 1,12 přes desku L14 (editor `shots:20261003_200833_wayfarer_exterior_review/05_day_close_nose.png`),
  opraveno lomenou čarou v kanálu.
- Snímky: editor `shots:20261003_201427_wayfarer_exterior_review/`, zabalená hra `shots:20261003_202636_wayfarer_exterior_review/`.
- Testy: `Test.ps1 -All` offline 13/13, Blender 1/1, UE 22/22; balení OK.

## Kritik (Opus, práh `step`): 1 kolo, PASS 6,5

| Kolo | Průměr | Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Styl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6,5 | 7 | 6 | 6 | 6 | 6 | 7 | 7 | 7 |

Proti kolu 3 kitu celé lodi (6,0): silueta, geometrie a čitelnost drží, styl 5 → 7, hierarchie 5 → 6, materiály
a decaly 6. Listy a výstup: `2026-10-03_wayfarer_sides_revF/round1/` (`critic.md`).

Reakce na body (všechny „doporučeno“, žádný „musí se opravit“):
1. Střední vrstva na deskách L a U (poklopy, mřížky, madla) – neopraveno, další krok kitu (bylo i v recenzi kitu).
2. Čísla panelů a shluky šablon na bocích – neopraveno; pravidlo D-R-PANEL-NUMBERS je postavené jen na R a S,
   rozšířit na K, L, U, N je další krok.
3. Variace lesku a špína v kanálech – neopraveno, otevřené už v CURRENT (atlas špíny pro kanály).
4. Protisvětlo bez světel – neopraveno; poziční světla na konce křídel jsou v otevřených bodech kitu.
5. „HE-0417“ – **ověřeno, platí**: přes písmeno F vede tmavý šikmý decal s oranžovým koncem. Byl tam už před
   revizí F (`shots:20261003_025731_wayfarer_exterior_review/04_day_close_front34.png`); příčina nedohledána, další krok.
6. Tmavá příď – rozsah tmavé špičky Z-B-01 (od x 20,3) je podle výkresu; deska N15 začíná hned za RCS. Členění
   tmavé plochy spárami a prvky je námět pro další krok.
7. Světelný pásek ve dne přepálený, linka kolem kokpitu – neopraveno; tlumenější pásek už doporučoval kritik kitu.
   Linku kolem skla kokpitu jsem v tomto kroku nezkoumal (pásky boku vedou v kanálu L/U); další krok.
8. Nýty po celém obvodu desek – neopraveno; rozestup šroubů je data kitu (`bolt_pitch`), změna je rozhodnutí stylu.
