# Verdikt: FAIL

První dojem: Prostor má správný průřez a barvu grafitu, ale jako hráč vidím čistý showroom s přepálenými zářivkami, ne pracovní loď – špína, která je předmětem tohoto kroku, se na žádném detailním listu nečte.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 7 | Chodba má lichoběžníkový/osmiúhelníkový průřez, žebra a nízký strop (list 01, 04 vpravo); schodiště na listu 08 stojí v černé prázdnotě bez okolních stěn. |
| Hierarchie a hustota detailu | 6 | Stěny chodby jsou velké prázdné desky bez shluků kolem funkčních míst (list 01 vpravo, levá i pravá stěna), strop je monotónní řada čtyř stejných pásů; reference (list 01 vlevo) shlukuje větrák, kabely, panely s hloubkou. |
| Materiály | 4 | Karty špíny (sokl, spáry, stékání pod mřížkou, rám poklopu a mřížky) nejsou čitelné na žádném detailním listu; místo toho je po celých plochách jemný rovnoměrný šum a lamely mřížky jsou béžový plast (list 03 vpravo). |
| Decaly | 7 | „F02“, „VENT – KEEP CLEAR“, „SERVICE ACCESS“ jsou čitelné a nezrcadlené (list 01, 03 vpravo); značení je mimo tento krok, takže jen málo materiálu k hodnocení. |
| Světlo | 4 | Stropní pásy na listech 01 a 04 vpravo a velké panely na listu 09 vpravo (levý horní a levý dolní roh) jsou vypálené do čisté bílé s halo; brief výslovně chce „jádro ne čistě bílé“. |
| Čitelnost (text, displeje, HUD) | 7 | Popisky na listu 03 vpravo jsou čitelné; svislý nápis na listu 09 vpravo (pravá spodní čtvrtina) je příliš malý na přečtení; displeje v záběrech nejsou. |
| Chyby geometrie | 7 | Žádné díry ani průniky, ale list 08 vpravo je schodiště v černém prázdnu a list 09 vpravo má uprostřed velkou hladkou světle šedou plochu bez kresby (střed obrazu). |
| Soulad stylu mezi díly | 6 | Chodba je teplý grafit (list 01), stěna s mřížkou je teplá béžově hnědá (list 03 vpravo) a schodiště studeně šedá ocel s čistě bílými nášlapnými hranami (list 08 vpravo). |

## Rozdíly proti referenci

1. **Špína u soklu a v podélných spárách podlahy neexistuje** – kde: list 02, pravá půlka, pata stěny a sokl (dolní třetina, střed obrazu) a spáry podlahy (pravá dolní čtvrtina); list 05, pravá půlka, spára mezi deskami (diagonála od horního středu k pravému dolnímu rohu) a spára kolem rámu mřížky (horní okraj) – co je špatně: spáry jsou čisté tenké čáry, sokl i pata stěny mají naprosto stejný tón jako plocha panelu; v referenci (list 02 vlevo, spodní okraj podlahy a pata skříněk) se špína čte jako tmavší matný pás v rohu a v drážkách – závažnost: musí se opravit – oprava: maska v pásu 2–5 cm od hrany se znatelně tmavším albedem (o 25–35 %) a vyšší roughness, měkký přechod a nepravidelnost podél délky; u soklu pás 5–8 cm s rozmytým horním okrajem.

2. **Stékání pod větrací mřížkou chybí** – kde: list 03, pravá půlka, panel pod rámem mřížky (střed obrazu, spodní polovina) – co je špatně: pod mřížkou není žádná stopa, panel je totožný s panelem vedle; jediný rozdíl tvoří rovnoměrný mikro-šum po celé ploše – závažnost: musí se opravit – oprava: 3–5 svislých stop nestejné délky (10–30 cm) vycházejících ze spodních lamel, tmavší a matnější, nejsilnější těsně pod rámem a slábnoucí dolů; tmavý prach v dolních rozích rámu.

3. **Přepálená svítidla, jádro čistě bílé** – kde: list 09, pravá půlka, velký panel v levém horním rohu a v levém dolním rohu (bílé plochy bez kresby, halo na okolní konstrukci); list 01 a 04, pravá půlka, všechny čtyři stropní pásy (bílé linky, rámeček ani difuzor nejsou vidět) – co je špatně: brief chce rámeček a jádro ne čistě bílé, výsledek je clipping do bílé; reference (list 09 vlevo, svítidla u stropu) má viditelné pouzdro a teplé jádro – závažnost: musí se opravit – oprava: snížit emisivitu tak, aby jádro zůstalo pod clippingem (po tone mappingu cca 0,85–0,9), teplá barva 3500–4000 K, viditelný rámeček a lehká struktura difuzoru, omezit bloom.

