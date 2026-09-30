# Verdikt: FAIL

První dojem: Úzká chodba lodního kitu s dobře navrstveným stropem, která už působí jako udržovaná pracovní loď – ale stěny a konstrukce jsou pořád jedna hladká tmavá hmota v několika odstínech, ne kov, lak a guma.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 7 | Zkosené horní rohy se žlábkem, nízký konstrukční strop a lichoběžníkový průřez (list 01, 03) jsou správně; pod zkosením jsou stěny čistě rovné, prostor se čte jako chodba, ne jako tvarovaný trup. |
| Hierarchie a hustota detailu | 7 | Strop má žlab, kabely, trubky na závěsech, poklop; stěny mají vložené panely, skříňku, mřížku s krabicí – ale stropní panely zblízka (list 04) a čelo kolem dveří (list 02) jsou prázdné plochy. |
| Materiály | 6 | Tónové rozlišení (tmavý panel / světlejší žebro / světlá skříňka) je, ale všechno má stejnou drsnost a odezvu; broušený kov, guma a opotřebené hrany na listech 03 a 04 nejsou vidět. |
| Decaly | 7 | CREW QUARTERS, 05/06 SECTION, COCKPIT »», výstražné pruhy v chodbě jsou čitelné a nezrcadlené; chybí nouzové značení a popisky ovladačů. |
| Světlo | 7 | Přepaly zmizely, svítidla jsou v pouzdrech, žlábek a světelné skvrny jsou tlumené; schody svítí studeně modře a závěsy trubek jsou skoro bílé. |
| Čitelnost (text, displeje, HUD) | 7 | Nápisy jsou čitelné ze vzdálenosti hráče; štítky na panelech (LIFE SUPPORT) jsou na hraně čitelnosti. |
| Chyby geometrie | 7 | Žádné díry ani průniky; dočasný nábytek nekoliduje se stěnami; otazník u ukotvení zábradlí (list 05) a hluboké šachty svítidla (list 04). |
| Soulad stylu mezi díly | 7 | Kit je jednotný (grafit, světlá konstrukce, oranžové akcenty); modrobílé schodišťové pásy vybočují z „teplá architektura / studené UI“. |

## Ověřované body z minulého kola

1. **Prázdné stěny mezi žebry, servisní modul bez hloubky – OPRAVENO (s výhradou).** List 03 pravá půlka: panely 05 a 06 jsou vložené se stínovou spárou a oranžovým proužkem, skříňka má rám s viditelnou hloubkou, dvě oranžové západky a indikátor, u mřížky vlevo dole je krabice s přípojkou. List 01/02: stěna už není holá. NELZE OVĚŘIT na dodaných listech: těsnění a panty skříňky (střední vzdálenost je nerozliší), svod od krabice dolů (nevidím ho), madlo podél lišty u dveří (list 02 vpravo od rámu dveří, y≈300, vidím jen malý tmavý objekt, ne madlo). Chybí list zblízka.
2. **Jeden jednolitý matný materiál – ČÁSTEČNĚ, NEOPRAVENO v plném rozsahu.** Rozlišení je jen tónové: tmavý panel, světlejší žebro a lišta, světlá skříňka. Broušený kov konstrukce (anizotropní lesk, světlé hrany) na žebrech a liště (list 03, x≈1270 a 1490) není vidět; guma nikde (těsnění skříňky, madla, sokl); opotřebené hrany konstrukce nejsou vidět; stropní panel zblízka (list 04) je dokonale jednolitý. Trubky a žlaby mají kovový lesk, to je jediný povrch, který se čte jako kov.
3. **Přepálené zdroje světla – OPRAVENO.** Skvrny na horním panelu pod stropem (list 03, x≈1130 a x≈1750, y≈250–310) jsou tlumené teplé přechody, ne bílé přepaly. Pás nad průchodem ke schodům (list 01 vrchol průchodu; list 05 horní rám) není přepálený. Světlo z technické chodby za dveřmi (list 02) je tlumené, chodba je čitelná jako sousední místnost.

## Rozdíly proti referenci

