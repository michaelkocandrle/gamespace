# Brief pro vizuálního kritika

## Co to má být
Interiérový kit lodi, dávka 1: stěnové moduly (plný, s mřížkou, se skříňkou, s trubkami, se servisním poklopem, s displejem) složené do chodby široké 2,4 m. Pohled z první osoby (oko 1,65 m) podél chodby, stěny ve 3/4 pohledu a detaily zblízka.

## Styl
Star Citizen: průmyslový interiér lodi, tři vrstvy (konstrukce, panely s přesahem, výbava), lichoběžníkový průřez se zkosením, teplý grafit, oranžová signální barva výrobce jen na madlech a linkách, světelné lišty ve vybrání u stropu a u podlahy, studené UI displejů; úroveň zpracování SC.

## Srovnávací listy
Vlevo reference, vpravo náš výsledek. Reference ukazuje cílovou úroveň a styl, ne nutně stejný objekt.
- Pozn.: Text vpravo nahoře (FPS, stat unit) je měřicí overlay, ne součást výsledku.
- Pozn.: Rozměry chodby jsou pevné z pravidel kitu (změřeno): šířka 2,4 m, svislá stěna do 1,3 m, zkosení do 2,1 m, strop 2,3 m; kamera ve výšce oka 1,65 m, zorné pole 90°.
- Pozn.: Hodnotí se stěnové moduly. Podlaha, strop, koncové stěny chodby a světla ve stropě jsou provizorní (přijdou v dalších dávkách kitu: portály, strop se svítidly, podlaha s lištami).
- Pozn.: Reference jsou interiéry různých lodí SC; ukazují cílovou úroveň a styl, ne stejný objekt.

- `C:/gamespace/gamespace/Docs/Reviews/2026-09-27_kit_batch1_walls/verify/sheet_01_chodba_z_kitu_pohled_podel.jpg` – Chodba z kitu, pohled podél (střední vzdálenost · interior); reference: SC chodba (Drake); výsledek: ve hře, oko 1,65 m
- `C:/gamespace/gamespace/Docs/Reviews/2026-09-27_kit_batch1_walls/verify/sheet_02_stena_ve_3_4_pohledu_skrinka_displej_tru.jpg` – Stěna ve 3/4 pohledu: skříňka, displej, trubky (střední vzdálenost · interior); reference: SC stěna: tři vrstvy; výsledek: ve hře
- `C:/gamespace/gamespace/Docs/Reviews/2026-09-27_kit_batch1_walls/verify/sheet_03_protejsi_stena_mrizka_skrinky_poklopy.jpg` – Protější stěna: mřížka, skříňky, poklopy (střední vzdálenost · interior); reference: SC infrastruktura; výsledek: ve hře
- `C:/gamespace/gamespace/Docs/Reviews/2026-09-27_kit_batch1_walls/verify/sheet_04_mrizka_poklop_a_trubky_zblizka.jpg` – Mřížka, poklop a trubky zblízka (zblízka · interior); reference: SC detail stěny; výsledek: ve hře
- `C:/gamespace/gamespace/Docs/Reviews/2026-09-27_kit_batch1_walls/verify/sheet_05_horni_vybrani_se_svetelnou_listou.jpg` – Horní vybrání se světelnou lištou (zblízka · interior); reference: SC chodba; výsledek: ve hře
- `C:/gamespace/gamespace/Docs/Reviews/2026-09-27_kit_batch1_walls/verify/sheet_06_sokl_se_svetlem_u_podlahy.jpg` – Sokl se světlem u podlahy (zblízka · interior); reference: SC podlaha a sokl; výsledek: ve hře

## Checklist
- Tvar prostoru vychází z trupu: zalomené a zkosené stěny, nízký konstrukční strop, průřez spíš
  lichoběžník / osmiúhelník. Pravoúhlá místnost s rovnými stěnami je chyba.
- Vrstvy: žebra, kabelové žlaby a trubky pod stropem, panely s hloubkou a přesahy, madla, skříňky
  se západkami, mřížky v podlaze, přípojky. Detail shlukovaný kolem funkčních míst.
- Každý předmět má účel; žádné výplňové rekvizity, žádné krabicové pulty.
- Materiály: čalounění, guma, broušený i lakovaný kov, akcenty palety; tmavá teplá architektura,
  studené UI. Béžová / jednolitá / plastová plocha je chyba.
- Decaly: označení místností a sekcí, nouzové značky, popisky ovladačů; čitelné, nezrcadlené.
- Světlo: kontrast, svítidla v pouzdrech, kužely, tmavá místa, akcenty. Ploché rovnoměrné světlo
  ze stropu je chyba, stejně jako přepálená skvrna.
- Geometrie: žádné díry do prázdna, průniky stěnou, plovoucí díly, lišty mimo místo.

## Ověřovací kolo: posuď jen tyto body

Na předchozí verzi těchto snímků padly následující výtky. U každé rozhodni podle listů výše, jestli je teď
vyřešená, a to proti referenci. Nehodnoť nic jiného. Nové vady, které přímo souvisí s těmito body, uveď zvlášť.

1. **Prázdné panely, chybí střední vrstva detailu:** horní zkosení bylo hladkou plochou jen se štítkem 3 cm a svislé
   panely mezi výbavou byly jednolité desky bez členění a přesahů (listy 01, 03).
2. **Jednolitý plastový materiál:** jedna barva a jedna drsnost, žádné opotřebení hran, žádné gumové těsnění kolem
   poklopu a mřížky, žádný kontrast lakovaný / holý kov (listy 02, 04, 06).
3. **Popisky bez hardwaru a opakované decaly:** „EXT PWR“ a „GND POINT“ označovaly zásuvku a zemnicí bod, které na
   stěně nejsou; stejný štítek se opakoval vedle sebe; výstražné pruhy nad výbavou bez nebezpečí (listy 03, 04, 06).
4. **Schody na světelné liště ve vybrání:** každý modul měl vlastní segment lišty s koncovkou a sousední segment
   navazoval s odsazením (list 05).
5. **Trubky končí naslepo v žebru:** trubky mizely do sloupu rámu bez příruby nebo prostupu (list 02).

## Formát výstupu ověřovacího kola

```
# Ověření: VYŘEŠENO | ČÁSTEČNĚ | NEVYŘEŠENO   (celkově)

| Bod | Stav | Kde to vidíš (list, oblast) | Proč (jedna věta) |
|---|---|---|---|
| 1 | vyřešeno / částečně / nevyřešeno | | |
...

## Nové vady související s body 1–5
- ... (nebo „žádné“)
```
