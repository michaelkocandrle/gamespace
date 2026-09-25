<!-- kolo 1: zadání visual-critic v1 (bez pravidla o výhledu z kokpitu), bez checklistu; Explore + Fable 5.1 -->
# Verdikt: FAIL

První dojem: Z chase kamery to působí jako slušný AI-generovaný „SC-like“ trup s krémovým lakem a oranžovým pruhem, ale při pohledu zezadu a zblízka se rozpadá na rozmazaný, měkký blob bez skutečných mechanických dílů, s bakeovanými „motory“ místo geometrie.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
| --- | --- | --- |
| Silueta a tvar | 6 | Ze tří čtvrtin a z boku silueta sedí do stylu (dlouhý trup, dvě gondoly, ocasní plochy), ale zezadu a zespodu je trup zaoblený „batoh“ bez ostrých hran a bez odsazených dílů. |
| Hierarchie a hustota detailu | 4 | Chybí střední a mikro úroveň detailu – žádné odsazené panely s viditelnou spárou, žádné šrouby, kryty, kanály, klouby; jen jeden bakeovaný vzor „panelů“ v textuře. |
| Materiály | 4 | Lak nemá vrstvení SC (kov pod lakem, oděr hran, špína ve spárách), působí jako jednolitá rozmazaná difúzní textura; sklo kokpitu je tmavá hmota bez odlesku. |
| Decaly | 3 | Kromě oranžového pruhu a nečitelných skvrn není žádný čitelný decal – žádné číslo lodi, výstražné pásy, značky výrobce, technické popisky. |
| Světlo | 5 | Ve scéně je jen tvrdé slunce + tmavý vesmír; strana ve stínu je černá bez fill/odrazu od planety, motory svítí plošně bakeovanou texturou místo emisivního jádra s vnitřní geometrií. |
| Čitelnost (text, displeje, HUD) | 3 | Jediný text ve snímcích je debug HUD „FREE LOOK“ v horní části obrazu, na modelu není žádný čitelný text a zrcadlení/otočení nelze ani ověřit. |
| Chyby geometrie | 2 | Motory zezadu jsou dvě ploché „mince“ s bakeovanou fotkou turbíny, mezi nimi trčí čtyři nedefinované válce, zdola je viditelný artefakt soustředných kruhů a zubaté siluety. |
| Soulad stylu mezi díly | 5 | Přední polovina (nos, kokpit, pruh) je stylově blízko Origin/SC, zadní polovina (motory, ocas, podvozek) je z jiné, mnohem nižší úrovně a z jiného jazyka tvarů. |

## Rozdíly proti referenci

1. **Motory jsou bakeované placky, ne geometrie** – kde: list 03 pravá půlka, střed obrazu; list 05 pravá půlka, pravý snímek zezadu – co je špatně: každý motor je téměř plochý disk s vpálenou „fotkou“ turbínových lopatek; chybí tryska s hloubkou, vnitřní kužel, emisivní jádro, lamely – závažnost: musí se opravit – oprava: vymodelovat trysky jako skutečný válec/kužel s vnitřní geometrií, emisivní materiál místo baked textury.
2. **Zadní blok mezi motory je nedefinovaná hmota** – kde: list 03 pravá půlka, střed mezi motory a pod nimi – co je špatně: čtyři tmavé válce bez ukotvení a funkce, pod nimi visící šedý díl – závažnost: musí se opravit – oprava: zadní stěnu uzavřít definovaným panelem, válce odstranit nebo udělat čitelné nádrže s držáky.
3. **Spodek lodi s artefakty soustředných kruhů** – kde: list 04 pravá půlka, pravý snímek (zespodu) – co je špatně: soustředné kruhy/prstence (UV/reprojekční artefakt), hnědo-bílé pruhy, které nepatří k lakování – závažnost: musí se opravit – oprava: zkontrolovat UV a texturu spodku, přemalovat v jednotném laku s tmavými servisními panely.
4. **Chybí hard-surface panelace a spáry** – kde: list 02 a 01 pravá půlka, boky trupu – co je špatně: reference má odsazené panely, dvířka, kryty se šrouby; náš výsledek má plochou texturu s náznakem linek, geometrie je hladká, silueta hran je „bublinovitá“ – závažnost: musí se opravit – oprava: sekundární geometrie (panely, dvířka, kryty), normálová mapa se spárami, zostřit hrany (bevel + weighted normals).
5. **Sklo kokpitu bez materiálu** – kde: list 01 a 05 pravá půlka – co je špatně: kanopy je tmavě šedá matná hmota bez odlesku a rámu – závažnost: musí se opravit – oprava: materiál skla a rám kanopy jako geometrie.
6. **Žádné čitelné decaly** – kde: list 02 a 04 pravá půlka – závažnost: doporučeno – oprava: sada 8–12 decalů (registrace, logo, NO STEP, výstražné pásy, čísla panelů).
7. **Podvozek a zbraně nejsou definovány** – kde: list 01 pod přídí, list 03 konce křídel – závažnost: doporučeno – oprava: podvozek zatáhnout nebo vymodelovat s klouby, zbraně na výložník s držákem.
8. **Stínová strana je čistě černá** – kde: list 02 a 05 pravá půlka – závažnost: doporučeno – oprava: fill z planety, navigační světla, emisivní linky.
9. **Debug HUD ve schvalovacích snímcích** – kde: listy 01, 03, 04, 05 nahoře („FREE LOOK“) – závažnost: doporučeno – oprava: HUD pro snímky vypnout.
