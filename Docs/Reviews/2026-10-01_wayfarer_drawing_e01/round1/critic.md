# Verdikt: PASS
První dojem: Čistý, hustý a profesionálně působící list s jednotným barevným kódováním stavů, který sedí s daty; slabiny jsou v příliš drobném písmu pro tisk A0, v detailu 1:20 bez jediné kóty a v několika nedotažených konvencích (razítko, křížení odkazů, chybějící stará poloha pruhu Z-B-03).

| Kategorie | Skóre | Proč |
| --- | --- | --- |
| 1. Čitelnost | 6 | Hierarchie titulků a šrafy jsou v pořádku, ale ID desek a staničení mají ~1,2 mm, tabulky ~1,5 mm (pod normou pro A0), modré ID na gunmetalu nejdou číst, popisky L05–L07 kolidují s řadou šroubů a v detailu A se kříží odkazové čáry. |
| 2. Úplnost proti zadání | 8 | Všechny body zadání jsou na listu (desky B+C, zóny s legendou, F/L/D s ID, stavy, kontrola orientace „čte“, RCS 8, koncept včetně „nepřebírá se“); chybí jen pár kót a vzorové číslo panelu. |
| 3. Soulad s daty | 8 | 20+ namátkově ověřených prvků sedí na polohu, stav i počet, digesty v razítku odpovídají JSON; nesedí jen nenakreslená stará poloha Z-B-03 a nekonzistentní skrytost F-RCS-09. |
| 4. Konvence technického výkresu | 6 | Rámeček, razítko, měřítka, výškové kóty a legenda jsou; chybí pole Kreslil/Kontroloval/Schválil a počet listů, detail bez kót, odkazy se kříží, vzorek Δ v legendě je totožný s „+“, kružnice detailu nekryje rozsah detailu. |
| 5. Návrh povrchu (B + C) | 7 | Rozvržení pásů K/L/U/S na gunmetal rámu, žebra na příčkách, podélníky, šrouby na těžkých plátech a zapuštěné šachty odpovídají konceptu; zbytkové desky (U-rámeček P-S-S04 kolem R-B-01, 0,2m pásky U07/U11) konstrukčně nedávají smysl. |
| 6. Srozumitelnost pro autora | 7 | Barvy stavů, tabulka změn s důvody a „kontrola dat“ řeknou, co se staví a proč; kazí to useknuté poznámky „…“, anglické útržky z dat stavby a drobné písmo. |

Průměr: 7,0

## Musí se opravit
Žádná výtka této váhy.