1. **Materiály bez odezvy povrchu (bod 2 jen částečně)** – kde: list 03 pravá půlka, celá stěna (horní panely, lišta v 1,3 m, žebra, skříňka); list 04 pravá půlka, stropní panely zblízka – co je špatně: tři odstíny jednoho matného materiálu; žádný broušený kov na konstrukci, žádná guma, žádné opotřebené hrany žeber a rohů lišty; stropní panel zblízka bez šumu, šroubů a spár – závažnost: musí se opravit – oprava: konstrukce (žebra, lišta, rámy) brushed metal s vyšší speculární odezvou a světlou hranou přes edge mask; panely matný lak s jemným šumem roughness; černé gumové prvky (těsnění dvířek skříňky, konce madel, lišta u soklu); dodat list zblízka (≤ 1 m) na spoj žebro / panel / lišta.
2. **Detaily servisního modulu nelze ověřit** – kde: list 03 pravá (skříňka střed, krabice u mřížky vlevo dole); list 02 pravá (vpravo od dveří, y≈300) – co je špatně: těsnění, panty, svod a madlo u dveří na střední vzdálenosti nerozeznám – závažnost: doporučeno – oprava: list zblízka na skříňku a na oblast dveří; panty a svod udělat kontrastnější (tmavší, silnější profil), aby byly čitelné i ze 2 m.
3. **Strop: prázdná pole panelů a hluboká šachta svítidla** – kde: list 04 pravá, střed (svítidlo x≈1440–1580, y≈200–320) a okolní panely – co je špatně: hlavní svítidlo je vícestupňová hluboká šachta, zblízka působí jako otvor do stropu, ne jako svítidlo v pouzdře; panely kolem jsou velké prázdné plochy – závažnost: doporučeno – oprava: zploštit na jeden stupeň rámu + difuzor; šrouby v rozích panelů, jeden servisní štítek, případně tenčí hadice/žlab mezi panely.
4. **Studené schodišťové pásy** – kde: list 01 pravá, schody (x≈1440–1540, y≈360–460); list 05 – co je špatně: LED pásy pod nášlapy jsou modrobílé a jasné, obarvují spodní stupně do modra; v teplém interiéru se čtou jako UI, ne architektura – závažnost: doporučeno – oprava: teplá/neutrální bílá, intenzita o třetinu níž, kužel jen na nášlap.
5. **Světlé závěsy trubek působí jako svítidla** – kde: list 01 pravá, vpravo nahoře (x≈1680–1900, y≈60–110); list 06 pravá nahoře (x≈1620 a 1840, y≈60) – co je špatně: konzoly trubek jsou téměř bílé bloky, jasnější než okolí – závažnost: doporučeno – oprava: stejný tmavý kov jako trubky, vyšší roughness, případně oranžová svorka jako akcent.
6. **Světelné skvrny na horní stěně jsou měkké kruhy bez zdroje** – kde: list 03 pravá, horní panel nad skříňkou (x≈1130 a x≈1750, y≈250–310) – co je špatně: už ne přepálené, ale rozmazané kruhy bez hrany, nesedí k viditelnému pouzdru – závažnost: doporučeno – oprava: kužel ze stropního svítidla (IES / užší cutoff), aby skvrna měla tvar a hranu.
7. **Čelo přepážky kolem dveří je holé** – kde: list 02 pravá, plocha kolem rámu dveří (x≈1350–1400 a 1580–1620, y≈200–450) – co je špatně: rovný tmavý panel, dvě stavové kontrolky a nápis; chybí těžký rám dveří s kabelovým vstupem, ovládací panel s popiskem, výstražný pruh na prahu – závažnost: doporučeno – oprava: rám s přesahem 5–8 cm, ovládací panel dveří s popiskem, výstražný pruh na podlaze u prahu (reference list 02 vlevo dole).
8. **Ukotvení zábradlí schodů** – kde: list 05 pravá, levé zábradlí (x≈1290–1400, y≈330–480) – co je špatně: spodní konec trubky končí nad nášlapem bez viditelné patky – závažnost: doporučeno – oprava: patka do stupně nebo kotva do stěny.
9. **Příčky na stěně u průchodu** – kde: list 05 pravá, pravá stěna (x≈1820–1900, y≈100–330) – co je špatně: sada příček vedle průchodu, účel z místa nečitelný (žebřík k poklopu? madlo?) – závažnost: doporučeno – oprava: je-li to žebřík k poklopu (list 04, poklop s oranžovými západkami), umístit poklop přímo nad něj a označit; je-li to madlo, jeden kus ve výšce lišty.
10. **Chybí nouzové značení a popisky ovladačů** – kde: list 02 a 05 pravá, okolí dveří a průchodu – co je špatně: jen názvy sekcí a směrovka; žádný EXIT / nouzové světlo, žádný popisek u ovládacího panelu (list 05, x≈1130, y≈480) – závažnost: doporučeno – oprava: nouzový štítek nad dveřmi do chodby, popisek DOOR / LOCK u panelu, čitelný z 1,5 m.

## Checklist z briefu

- **Tvar prostoru z trupu:** splněno – zkosené horní rohy se žlábkem, nízký strop, lichoběžníkový průřez (list 01, 03, 06).
- **Vrstvy:** převážně splněno – žebra, žlab s kabely, trubky na závěsech, vložené panely se spárou, skříňka se západkami, mřížka s krabicí; mřížka v podlaze jen v technické chodbě (list 02); madla neověřeno (bod 2).
- **Účel předmětů:** splněno (dočasný nábytek mimo hodnocení); příčky u schodů (list 05) mají nejasný účel.
- **Materiály:** nesplněno – chybí guma, broušený kov a opotřebení, panely jednolité (list 03, 04); béžová jen u dočasného nábytku (mimo hodnocení).
- **Decaly:** částečně – CREW QUARTERS, 05/06 SECTION, COCKPIT »», výstražné pruhy; čitelné, nezrcadlené; chybí nouzové značky a popisky ovladačů.
- **Světlo:** splněno – bez přepalů, svítidla v pouzdrech, žlábek, tmavé kouty (list 02 vlevo); výhrady: studené schody, ploše osvětlená podlaha (list 01), světlé závěsy.
- **Geometrie:** splněno – žádné díry ani průniky; nábytek nekoliduje se stěnami (list 06: skříň těsně pod žlábkem, bez průniku); otazník u konce zábradlí (list 05).

Důvod FAIL: bod 2 z minulého kola není dopracovaný (materiály 6/10, výtka 1 „musí se opravit“). Body 1 a 3 jsou opravené; u bodu 1 zůstávají dílčí prvky (těsnění, panty, svod, madlo u dveří), které tyto listy neumožňují ověřit – doporučuji list zblízka.
