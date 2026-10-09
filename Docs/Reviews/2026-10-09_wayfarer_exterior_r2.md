# Recenze: exteriér Wayfareru, kolo r2 (9. 10. 2026)

Zadání: po dosažení úrovně SC v kokpitu doladit exteriér na stejnou úroveň. Kritik má ohodnotit exteriér proti SC
a vypsat systémová zlepšení s největším dopadem. Silueta je daná schváleným výkresem a nemění se. Díly jsou nové,
takže se nežádá opotřebení ani špína. Způsob hodnocení: `sc-quality-interior` kap. 1, 4 a 5 (vrstvy detailu, tón
po panelech, logické mesh decaly, světelné linky) použitý na exteriér.

- Zadání: [2026-10-09_wayfarer_exterior_r2.json](2026-10-09_wayfarer_exterior_r2.json), listy a brief:
  [2026-10-09_wayfarer_exterior_r2/](2026-10-09_wayfarer_exterior_r2/brief.md) (22 listů), snímky
  `shots:20261009_121513_wayfarer_exterior_review`.
- Reference: autorův vlastní záznam RSI Aurora v hangáru (`sc_own_04`); list 1 = schválený výkres.
- Práh: hotová loď (`"gate": "ship"`).

# Verdikt: FAIL

První dojem: Čistá, čitelná pracovní loď s věrnou siluetou a konečně správnými nápisy. Povrch ale působí jako
jednolitý bílý plech posetý stejnými nýty, s nakreslenými poklopy a bílými svítícími čarami. Podvozek, trysky
a křídla jsou pořád o třídu níž než SC.

| Kategorie | Skóre 1–10 | Proč (jedna věta) |
|---|---|---|
| Silueta a tvar | 6 | Celek přesně odpovídá výkresu (list 1), ale díly podvozku (list 9), zbraně (listy 7, 11) a křídla (list 7) jsou jednoduché bloky a válce bez konstrukce. |
| Hierarchie a hustota detailu | 6 | Velká vrstva a desky nad rámem už existují (listy 5, 20), ale střední vrstvu tvoří hlavně nakreslené obrysy poklopů a pravidelné řady nýtů. Hřbet je řada stejných černých obdélníků (list 8). |
| Materiály | 5 | Všechny bílé panely mají stejný tón i drsnost. Chybí holý kov, guma a satén vs. lesk; na ploutvích a křídle jsou šmouhy, které se k nové lodi nehodí (listy 7, 16). |
| Decaly | 6 | Nápisy jsou nově čitelné a nezrcadlené a čísla panelů (N15, U14, L14) leží logicky. Poklopy jsou ale jen tenké obrysy se dvěma černými obdélníky (list 6) a malé šablonové značky nejsou shlukované. |
| Světlo | 5 | Bílé světelné linky ve dne čtou jako přepálené čáry (list 6 klikatá linka, list 7 šmouhy po křídle) a červené poziční světlo zalévá křídlo (list 7). Za soumraku a v protisvětle loď nemá světelný obrys (listy 13, 21). Trysky jsou plochý oranžový kruh (list 10). |
| Čitelnost (text, displeje, HUD) | 7 | WAYFARER, HF-0417, NO STEP a RAMP – STAND CLEAR jsou čitelné z obou boků (listy 5, 10, 20). |
| Chyby geometrie | 6 | Podvozek vypadá jako placeholder (šedá krabice + černá deska, list 9). Na přídi je natočená krabička „Q“ pod černým panelem (list 6, dole uprostřed). Přistálá loď leží trupem v terénu (list 11). |
| Soulad stylu mezi díly | 6 | Trup (nýtovaný bílý plech), gondoly (hladké s oranžovými pásy), černý ostrý nos a ploutve se šmouhami mluví každý trochu jiným jazykem. Podvozek a trysky do něj nezapadají vůbec. |

Průměr: 5,9 (práh: hotová loď – všechny kategorie aspoň 7 a žádný bod „musí se opravit“)

## Rozdíly proti referenci

