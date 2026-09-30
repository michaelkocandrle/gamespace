<!-- kolo 3 (30. 9. 2026): zadání visual-critic v3 (bez „nejméně 5 rozdílů“, všechny relevantní nálezy podle závažnosti), bez checklistu; Explore + Fable, jen brief a listy -->
# Verdikt: FAIL

První dojem: Z dálky (list 04, pohled shora) je to rozpoznatelně loď z rodiny SC, ale při každém přiblížení se rozpadne na sádrově mramorovaný trup bez panelů, černý nos a zadní motory, které svítí texturou trupu místo tahu.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 5 | Půdorys (list 04 vlevo) sedí s referencí (dvě gondoly, šípová křídla, dvojité SOP), ale bokorys (list 02) je plošší a delší než reference a záď (list 03) tvoří jiná loď: dva sudy plus blok se čtyřmi otvory. |
| Hierarchie a hustota detailu | 3 | Chybí střední a malá úroveň detailu; spáry panelů čtou jako náhodné vlásečnice v šumu, žádné nýty, průduchy, poklopy ani vedení, které reference (list 02 vlevo) má po celém trupu. |
| Materiály | 3 | Trup je jednotný šedobílý „popraskaný“ povrch místo hladkého krémového laku, nos je plochá čerň bez odlesku a vnitřek trysek nese albedo trupu. |
| Decaly | 2 | Na výsledku není jediná značka, číslo, stencil ani výstražný pruh; z akcentů zůstal jeden boční oranžový pruh a kroužky na gondolách. |
| Světlo | 4 | Na listech 02 a 05 vpravo je stínová strana lodi plochá čerň bez ambientu, odrazu nebo obrysového světla; loď se změní na vystřižený obrys. |
| Čitelnost (text, displeje, HUD) | 3 | Na lodi není žádný čitelný text; do snímků je navíc vypálený HUD „FREE LOOK“ (listy 01, 03, 04, 05), který v assetovém záběru nemá co dělat. |
| Chyby geometrie | 3 | Trysky se svítící texturou trupu, nedefinovaný zadní blok s otvory, výstupky pod trupem za letu a papírově tenké SOP. |
| Soulad stylu mezi díly | 4 | Trup, křídla a gondoly drží jednu (byť špatnou) řeč, ale záď s krémově „popraskanými“ svítícími disky vypadá jako díl z jiného assetu. |

## Rozdíly proti referenci

