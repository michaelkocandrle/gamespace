# Verdikt: FAIL

První dojem: Hladká bílá „vlaková“ trubka s nalepenými pruhy, plechově tenkými křídly a dvěma přerostlými ploutvemi – čistá, ale bez hmoty, mechaniky a světel, které dělají loď ze SC.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 6 | Rozvržení z výkresu sedí (list 1), ale ploutve jsou 2–3× větší než „malá ploutev“ z výkresu, křídla jsou plechy bez tloušťky, podvozkové patky a trysky jsou hrubé bloky. |
| Hierarchie a hustota detailu | 4 | Existuje jen velká vrstva (trup, kabina, gondoly, ploutve); střední vrstva (desky nad rámem, zapuštěné poklopy, mechanika, trubky) chybí a malá vrstva jsou dvě krabičky a bledé nápisy. |
| Materiály | 5 | Dva laky (lesklá bílá, satén tmavá) + oranžová; žádný holý kov, guma ani tmavá mechanika, žádná variace drsnosti, opotřebení jako měkké šmouhy uprostřed panelů místo hran. |
| Decaly | 3 | Nápis WAYFARER je na pravoboku zrcadlený, šablonové značky jsou tak bledé, že nejsou čitelné, nic není shlukované, nýty a čísla panelů prakticky chybí. |
| Světlo | 4 | Trysky za letu nesvítí vůbec a s přídavným tahem jen dvě tečky, poziční světla jsou přepálené barevné skvrny, v protisvětle ve vesmíru loď nemá žádné obrysové světlo. |
| Čitelnost (text, displeje, HUD) | 4 | Jméno čitelné jen z levoboku, z pravoboku zrcadlené; HALCYON FREIGHTWORKS na ploutvi a servisní značky na trupu jsou příliš malé a málo kontrastní. |
| Chyby geometrie | 4 | Zrcadlený decal, roztažená textura na křídle, zbraně jako holé trubky, podvozkové patky a trysky jako placeholdery, panelové čáry se kříží v nahodilých úhlech. |
| Soulad stylu mezi díly | 5 | Trup (bílý, tenké čáry) vs. křídla (holé tmavé plechy s jiným rastrem), záď (krémová) vs. bok (neutrálně bílý), trysky béžové – každý díl má jiný jazyk. |

Průměr: 4,4 (práh: hotová loď – všechny kategorie aspoň 7 a žádný bod „musí se opravit“)

## Rozdíly proti referenci

1. **Zrcadlený nápis WAYFARER na pravoboku** – kde: list 01 pravá půlka, spodní pravý snímek; list 14 pravá, střed; list 15 pravá, střed (nad HF-0417); list 16 pravá, horní pravý roh; list 18 pravá, střed; list 20 pravá, střed – co je špatně: písmena „ЯƎЯAꟻYAW“ jsou zrcadlená, zatímco HF-0417 na téže straně (listy 15, 20) čte správně; na levoboku (listy 05, 11) je vše správně – závažnost: musí se opravit – oprava: samostatné umístění nápisu pro každý bok (neklonovat zrcadlením), nebo na pravoboku otočit UV decalu; ověřit i menší nápisy.

2. **Trysky bez hloubky a bez záře** – kde: list 10 pravá, obě velké kruhové plochy vlevo a vpravo; list 01 pravá, spodní levý snímek; list 22 pravá, pravý malý snímek (přídavný tah); listy 04, 14, 19 (z boku/zezadu za letu) – co je špatně: tryska je béžová miska s malým tmavým kuželem uprostřed, žádné prstence, lopatky ani tmavý kov; za letu nesvítí vůbec, s přídavným tahem jen dvě slabé tečky bez plamene; reference (list 10 vlevo) má vrstvené prstence a modré emisivní jádro, list 22 vlevo plný oblak tahu – závažnost: musí se opravit – oprava: zapuštěná tryska (vnější prstenec, vnitřní lopatky/vany, tmavý kov), emisivní jádro se slabou září ve volnoběhu a plnou při tahu, VFX plamen při přídavném tahu.

3. **Ploutve násobně větší než na výkresu** – kde: list 02 pravá, obě strany snímku; list 08 pravá, střed; list 10 pravá, oba horní rohy; list 16 pravá, střed – co je špatně: na výkresu (list 01 vlevo, pohled z boku, štítek „ploutev“) je ploutev malý trojúhelník zhruba čtvrtinové výšky trupu; ve hře sahá k hřbetu trupu a nad něj, v pohledu zezadu trup přerůstá a v chase kameře zakrývá výhled – závažnost: musí se opravit – oprava: zmenšit na poměr z výkresu (tvar zachovat), zkontrolovat v pohledech zezadu a z chase kamery.

