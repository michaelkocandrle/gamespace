# Brief: vzorový technický výkres E-01 – Wayfarer, exteriér pravobok

Hodnotíš **technický výkres**, ne herní vzhled. Je to vzorový list, podle kterého autor schválí styl všech
dalších výkresů exteriéru a interiéru lodi Wayfarer (dossier lodi, bod 3). Výkres kreslí skript z týchž dat,
ze kterých se loď staví; každá postavená i navržená část nese ID, které je v datech.

## Co má list podle zadání autora obsahovat

- Exteriér, pravý bok (pravobok), v měřítku: desky trupu podle vybraného konceptu povrchu (koncept B + C),
  materiálové zóny se šrafami a legendou, funkční prvky s ID, světla (typ, barva, intenzita), decaly s ID
  z knihovny a kontrolou orientace na obou bocích.
- Profesionální styl: rámeček, popisové pole (razítko), měřítko, legenda, kóty, odkazové čáry s ID; export do
  obrázku ve vysokém rozlišení (A0, 1:30, detail 1:20).
- Stavy prvků odlišené: postavené (černě), návrh (modře, +), změna postaveného (modře, Δ, stará poloha
  čárkovaně červeně), odstranit (červeně, ×). Nepostavené prvky jsou „návrh" a později se staví z těchže dat.
- Koncept B (vrstvený utilitární): vystouplé desky přišroubované na tmavší konstrukční rám, žebra rámu mezi
  deskami, zapuštěné servisní šachty s mřížkami. Koncept C (průmyslový tahoun): těžké pláty s řadami šroubů,
  robustní bloky RCS, gunmetal spodek trupu, odhalená hydraulika. Nepřebírá se nic mimo výkres (antény a
  kupole na hřbetu z konceptu D, překlep IF-0417 z konceptu A).
- Specifikace lodi: 8 manévrovacích trysek TR1 (4 kolem přídě, 2 na každé gondole).

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace\d47f202a-2a8c-4fd6-a4c8-e2f11e3e4534\scratchpad\e01_review\`:
`00_celkovy_pohled.png` (celý list A0 zmenšený) a výřezy v plném rozlišení 200 dpi: `01`–`03` pohled A
(desky a materiály), `04`–`06` pohled B (funkční prvky, světla, decaly), `07` detail A (gondola 1:20),
`08` legenda, řez R1 a koncept, `09`–`10` tabulky, `11` změny, kontrola dat a popisové pole.
Celý list: `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_E01_starboard.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Wayfarer_exterior_design.json` – návrh (nové prvky, změny, odstranění, materiály, kit)
- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – data stavby (pole `id`, souřadnice x od zádi, z od paluby, metry)
- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Wayfarer_setup.json` – velké decaly (Unreal cm, +Y pravobok)
- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_E01_starboard.json` – ID nakreslená a popsaná v pohledech a tabulkách
Udělej namátkovou kontrolu aspoň deseti prvků (ID, poloha na výkresu proti souřadnicím v datech, stav).

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost: velikost a hierarchie písma, tloušťky čar, šrafy, překryvy, odkazové čáry (při tisku A0 i na monitoru se zoomem).
2. Úplnost proti zadání listu (body výše).
3. Soulad s daty: ID, polohy, stavy, počty (RCS), tabulky.
4. Konvence technického výkresu: rámeček, razítko, měřítko, kóty, skryté hrany, legenda, odkazy na detail.
5. Návrh povrchu: odpovídá rozvržení desek, rámu a materiálů konceptu B + C a dává konstrukčně smysl?
6. Srozumitelnost pro autora, který není herní vývojář: pozná z listu, co se postaví, co se mění a proč?

Práh PASS (dílčí krok): průměr aspoň 6,5, žádná kategorie pod 6, žádná výtka „musí se opravit".

## Formát odpovědi (česky, Markdown)

```
# Verdikt: PASS | FAIL
První dojem: <jedna věta>
| Kategorie | Skóre | Proč |
...
Průměr: <x,x>
## Musí se opravit
1. <list, oblast> – <co> – <jak to má být>
## Mělo by se opravit
## Drobnosti
## Namátková kontrola dat (prvek, výkres, data, sedí/nesedí)
```
Buď konkrétní: každá výtka říká, na kterém výřezu a kde přesně.