4. **Vyšlapaná linie uprostřed podlahy se nečte** – kde: list 04, pravá půlka, osa chodby mezi oběma mřížkami; list 05, pravá půlka, prostřední deska mezi dvěma diamantovými proužky (svislý pruh oranžových teček ve středu obrazu) – co je špatně: na listu 04 se osa chodby nijak neliší od krajů; na listu 05 se stopa čte jako pruh oranžových odlesků/teček, ne jako ohlazený, lehce světlejší a hladší pás – závažnost: musí se opravit – oprava: pás 60–80 cm v ose s nižší roughness a mírně světlejším albedem, měkké okraje; na diamantovém vzoru ohlazené světlejší vršky hrotů; oranžový tečkovaný vzor odstranit.

5. **Špína kolem rámu poklopu, u madla a podél rámu mřížky nad kanálem chybí** – kde: list 06, pravá půlka, drážka kolem rámu poklopu (střed) a oranžové madlo (vpravo dole od středu); list 07, pravá půlka, rám mřížky a pruty (střed) – co je špatně: rám i drážka jsou čisté, hrany rámu se lesknou, pruty mřížky jsou rovnoměrně světlé po celé ploše, kolem madla není žádné ušmudlání; v referenci (list 07 vlevo, podlaha u mřížek vpředu) je rám tmavší než okolní deska – závažnost: musí se opravit – oprava: tmavý prach v drážce po obvodu rámu (1–2 cm), matnější oválné ušmudlání 10×15 cm kolem madla, na mřížce světlejší (ošlapané) hrany prutů uprostřed a tmavší nános u rámu.

6. **Špína je rozprostřená jako rovnoměrný šum místo koncentrace ve spárách** – kde: list 03, pravá půlka, celé plochy stěnových panelů; list 02, pravá půlka, panely vlevo od sloupu; list 05, pravá půlka, hladké desky – co je špatně: po celé ploše je jemný mikro-šum, který panely tónuje do plastové matnosti, zatímco záměr je čistá plocha a špína v hranách; energie masky je na špatném místě – závažnost: doporučeno – oprava: plošný šum stáhnout na 0–10 % a stejnou energii přesunout do hranových a rohových masek.

7. **Světlo je ploché a rytmicky monotónní** – kde: list 01 a 04, pravá půlka, strop po celé délce a podlaha pod ním – co je špatně: čtyři totožné pásy stejné intenzity, žádné kužely, tmavá místa ani akcenty; reference (list 01 vlevo) má oranžové akcenty u panelů, tmavé kapsy a jedno silné svítidlo u portálu – závažnost: doporučeno (souvisí s bodem 3) – oprava: střídat intenzity pásů, u portálu vynechat, doplnit slabé oranžové akcenty u přípojek a lišt.

8. **Nesoulad materiálů mezi díly** – kde: list 03, pravá půlka, lamely mřížky (střed) světle béžové a matné; list 08, pravá půlka, schodnice a stupně studeně šedé, nášlapné hrany čistě bílé; list 01, pravá půlka, chodba teplý grafit – co je špatně: tři díly kitu, tři různé teploty a odstíny kovu, lamely působí jako plast – závažnost: doporučeno – oprava: lamely ze stejného kovu jako rám, o tón tmavší; schodnice a stupně do teplého grafitu chodby; nášlapná hrana s lehkým ušpiněním, ne čistě bílá.

9. **Oděr madel je nečitelný a nepřirozeně umístěný** – kde: list 08, pravá půlka, spodní konce obou madel u dolních sloupků (levý a pravý okraj obrazu, střední výška) – co je špatně: světlé skvrny jsou jen na samých koncích u sloupků, zbytek laku je neporušený; ruce se drží podél celé délky, nejvíc na začátku a konci schodů, ne na koncovkách – závažnost: doporučeno – oprava: slabý matný pás oděru na horní straně madla po celé délce, zesílený v místech uchopení, koncovky nechat.

10. **Schodiště bez kontextu** – kde: list 08, pravá půlka, okolí schodů (levá a pravá stěna, celé pozadí) – co je špatně: černá prázdnota a flat tmavé stěny bez detailu; nejde posoudit, jak špína nášlapů navazuje na sokl a podlahu okolo – závažnost: doporučeno – oprava: příště snímat schodiště osazené do chodby z kitu, aby byla vidět návaznost na sokl a podlahu.

## Checklist z briefu

- Tvar prostoru z trupu: splněno (list 01, 04 vpravo – zalomené stěny, nízký strop, osmiúhelníkový průřez).
- Vrstvy a shlukování detailu: částečně – žebra a trubky pod stropem ano (list 01 vpravo, pravá strana), kabelové žlaby a skříňky se západkami nevidím, detail není shlukovaný (velké prázdné desky na obou stěnách).
- Účel předmětů: bez výplňových rekvizit, nic k výtce.
- Materiály: nesplněno – béžové lamely (list 03) a plastově rovnoměrné panely (list 02, 03); viz body 6 a 8.
- Decaly: mimo krok; co je vidět, je čitelné a nezrcadlené.
- Světlo: nesplněno – přepálené jádro a ploché rovnoměrné pásy (body 3 a 7).
- Geometrie: bez děr a průniků; jen prázdné okolí schodiště (bod 10).
</agent-message>