4. **Křídla jsou plechy bez tloušťky a bez nádrží** – kde: list 07 pravá, celý snímek (křídlo shora); list 04 pravá, spodní levý roh; list 08 pravá, spodní levý roh (tmavý proužek); list 11 pravá, vpravo; list 18 pravá, dole – co je špatně: křídlo je plochá deska bez viditelné náběžné hrany a tloušťky, shora jen dva velké obdélníky s černým lemem; výkres popisuje „křídlo s nádržemi vodíku“, žádné nádrže ani závěsy vidět nejsou – závažnost: musí se opravit – oprava: profil s reálnou tloušťkou, vyboulení nádrží, závěsník pro zbraň, panely s hloubkou, servisní poklopy shora.

5. **Zbraně S3 jako holé trubky** – kde: list 03 pravá, konec křídla (tenká tyč dopředu) a nad kabinou; list 04 pravá, spodní levý roh (černý válec s tyčkou) a tenká tyč nad trupem; list 07 pravá, spodní levý roh; list 18 pravá, tyč nad přídí – co je špatně: zbraň je hladký válec s tenkou hlavní, bez závěsu, těla, chladicích žeber a ústí; z několika úhlů trčí nad trupem jako drát – závažnost: musí se opravit – oprava: modelovat zbraň s tělem, závěsem na křídle, hlavní s ústím a žebry; velikost ověřit proti výkresu (S3).

6. **Detail trupu jsou čáry na hladkém povrchu** – kde: list 06 pravá, celý snímek; list 05 pravá, celý bok; list 20 pravá, příď a bok – co je špatně: panelové spáry jsou tenké černé čáry bez hloubky, kříží se v nahodilých úhlech (list 06 střed: diagonála z levého horního rohu přes svislice; list 20 vějíř čar k špici); reference (list 06 vlevo) má desky s viditelnou tloušťkou, zapuštěné plochy a vrstvené hrany – závažnost: musí se opravit – oprava: navrhnout rozvržení panelů podle konstrukce (velké desky nad rámy), spáry jako reálné mezery nebo mesh decaly s normálou/parallaxem, přidat střední vrstvu: zapuštěné servisní poklopy, vystouplé desky, trubky na hřbetním krytu.

7. **Přepálená poziční světla** – kde: list 16 pravá, střed dole (zelená skvrna na křídle a ve vzduchu u gondoly); list 15 pravá, vlevo (zelený svit na křídle); list 07 pravá, vpravo (červený obdélník na čele gondoly + červený flek na křídle za denního světla) – co je špatně: světla jsou velké rozmazané barevné skvrny, ne malé lampy s čočkou; ve dne září jako reflektor – závažnost: musí se opravit – oprava: snížit intenzitu a dosah, malý bodový zdroj s čočkou, den/noc adaptace intenzity.

8. **Podvozek jako placeholder** – kde: list 09 pravá, celý snímek (přední i zadní noha) – co je špatně: patka je velký černý kvádr se třemi lištami, noha je bílá krabice s jedním kolečkem, žádná viditelná šachta ani dveře v břiše, na výkresu jsou nohy malé s malými patkami – závažnost: musí se opravit – oprava: menší kloubová patka, viditelná hydraulika a nůžky na vzpěře, šachta s dveřmi, tmavý kov a guma.

9. **Záď: plochá přepážka bez rampy, mechaniky a světel** – kde: list 10 pravá, střed – co je špatně: rampa je krémová deska s dvěma štítky, drobnou šipkou a miniaturními výstražnými pruhy v rozích; žádný rám, panty, písty, těsnění ani zadní poziční světla (reference list 10 vlevo má červená zadní světla a vrstvený trup) – závažnost: musí se opravit – oprava: rampu zapustit do rámu s panty a písty, výstražný pruh po celém obvodu, zadní poziční/strobe světla, panely přepážky s hloubkou.

10. **Roztažená textura na křídle** – kde: list 07 pravá, střed (krémová plocha se svislými šmouhami) – co je špatně: textura je podél křídla roztažená do pruhů, působí měkce a zvlněně – závažnost: doporučeno – oprava: opravit UV a texel density křídla.

11. **Šablonové nápisy nečitelné a rozházené** – kde: list 06 pravá, vlevo dole („B07“, šrafovaný obdélník, trojúhelník, šipky) a vpravo dole; list 16 pravá, ploutev (HALCYON FREIGHTWORKS) – co je špatně: šedá na bílé s minimálním kontrastem, malé, rozprostřené náhodně, ne u poklopů a portů; reference (list 06 vlevo) má „01-L ANTENNA“ tmavě, velké, u příslušného prvku – závažnost: doporučeno – oprava: tmavá šablonová barva, shlukovat k poklopům/portům/nádržím, čísla panelů, pár nýtů/šroubů u desek.

