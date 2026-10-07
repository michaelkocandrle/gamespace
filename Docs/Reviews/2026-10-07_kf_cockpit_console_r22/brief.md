# Brief pro vizuálního kritika

## Co to má být
Levá loketní konzole kokpitu, VARIANTA B postavená podle našeho 2D návrhu (Docs/Kit/parts/KF-COCKPIT-CONSOLE/concept, autor 7. 10.: reference SC jsou styl, rozměry a skladba naše). Ošoupaný světlý kovový rám s tmavými panely, opěrka předloktí jako nosník na dvou šikmých konzolách nad podstavcem (mezera), knipl na vlastním bloku před opěrkou, prostřední blok se sáním a stavovým pásem a klávesami na zkosení ke křeslu, věž s nouzovou klávesou pod krytem a kolébkami (otočené k pilotovi), modul tří jištěných přepínačů, servisní poklop vzadu, trubkové madlo s oranžovým návlekem, oranžové šrafy, vrstvené decaly (oděry, škrábance, štítky), nové opotřebení ploch v materiálu kitu. Díl sám v testovacím úseku pod neutrálním světlem, úhly jako reference. ROZHODNUTÍ AUTORA 8. 10.: díly našich lodí jsou nové z výroby – lesklé, matné, naleštěné, BEZ opotřebení, oděrů, škrábanců a špíny. Opotřebení NEHODNOŤ a nežádej. Hodnoť detail, vrstvení decalů a textur, materiálový kontrast (lesk/mat, lak/grafit/kov), čistotu provedení. Kolo 20: lak rámu pod čirým lakem, leštěná zkosení chytající světlo, grafitové vložky, vrstvené decaly (servisní a HV šablony, nýty, zásuvka, výstražný pás, štítky), čelo věže s logem a šrafami, svítící klávesy s gradientem. Kolo 21 po kole 20 (6,4): materiálový kontrast – rám světlejší lak (sRGB ~0,5) pod plným čirým lakem s jemnou pomerančovou kůrou (normálová mapa), zkosení leštěný kov (metallic 1, albedo 0,75, drsnost 0,18), všechny vložky nová role hluboký matný grafit (albedo ~0,06, drsnost 0,62, práškové zrno) včetně ovládacího pole věže, poklopu, čela věže a podstavce; odstraněna čára přes bok věže. Kolo 22 po kole 21 (6,5): grafit vložek tmavší (albedo 0,035, drsnost 0,62) i na desce pod opěrkou a poklopu, výstražný pás na čele věže jako ucelený pás 38 mm s pruhy 9 mm pod 45° v černém rámečku, návlek madla s diamantovým rýhováním (normálová mapa) a leštěnými koncovými kroužky, jemnější pomerančová kůra laku.

## Styl
Úroveň SC, ne přesná kopie (autor 7. 10.). Halcyon: oranžové akcenty místo žlutých, šedé laky, udržovaná pracovní loď.

## Srovnávací listy
Vlevo reference, vpravo náš výsledek. Reference ukazuje cílovou úroveň a styl, ne nutně stejný objekt.
- Pozn.: Hodnotí se jen konzole (díl továrny), ne stěny a podlaha testovacího úseku.
- Pozn.: Světlo testovacího úseku je neutrální a jasnější než kokpit SC na referencích – jas sám o sobě nehodnoť, hodnoť tóny materiálů mezi sebou.

- `C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_01_1_konzole_3_4_zepredu_nad_loketni_jednot.jpg` – 1 Konzole 3/4 zepředu nad loketní jednotkou (střední vzdálenost · studiové světlo); reference: SC Aurora; výsledek: KF konzole B
- `C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_02_2_zepredu_pres_nos_konzole.jpg` – 2 Zepředu přes nos konzole (střední vzdálenost · studiové světlo); reference: SC Aurora; výsledek: KF konzole B
- `C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_03_3_ovladaci_blok_zblizka.jpg` – 3 Ovládací blok zblízka (zblízka · studiové světlo); reference: SC Aurora; výsledek: KF konzole B
- `C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_04_4_knipl_a_operka_zapesti_zblizka.jpg` – 4 Knipl a opěrka zápěstí zblízka (zblízka · studiové světlo); reference: SC Aurora; výsledek: KF konzole B
- `C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_05_5_bok_od_pilota_mezera_pod_loketni_jedno.jpg` – 5 Bok od pilota (mezera pod loketní jednotkou) (střední vzdálenost · studiové světlo); reference: SC Aurora; výsledek: KF konzole B
- `C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_06_6_shora.jpg` – 6 Shora (střední vzdálenost · studiové světlo); reference: SC Aurora; výsledek: KF konzole B

## Etalon
`C:/gamespace/gamespace/Docs/Reviews/2026-10-07_kf_cockpit_console_r22/sheet_00_etalon.jpg` – kotevní záběry Star Citizenu pro tento díl: SC konzole; SC loketní konzole s kniplem; SC křeslo a konzole.

## Práh
Dílčí krok (díly kitu, nábytek, jednotlivé místnosti): PASS, když průměr kategorií je aspoň 6,5, žádná kategorie nemá méně než 6 a žádný bod není „musí se opravit“.

## Checklist
- Tvar prostoru vychází z trupu: zalomené a zkosené stěny, nízký konstrukční strop, průřez spíš
  lichoběžník / osmiúhelník. Pravoúhlá místnost s rovnými stěnami je chyba.
- Vrstvy: žebra, kabelové žlaby a trubky pod stropem, panely s hloubkou a přesahy, madla, skříňky
  se západkami, mřížky v podlaze, přípojky. Detail shlukovaný kolem funkčních míst.
- Každý předmět má účel; žádné výplňové rekvizity, žádné krabicové pulty. U dveří dotykový panel jako v SC
  (od 5. 10. 2026, `USpaceDoorPanel`): čitelný stav (OPEN / CLOSED), ve fyzickém pouzdře; numerická klávesnice
  ne.
- Materiály: čalounění, guma, broušený i lakovaný kov, akcenty palety; tmavá teplá architektura,
  studené UI. Béžová / jednolitá / plastová plocha je chyba.
- Decaly: označení místností a sekcí, nouzové značky, popisky ovladačů; čitelné, nezrcadlené.
- Světlo: kontrast, svítidla v pouzdrech, kužely, tmavá místa, akcenty. Ploché rovnoměrné světlo
  ze stropu je chyba, stejně jako přepálená skvrna.
- Geometrie: žádné díry do prázdna, průniky stěnou, plovoucí díly, lišty mimo místo.
