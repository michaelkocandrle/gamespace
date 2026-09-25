# Kalibrace vizuálního kritika (visual-critic)

Kritik (`.claude/agents/visual-critic.md`) se před nasazením testoval na pěti verzích, které autor
už zkritizoval. U každé musel najít autorovy podstatné výtky. Zadání kritika se upravuje jen podle
toho, co přehlédl, a každá úprava je zapsaná tady.

## Metodika
- Kritik dostal jen `brief.md` (co to má být, styl) a srovnávací listy z `Tools/Review/make_compare_sheet.py`
  (reference vlevo, výsledek vpravo). Nedostal autorovy výtky, postup ani názor.
- **Kolo 1 bez checklistu** ze skillu. Checklisty ve skillu už obsahují poučení z těchto výtek, takže
  kolo 1 testuje vlastní oko kritika. S checklistem by kalibrace nic neměřila.
- Model: Fable 5.1 (dokumentace: „highest available capability“), effort max.
- Technická poznámka: složka `.claude/agents/` vznikla za běhu session. Claude Code sleduje jen složky,
  které existovaly při startu, takže `visual-critic` šel v této session spustit až po restartu. Kalibrace
  proto běžela přes read-only agenta Explore s modelem Fable a s **doslovným** textem zadání
  z `visual-critic.md` (nástroje omezené na Read/Glob/Grep instrukcí). Od příští session se volá přímo
  `subagent_type: visual-critic`.
- Listy a výstupy: `Docs/Reviews/calibration/<verze>/` (`brief.md`, `sheet_*.jpg`, `critic_round<N>.md`).

## Sada se známými odpověďmi

| Verze | Snímky | Reference | Autorovy výtky (zápis) |
|---|---|---|---|
| 1 Wayfarer z Meshy | autorovy snímky ze hry (24. 9.) | koncept Wayfareru ve stylu SC (Higgsfield) | „vypadá nekvalitně, jak kdyby byla rozbitá, špinavá“; „geometrie je mimo, lak s tím nesedí“ – roztavený povrch, rozeklané hrany |
| 2 čistá verze v2 | `Docs/Shots/Wayfarer/v2_*` | týž koncept | „trubka s nakreslenými čarami“, chybí vrstvy, střední detail, materiály |
| 3 první interiér | `Saved/Shots/20260925_015641_wayfarer_interior` | 8 snímků interiérů SC z `starcitizenreference/` | „prázdný byt nebo kancelář“, rovné stěny, béžové, ploché světlo |
| 4 černá kabina | `Saved/Shots/20260925_032901_wayfarer_interior` | kokpity SC 1–5, kabiny zezadu | „hlavně černá: tlustý tmavý rám skla, černá police nad displeji, tmavé stěny bez tvaru, žijí jen displeje a HUD; zezadu hranaté bloky“, výhled |
| 5 kabina s tablety | `…111836_cockpit_daynight`, `…122015_cockpit_daynight`, `…121035_wayfarer_interior` | kokpity SC | displeje jako tablety na stole, kulaté „čudlíky“ po stranách, rozbitá geometrie, zrcadlené nápisy na dveřích |

Snímky SC u exteriéru nejsou: reference je koncept lodi ve stylu SC (jiné snímky exteriérů SC
v projektu nejsou).

## Kolo 1 (zadání v1, bez checklistu)

| Verze | Verdikt | Našel | Přehlédl |
|---|---|---|---|
| 1 Meshy | FAIL | „rozpadá se na rozmazaný, měkký blob“, „zaoblený batoh bez ostrých hran“, „zubaté siluety“, „silueta hran je bublinovitá“, lak bez vrstvení, bakeované motory, artefakty spodku | – (silueta 6/10 je shovívavá, ale výtka zazněla) |
| 2 v2 | FAIL | „jeden měkký zaoblený válec bez zlomů“, „pravidelná mřížka panelových linek“ místo detailu, žádná druhá a třetí úroveň detailu, jednolitý matný krém, „hladký blockout“ | – |
| 3 interiér | FAIL | „holé krabice s plochými stěnami“, „jediný matný šedohnědý plast“, „béžová stěna přes 40 % snímku“, přepálené lišty a plochý zbytek, „blockout“ | slovo „byt/kancelář“ nepadlo, ale obsah (prázdné krabice, jeden materiál, ploché světlo) ano |
| 4 černá kabina | FAIL | „prázdná černá plocha“ mezi sklem a displeji, podexponovaná kabina, jen MFD „hotové“, zezadu „monolitické desky“ | **tlustý rám skla, černá police nad displeji, výhled ven** – nezmínil |
| 5 tablety | FAIL | „MFD jako tablety na stojanu… řada svítících teček… spotřební tablet“, rozbitý záběr (kamera v geometrii), zrcadlený „ENGINEERING“ na dveřích, holé stěny | – (tvrzení „v oknech není sklo“ je nepřesné: sklo je čiré) |

Úprava zadání po kole 1: do bodu 7 přidáno obecné pravidlo pro kokpity – vždy posoudit pohled
pilota (podíl výhledu ven, tloušťka rámu a sloupků, co zakrývá výhled, kolik obrazu zabírají tmavé
plochy bez tvaru) a zabudování displejů. Pravidlo nejmenuje konkrétní autorovy výtky (polici apod.),
aby kolo 2 měřilo, ne napovídalo.

## Kolo 2 (zadání v2, bez checklistu, verze 4 a 5)

| Verze | Verdikt | Našel | Přehlédl |
|---|---|---|---|
| 4 černá kabina | FAIL | „výhled ven jen střední třetina výšky obrazu“, „masivní středový sloupek a diagonální výztuhy 3–4 % šířky“, dvojité sloupky, „klín, který zakrývá výhled“, „černé plochy bez tvaru“ v horních rozích, „černá deska od okraje k okraji“ s displeji jako samostatnými deskami, neosvětlený interiér, zezadu nečitelná změť ploch | – |
| 5 tablety | FAIL | znovu tablety („dvěma tablety postavenými na stole“), zrcadlené COCKPIT/ENGINEERING, průnik a kamera v geometrii; nově i sloupky ~10 % šířky a výhled ~35 % proti 60 % v referenci; kajuta „kancelářská chodba“ | – |

**Výsledek kalibrace:** se zadáním v2 kritik našel podstatné autorovy výtky u všech pěti verzí,
bez checklistu. U ostrých recenzí dostává navíc checklist ze skillu `ship-pipeline` 7b, který
výtky z historie obsahuje výslovně.

Pozorované slabiny (sledovat):
- Skóre bývá v kategoriích, kde je první dojem v pořádku, o 1–2 body shovívavější (Meshy silueta 6).
  Rozhoduje ale seznam „musí se opravit“, ne skóre.
- Kritik občas tvrdí věci, které ze snímku neplynou (čiré sklo = „sklo chybí“). U každé výtky se
  proto v recenzi ověřuje, jestli platí; nepravdivá výtka se označí „neplatí“ s důvodem.
- Měřicí overlay (FPS) hodnotí jako vadu, pokud ho brief nevysvětlí → `notes` v `review.json`.

## Průběžné doplňky
Když autor po předání vytkne něco, co kritik přehlédl, zapíše se to sem (datum, co, jak se upravilo
zadání nebo checklist).
