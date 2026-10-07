# KF-COCKPIT-CONSOLE – levá loketní konzole pilota

Díl továrny `SM_Kit_Cockpit_Console12W_A` (`Tools/Kit/kit_cockpit.py`), v lodi Wayfarer přes
`interior.kit_modules.run_parts`, hodnocení `Docs/Reviews/2026-10-07_kf_cockpit_console.md`.

## 2D návrh (7. 10. 2026)

Autor 7. 10.: reference SC jsou styl a design, ne rozměry; návrh je náš, 2D pohledy z AI ze všech potřebných úhlů.
Vygenerováno `concept/gen_concepts.py` (Scenario, GPT Image 2.5 Sunburst; reference SC `Docs/Kit/etalon/sc/` jen jako
styl, zadání v `concept/prompt.txt`). Přehled `concept/overview.jpg`.

| Soubor | Pohled |
| --- | --- |
| `hero_34.png` | hlavní 3/4 zepředu shora od křesla (zdroj pro ostatní) |
| `front.png` | zepředu (čelo, madlo, knipl) |
| `top.png` | shora šikmo |
| `face_close.png` | detail čela: kryt EMER, kolébky THR/LAND/CARGO, stavový pás, klávesy, madlo |
| `sheet_turnaround.png` | ortogonálně: půdorys, vnitřní bok, vnější bok, čelo (stejné měřítko) |
| `sheet_details.png` | knipl, opěrka na konzolách zespodu, přední část, stavový pás a klávesy |
| `hero_34_v1_stick_behind.png` | zamítnutá první verze: knipl za opěrkou (ruka musí být před loktem) |

Jednotlivé pohledy z boku a zezadu model kreslil jako kopii hlavního 3/4 – ortogonální pohledy proto jdou listem.

## Co z návrhu plyne pro stavbu (oproti v6)

- **Opěrka předloktí** je samostatný nosník po celé zadní části vnitřní hrany: lomený profil (zkosené čelo
  a spodní hrana), na **dvou šikmých konzolách** nad podstavcem, tmavý perforovaný polštář ve dvou dílech.
- **Knipl** před opěrkou na vlastní desce s kruhovým šrafovaným lemem; hlava šedá kovová, ne bílá; lučík
  plochý pás.
- **Podstavec** z velkých tmavých panelů ve světlém kovovém rámu (lomené obrysy, zkosené rohy), větrací mřížka
  dole, štítek HF-3287 PILOT INTERFACE L ARM, oranžové šrafy.
- **Vpředu zvednutý blok** (lichoběžníkový, zkosené hrany): klávesa EMER pod krytem v oranžovém rámu, tři kolébky
  s legendami na tmavém poli, LED nad nimi; stavový pás PWR/SYS/FLT a klávesy 2×2 v tmavých polích s rámem.
- **Madlo** trubkové s oranžovým návlekem, vpředu přes celou šířku.
- **Materiály:** světlý ošoupaný kov (ne bílý lak) s tmavými poli, hodně šroubů, oděr na všech hranách, špína.
- Rozměry a rozložení drží náš návrh (1,2 × 0,67 m, výška lokte), návrh je styl a skladba.

## Varianta B podle návrhu (7. 10. 2026)

`SM_Kit_Cockpit_Console12W_B` (`Tools/Kit/kit_cockpit_b.py`) v testovacím úseku 1,6 m za variantou A (A zůstává
v lodi). Snímky `Tools/Shots/kit_cockpit_console_b.json` (stejné úhly jako `kit_cockpit_console_studio`).

- Tvar podle návrhu: opěrka předloktí jako nosník na dvou šikmých konzolách a zadní noze (mezera 9 cm), blok kniplu,
  prostřední blok se sáním nahoře a stavovým pásem a klávesami na zkosení ke křeslu, věž s klávesou EMER a kolébkami,
  trubkové madlo s oranžovým návlekem, tmavé panely v bocích, oranžové šrafy.
- **Odchylka:** ovladače věže jsou na jejím zadním svahu k pilotovi (v návrhu na čele – z křesla nevidět, nedosáhnout).
- Nová role `Kit_Frame` (ošoupaný světlý kov s leskem), ostrá zkosení (`Part.sharp_deg` 20° – zkosení 25–55° se
  pod 40° stínovala jako oblé plochy).
- **Stav:** tvar sedí, povrch ne – pořád čistá šedá, karty ošoupání skoro nevidět, velké prázdné plochy desky.
  Další krok je systémový: viditelné opotřebení v materiálu továrny (maska oděru hran, špína ve spárách, šum
  drsnosti) a hustší panelizace (tmavá pole v rámech, šrouby) podle `sheet_turnaround.png`.
