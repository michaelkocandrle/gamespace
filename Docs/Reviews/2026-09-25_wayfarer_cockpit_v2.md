# Recenze: Wayfarer kokpit v2 (25. 9. 2026)

- Předmět: kokpit v2 podle plánu schváleného autorem (commit tohoto kroku), zabalená hra, 1080p.
- Kritik: zadání `visual-critic` v2, checklist `cockpit`, Fable 5.1. Spouštěný jako read-only agent (Explore)
  s doslovným textem zadání (nový podagent se načte až po restartu session, WORKFLOW 9.6 bt).
- Listy, briefy a výstupy kritika: `2026-09-25_wayfarer_cockpit_v2/round1|round2|round3/`
  (`review.json`, `brief.md`, `sheet_01…09.jpg`, `critic.md`).
- Důkazní výřezy k neplatným výtkám: `2026-09-25_wayfarer_cockpit_v2/evidence/`.
- Předchozí recenze (před v2): `2026-09-25_wayfarer_cockpit.md`.

## Průběh

| Kolo | Doba kritika | Verdikt | Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Soulad |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 190 s | FAIL | 6 | 4 | 5 | 5 | 4 | 6 | 6 | 6 |
| 2 | 177 s | FAIL | 5 | 4 | 5 | 4 | 5 | 6 | 5 | 6 |
| 3 | 214 s | FAIL | 6 | 5 | 5 | 6 | 5 | 7 | 6 | 6 |

Pokaždé k tomu ~1 min skládání listů (`make_compare_sheet.py`) a čtení výstupu. Kritik tedy stojí ~4–5 min na kolo,
3 kola ~15 min. Mnohem víc stojí opravy mezi koly a nové balení se snímky (~12 min na kolo).

Tři kola jsou vyčerpaná, předává se s otevřenými body níže. Po kole 3 jsem ještě opravil čtyři jasné chyby,
které kritik ani autor nemuseli posuzovat (useknuté nadpisy středových displejů, plovoucí sloupek madla,
modré skvrny od světel desky, svítící disk projektoru hologramu). Ověřené jsou jen mými snímky
(`Saved/Shots/20260925_2017*`), kritik je už neviděl.

## Kolo 1 – reakce

| # | Výtka | Závažnost | Platí? | Stav | Reakce |
|---|---|---|---|---|---|
| 1 | Noční kabina mizí v černé | musí | platí | zčásti | Obloha teď v noci opravdu tmavne (`ASkyDome`, WORKFLOW bu). Přibyla světla displejů na desku a ostrůvek nad konzolí. Deska je v noci pořád tmavá, viz otevřené body. |
| 2 | Středové displeje zakryté a oříznuté | musí | platí | opraveno | Tři příčiny (WORKFLOW bw). Po kole 3 ověřeno ray castem z oka a snímkem: `evidence/9_stredove_displeje_pred_po.jpg`. |
| 3 | Velké prázdné plochy | musí | platí | zčásti | Spáry a šrouby na glare shieldu i konzolích, protiskluzové lišty podlahy, žebra obložení, dva rozptyly decalů (osa x na čelo desky, osa z shora na desku). Hustota je pořád pod SC. |
| 4 | MFD jako samostatné monitory | musí | zčásti | zčásti | Rám je grafitový, clona navazuje na desku, pod sklem svítí linka, úchyty jsou menší. Koncept „pody se skleněnými panely na držácích“ ale schválil autor (koncept A a zadání kabiny), takže přestavbu desky nechávám na něm. |
| 5 | Přepálené body a šmouha na skle | musí | neplatí (body) / zčásti (odlesk) | – | Bílé body jsou tělesa na obloze za sklem: `evidence/5_tecky_jsou_telesa_na_obloze.jpg`. Odlesky vnitřních světel na skle jsem přesto ztlumil (specular 0,25, drsnost skla 0,08). |
| 6 | Hologram vypálený do bílé | musí | platí | opraveno | Hlubší modrá, síla 0,9, okraj 2,4, decimovaný mesh bez smetí. Rozmazání zůstává (kolo 3, bod 2). |
| 7 | HOTAS jako stolní periferie | doporučeno | zčásti | zčásti | Gumové gripy, manžeta, silnější páka plynu. |
| 8 | Sedadlo bez polstrování, popruhy nalepené | doporučeno | platí | opraveno | Sedadlo z Meshy vyřazené (zadání autora), nové procedurální: skořepina, polstrované panely se švy, boční vedení, opěrka hlavy na sloupcích, popruhy přes horní hranu do štěrbin, přezka, rám. |
| 9 | Ovladače zjednodušené | doporučeno | platí | opraveno | Vroubkované voliče se stupnicí, hranatá podsvícená tlačítka, kolébky, kryté přepínače, enkodéry, LED; 10 nových štítků. |
| 10 | Holý válec na podlaze, oranžový hranolek | doporučeno | zčásti | opraveno | Válec je hlava páky plynu shora (dostala tlačítka a hat). Hranolek patřil sedadlu z Meshy, které je pryč. Pedály dostaly základnu, čep, táhlo a tlumič. |
| 11 | Zadní pohled neukazuje dveře | doporučeno | platí | neopraveno | Kamera snímku stojí za sedadlem, které dveře zakrývá. Úprava presetu je otevřený bod. |
| 12 | Materiály bez opotřebení | doporučeno | zčásti | neopraveno | Procedurální díly nemají UV pro opotřebení (WORKFLOW 9.3 y). Patří do kroku materiálů. |

