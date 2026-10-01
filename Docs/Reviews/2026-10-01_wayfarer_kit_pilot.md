# Wayfarer – pilot exteriérového kitu (hřbet, ramena, záď, gondoly), 1. 10. 2026

**Zadání (autor 1. 10.):** výkresy E-01 až E-08 schválené, hřbet v desky primárního laku (gunmetal jen na břiše),
rám rampy schválen; postavit exteriérový kit a pilot podle schválených výkresů na části lodi, kterou chase kamera
vidí nejvíc (hřbet a záď s gondolami); kritik s dílčím prahem.

**Postaveno** (`Tools/Design/exterior_kit_layout.py` → `Design/Wayfarer_exterior_kit.json` →
`Tools/Blender/hs_exterior_kit.py`):
- 20 desek hřbetu R (primární lak) a 11 desek ramene S (sekundární lak, zrcadlené), 328 šroubů;
- rám: žebra nad v 0,75 a přes hřbet, podélníky FR-LONG-HI a FR-LONG-TOP, páteř FR-SPINE (gunmetal);
- plášť pod deskami v oblasti x 3,0–15,4 nad v 0,76 gunmetal (nový slot `Gunmetal`);
- záď: rám rampy F-RAMP-FRAME, písty F-RAMP-PISTON, pracovní světlo L-RAMP (reflektor 150 cd);
- gondoly: bloky XK-RCS F-RCS-12 (dole) a F-RCS-13 (nahoře), záblesková světla ploutví a křídel (slot `Strobe`);
- skříň ploutve v sekundárním laku; grafitové sedlo livery A vypnuté (hřbet v primárním laku);
- z receptu odebráno, co kit nahrazuje: desky P-B-02/03/04/14/15/16/17, bloky RCS F-RCS-07/10/11.

Snímky: `shots:20261001_161422_wayfarer_kit_pilot/` (sada `Tools/Shots/wayfarer_kit_pilot.json`).

## Kola kritika

### Kolo 1 – FAIL, průměr 5,4 (práh dílčího kroku 6,5, žádná kategorie pod 6)

