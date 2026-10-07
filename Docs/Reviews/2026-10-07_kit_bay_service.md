# Servisní stěna (hasicí skříň, skříňky, kryt COMPONENT BAY) – 7. 10. 2026

Díl `SM_Kit_Bay_Service10W_A` (`Tools/Kit/kit_factory.py`, `bay_service`), reference `Docs/Kit/etalon/sc/decal_aurora_bay.jpg`
(autorův záznam z Aurory). Zadání autora 7. 10.: pokračovat se skříňkami a krytem component bay, hasičák větší.
Práh `step`. Snímky preset `kit_bay` (`-Editor`, 2560×1440).

## Kolo 1 – FAIL, průměr 5,9

Listy `2026-10-07_kit_bay_service/`, snímky `shots:20261007_015422_kit_bay`.
Skóre: silueta 6, hierarchie 5, materiály 5, decaly 5, světlo 6, čitelnost 6, geometrie 7, styl 7.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Jednolité „plastové“ materiály, bez špíny a variací (musí) | Částečně: karty špíny (`rim`, `smear`, `streaks`) u paty, prahů skříněk, madla krytu a pod nišou. Variace drsnosti a opotřebení hran dává sdílený materiál kitu; systémová změna materiálů kitu (`kit_materials.json`) mimo tento krok – týká se všech dílů. |
| 2 | Chybí nouzové značení hasicí skříně (musí) | Opraveno: ražený nápis FIRE EXTINGUISHER UNIT pod nišou, červený štítek s piktogramem přístroje na dvířkách, jejich účel SPARE CHARGE. |
| 3 | Prázdný štítek, rovná hadice, kolébka kvádr (musí) | Opraveno: potisk CO2 / FIRE EXTINGUISHER / CLASS B C E – 5 KG obtočený kolem válce (`emboss_text(wrap=...)`), červená linka; hadice v měkkém S; kolébka zaoblená, leštěný prstenec, dva šrouby. |
| 4 | Nízká hustota detailu (musí) | Opraveno: 20 šroubů v rozích buněk a otvorů, servisní spáry, štítek INSP, LOCKER 01/02, servisní poklop s mřížkou nad krytem (z kola 0). |
| 5 | Proporce skříněk a krytu (doporučeno) | Neopraveno: rozvržení drží šířku stěny 1,0 m a výšku 1,72 m z rozvrhu sekce; čtvercové skříňky by vyžadovaly širší díl – rozhodne autor. |
| 6 | Přesvětlené vnitřky skříněk (doporučeno) | Opraveno: světlo 0,3 → 0,2 cd. |
| 7 | Červená niša plochá barva (doporučeno) | Opraveno: zadní stěna červený lak místo emise, zdroj = svítící pás pod horním držákem, bodové světlo 0,9 cd shora (gradient dolů). |
| 8 | Drobné popisky nečitelné (doporučeno) | Opraveno: TORQUE větší (0,8), nové nápisy 17–19 mm. |
| 9 | Ražené logo bez opotřebení (doporučeno) | Částečně: karta špíny kolem loga; hrany písmen bez zaoblení (zaoblení písma ztrojnásobilo trojúhelníky, rozpočet 40 k). |

Rozpočet: text jako geometrie s výchozím rozlišením křivek 12 dal 90 k trojúhelníků; `resolution_u = 3` → 37 k (strop 40 k).

## Kolo 2 – FAIL, průměr 6,4