## Kolo 2 – reakce

| # | Výtka | Závažnost | Platí? | Stav | Reakce |
|---|---|---|---|---|---|
| 1 | Zakrytý středový displej | musí | platí | opraveno | Šířka zpět na 9 cm (při 11 cm zašly hrany za pody). Zbytek zakrytí opraven až po kole 3 (WORKFLOW bw). |
| 2 | Tvary mizí v černé v noci a ve vesmíru | musí | zčásti | zčásti | Přidána světla displejů na desku (studená, bez stínu). Deska je tmavší než v referenci, viz otevřené body. |
| 3 | Sedadlo jako placeholder, plovoucí popruhy | musí | zčásti | opraveno | Panely místo polštářů (poloměr 2,8 cm, švy). Ramenní popruhy vedou přes horní hranu do štěrbin, bederní do přezky. |
| 4 | Displeje jako krabice na stole | musí | nesouhlasím | neopraveno | Pody se skleněnými panely na držácích jsou schválený koncept A a autorovo zadání kabiny. Přestavbu desky nedělám bez autora. |
| 5 | Prázdná plochá deska | musí | platí | zčásti | Rozptyl decalů shora na desku (osa z: spáry, mřížky, šrouby, štítky). |
| 6 | Sklo zvenku není vidět | musí | zčásti | neopraveno | Sklo má jen jemný odraz, protože silnější odraz by zhoršil výhled zevnitř. Kompromis nechávám autorovi. |
| 7 | Ovladače jsou hladké válce a tečky | musí | neplatí | – | `evidence/7_ovladace_nejsou_hladke_valce.jpg`: vroubkovaný volič se stupnicí a ryskou, hranatá tlačítka s podsvícenou lištou. |
| 8 | Throttle na tyčce, stick nízkopolygonový | doporučeno | zčásti | zčásti | Stick má spoušť, dva haty, pickle a boční tlačítka (spoušť z úhlu snímku není vidět). Páka plynu má gumovou manžetu, ne měch. Fasety gripu zůstávají. |
| 9 | Hologram velký, na bílém disku | doporučeno | zčásti | opraveno po kole 3 | Místo svítícího disku je tmavá čočka s tenkým modrým okrajem v grafitovém prstenci. Velikost 20 cm nechávám, z oka je hologram malý. |
| 10 | Čára přes okno, odlesk na skle | doporučeno | zčásti | neopraveno | Čára je horní hrana rámu skla viděná z boku. Skvrna je těleso na obloze (viz důkaz 5). |
| 11 | Zadní pohled bez dveří | doporučeno | platí | neopraveno | Stejné jako kolo 1, bod 11. |
| 12 | Exteriér bez panelování | doporučeno | mimo rozsah | – | Recenze se týká kokpitu. Exteriér je hotový krok s vlastními decaly. |

## Kolo 3 – výstup kritika

Výstup: `round3/critic.md`. První dojem kritika: „Čistý, ale prázdný blockout kokpitu s hotovým HUD a MFD; v noci
a ve vesmíru se kabina rozpustí do černé a hologram je rozmazaná modrá skvrna.“

## Kolo 3 – reakce