Silueta 7, hierarchie 5, materiály 5, decaly 5, světlo 4, čitelnost 6, geometrie 6, soulad stylu 5.
Výstup kritika: [round1/critic.md](2026-10-01_wayfarer_kit_pilot/round1/critic.md), listy v `round1/`.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Písty rampy jsou dráty (musí) | Opraveno: XK-PISTON rev. D – gunmetal válec Ø 160 s kovovými prstenci, chromová pístnice Ø 70, oka ve vidlicových držácích (dvě líce a základní deska se 2 šrouby, nahoře na rámu rampy, dole na zádi), tlaková hadice Ø 30 z paty válce do stěny. |
| 2 | Hřbet je jednotvárná dlažba (musí) | Opraveno: tři velikosti desek – desky R, přídavné panely XK-DOUBLER 12 mm nad deskou se šrouby (v lichých polích dlouhý pás u páteře, v sudých čtvercový panel) a malé poklopy XK-HATCH v rovině desky se spárou 12 mm a dvěma západkami; páteř XK-SPINE 280 mm s hřebenem 100 mm proti žebrům 80 mm. Model výkresu panely umístí sám (70 mm od hran a výřezů, posun po poli, jinak vynechá): 11 panelů, 14 poklopů. Zapuštěné mřížky u páteře E-03 nemá; tmavá pole u páteře jsou výřezy kolem poklopů a zapuštění, ta postavená jsou. |
| 3 | Rám bez konstrukce (musí) | Opraveno: žebra a podélníky mají profil T (stojina 30 × 12 mm na pásnici 80 mm), řady šroubů Ø 12 po 250 mm po obou stranách stojiny; dno kanálu má nový materiál Channel (tmavší a hrubší než rám, se špínou), takže kanál čte hloubku. |
| 4 | Záď je prázdná bílá krabice (musí) | Opraveno: na dveřích rampy nášlapné lišty po 160 mm a tmavý pryžový práh místo béžového pruhu (projekční decal D-HAZARDRAMP i ošlapaná hrana D-H-35 odstraněny); pant s 5 oky na spodní hraně; rám rampy 50 mm se šrouby po 150 mm a styčníky v horních rozích; výstražné pruhy podél rámu; nápis RAMP – STAND CLEAR přes dveře (písmo 10 cm). Madlo D-H-31 a šrouby závěsu D-H-34 zrušeny (místo zabraly písty a pant). Zbytek zadní stěny (desky P-B-08/09, mřížky) beze změny. |
| 5 | Světla kitu ve tmě nesvítí (musí) | Opraveno: pouzdra XK-STROBE 260 × 80 mm mají vedle záblesku stálé poziční světlo (bílé na ploutvích, vlevo červené a vpravo zelené na koncích křídel, emise jako navigační světla); pracovní světlo je kulatá lampa s clonou, držákem a teplou svítící čočkou, reflektor 300 cd. Hra záblesk bliká (0,06 s), mezi záblesky je tma; stálé světlo teď drží měřítko. Snímky soumraku a vesmíru byly špatně (bod 12). |
| 6 | Blok RCS je drobná krabička (musí) | Opraveno: XK-RCS 800 × 500 × 180 mm, gunmetal skříň se stupněm na montážní desce s 8 šrouby (zapuštěné do gondoly, bez mezery na oblém povrchu), 5 otevřených trysek do 4 směrů s tmavým vnitřkem a prstencem tepelného zabarvení; stejný blok nahoře i dole na obou gondolách. |
| 7 | Materiály bez variace (doporučeno) | Částečně: špína a hrubost ve dnech kanálů (Channel), variace tónu desek 0,07 → 0,10 a drsnosti 0,12 → 0,18. Odření hran nezvyšuji: autor 26. 9. – lak SC nemá odřené hrany, špína je v lesku. |
| 8 | Decaly řídké (doporučeno) | Částečně: nápis rampy tmavý a 10 cm, výstražné pruhy u rampy. Čísla panelů jsou ve výkresu jako navržené pravidlo D-R-PANEL-NUMBERS s novou položkou knihovny `xst_panel` (číslo pro každou desku), postaví se s kitem celé lodi. U bloků RCS pruhy ne: koncept C chce žlutočerné pruhy jen u servisních míst. |
| 9 | Dvě symetrické desky zádi s jiným leskem (doporučeno) | Opraveno: zrcadlové kopie (_L / _R) byly dva zdrojové objekty s vlastní náhodnou variací panelu (jedna holý kov); `hs_assemble_ship` jim teď dává jednu identitu panelu. |
| 10 | Žluté okno na gondole (doporučeno) | Je to otevřená šachta gondoly F-POD-BAY s rozvody (schválený prvek) a pracovním světlem L-BAY-GLOW; světlo ztlumeno z 10 na 4 cd, aby z chase kamery nečetlo jako okno kabiny. |
| 11 | Trysky motorů jako krémové disky (doporučeno, mimo pilot) | Mimo pilot: vnitřek trysky s žebry a emisivním jádrem patří do dalšího kroku (gondoly), zapsáno do CURRENT.md. |
| 12 | Soumrak a vesmír neukazují kit (doporučeno) | Opraveno: loď stojí na straně planety ve směru −X (lokální „nahoru“ = světové −X, doleva = světové −Y; ověřeno zkušebními snímky `wayfarer_sun_calib`), takže `space.SunDir -52 102` dávalo slunce 7° pod obzorem. Soumrak teď 6° nad obzorem zezadu zleva (nízké světlo přes záď a hřbet), noční snímek zádi se světly (slunce 10° pod obzorem), vesmír 30° zezadu zleva s kamerou u lodi (loď zabírá třetinu obrazu i víc). |

Výkresy prošly revizí D (`_revision_D` v návrhu): E-01 až E-08 přegenerované, test „výkres = data“ PASS; razítko
„REV. D KE SCHVÁLENÍ (SCHVÁLENA C)“. Šrouby desek se nově rozkládají rovnoměrně (`em.bolt_columns`).

Nalezeno při opravách (mimo výtky):
- Pod každým žebrem je šev trupu – drážka do V 30 mm široká a 10 mm hluboká se stěnami se sklonem nz 0,6. Filtr
  normál žeber přes hřbet (nz ≥ 0,9) je vyřadil, takže žebra měla uprostřed propad a stojina se nevyřízla vůbec.
  `fill_grooves` teď zvedne vrcholy v drážce na úroveň okolí (350 vrcholů) a filtr žeber na hřbetu je nz ≥ 0,5.