Listy `2026-10-07_kit_bay_service_r2/`, snímky `shots:20261007_020328_kit_bay`.
Skóre: silueta 7, hierarchie 6, materiály 5, decaly 7, světlo 6, čitelnost 7, geometrie 7, styl 6.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Plastové, příliš světlé panely (musí) | Opraveno: nová role `Kit_Housing` (lak gunmetal 0,105, kov 0,35, drsnost 0,34 s variací a grunge 0,32, opotřebené hrany) pro skříň jednotky. Paleta stěn chodby zůstává (autor 6. 10.: stěny středně šedé). |
| 2 | Plochý lososový rám niše (musí) | Opraveno: rám je teď z `Kit_Housing`, světlo niše 0,7 cd s dosahem 0,32 m (bylo 0,9 / 0,6). |
| 3 | Červená prosvítá na vnější rám (doporučeno) | Částečně: menší dosah světla; zbytek je odraz emisního pásu přes Lumen na sousední portál. |
| 4 | Proporce skříněk (doporučeno) | Neopraveno: viz kolo 1, bod 5 – rozhodne autor. |
| 5 | Kryt: logo moc velké, tenká deska (doporučeno) | Opraveno: HALCYON 5 cm (≈ 50 % šířky), deska 30 mm se zkosením 22 mm. |
| 6 | Přepálená horní skříňka (doporučeno) | Opraveno: světlo 0,2 → 0,12 cd. |
| 7 | Rohože jako díry (doporučeno) | Opraveno: protiskluzová rohož s gumovými žebry. |
| 8 | Prázdné plochy, chybí ovládací prvek (doporučeno) | Opraveno: červené tlačítko RELEASE v ochranném věnci na dvířkách pod nišou. |
| 9 | Málo kontrastní popisky (doporučeno) | Opraveno: tmavé pásy pod světlým ražením (styl textových pásů SC). |

## Kolo 3 – FAIL, průměr 6,75

Listy `2026-10-07_kit_bay_service_r3/`, snímky `shots:20261007_020851_kit_bay`.
Skóre: silueta 6, hierarchie 6, materiály 6, decaly 7, světlo 7, čitelnost 8, geometrie 7, styl 7.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Kryt bez silné desky a širokého zkosení (musí) | Opraveno: deska 30 mm, obvodová fazeta 45 mm jako skutečná šikmá plocha (`chamfer_band`, ploché stínování) ze světlejšího `Kit_Panel`; poly_prism s `bevel` fazetu nevykreslil čitelně. |
| 2 | Jednolitý grafit krytu a rámů (musí) | Opraveno: `Kit_Housing` grunge 0,42, variace drsnosti 0,3, škrábance 0,045; šmouhy u západek a madla, špína u paty krytu. |
| 3 | Málo vrstev kolem nik (doporučeno) | Opraveno: vystupující zkosené rámy kolem niky hasičáku a obou skříněk (`raised_frame`). |
| 4 | Proporce skříněk (doporučeno) | Neopraveno, viz kolo 1 bod 5 – rozhodne autor. |
| 5 | Světlá skvrna nahoře ve skříňkách (doporučeno) | Neopraveno: po snížení na 0,12 cd je to záměrný gradient od pásu pod stropem; posoudí autor ve hře. |
| 6 | Leštěný práh nečitelný (doporučeno) | Neopraveno: práh je `Kit_Lip`, z oka ho zakrývá rohož; drobnost. |
| 7 | Zkosení krytu přesahuje sloupec (doporučeno) | Neplatné: kryt 0,135–0,445 m leží uvnitř lůžka 0,10–0,48 m; šikmina vpravo nahoře je zkosený roh lůžka. |
| 8 | Kolébka je krabice (doporučeno) | Částečně z kola 1 (zaoblení 10 mm, prstenec, šrouby); prolis pod dnem neopraven. |

## Ověřovací kolo – PASS, průměr 6,75

Listy `2026-10-07_kit_bay_service_v/` (záběry 1, 2, 5), snímky `shots:20261007_021858_kit_bay`.
Skóre: silueta 7, hierarchie 6, materiály 7, decaly 7, světlo 6, čitelnost 7, geometrie 7, styl 7.
Bod 1 splněn, bod 2 splněn zblízka. Doporučení: větší měřítko masky drsnosti grafitu (z 1,65 m splývá), plošné
studiové světlo zkušebního úseku (posoudit pod lodním osvětlením), fazeta krytu vpravo opticky užší (úhel pohledu).
Otevřené pro autora: proporce skříněk a krytu (SC má skoro čtvercové skříňky) – chce to širší díl než 1,0 m.

Finální snímky ze zabalené hry: `shots:20261007_022246_kit_bay`.
