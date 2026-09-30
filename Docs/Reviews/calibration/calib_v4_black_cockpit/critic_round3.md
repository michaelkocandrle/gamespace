<!-- kolo 3 (30. 9. 2026): zadání visual-critic v3 (bez „nejméně 5 rozdílů“, všechny relevantní nálezy podle závažnosti), bez checklistu; Explore + Fable, jen brief a listy -->
# Verdikt: FAIL

První dojem: Neosvětlená černá krabice se čtyřmi plovoucími tablety a bílým oknem do prázdna; jako kokpit ze Star Citizenu to nepůsobí, spíš jako blokový prototyp před nasvícením.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 4 | Šestiúhelníkový rám kabiny (list 01) je jediný čitelný tvar; palubní deska je hladký kvádr, sedačka sada šedých kvádrů a záběr zezadu (list 03) nemá vůbec žádný čitelný tvar. |
| Hierarchie a hustota detailu | 3 | Velké prázdné roviny bez sekundárního a terciárního detailu; kromě čtyř MFD a řádky teček pod displeji (list 02) není na čem zastavit oko. |
| Materiály | 3 | Jednolitá tmavě šedá bez opotřebení a variace, podlaha na listu 02 vypadá jako mramor/kámen, sklo je přepálená bílá plocha bez odrazů. |
| Decaly | 2 | Žádné popisky, varovné pruhy, čísla panelů ani štítky; jediný text mimo displeje jsou nečitelné cedulky ve dveřích na listu 03. |
| Světlo | 3 | List 01: interiér neosvětlen, ~60 % obrazu je černá bez tvaru; list 02: tabule kabiny přepálené do bílé proti tmavému interiéru; list 03: ploché bez modelace. |
| Čitelnost (text, displeje, HUD) | 5 | HUD a MFD na listu 01 jsou čitelné a stylově blízko SC, ale na listu 02 jsou všechny displeje černé, text ve dveřích na listu 03 je nečitelný a ve všech snímcích straší debug overlay. |
| Chyby geometrie | 3 | List 03: kamera za/uvnitř hmoty, dolní polovina záběru je jediný tmavý kvádr; list 02: černá beztvará hmota přes celou levou část; spoje vzpěr nahoře vypadají jako překrývající se roviny. |
| Soulad stylu mezi díly | 4 | Kokpit (listy 01, 02) je studená černá bez barvy, kabina (list 03 a pravá stěna listu 02) teplá béžová s oranžovými pásy; vypadají jako dva různé assety. |

## Pohled pilota (list 01, pravá půlka) – zvláštní posouzení

- **Podíl výhledu ven:** cca 25 % obrazu (horní středová tabule nad centrálním pilířem a dvě boční tabule mezi vzpěrami). Reference vlevo: cca 55–60 %, sklo sahá až k okrajům snímku.
- **Tloušťka rámu:** centrální pilíř od horního okraje dolů ke středu HUD má zhruba 5 % šířky obrazu; šikmé boční vzpěry po cca 4 % každá; k tomu spodní práh kabiny přechází bez hrany rovnou do tmy palubní desky.
- **Co zakrývá výhled:** (a) centrální pilíř přímo v ose pohledu, (b) dvě šikmé boční vzpěry, (c) černé boční hmoty od vzpěr k okrajům obrazu v levém a pravém horním kvadrantu, (d) horní plocha palubní desky v dolních ~38 % obrazu.
- **Tmavé/černé plochy bez tvaru:** levý horní kvadrant (od levého okraje po levou vzpěru, od horního okraje po desku), pravý horní kvadrant (zrcadlově), celá dolní třetina mimo čtyři MFD včetně obou dolních rohů. Dohromady odhadem 60–65 % obrazu.
- **Zabudování displejů:** čtyři samostatné desky (FLIGHT vlevo, RADAR + SELF STATUS ve středovém sloupci, STATUS vpravo) s tenkým světlým rámečkem položené na plochou tmavou stěnu, mezi nimi černé mezery; žádná tvarovaná schránka, žádná tlačítka kolem, žádné podsvícení lemů. Reference vlevo: MFD zapuštěné do tvarované desky, mezi nimi knipl.

## Rozdíly proti referenci