| # | Výtka | Závažnost | Platí? | Stav | Reakce |
|---|---|---|---|---|---|
| 1 | Kabina v noci a ve vesmíru mizí v černé | musí | zčásti | zčásti | Světla displejů na desku posunutá před sklo a zesílená na 3 cd. Deska je v noci pořád tmavá. Otevřený bod: rect light a fill kabiny, jak navrhuje kritik. |
| 2 | Hologram je rozmazaná hmota s probleskujícími vnitřními plochami | musí | platí | neopraveno | Chce vlastní obálkový mesh bez vnitřních ploch (ne decimaci celého exteriéru), Fresnel hranu a responsive AA proti TSR. Otevřený bod pro další krok. |
| 3 | Placeholderové ovladače, chybí popisky | musí | zčásti | zčásti | Neplatí: tlačítka mají popisky ENG/SHLD, RCS je kolébka (`evidence/3_popisky_a_kolebka_RCS.jpg`). Platí: tři stavové LED nad voličem nemají popisek, volič WPN je enkodér s hladkým pláštěm. |
| 4 | HOTAS je jen joystick, throttle chybí | musí | neplatí (throttle) / zčásti | – | Páka plynu je na listu 07 vpravo: `evidence/4_throttle_existuje.jpg`. Platí: spoušť stick z úhlu snímku není vidět, grip má fasety, páka nemá měch. |
| 5 | Prázdné plochy desky | musí | platí | zčásti | Stejné jako kolo 1, bod 3. Chybí hlavně druhá vrstva detailu (kryty, mřížky, průchodky) a zrno materiálu. |
| 6 | Sedadlo je krabice z polštářů | doporučeno | zčásti | neopraveno | Rám, sloup a boční tyče má. Chybí loketní opěrky a kovové kotvy popruhů. |
| 7 | Přepálené skvrny na skle, plochá obloha | doporučeno | neplatí (skvrny) / zčásti | – | Skvrny jsou tělesa na obloze (důkaz 5). Denní pohled pilota je ve 3 km v oparu, takže horizont je jen tušit. Změna výšky snímku je otevřený bod. |
| 8 | Zadní pohled bez dveří, plovoucí tyč | doporučeno | platí (tyč) | opraveno po kole 3 | Tyč je horní sloupek madla schodů. Končil na boční stěně nad její horní hranou. Sloupky jsou teď svislé až na stupeň nebo podlahu, s přírubou. Kamera zadního snímku je otevřený bod. |
| 9 | Nečitelné mini displeje, modrý průsvit dole | doporučeno | platí | opraveno po kole 3 | Nadpisy byly useknuté, ne malé. Příčiny a oprava ve WORKFLOW bw, důkaz `evidence/9_stredove_displeje_pred_po.jpg`. Modré skvrny dělala světla desky u kolenního panelu (WORKFLOW bz), jsou pryč. Sloučení do jednoho displeje nedělám: radar a self status odpovídají referenci. |
| 10 | Kanopa jako skleník, interiér ve špatném měřítku | doporučeno | nesouhlasím | – | Kanopa a paluba jsou postavené přesně podle schváleného výkresu lodi (bez AI geometrie). Změna měřítka je rozhodnutí autora o designu lodi. Podlaha za sedadlem je nástup ze schodů. |

## Otevřené body (předání)

1. Noc: plošné světlo před MFD a hologram, slabý fill kabiny (kolo 3, bod 1).
2. Hologram: obálkový mesh bez vnitřních ploch, Fresnel, ochrana proti TSR (kolo 3, bod 2).
3. Druhá vrstva detailu desky a zrno materiálů (kolo 3, bod 5; kolo 1, bod 12).
4. Popisky stavových LED, vroubkovaný WPN, měch páky plynu, hladší grip (kolo 3, body 3, 4).
5. Loketní opěrky a kotvy popruhů sedadla (kolo 3, bod 6).
6. Presety snímků: zadní pohled mimo osu sedadla, denní pohled pilota níž nad terénem.
7. Rozhodnutí autora: MFD pody vs. displeje zapuštěné v desce; síla odrazu skla zvenku; měřítko kanopy.

## Co kritik přehlédl / co našla kontrola

- Kritik v kole 3 přehlédl throttle na vlastním listu 07 a popisky ENG/SHLD. Kalibraci to nemění: jde o chyby čtení
  malých detailů, ne o slepé místo v zadání.
- Useknuté nadpisy kritik hlásil od kola 1. Tři různé příčiny odhalil teprve ray cast z oka. Pravidlo z toho:
  u výtky na čitelnost displeje z oka vždy střílej paprsky, nehádej (WORKFLOW bw).
