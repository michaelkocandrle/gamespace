# Recenze: obsah nastavení podle SC 4.10, 4. 10. 2026

Listy: `Docs/Reviews/2026-10-04_settings_content/` (brief; listy jen lokálně, obsahují snímky z autorova záznamu SC).
Práh `step`. Styl menu schválen v `2026-10-04_menu_sc.md`. Snímky kola 1 `shots:20261004_105941_menu_sc`, ověřovacího
kola `shots:20261004_110608_menu_sc`, ze zabalené hry `shots:20261004_111323_menu_sc`.

## Kolo 1 – PASS, průměr 7,5

Skóre: silueta 8, hierarchie 7, materiály 8, decaly 7, světlo 8, čitelnost 7, geometrie 8, styl 7.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Nové řádky grafiky nejsou na listu | doporučeno | opraveno: snímek grafiky posunuté na konec (`space.Menu 2 1 1`) |
| 2 | Šipky nereagují na kraj seznamu | doporučeno | opraveno: v GAME SETTINGS má SC ztlumenou šipku na kraji (Yes = pravá, No = levá). Moje změna na přetáčení z recenze menu (bod 3) byla omyl podle VSync v grafice; vráceno |
| 3 | Nejednotné předpony popisků | doporučeno | opraveno: Let – / HUD – / Kamera – / Rozhraní –, seřazeno |
| 4 | „Coupled“ anglicky mezi češtinou | doporučeno | ponecháno: termín SC, stejný jako CPLD na HUD a v nápovědě kláves |
| 5 | OVLÁDÁNÍ bez nadpisů sekcí | doporučeno | opraveno: nadpisy „Inverze“ a „Myš“ se značkou ⊟ a odsazené řádky |
| 6 | List 03 příliš zmenšený | doporučeno | opraveno: ZVUK a OVLÁDÁNÍ na samostatných listech |

## Ověřovací kolo – PASS, průměr 7,5

Body 1, 2, 3, 5, 6 opravené. Nová doporučení: chromatická aberace a zrnitost jako posuvník (SC 0–100; naše konzolové
proměnné umí jen zapnout/vypnout – ponecháno), technika upscalingu s oběma šipkami ztlumenými (TSR je jediná, dokud
projekt nemá plugin DLSS – ponecháno), sekce a řádek „Citlivost myši“ stejně pojmenované (opraveno po kole: sekce
„Myš“, jen text, bez dalšího kola).

Mimo listy: Ostření se v prvním snímku ukazovalo 0. `r.Tonemapper.Sharpen=0.6` v `DefaultEngine.ini` přebíjelo nastavení
(vyšší priorita než herní nastavení); přesunuto do výchozí hodnoty nastavení (30) s migrací na verzi 5.