12. **Materiály bez variace a bez hranového opotřebení** – kde: list 05 pravá, celý bok; list 15 pravá, celý trup; list 20 pravá; list 06 pravá, horní střed (měkká šedá šmouha uprostřed panelu) – co je špatně: bílá je jednotně lesklý plast, tmavý hřbet jednotný satén, špína je v měkkých skvrnách uprostřed ploch místo na hranách; žádný holý kov na špici a zkoseních, žádná guma na těsnění skla – závažnost: doporučeno – oprava: maska hranového opotřebení, variace drsnosti v panelech, holý kov na špici/hranách, gumové těsnění kolem skla, tmavá mechanika v zapuštěných místech.

13. **Čelo gondoly je plochý kryt s lampou** – kde: list 07 pravá, vpravo; list 20 pravá, vlevo; list 03 pravá, vpravo – co je špatně: čelo gondoly nemá sání ani strukturu, jen disk s poziční lampou; reference (list 07 vlevo) má vrstvený plášť se spárami a nýty – závažnost: doporučeno – oprava: sání s lamelami nebo krytem s hloubkou, spáry pláště, lampu do zapuštěného pouzdra.

14. **V protisvětle loď nemá obrysová světla** – kde: list 21 pravá, oba malé snímky – co je špatně: svítí jen interiér kabiny, trup a křídla jsou černá hmota; reference (list 21 vlevo) má bílá obrysová světla na koncích křídel a záři motorů – závažnost: doporučeno – oprava: bílá obrysová světla na koncích křídel a ploutví, strobe, spolu s bodem 2.

15. **Bílý pás pod spodní hranou trupu vypadá jako artefakt** – kde: list 06 pravá, střed (zrnitý světlý pruh se šmouhou); list 09 pravá, nahoře; list 11 pravá, spodní hrana trupu – co je špatně: pruh nemá tvar lampy ani lišty, ve dne je to jen bílá čára s šumem – závažnost: doporučeno – oprava: buď reálná lišta světla s čočkou v drážce, nebo pás odstranit; prověřit šum odrazu/TSR.

16. **Oranžově svítící šachta v gondole působí jako pec** – kde: list 08 pravá, střed dole; list 16 pravá, vpravo dole – co je špatně: otevřená šachta s lamelami září oranžově i za dne, bez tmavého kovového rámu – závažnost: doporučeno – oprava: ztlumit emisi, lamely jako tmavý kov s jemným žárem, rámovat mřížkou.

17. **Trup čte jako vagon** – kde: list 05 pravá; list 11 pravá; list 19 pravá; list 20 pravá – co je špatně: pravidelně rozmístěné příčné prstence po celé délce bez variace dávají dojem vlakového vozu – závažnost: doporučeno – oprava: rozbít rytmus (různé délky segmentů, jeden velký boční poklop, zapuštěná servisní zóna), souvisí s bodem 6.

18. **Dva různé odstíny bílé** – kde: list 10 pravá, zadní přepážka (krémová) a mísy trysek (béžové) vs. list 20 pravá, bok (neutrálně bílý); list 07 pravá, křídlo (krémová + světle šedá) – co je špatně: primární lak nemá jednotný tón, ačkoli má být jedna teplá lomená bílá – závažnost: doporučeno – oprava: jeden materiál primárního laku pro trup, záď, křídla i gondoly.

19. **Výchozí chase kamera příliš blízko** – kde: list 02 pravá, celý snímek – co je špatně: loď zabírá spodní polovinu obrazu a ploutve zakrývají okraje, hráč lodi vidí jen hřbet; reference (list 02 vlevo) ukazuje celou loď v krajině – závažnost: doporučeno – oprava: zvětšit odstup a výšku výchozí chase kamery (týká se prezentace lodi, ne meshe).

## Checklist z briefu
- Rovné panely, čisté zkosené hrany: částečně – fasety a zkosení na přídi ano, ale roztažená textura na křídle (bod 10) a měkké šmouhy na trupu (bod 12).
- Vrstvený tvar s tloušťkou, střední vrstva: ne (body 4, 6, 9).
- Detail jako tvar nebo mesh decal s hloubkou: ne, čáry na hladkém povrchu (bod 6).
- Materiály (dva laky, holý kov, guma, tmavá mechanika, drsnost, opotřebení na hranách): jen dva laky a oranžová (bod 12).
- Decaly (čísla, šablony, pruhy, šipky, nýty; shlukované, čitelné, nezrcadlené): jméno a ID ano, zbytek bledý a rozházený, jméno na pravoboku zrcadlené (body 1, 11).
- Světla (poziční, šachty, emisivní prvky, nic přepáleného): poziční přepálená, trysky tmavé, obrys v protisvětle žádný (body 2, 7, 14, 16).
- Silueta podle výkresu, nic netrčí šikmo, nic nevisí: rozvržení ano, ploutve, křídla a podvozek ne (body 3, 4, 8); zbraně trčí jako dráty (bod 5).