- `kdop_hull` (kolize) po 12 pokusech použil uvolněný bmesh; spustily to nové díly na zádi. Blender při výjimce
  v `--python` skončil kódem 0 a dvě přestavby tiše nezapsaly game blend (WORKFLOW 9.6 fg). Opraveno: 40 pokusů,
  potom kvádr oblasti; přestavby jedou s `--python-exit-code 1`.
- Přídavné panely a poklopy se vyhýbají decalům (dva poklopy padly přes štítky); výstražné pruhy u rámu přešly na
  y 1,36 (na 1,335 jejich mřížka narazila na hadici válce a decal se přeskočil).

### Kolo 2 – FAIL, průměr 5,9

Silueta 7, hierarchie 5, materiály 5, decaly 5, světlo 5, čitelnost 7, geometrie 7, soulad stylu 6.
Výstup kritika: [round2/critic.md](2026-10-01_wayfarer_kit_pilot/round2/critic.md), snímky
`shots:20261001_174928_wayfarer_kit_pilot/`.

Musí se opravit (kolo 3 – nedokončeno, limit využití 1. 10. 2026 večer): (1) hřbet čte jako dlaždice / okna – kanál
tmavě šedý místo černého, menší zkosení desek (XK-PLATE bevel 4 mm), bez karbonových panelů (CarbonShare 0) na
dílčích panelech; (2) rám jako konstrukce – rám světlejší a kovový (Gunmetal 0,24, metallic 0,8), větší šrouby rámu;
(3) střední vrstva – rozvody podél páteře (koncept B „rozvody po hřbetu“), větrací skříně místo části panelů -D,
větrací skříně na zádi místo decalu D-H-01, zostřit desky P-B-08/09; (4) materiály – RoughVariation 0,45,
GrungeAmount 0,3, ClearCoatRoughVariation 0,3, špína v kanálech; (5) čísla desek z výkresu (pravidlo
D-R-PANEL-NUMBERS: nové položky `panel_RL03…` v `decal_library.json`, přestavba knihovny `decal_library.py`; ověřit,
jak se atlas T_Decals_* dostane do UE – import ho nenašel); (6) soumrak teplé slunce (`space.Sun` barva) a noc
s `space.Sky Intensity 0.03`, silnější pracovní světlo. Doporučené: lišty jen ve spodní polovině dveří, válec tmavý /
pístnice kov, hadice se smyčkou, širší pruhy, hřeben páteře světlejší.

Reakce na kolo 2 (provedeno 1. 10. 2026 večer, před kolem 3):

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Hřbet čte jako dlaždice / okna (musí) | Opraveno: dno kanálu tmavě šedé (Channel 0,10 místo 0,05), zkosení desek XK-PLATE 4 mm (bylo 8), bez karbonových panelů (CarbonShare 0 – tmavé desky četly jako díry). |
| 2 | Rám jako konstrukce (musí) | Opraveno: Gunmetal 0,24 (bylo 0,16), metallic 0,8, šrouby žeber a podélníků Ø 18 (12), páteře Ø 22 (16); hřeben páteře z holého kovu. |
| 3 | Střední vrstva (musí) | Opraveno: rozvody XK-CONDUIT (F-CONDUIT) v servisním kanálu 200 mm mezi páteří a deskami (spine_gap 0,34) – trubka Ø 60 gunmetal a Ø 40 tmavá, 30 mm nad pláštěm, objímky po 0,5 m mimo žebra, konce do pláště s přírubou; větrací skříně XK-VENTBOX na hřbetu v polích 08 a 12 místo čtvercových panelů -D (pole 06 a 10 je nepojmou: výřezy antény a dílů); na zádi F-VENT-AFT místo decalu D-H-01; desky P-B-08/09 40 mm a zkosení 3 mm. Decaly D-H-23 (poklop) a D-H-25 (řada šroubů) na hřbetu odebrány – nahrazují je skutečné poklopy a šrouby kitu. Pruh panelů v lichých polích užší (y 0,07–0,35), aby se vešel vedle poklopů. |
| 4 | Materiály (musí) | Opraveno: lak RoughVariation 0,45, GrungeAmount 0,3, ClearCoatRoughVariation 0,3; rám RoughVariation 0,35, Grunge 0,25. |
| 5 | Čísla desek (musí) | Opraveno: cesta atlasu ověřena – `Wayfarer_setup.json` `textures` → `ship_materials.import_texture` → `/Game/Ships/Wayfarer/Textures/T_Decals_*` při každém `import_ship.py` (ne `/Game/Ships/Shared`, proto ho hledání nenašlo). Čísla podle pravidla D-R-PANEL-NUMBERS na deskách R a S (29 desek; RL05/RP05 vynechané, číslo by leželo ve výřezu): ramena v dolním zadním rohu, hřbet u zadní hrany mezi panely a poklopy. Položka na číslo se do atlasu nevešla, čísla se skládají ze 14 znaků `pn_*`. |
| 6 | Soumrak a noc (musí) | Opraveno ve snímcích: soumrak s teplým sluncem (`space.Sun LightColor 255 160 95`), noc s oblohou `space.Sky Intensity 0.03` a nový noční snímek zezadu shora; pracovní světlo rampy 700 cd (bylo 300). Level sám den a noc nerozlišuje (známý problém). |
| dop. | Lišty, válec, hadice, pruhy, hřeben | Válec tmavý, pístnice chrom; hřeben páteře kov. Lišty už jsou ve spodní polovině dveří (z 0,06–0,70). Smyčka hadice a širší pruhy nedělány (doporučené, mimo rozsah kola). |