## Mělo by se opravit
1. Výřezy 01–03 (ID v deskách, staničení příček) a 09–10 (tabulky) – výška verzálek ID desek („P-S-U05“) a staničení („1,4“) je ≈ 1,2 mm, text tabulek ≈ 1,5 mm (měřeno z 200dpi výřezů); zadání chce čitelnost i při tisku A0, norma (ISO 3098) má minimum 2,5 mm, pro A0 obvykle 3,5 mm – ID desek a staničení ≥ 2,5 mm, popisky odkazů 3,5 mm, tabulky 2,5 mm s řádkem ≈ 4 mm (tabulky pak potřebují víc šířky nebo druhý list).
2. Výřez 02 (pás K, pole 05–10) a pás S obecně – modré ID „P-S-K05“ … „P-S-K10“ na gunmetalu (#7E848B) s křížovou šrafou jsou prakticky nečitelné – popisek dát na bílou podložku (halo) s přerušenou šrafou, nebo tmavé písmo v bílém rámečku.
3. Výřez 02 (pole 05–07, spodní bok) – popisky P-S-L05, P-S-L06, P-S-L07 jsou zatlačené pod raketnici F-MISSILE-S2 přímo na řadu šroubů (čte se „P-S-L0●“), P-S-L05 leží částečně pod raketnicí – popisek umístit do viditelné části desky nebo vynést odkazem mimo; celé zakryté desky uvádět v poznámce „skryté“ jako U01–U03.
4. Výřez 07 (detail A, spodní okraj x≈890–960 a x≈200–400, horní okraj x≈1200–1270) – odkazové čáry se kříží (D-H-18/D-H-51/P-POD s P-POD-05/P-POD-BODY/L-POD-RUN; D-H-49/D-T-03/D-H-11/L-MARKER-POD/D-HAZARDEXHAUST-R; D-H-03/D-H-05/D-H-09/P-POD-02) – odkazy řadit v pořadí cílů, nekřížit, případně lomená čára; ID se stejným cílem (P-POD/P-POD-BODY/P-POD-05) seskupit na jeden odkaz.
5. Výřezy 02–03 (oranžový pruh Z-B-03 Δ) – změna rozsahu z x 12,0–17,2 (hs) na 5,9–17,2 (návrh) je nakreslená jen v nové délce; podle legendy má mít změna starou polohu červeně čárkovaně, ta chybí, a tabulka změn (11) starý rozsah neuvádí – dokreslit starý rozsah 12,0–17,2 čárkovaně červeně (nebo značku starého začátku v x 12,0 se šipkou) a do tabulky změn doplnit „x 12,0–17,2 → 5,9–17,2“.
6. Výřez 04 (pohled B, x≈4,0 z≈1,9) a 07 (detail A nad D-H-09) – F-RCS-09 × je kreslen plně přes gondolu, ač leží v její siluetě (vrch gondoly v x 4,0 = 1,2 + 0,92 = 2,12 m, blok z 1,75–2,05), zatímco G-SN-02 (z 2,0) je správně čárkovaně a v „kontrole dat“ – sjednotit test skrytosti (silueta gondoly), F-RCS-09 kreslit čárkovaně a uvést v kontrole dat; stejně prověřit G-HT-03 (z 0,35 vs. spodek gondoly v x 1,9 ≈ 0,3).
7. Výřezy 09–10 (tabulky F, G, D) – poznámky useknuté trojtečkou („XK-RCS robustní blok RCS (C); spec 8× T…“, „Real landing gear inside the drawing's ge…“, „Struts across the canopy stay hull; the gl…“, řádky D-H-29, D-H-49, D-H-55, D-H-58, D-R-PANEL-NUMBERS) a anglické útržky z dat stavby („component access panels of the technica…“, „coolers access“, „quantum fuel filler on the belly“) – poznámky zalomit na víc řádků nebo smysluplně zkrátit, ne useknout; tabulky pro autora česky (přeložit `_what` nebo mít české pole).
8. Výřez 11 (razítko) – chybí pole Kreslil / Kontroloval / Schválil (datum, podpis), počet listů („List 1/1“), jednotky („rozměry v m, tloušťky v mm“) a tabulka revizí (A – 1. 10. 2026 – první vydání) – doplnit; pole „Schválil“ je pro schválení stylu (dossier bod 3) nutné.
9. Výřez 07 (detail A 1:20) – bez jediné kóty – detail má kótovat to, co 1:30 neunese: délku gondoly (−0,50…5,90), prstence (0,60–0,90; 4,40–4,70), špičku ploutve (+3,30), blok RCS 0,42×0,30, mezeru desek 40 mm a žebro 80 mm; doplnit 5–6 kót a jeden typický výsek „deska na rámu“ (XK-PLATE: 30 mm deska, 8 mm zkosení, žebro 15 mm nad pláštěm).
10. Výřez 01 (pole 04 kolem R-B-01) a 02/03 (pod F-GRILLE-01/02) – P-S-S04 + je po výřezu mřížky R-B-01 (4,45–5,45 v poli 4,30–5,60) zbytkový U-rámeček ~100 mm široký; P-S-U07 a P-S-U11 jsou jen ~0,2 m vysoké pásky pod šachtami – vystouplá 30mm deska jako 100mm rám konstrukčně nedává smysl: desku v tomto poli vynechat (gunmetal rám zůstane vidět, jak chce koncept B) nebo mřížce dát vlastní lem; k pravidlu min_area 0,12 m² přidat minimální šířku pásu (např. 0,25 m).

## Drobnosti
1. Výřez 08 (legenda, Stav prvku) – vzorek „+ návrh“ a „Δ změna“ jsou obě plná modrá čára; u Δ ukázat i červenou čárkovanou starou polohu a šipku, jak je to na výkresu.
2. Výřez 04 – kružnice detailu A (průměr ≈ 4,6 m, x ≈ 0,4–5,0) nepokrývá rozsah detailu (−0,5…6,4 m, ploutev do +3,3); použít obdélníkový rámeček odpovídající výřezu detailu a dopsat „DETAIL A (1:20)“; v pohledu A odkaz na detail chybí, ač detail nese i materiálové šrafy.
3. Výřezy 01–03 vs. 04–06 – pohled A má příčky a čísla polí, pohled B metrovou osu; sjednotit (v B tenké šedé příčky, v A metrová osa), aby šly polohy z tabulek číst přímo i v A.
4. Výřez 01 a 03 – dlouhé svislé odkazy (P-POD / P-POD-BODY vedené přes celý pás K dolů, Z-B-01 přes celou příď) – kratší šikmé odkazy nebo popisek u prvku.
5. Výřez 10 (tabulka D) – pravidlo D-R-PANEL-NUMBERS („číslo panelu v dolním zadním rohu každé desky, 3,4 cm“) není na výkresu ukázané; v detailu A nakreslit jedno vzorové číslo (např. „L04“) v rohu desky.
6. Výřez 11 (kontrola dat) – D-LOGO-R (x 3,9 z 1,5) je z boku za gondolou, logo tedy z boku není vidět; list to jen konstatuje bez rozhodnutí – buď poznámka „záměr (viditelné šikmo zespodu)“, nebo změna polohy do návrhu.
7. Výřez 04 – F-RCS-09 × a F-RCS-13 + uvnitř kružnice A jsou v B bez popisku (popsány až v detailu), zatímco jiné prvky v kružnici popsané jsou (L-TAIL, D-H-21, G-HT-03) – sjednotit.
8. Výřez 08 (Pásy desek) – hodnoty v jsou zaokrouhlené (0–0,17; 0,2–0,43; 0,53–0,76; 0,78–0,93) proti datům 0,165/0,195/0,758/0,782 – uvádět přesné hodnoty.
9. Výřez 09 (tabulka L) – typ „světlo nav“, „světelný pás pod_run“ míchá češtinu s názvy z dat; stačí ID a český typ.

## Namátková kontrola dat (prvek, výkres, data, sedí/nesedí)
1. F-RCS-01 – výřez 06: modře Δ, x ≈ 19,1 z ≈ 1,35, blok 0,30 × 0,42 (otočený) – hs x 19,1 z 1,35 rot 90, návrh změna kitu na XK-RCS – sedí.
2. F-RCS-02 – výřez 06: modře Δ, x ≈ 19,1 z ≈ 0,65 – hs 19,1 / 0,65, návrh změna – sedí.
3. F-RCS-05 – výřez 06: červeně ×, x ≈ 13,6 z ≈ 1,95 – hs 13,6 / 1,95, návrh odstranit – sedí.
4. F-RCS-06 – výřez 05: červeně ×, x ≈ 9,9 z ≈ 1,3 – hs 9,9 / 1,3, návrh odstranit – sedí.
5. F-RCS-13 – výřez 07: modře + na hřbetu gondoly x ≈ 5,35; F-RCS-12 Δ dole – návrh pod 5,35 / 90° a hs pod 5,35 / −90° – sedí; součet 2+2+2+2 = 8 bloků = spec 8 a hlavička tabulky F – sedí.
6. F-GRILLE-01 – výřez 05: x 8,36–9,14, z 1,62–2,22, 5 lamel, modře + – návrh – sedí; F-GRILLE-02 (05/06) x 12,98–13,82 – sedí.
7. G-VT-01 / G-VT-02 – výřez 05: červeně × x ≈ 9,8 / 10,25, z 1,9 pod nápisem WAYFARER – hs 9,8 / 10,25 / 1,9, návrh odstranit – sedí; tabulka G – sedí.
8. F-CONN-01 – výřez 05: stará poloha červeně čárkovaně x 6,6 z 0,55, nová modře x 13,0 z 0,75, modrá šipka – hs 6,6 / 0,55, návrh 13,0 / 0,75 – sedí.
9. D-H-58 – výřez 05: nová x 13,0 z 0,92, stará z 1,35 čárkovaně – hs 12,95 / 1,35, návrh 13,0 / 0,92 – sedí; D-H-29 (05) x 6,4, nová z 1,03 / stará 0,9 – sedí; D-H-55 (04) x 1,9, stará z 0,72 / nová 0,62, obě čárkovaně za gondolou – sedí.
10. D-NAME-R – výřez 05: box ≈ 1,9 × 0,24 m u x ≈ 10,3 z ≈ 1,85 s textem a šipkou „nahoru“ – setup location (5, 250, 65) cm, size 190 × 24 cm, počátek x 10,25 m / z 1,2 m – sedí; D-REG-R (605, 210, −40) → x 16,3 z 0,8, 0,7 × 0,18 – sedí; D-LOGO-R (−635, 250, 30) → x 3,9 z 1,5 – sedí; D-HAZARDEXHAUST-R (−1015, 440, 0) → x 0,1 z 1,2, 0,46 × 0,12 – sedí.
11. P-B-02 / P-B-10 / P-B-11 / P-B-13 / P-B-15 – výřezy 01–03: červeně čárkovaně x 3,1–4,25; 7,1–8,1; 10,5–11,5; 13,0–14,0; 11,7–12,7 – hs totéž, návrh odstranit – sedí.
12. R-B-01 – výřez 01: lamely x 4,45–5,45 z 2,36–2,85, černě – hs – sedí; P-B-01 / Z-B-02 (záďový kryt do x 3,0, z ≥ 2,2) – sedí.
13. L-STROBE-WING – výřez 04: hvězda x ≈ 5,15 na konci křídla, modře + – návrh 5,15 / y 7,0 – sedí; L-LANDING (06) x ≈ 17,85 reflektor – sedí; L-HULL-RUN-LOW (05/06) 7,2–16,6 z 0,35 a L-HULL-RUN-CANOPY 15,4–18,9 z 1,62 – sedí; L-NAV zeleně na pravoboku (mirror_color green) – sedí.
14. F-CANOPY-FRAME – výřez 06: příčky x ≈ 16,3 a 17,6 – hs struts_x – sedí; G-SN-01 19,6 / 1,1; D-H-37 19,9 / 1,3; D-H-57 19,0 / 0,8; D-H-40 16,2 / 0,55; D-H-43 15,6 / 1,75; F-GEAR-NOSE x 17,0; F-GEAR-MAIN x 5,2; G-SP-01 4,9 / 0,3 – sedí.
15. Příčky a pole – výřezy 01–03: staničení 1,4 / 3,0 / 4,3 / 5,6 / 6,9 / 8,2 / 9,3 / 10,4 / 11,6 / 12,8 / 14,0 / 15,2 / 16,7 / 18,2 / 19,4 = 16 polí – hs seams.x – sedí; chybějící S02 (záďový kryt) a S14–S16 (kabina) odpovídají `cut` – sedí.
16. Tabulka změn (výřez 11) – 29 položek = 33 změn návrhu minus 4 decaly (D-H-29, 42, 55, 58 v tabulce D) – sedí; digesty v razítku (layout acc9f035d195, hs 00a16c39374f, setup a8d6d330c526, návrh a22d941047d6, spec d9597dfcd605, knihovna 0f3a67cf7c68) = JSON výkresu – sedí.
17. Z-B-03 – výřezy 02–03: oranžový pruh 5,9–17,2, z ≈ 1,1–1,22, popisek Δ – hs where.x 12,0–17,2, návrh 5,9–17,2: nová poloha sedí, stará poloha na výkresu chybí – nesedí s konvencí legendy.
18. F-RCS-09 – výřez 04/07: červeně ×, x 4,0 z 1,9 plnou čarou – hs 4,0 / 1,9 tilt 30, návrh odstranit: poloha sedí, skrytost za gondolou (silueta do z 2,12) nesedí s pravidlem použitým u G-SN-02.
