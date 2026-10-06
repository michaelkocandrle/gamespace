# Podklady pro retrospektivu pilotu 1 (KF-PORTAL-01)

Sběr během pilotu. Retrospektiva po dokončení pilotu z nich udělá návrh workflow v1, který schvaluje autor.

## Návraty a přestavby

| Datum | Návrat | Příčina | Návrh opatření |
|---|---|---|---|
| 6. 10. | krok 3 → tabule vzorků neschválena | izolované vzorky snímané kolmo v tmavé místnosti | P26: materiály jen v kontextu, ze stejných úhlů jako etalon (v0.2, zapsáno) |
| 6. 10. | krok 3 schválen → zpět do kroku 2 (rev. C) | **návrhové chyby listu**: profil se četl jako proužky, patka jako krabička, podlaha jako rohožky bez sítě lemu | **přijato autorem 6. 10.:** krok 2 porovná pohled z oka v listu s etalonem (a po kroku 4 i s výsledkem) |
| 6. 10. | rev. C schválen kromě boty → rev. D | bota L1 tmavá a s reflektorem (ostré elipsy); etalon má světlou botu se září v kalichu | v kroku 1 popsat u každého svítidla etalonu i **charakter světla** (záře / kužel / skvrna), ne jen pozici a barvu |
| 6. 10. | kalibrace světla rev. C (4 kola) | rozložení jasu se ladilo naslepo intenzitami, automatická expozice kompenzovala | měřit `measure_look` podíl tmavých / světlých ploch už v kroku 3; tónová křivka interiéru (závoj) patří do základu |

## Návrhy změn workflow (zatím neschválené kromě označených)

1. **Krok 2:** pohled z oka v listu vedle kotevního záběru SC. *Přijato autorem 6. 10. 2026.* Po kroku 4 i vedle
   výsledku (list `sheet_05_oko_list_vs_hra.jpg`).
2. **Krok 1:** karta etalonu u svítidel zapíše charakter světla (záře / kužel / skvrna, dosah).
3. **Krok 3:** tabulka jasu (`measure_look`: průměr, p10, medián, p90, tmavé, světlé) proti etalonu je výstup kroku.

## Poučení z rev. E (autor 6. 10.: blockout schválen s úpravami tvaru)

| Problém | Poučení / pravidlo |
|---|---|
| Svislá čela stupňů (90°) četla ve světle shora jako tmavé proužky – rám jako 5–6 rovnoběžných pruhů | Čela profilů navrhovat jako plošky ≤ 45° k hlavnímu světlu; v kroku 2 stínovaný pohled z oka (proužky jsou vidět už v listu) |
| Bota se zkosením do pilíře četla z oka jako stříška | Tvary u paty: plochý vrch, zkosení jen svislých hran; zkontrolovat siluetu z oka 1,65 m |
| Kalich: světlo pár cm od světlého dna = plochý bílý osmiúhelník (3 kola) | Svítidlo-záře: tmavé dno, zdroj malý, světlo slabé (≈ 0,05 cd) u dna; ověřit snímkem zblízka v prvním kole |
| A/B (P5) odhalil, že se nepoložila žádná karta špíny (chyba v `hs_decals`) | A/B snímek je povinný i tehdy, když build hlásí jen „no faces“ – číst `decals_failed` v KITBUILD |
