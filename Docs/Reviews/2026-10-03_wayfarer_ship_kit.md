# Wayfarer – exteriérový kit na celé lodi, 3. 10. 2026

Zadání autora (2. 10. 2026): po opravě noci rovnou kit na celou loď. Pilot (hřbet, ramena, záď, gondoly, trysky) prošel
dříve (`2026-10-01_wayfarer_kit_pilot.md`, PASS 6,6).

## Co se postavilo
- Oblast rozvrhu `ship` (`Tools/Design/exterior_kit_layout.py --region ship`): desky na všech bočních pásech K, L, U, S,
  hřbet R, záď A; rám celý (žebra po celé výšce, podélníky LO/HI/TOP, páteř). `panels.built_bands` K–A, FR-RIB
  a FR-LONG-LO postavené (data `Wayfarer_exterior_design.json`, výkresy E-01 až E-08 a I-04 překreslené).
- Dno kanálu jen kolem desek a rámu (`skin.near_side`, okraj 0,1 m), jinde zůstává lak.
- Sloučená deska pod jménem (`panels.bands[U].merge` 8,2–12,8; žebra tam pás U přeruší); registrace HF-0417 na desku
  15,2–16,7 (setup x 570), WAYFARER na střed sloučené desky (x 55); šablona INSPECT D-H-59 na x 7,55.
- Střední vrstva na pásech L a U: přídavný panel a poklop na každé desce (`sub`, mimo sloučenou desku a registraci).
- Mezera deska–rám 25 mm (dřív 40), gunmetal rám světlejší (0,36, metallic 0,6), primární lak teplejší (0,76 0,73 0,66).
- Světelný pásek boku v tmavém kanálu L/U (z 1,18, x 5–17,8; dřív pod deskami, četl se jako přerušovaná čára).
- Kachle špíny: přeložená buňka se zahodí místo otočení (`hs_decals.card_at`; test `mirrored_decals`).
- Rozpočet: trup 455 k z 700 k; plášť 128 k (strop 145 k z rezervy: dno kanálu se kvůli zapečenému stínu neslučuje,
  odstranění pláště pod deskami patří do optimalizace na konci).

## Kritik (Opus, práh `step`): 3 kola, FAIL – předáno s otevřenými body

| Kolo | Průměr | Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Styl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5,5 | 7 | 5 | 5 | 5 | 6 | 6 | 5 | 5 |
| 2 | 6,0 | 7 | 5 | 5 | 6 | 6 | 7 | 7 | 5 |
| 3 | 6,0 | 7 | 5 | 6 | 6 | 6 | 7 | 6 | 5 |

Listy a výstupy: `2026-10-03_wayfarer_ship_kit/round1..3/` (`critic.md`). Snímky: editor
`shots:20261003_025731_wayfarer_exterior_review/`, zabalená hra `shots:20261003_172953_wayfarer_exterior_review/`.

Reakce na body:
- **Opraveno:** přerušovaná světelná čára (kolo 1 bod 3), nápisy přetnuté rámem (1/4), rám splývá s kanálem (1/2 –
  světlejší gunmetal), černý trup bez desek (1/1 – kanál jen kolem desek), studená šedá (2/2 – teplejší lak),
  holé boky (2/3 – panely a poklopy na L a U), INSPECT na jménu (test výkresu).
- **Otevřené, systémové (rozhodnutí autora):** boky a příď pořád čtou tmavěji než výkres a koncept B (kolo 3 body 1, 4).
  Příčina je v datech výkresu: kýlový pás K je gunmetal, kanál mezi L a U je široký (~0,1 výšky řezu), žebra jsou na
  všech 15 příčkách po celé výšce a příď se zužuje, takže desky tam vychází rozřezané (bod 2). Možnosti: K v laku,
  užší kanál L/U, žebra po celé výšce jen na přepážkách (ostatní jen u ramene), na přídi méně a větších desek.
- **Otevřené, doporučeno:** střední vrstva ještě hustší (mřížky, okénka, stupně u vstupu), shluky šablon na bocích,
  souvislý oranžový pruh, světelný pásek tlumenější nebo bodová světla, poziční světla na konce křídel, šedý opar nad
  záďovým krytem (kolo 2 bod 10), čárky na křídle (kolo 1 bod 10).