### Kolo 3 – FAIL, průměr 6,4 (poslední kolo; práh 6,5)

Silueta 7, hierarchie 6, materiály 6, decaly 6, světlo 6, čitelnost 7, geometrie 7, soulad stylu 6.
Výstup kritika: [round3/critic.md](2026-10-01_wayfarer_kit_pilot/round3/critic.md), snímky
`shots:20261001_205521_wayfarer_kit_pilot/` (editor); ze zabalené hry `shots:20261001_211213_wayfarer_kit_pilot/` (stejný obraz). Kolo 2 → 3: +0,5, všechny
kategorie aspoň 6.

| # | Výtka (závažnost) | Reakce |
|---|---|---|
| 1 | Desky ramen S čtou jako okna (musí) | Otevřené: sekundární lak (šedý, lesklý) odráží oblohu. Další krok: světlejší teplejší šedá s vyšší drsností, na desky S panely / poklopy / čísla jako na hřbetu (pás S v kitu zatím bez `sub`). |
| 2 | Záď bez vrstvení desek na rámu (musí) | Otevřené, systémové: kit zatím pokrývá jen rám rampy; zadní stěnu je třeba rozdělit na desky na rámu (pás AFT v rozvrhu jako R a S). Kritik píše, že rám nemá šrouby, styčníky a hadici – ty postavené jsou (kolo 1, bod 1 a 4); na snímcích ze vzdálenosti nečtou. |
| 3 | Noc neukazuje světla lodi (doporučeno) | Otevřené: `space.Sky Intensity 0.03` trup neztmavil – trup svítí dál od atmosféry / Lumenu; pracovní světlo 700 cd nedělá na rampě skvrnu. Ověřit zdroj osvětlení v noci (`space.LightList`). |
| 4 | Přepálené červené poziční světlo (doporučeno) | Otevřené: snížit bodové světlo u pouzdra XK-STROBE na křídle / gondole. |
| 5 | Hřbet z dálky jako žebřík (doporučeno) | Otevřené: tmavé výřezy kolem poklopů a skříní; zvážit gunmetal místo dna kanálu ve výřezech. |
| 6 | Málo šablon a výstrah (doporučeno) | Otevřené (koncept C: pruhy jen u servisních míst); rozšířit pruhy rampy. |
| 7 | Lak bez variace a špíny (doporučeno) | Variace a špína zvýšené v tomto kole (RoughVariation 0,45, Grunge 0,3); kritik je nevidí – další krok: karty špíny v kanálech (grime). |
| 8 | Rozvody nečitelné (doporučeno) | Zblízka čitelné (objímky z holého kovu); z dálky ne – zvážit světlejší trubku Ø 60. |
| 9 | Černé tyče v rohu zádě (doporučeno) | Ověřit: pravděpodobně hadice pístu nebo anténa; při kitu zádě. |

Mimo výtky: trup s rozvody přešel limit exportéru 1 M trojúhelníků (1,03 M) – rozvody jsou souvislá trubka místo válce
na segment, šrouby 8 stěn; trup 991 k. Trysky jako krémové disky (kolo 1, bod 11) zůstávají na krok gondol.
