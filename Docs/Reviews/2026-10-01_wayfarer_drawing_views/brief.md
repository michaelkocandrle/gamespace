# Brief: technické výkresy E-03 až E-07 – Wayfarer, exteriér (ostatní pohledy a detaily)

Hodnotíš **technické výkresy**, ne herní vzhled. Autor schválil styl vzorového listu E-01 (pravobok) a zadal
zbytek exteriéru lodi Wayfarer (dossier lodi, bod 3) ve stejném stylu. Výkresy kreslí skript z týchž dat, ze kterých
se loď staví; každá postavená i navržená část nese ID, které je v datech. Podle schválených výkresů se pak postaví
exteriérový kit.

## Co mají listy podle zadání autora obsahovat

- Šest pohledů: pravobok (E-01, už schválený styl), **levobok (E-06), shora (E-03), zespodu (E-04), zezadu
  a zepředu (E-05)**; v každém pohledu materiálové zóny se šrafami, desky podle konceptu povrchu B + C, funkční
  prvky s ID (RCS, trysky, poklopy komponent, plnicí hrdlo, senzory, antény, držáky zbraní a raket, podvozek,
  rampa s písty a rámem), světla, decaly s ID z knihovny a kontrolou orientace na obou bocích, kóty.
- **Detaily 1:10–1:20 (E-07):** příď s kabinou, gondola s tryskou, rampa, hlavní podvozek, koncový držák zbraně.
- Seznam dílů exteriérového kitu a tabulky všech prvků jsou na listu E-02 (není předmětem tohoto kola).
- Stavy prvků: postavené (černě), návrh (modře, +), změna postaveného (modře, Δ), odstranit (červeně, ×).
- Konvence pohledů (třetí úhel): shora příď vpravo, levobok nahoře; zespodu příď vpravo, pravobok nahoře;
  zezadu pravobok vpravo; zepředu levobok vpravo; levobok příď vlevo.
- Koncept B + C: vystouplé desky na tmavším gunmetal rámu (žebra, podélníky), zapuštěné šachty s mřížkou, těžké
  pláty se šrouby, robustní bloky RCS, gunmetal spodek. Specifikace: 8 manévrovacích trysek.

## Listy (otevři každý obrázek nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace\d47f202a-2a8c-4fd6-a4c8-e2f11e3e4534\scratchpad\views_review\`:
- `00`–`05` E-03 shora (celek, výřezy, poznámky)
- `06`–`09` E-04 zespodu
- `10`–`14` E-05 zezadu (1:20) a zepředu (1:30)
- `15`–`20` E-06 levobok (pohled A desky a materiály, pohled B prvky, světla, decaly; tabulka kontroly nápisů)
- `21`–`26` E-07 detaily B příď s kabinou, C zadní stěna s rampou, D hlavní podvozek, E držák zbraně, F gondola shora
Celé listy v plném rozlišení: `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_E0{3..7}_*.png`.
Pro srovnání stylu: `Wayfarer_E01_starboard.png` ve stejné složce.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – data stavby (pole `id`; x od zádi, y k levoboku, z od paluby, metry)
- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Wayfarer_exterior_design.json` – návrh (nové prvky, změny, materiály, kit)
- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – obrysy (exterior: side, top, front)
- `C:\gamespace\gamespace\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_E0{3..7}_*.json` – ID nakreslená a popsaná v každém pohledu
Udělej namátkovou kontrolu aspoň deseti prvků z různých listů (ID, poloha proti souřadnicím, stav, strana).

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost: písmo, čáry, šrafy, překryvy, odkazové čáry (monitor se zoomem).
2. Úplnost proti zadání (body výše).
3. Soulad s daty: ID, polohy, strany (zrcadlení), stavy.
4. Konvence technického výkresu: orientace pohledů, razítko, měřítko, kóty, skryté hrany, odkazy, legenda.
5. Návrh povrchu: dává rozvržení desek, rámu a materiálů v ostatních pohledech smysl a navazuje na E-01?
6. Srozumitelnost pro autora, který není herní vývojář.

Práh PASS (dílčí krok): průměr aspoň 6,5, žádná kategorie pod 6, žádná výtka „musí se opravit".

## Formát odpovědi (česky, Markdown)

```
# Verdikt: PASS | FAIL
První dojem: <jedna věta>
| Kategorie | Skóre | Proč |
...
Průměr: <x,x>
## Musí se opravit
1. <list, výřez, oblast> – <co> – <jak to má být>
## Mělo by se opravit
## Drobnosti
## Namátková kontrola dat (prvek, výkres, data, sedí/nesedí)
```
Buď konkrétní: každá výtka říká, na kterém výřezu a kde přesně.