1. **Trysky svítí texturou trupu** – kde: list 03 pravá půlka, dva velké kruhy uprostřed záběru (vlevo a vpravo od středu); list 05 pravá půlka, oba disky – co je špatně: vnitřek trysek je jasně krémový s tmavým popraskaným vzorem, tj. albedo trupu nasazené jako emisivní plocha; reference (list 03 levá půlka, zadní konec horní gondoly) má tmavý kovový kužel trysky s oranžovým prstencem a modro-oranžovou září uvnitř – závažnost: musí se opravit – oprava: samostatný materiál motoru: tmavý kov kužele, emisivní oranžový prstenec + vnitřní žhavení, jemný bloom výfuku; texturu trupu z UV trysek úplně odstranit.
2. **Zadní střed je nedefinovaný blok s otvory** – kde: list 03 pravá půlka, mezi oběma tryskami (střed záběru) a tmavá hmota visící pod ním – co je špatně: tmavý hranatý blok se čtyřmi kruhovými otvory a beztvará hmota pod ním čtou jako placeholder; reference má mezi gondolami hladký hřbet trupu a pod ním rampu/podvozek s tvarem – závažnost: musí se opravit – oprava: rozhodnout, co uprostřed zádi je (jeden centrální motor, nákladová vrata nebo hladký hřbet), otvory zrušit, spodní hmotu buď ubrat, nebo jí dát tvar podvozkové šachty.
3. **Trup je mramorovaný „sádrový“ povrch, ne lak s panely** – kde: list 01 pravá půlka, celý trup lodi vpravo dole; list 04 pravá půlka, levý rámeček (pohled shora), celá horní plocha; list 05 pravá půlka, levý rámeček, trup za kabinou – co je špatně: povrch je jednolitá šedobílá skvrnitost jako popraskaná omítka, bez hladkých ploch, spáry panelů se ztrácejí v šumu; reference (list 02 levá půlka) má hladký krémový lak, ostré spáry, nýty a špínu jen ve stékancích od spár – závažnost: musí se opravit – oprava: nová sada textur: základní krémový lak (rovnoměrná barva, střední roughness), spáry panelů normálovou mapou/decaly, nýty, špína jen maskou na hranách a pod spárami; skvrnitý albedo šum odstranit.
4. **Nos bez materiálu** – kde: list 05 pravá půlka, levý rámeček, špička lodi (levý okraj lodi); list 01 pravá půlka, špička – co je špatně: kužel nosu je plochá čerň bez odlesku, tvar není čitelný; reference (list 02 levá půlka, pravý konec) má tmavošedý kov s odleskem, světlejší čepičku a dělicí prstenec – závažnost: musí se opravit – oprava: kovový materiál s viditelnou roughness/spekulárem, světlejší tón, prstencová spára k trupu.
5. **Stínová strana lodi je plochá čerň** – kde: list 02 pravá půlka, celá loď (slunce v pravém horním rohu za lodí); list 05 pravá půlka, pravý rámeček, celá záď kromě trysek – co je špatně: bez ambientu, odrazu ani obrysového světla nejde posoudit tvar ani materiál; na referenci má i zastíněná plocha čitelné panely – závažnost: musí se opravit – oprava: nasnímat znovu s klíčovým světlem na lodi; zároveň doplnit ambient/odrazy (sky light, reflection capture), aby zastíněná strana nezmizela.
6. **Žádné decaly ani značení** – kde: všechny listy, pravé půlky; nejvíc vidět list 04 pravá půlka, levý rámeček (celý hřbet bez jediné značky) – co je špatně: reference (list 02 levá půlka) má výstražné šrafování u nosu, čísla na SOP, drobné stencily u poklopů a oranžové pruhy s ukončením; výsledek má jen jeden boční pruh a kroužky na gondolách – závažnost: musí se opravit – oprava: decalová vrstva: registrace na SOP a boku trupu, výstražné šipky u sání a podvozku, stencily u poklopů, logo výrobce, oranžové akcenty i na náběžných hranách křídel a SOP.
7. **Výstupky pod trupem za letu** – kde: list 02 pravá půlka, pod středem trupu tři tmavé pahýly; list 03 pravá půlka, tmavá hmota pod středem zádi – co je špatně: vypadá jako vysunutý podvozek nebo nedokončené díly; loď letí ve vesmíru a reference ukazuje čistou břišní linii – závažnost: musí se opravit – oprava: podvozek za letu zatáhnout; pokud jde o jiné díly, dát jim tvar a účel, jinak odstranit.
8. **Sání motorů bez záře** – kde: list 04 pravá půlka, levý rámeček, přední konce obou gondol – co je špatně: jen oranžové kroužky, žádné žhavé sání; reference (list 01 levá půlka, čela gondol) má červenooranžově svítící prstenec sání – závažnost: doporučeno – oprava: emisivní prstenec sání s bloomem, tmavší vnitřek.
9. **Snímky příliš malé a s HUDem** – kde: list 01 pravá půlka, loď zabírá asi pětinu šířky; list 04 pravá půlka, oba rámečky jsou miniatury; HUD „FREE LOOK“ na listech 01, 03 (oříznutý nahoře), 04 a 05 – co je špatně: „střední vzdálenost“ a „zblízka“ neodpovídají velikosti lodi v záběru, detail nejde posoudit, HUD ruší – závažnost: doporučeno – oprava: nasnímat s lodí na 50–70 % šířky záběru, HUD vypnout.
10. **Spodek nečitelný** – kde: list 04 pravá půlka, pravý rámeček – co je špatně: loď je zespodu tmavá a splývá s plynovým obrem a prstenci za ní; nelze ověřit podvozkové šachty ani břišní panely – závažnost: doporučeno – oprava: nasnímat zespodu s osvětlením zdola a neutrálním pozadím.
11. **Papírové SOP** – kde: list 03 pravá půlka, obě svislé plochy nad tryskami – co je špatně: plochy bez tloušťky s jasně svítící hranou, bez kořenového přechodu; reference (list 03 levá půlka) má tloušťku, panely a kořen – závažnost: doporučeno – oprava: dát tloušťku, kořenový přechod a spáry.

## Checklist z briefu

Brief žádný checklist neobsahuje, hodnotím proto proti jeho popisu stylu:

- **Krémový lak** – nesplněno: povrch je šedobílá skvrnitost, ne lak (bod 3).
- **Oranžové akcenty** – částečně: jeden boční pruh a kroužky na gondolách; chybí náběžné hrany, SOP, ukončení pruhů a výstražné prvky (bod 6).
- **Čistý styl Origin** – nesplněno: výsledek je špinavější a hrubší než reference, bez hladkých ploch a čistých spár (body 3, 6).
- **Úroveň zpracování SC** – nesplněno: trysky, zadní blok a chybějící detail (body 1, 2, 3).