1. **Záběr zezadu neukazuje kabinu** – kde: list 03, pravá půlka, celá dolní polovina a střední pás – co je špatně: dolní polovinu obrazu vyplňuje jediný tmavý kvádr s lehkým leskem bez jakéhokoli tvaru, přes střed vede světle šedý vodorovný trám; kabina (sedačka, deska, kabina) není vidět, jen dveře s oranžovým pásem v pozadí; reference ukazuje sedačky, desku a kabinu v celku – závažnost: musí se opravit – oprava: postavit kameru za sedačku do výšky hlavy stojícího pilota tak, aby byla vidět opěrka, palubní deska a kabina; pokud je tmavá hmota opěradlo sedačky, zmenšit ji a dát jí tvar.
2. **Interiér z pohledu pilota je z 60 % černá bez tvaru** – kde: list 01, pravá půlka, levý a pravý horní kvadrant, dolní třetina mimo MFD – co je špatně: boční stěny/konzole a plocha desky nemají žádné nasvícení ani hranu, čtou se jako díra; reference má boční sklo a nasvícené konzole s tlačítky – závažnost: musí se opravit – oprava: přidat vnitřní vyplňové světlo (podsvícení tlačítek, lemy MFD, pásky na prahu), dát bočním hmotám tvar (panely, spáry) nebo je nahradit sklem.
3. **Výhled ven jen ~25 % obrazu** – kde: list 01, pravá půlka, boční vzpěry a černé boční hmoty, centrální pilíř – co je špatně: tlusté vzpěry a neprůhledné boky zmenšují výhled na méně než polovinu reference, centrální pilíř leží v ose pohledu – závažnost: musí se opravit – oprava: ztenčit vzpěry na 1–2 % šířky obrazu, protáhnout zasklení k bokům, snížit horní hranu desky nebo zvednout bod oka.
4. **Za sklem nic není** – kde: list 01 pravá půlka (všechny tabule), list 02 pravá půlka (tabule kabiny nahoře) – co je špatně: jednolitá šedá/bílá plocha bez horizontu, terénu nebo objektů, nelze poznat, že jde o sklo; reference ukazuje přistávací plochu, hory a mlhovinu – závažnost: musí se opravit – oprava: snímat s viditelným horizontem a terénem (denní scéna s plochou), ověřit, že sklo je průhledné a ne emisivní/šedé.
5. **Displeje na listu 02 jsou vypnuté** – kde: list 02, pravá půlka, tři černé obdélníky v horní části palubní desky – co je špatně: všechny tři obrazovky jsou černé bez obsahu, zatímco na listu 01 svítí; reference (obě půlky vlevo) má rozsvícené MFD s obsahem – závažnost: musí se opravit – oprava: displeje musí svítit i mimo pohled pilota (nebo alespoň při snímkování), obsah shodný s listem 01.
6. **Expozice listu 02: přepálené tabule, černá hmota vlevo** – kde: list 02, pravá půlka, horní tabule kabiny čistě bílé; levá část snímku od horního okraje po podlahu jednolitá černá polygonální hmota – co je špatně: dynamický rozsah rozbitý, interiér neosvětlen, levá hmota nemá tvar ani materiál – závažnost: musí se opravit – oprava: nastavit expozici na interiér, přidat vnitřní světla, dát levé stěně panely a nasvícení.
7. **Chybí fyzické ovladače** – kde: list 01 pravá půlka (mezi MFD a pod nimi), list 02 pravá půlka (deska a před sedačkou) – co je špatně: žádný knipl, plynová páka, přepínače ani tlačítka s popisky; jen řádka drobných teček pod displeji na listu 02; reference vlevo na listu 01 má knipl uprostřed, reference vpravo na listu 02 řady popsaných tlačítek (PWR, WPN, THR, SHLD…) – závažnost: musí se opravit – oprava: přidat knipl a plyn v dosahu sedačky, řady tlačítek/přepínačů s popisky kolem MFD.
8. **Chybí hologram lodi** – kde: list 01 pravá půlka (střed desky), list 02 pravá půlka (deska) – co je špatně: brief ho vyžaduje, reference (list 02 vlevo, středový projektor s modrým hologramem) ho má; u nás jen malá ikona lodi na SELF STATUS – závažnost: musí se opravit – oprava: holografický projektor ve středovém sloupci desky s 3D modelem lodi.
9. **Displeje nejsou zabudované, deska je kvádr** – kde: list 01 pravá půlka, čtyři MFD; list 02 pravá půlka, celá palubní deska – co je špatně: na listu 01 MFD leží jako samostatné tablety s tenkým rámečkem na ploché stěně s černými mezerami; na listu 02 jsou to holé obdélníkové výřezy v hladkém kvádru bez zkosení, rámu nebo tlačítek; reference má MFD zapuštěné do tvarovaných schránek s tlačítky – závažnost: musí se opravit – oprava: vymodelovat schránky MFD (zkosené rámy, tlačítka po obvodu, podsvícený lem) a rozčlenit desku na několik úhlů a panelů.
10. **Sedačka je sada kvádrů** – kde: list 02, pravá půlka, dolní pravá čtvrtina – co je špatně: šedé hranaté bloky bez polstrování, pásů, švů, tvarované opěrky hlavy; reference (list 03 vpravo) má tvarovanou pilotní sedačku – závažnost: musí se opravit – oprava: tvarované polstrování, pásy, opěrka hlavy, materiál látka/kůže odlišný od kovu.
11. **Debug overlay ve snímcích** – kde: listy 01, 02, 03, pravá půlka, pravý horní roh (FPS, Frame, Draw, VRAM…) – co je špatně: ladicí text v předávaném snímku – závažnost: musí se opravit – oprava: snímat bez stat overlay.
12. **Rám kabiny bez detailu a se špatnými spoji** – kde: list 01 pravá půlka, spoj centrálního pilíře s horní příčkou; list 02 pravá půlka, horní střed, kde se vzpěry sbíhají – co je špatně: vzpěry jsou hladké tmavě šedé plochy bez šroubů, těsnění a spár; spoj nahoře vypadá jako dva překrývající se polygony, ne jako konstrukční uzel – závažnost: doporučeno – oprava: těsnění skla, šrouby, spáry, jednoznačná geometrie spojů.
13. **Podlaha a děrovaný plech jako placeholder** – kde: list 02, pravá půlka, levý dolní roh – co je špatně: světlá mramorovaná textura působí jako kámen, tmavý plech s mřížkou kulatých děr je generický; reference má tmavou technickou podlahu s rošty a pásky – závažnost: doporučeno – oprava: tmavý kovový/pryžový povrch s protiskluzem, děrovaný plech nahradit členěným krytem.
14. **Světelné pásy bez účelu, přepálené** – kde: list 02, pravá půlka, bílý pás podél pravého boku sedačky dole; oranžový pás pod palubní deskou – co je špatně: bílý pás je vypálený do čisté bílé, oranžový pás svítí bez vazby na tvar; reference má světla u tlačítek a lemů – závažnost: doporučeno – oprava: snížit intenzitu, navázat světla na hrany panelů a ovladače.
15. **Dveře s nečitelnými štítky a nejasný objekt** – kde: list 03, pravá půlka, dveřní otvor uprostřed vpravo – co je špatně: drobné cedulky uvnitř dveří nejsou čitelné, béžový lesklý zaoblený objekt v dolní části otvoru nelze identifikovat – závažnost: doporučeno – oprava: štítky ve velikosti čitelné ze střední vzdálenosti, objekt ve dveřích buď dát tvar nebo odstranit.
16. **Nesoulad stylu kokpit vs. kabina** – kde: listy 01 a 02 (černá studená kabina) vs. list 03 a pravá stěna listu 02 (béžové panely, oranžové pásy) – co je špatně: dva barevné jazyky a dvě úrovně členění; reference drží jednotný jazyk – závažnost: doporučeno – oprava: jedna paleta a jeden panelový jazyk pro kokpit i zbytek kabiny.
17. **STATUS MFD duplikuje HUD** – kde: list 01, pravá půlka, pravý MFD vs. pravý sloupec HUD (R-ALT, VSI, ATMO, GEAR) – co je špatně: stejná data dvakrát, SELF STATUS jen ikona a „UP 58 %“; reference dává na MFD jiný obsah než HUD (zbraně, štíty, energie) – závažnost: doporučeno – oprava: na MFD energie/štíty/zbraně/cíl, HUD nechat letové údaje.

## Checklist z `brief.md` bod po bodu

Brief nemá samostatný oddíl „checklist“; procházím požadavky z „Co to má být“ a „Styl“.

- Kokpit malé jednomístné lodi: jedna sedačka je vidět (list 02) – splněno.
- Pohled pilota z oka, FOV 88°: záběr existuje (list 01), ale výhled ven ~25 % a ~60 % obrazu je černá bez tvaru – nesplněno v úrovni SC.
- Záběr kabiny z boku: existuje (list 02), displeje vypnuté, expozice rozbitá – částečně.
- Záběr kabiny zezadu: existuje (list 03), ale kabinu neukazuje – nesplněno.
- Moderní futuristická kabina: rám kabiny ano, deska a sedačka jsou kvádry – částečně.
- Zabudované displeje: samostatné desky / holé výřezy – nesplněno.
- Fyzické ovladače: žádné – nesplněno.
- Hologram lodi: žádný – nesplněno.
- Úroveň zpracování SC: nedosaženo (detail, materiály, světlo, decaly).