1. **Jednolitý lak bez tónu po panelech** – kde: listy 5, 6, 15, 20, všechny bílé plochy trupu – co je špatně: každý
   panel má stejný odstín i drsnost, takže trup působí jako jeden plech. Na Auroře (vlevo) se sousední panely liší
   tónem i leskem. – závažnost: musí se opravit – oprava: stejný systém jako v kokpitu, tedy tón po panelech
   zapečený do cavity. Lak ±5 %, 12–15 % panelů v sekundárním teplém šedém laku (~#B8B2A6), 6–8 % gunmetal,
   drsnost po panelech 0,25–0,45 (lesklé velké plochy, satén na svislých).
2. **Nýty jako tapeta, poklopy jako kresba** – kde: list 6 (celý pravý díl), listy 5, 20 – co je špatně: rovnoměrné
   řady nýtů po ~25 cm podél všech hran (letadlo ze 40. let). Poklopy jsou jen tenké obrysové čáry se dvěma černými
   obdélníky, bez hloubky. – závažnost: musí se opravit – oprava: nýty ubrat o ~70 %, nechat jen na konstrukčních
   spárách a v rozích (shluky 3–4 šroubů 15–20 mm). Poklopy udělat jako skutečné zapuštění 8–12 mm se zkosením
   15 mm a 4 šrouby, nebo jako mesh decal s normálem a AO z knihovny decalů. Číslo panelu nechat vlevo nahoře
   u každého poklopu.
3. **Hlavní podvozek je placeholder** – kde: list 9 vpravo – co je špatně: šedý kvádr s oranžovým pruhem, lesklý
   válec a černá deska s lištami. Na Auroře (vlevo) je kloubová noha z tmavých mechanických dílů. – závažnost:
   musí se opravit – oprava: gunmetal noha ze dvou ramen s torzním kloubem, hydraulický válec Ø 80 mm s lesklou
   pístnicí, patka se zkosenými hranami a gumovou podrážkou 40 mm, šachta s dvířky a osvětleným vnitřkem.
4. **Křídlo je plochá deska** – kde: list 7 vpravo – co je špatně: horní plocha jsou dva obdélníky s NO STEP,
   bez náběžné hrany, klapek, závěsů a poklopů. Ve stínu jsou šmouhy. – závažnost: musí se opravit – oprava:
   náběžná lišta 0,12 m v saténové gunmetal, klapka nebo křidélko 0,6 m hluboké se spárou 20 mm a 2 kryty
   aktuátorů, 2–3 zapuštěné servisní poklopy, rohové značky ohraničující zónu NO STEP. Šmouhy ze textury
   křídla a ploutví (list 16) odstranit.
5. **Světlo lodi** – kde: list 6 (bílá klikatá linka), list 7 (bílé čáry po křídle a červená skvrna), listy 13,
   14, 21 – co je špatně: světelné linky ve dne přepalují do bílé a jejich průběh nesleduje konstrukci. Poziční
   světlo nemá těleso a zalévá křídlo. Za soumraku a v protisvětle loď nemá obrys. – závažnost: musí se opravit –
   oprava: linky 15–20 mm jen podél souvislých konstrukčních hran, emise ve dne ~¼ dnešní hodnoty, s barvou
   (teplá bílá nebo azurová), ne čistá bílá. Poziční světla jako čočky 6–8 cm v pouzdře na koncích křídel
   (červená/zelená), bílý stroboskop na ploutvích 1 Hz, přisvětlení plochy pod světlem nejvýš na 1 m. Pár
   tlumených obrysových linek na hřbetu a v rámu kabiny pro protisvětlo.
6. **Trysky jako oranžový ciferník** – kde: list 10 (obě gondoly), list 2, list 22 vpravo – co je špatně: plochý
   oranžový kruh s kuželem a paprsky svítí stejně i bez tahu. S přídavným tahem není vidět plamen. – závažnost:
   musí se opravit – oprava: vrstvená tryska (vnější lem z holého kovu, lamely, tmavé hrdlo). Emise jen v jádru do
   30 % poloměru a podle tahu (volnoběh 0,2, plný 1,0, přídavný tah + plamen nebo kužel výtoku 2–4 m).
7. **Opakující se hřbet a chybějící technické díly** – kde: list 8 (hřbet), list 10 (střecha zádi) – co je špatně:
   řada stejných černých obdélníků v pravidelném rytmu („vagon“), bez antén, senzorů, trubek a madel. – závažnost:
   doporučeno – oprava: tři délky modulů (0,6 / 1,2 / 1,8 m) střídat nepravidelně, přidat 2 trubkové vedení podél
   hřbetu na sponách, anténu a senzorovou kopuli na přední části hřbetu a madla u servisních poklopů.
8. **Chybějící materiálové zóny** – kde: listy 7, 9, 10, 11 – co je špatně: kromě bílé, černé a oranžové není
   nic. Chybí holý kov (závěsy, písty, ústí zbraní, lemy trysek), guma (těsnění rampy a poklopů) a tmavá mechanika.
   – závažnost: musí se opravit – oprava: kovová zóna (metallic 1, drsnost 0,3–0,4) na mechanice, gumové těsnění
   10 mm kolem rampy a poklopů, saténová gunmetal na aktuátorech.
9. **Zbraně jako trubky** – kde: list 7 (černá trubka podél křídla), list 11 – co je špatně: válec s prstencem, bez
   pláště, chlazení a závěsu. – závažnost: doporučeno – oprava: hranatý plášť, chladicí žebra, úsťová brzda,
   závěs se 4 šrouby na křídle.
10. **Šachta gondoly ve dne jako pec** – kde: listy 8, 16 – co je špatně: otevřená šachta svítí oranžově i za
    denního světla. – závažnost: doporučeno – oprava: emise šachty ve dne na ~30 %, studenější teplota barvy
    a víc tmavé mechaniky uvnitř.
11. **Malé šablonové značky nejsou shlukované** – kde: listy 5, 6, 20 – co je špatně: značky ACCESS, trojúhelníky
    a čísla jsou rozptýlené po jedné. Na Auroře tvoří shluky (výstražný štítek + šipka + kód) u funkčních míst.
    – závažnost: doporučeno – oprava: shluky 3–5 značek u každého poklopu, sání a madla; výstražné pruhy u sání
    a hran rampy.
12. **Natočená krabička na přídi** – kde: list 6, dole uprostřed („Q“ pod černým panelem) – co je špatně: díl je
    pootočený mimo rovinu panelu a vypadá uvolněný. – závažnost: doporučeno – oprava: srovnat do roviny panelu,
    nebo ho odstranit.
13. **Přistálá loď v terénu** – kde: list 11 – co je špatně: trup leží v svahu a podvozek není vidět. Jde o herní
    logiku přistání, ne o model. – závažnost: doporučeno – oprava: mimo model exteriéru.

Checklist: povrch rovný se zkosenými hranami ano. Vrstvený tvar zčásti (desky nad rámem ano, mechanika a trubky
ne). Detail jako tvar nebo mesh decal zčásti (poklopy jsou kresba). Materiály ne (chybí sekundární lak, holý kov,
guma a variace drsnosti). Decaly čitelné a nezrcadlené ano, shlukované ne. Světla ne (linky přepálené, chybí
obrys a pouzdra). Silueta podle výkresu ano.
