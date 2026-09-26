# Detail lodí SC: rozbor tří videí Markom3D (26. 9. 2026)

Zdroj: tři rozbory lodí SC otevřených v Blenderu (kanál Markom3D, 1080p). Video a snímky leží lokálně v
`ArtSource/Reference/Video/markom_*` (mimo git). Snímky jsou po 2 s, přehledy v `sheets/`, u prvních dvou videí i
přepis automatických titulků (`transcript.txt`). U třetího YouTube titulky zablokoval ověřením proti botům, takže
je rozebrané jen ze snímků. Poznatky jsou psané vlastními slovy a časy vedou do videa.

| Zkratka | Video | Loď |
|---|---|---|
| **C2** | [How SC make their models look awesome](https://www.youtube.com/watch?v=EOaiEeEjCGM) (9:31) | C2 Hercules, exteriér a nákladový prostor |
| **KOK** | [SC cockpits in Blender](https://www.youtube.com/watch?v=fwhcB5NOXnI) (9:05) | C2 Hercules, kokpit (Blender i ve hře) |
| **MOLE** | [SC spaceship creation](https://www.youtube.com/watch?v=VE4bZoJvlqI) (8:21) | Argo MOLE, jeden panel trupu; na konci jiný interiér |

## 1. Co je geometrie a co decal

- **Trup C2 bez decalů je skoro hladký.** Se skrytými decaly zbudou velké tmavé plochy s několika širokými
  drážkami ([C2 0:38](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=38),
  [0:42](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=42)). Panelové linky jsou tenké pásy decalů, které jdou
  po trupu. V drátovém zobrazení jsou to dlouhé úzké proužky ([C2 0:28](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=28),
  [0:32](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=32)). Pod motorem jsou decaly i spáry, které vypadají
  jako vymodelované ([C2 1:55](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=115)).
- **Stěny nákladového prostoru:** panely, madla, mřížky a kryty jsou geometrie (v solid režimu jsou vidět,
  [C2 5:00](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=300)). Pruhy, šrouby na hranách, čísla a štítky jsou decaly
  ([C2 4:30](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=270), [5:10](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=310)).
- **Panel MOLE:** hlína ukazuje mělké vybrání panelů a lišty ([MOLE 0:38](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=38)).
  Všechno ostatní jsou decaly: logo výrobce, velké „08“, žaluzie větrání, DANGER, šrafy a kolečka
  ([MOLE 0:32](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=32)). Žaluzie, které vypadají jako hluboké, jsou
  normálový decal na rovném laku.

**U nás:** stejný princip. Trup z hs pipeline má skutečné spáry jen na hlavních přepážkách, zbytek dělají mesh
decaly (pásy `panel_lines`, ~800 decalů, 650 m pásů). Interiér kokpitu je naopak z velké části geometrie
(moduly, pouzdra, šrouby).
**Převzít:** v interiéru víc decalů na rovných plochách (štítky, spáry, šrouby, pruhy, obrysy) a méně
modelovaných drobností. Decal je levný, geometrie drobností stojí trojúhelníky i čas stavby.

## 2. Hustota decalů

- **Dveře a chodby:** každý rám dveří je poset značkami, čarami a kroužky
  ([C2 7:12](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=432)). Tunel na můstek má na podlaze nápis BRIDGE
  a u prahu pruhy ([C2 6:58](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=418)).
- **Podlaha nákladového prostoru:** tmavé desky, protiskluzové lišty a přerušované čáry. V solid režimu je
  černá plocha decalů větší než polovina podlahy ([C2 5:40](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=340)).
- **Kokpit:** kolem každé skupiny ovladačů je tištěný zaoblený rámeček s názvem skupiny v přerušené horní hraně
  (DISP, QNTM, CTRM). Kolem otočných voličů jsou oblouky stupnice, pod každým ovladačem popisek
  ([KOK 1:40](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=100)). Samotné knoflíky jsou jednoduché válce
  s kroužkem a páčky hladké, bohatost dělá tištěná vrstva. Hlavní funkce má jedno velké podsvícené tlačítko
  (LIFT). Emisní nápisy jsou decaly se svítícím materiálem ([KOK 3:13](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=193)).
- **Sedadlo:** švy a lemy jsou decaly z trim sheetu, ne geometrie ([KOK 3:32](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=212)).
- **Horní plocha desky C2 je velká a čistá** ([KOK 3:28](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=208)).
  Hustota je soustředěná do panelů, ne rozprostřená všude.

**U nás:** moduly mají každý ovladač v samostatném pouzdře s obrubou a popiskem, skupiny nemají rámeček ani
název, stupnici má jen otočný volič. Rozptyl decalů v kokpitu je náhodná mřížka, na podlaze jsou jen lišty.
**Převzít:**
- tištěné rámečky skupin s názvem, oblouky stupnic a menší obruby jednotlivých ovladačů;
- jedno velké podsvícené tlačítko na panel;
- emisní štítky;
- na podlaze čáry, pruhy u prahů a nápisy sekcí;
- hustotu soustředit do shluků u funkčních míst, velké plochy nechat klidné (kritik ale prázdné plochy vytýká,
  takže klidná plocha musí mít aspoň spáry a zrno materiálu).

## 3. Velké decaly špíny

- Nad motory a přes křídla C2 leží **velké plochy (karty) se stékající špínou**: bílá textura s tmavými svislými
  šmouhami, rovina těsně nad trupem, přes celé křídlo a svislou plochu
  ([C2 0:50](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=50), [0:54](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=54),
  na celé lodi [8:00](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=480)). Ve hře je efekt jemný
  ([C2 1:04](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=64)).

**U nás:** špína je procedurální v materiálu trupu (`DirtAmount` 0,15, `GrungeAmount` 0,15, dlaždice 160 cm),
jinak jen malé stékání pod mřížkami (`streak_chance`). Velké směrované stopy nemáme.
**Převzít:** karty špíny 1–4 m jako mesh decaly (tmavá barva × alfa ze šmouh, drsnost nahoru) na místech, kde by
se špína reálně tvořila: za a nad tryskami, na náběžných hranách a kořenech křídel, pod výdechy a u podvozku.
Pravidlo v `hs_decals` a textury šmouh v knihovně.

## 4. List decalů a natažené úseky atlasu

- Barevný atlas C2 obsahuje výstražné značky, šrafy, číslice 0–9, nápisy (CAUTION, EXHAUST, AIRLOCK, VENT…)
  a logo výrobce ([C2 5:50](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=350)). Druhý atlas je šedý
  (výška a normála): mřížky, šrouby, kryty, madla, kroužky a lišty ([C2 6:02](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=362)).
- **Natažené úseky:** dlouhá čára na podlaze používá kus atlasu roztažený do délky, v UV je vidět úzký obdélník
  přes úsek atlasu ([C2 6:04](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=364)). Jeden malý kus textury pokryje
  metry podlahy.
- MOLE má atlas lišt se svislými pruhy na panelové linky ([MOLE 5:24](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=324))
  a atlas s logem výrobce ([MOLE 1:36](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=96)).

**U nás:** atlas decalů 4096 px s pevnou hustotou 2048 px/m, strukturní položky (normála, drsnost, AO) a
informační (barva). Stejné rozdělení jako SC. Pásy panelových linek už kus textury táhnou do délky.
**Převzít:** natažené pásy i pro interiér (čáry na podlaze, pruhy u prahů, lemy stěn, hrany schodů) z jedné
položky atlasu, místo opakování malých decalů.

## 5. Materiály

- Lak C2 je **jednoduchý a plochý, bez opotřebení hran** ([C2 1:17](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=77)).
  Špinavý dojem dělá mapa drsnosti přes rovný lak, ne barva ani otřené hrany
  ([C2 4:35](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=275)).
- MOLE: oranžový lak a dlaždicová šedá textura se svislými škrábanci a šmouhami v drsnosti
  ([MOLE 2:10](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=130), [2:22](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=142),
  [5:16](https://www.youtube.com/watch?v=VE4bZoJvlqI&t=316)). Černé kolejnice mají vlastní materiál.
- Stěny nákladového prostoru: bílý lak s jemnými skvrnami v lesku, které se ukážou až v odlesku světla
  ([C2 4:32](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=272)).

**U nás:** vrstvený master trupu má `EdgeWear` 0,8 (práh 0,45), procedurální grunge a špínu, variaci drsnosti
0,28 a lesk po panelech. Interiér (`M_Ship_*Int*`) má hladké plochy bez zrna, to kritik vytýkal („jednolitý
matný grafit bez mikrostruktury“).
**Převzít:**
- opotřebení hran trupu stáhnout na minimum (0–0,2);
- variaci drsnosti dělat dlaždicovou texturou šmouh a škrábanců (CC0, ambientCG) ve světových souřadnicích,
  pro trup i interiér;
- interiér: lak s jemnou variací lesku, viditelnou v odlescích.

## 6. Světla

- Outliner C2 ukazuje počty podle typu v kolekcích ([C2 8:04](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=484)):
  - můstek 74 světel;
  - únikové moduly 80;
  - horní paluba 418;
  - systémy 56;
  - nákladový prostor 160.

  Dohromady zhruba **790 světel** (scéna má 9 203 objektů, 2,2 M vrcholů).
- Nákladový prostor: světla po celém stropě, v rozích i u stěn, žádné jedno velké
  ([C2 8:10](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=490)). Autor videa zdůrazňuje, že každé svítidlo má
  své světlo, protože to dává stíny a objem v mlze ([C2 7:51](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=471)).
- Chodba na můstek: svítící prstence na každém rámu a lišty podél hran podlahy, silný kontrast světla a tmy
  ([C2 6:48](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=408)). Kokpit C2: tmavý, s barevným podsvícením pod
  deskou a kolem nohou ([KOK 3:12](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=192)).

**U nás:** Wayfarer má 35 světel interiéru na celou loď, kokpit asi deset. Stejná hustota jako C2 (můstek
~74 na ~80 m², tedy ~1 světlo na m²) by u kokpitu Wayfareru (~8 m²) dala 8–10 světel jen na kabinu a na celou
loď ~60–90.
**Převzít:** světlo u každého svítidla a každé svítící lišty: krátký dosah, bez stínů (stíny jen 2–3 hlavní),
akcent u podlahy a pod deskou, světla displejů. Měřit na RTX 2060: interiér je vázaný na pixely, levná světla
bez stínů s malým dosahem by měla stát málo. Ověřit `stat gpu`.

## 7. Kokpit C2 (pro krok 4, přestavbu z kitu)

- Displeje jsou v řadě zapuštěné v tělese desky pod linií pohledu, každý ve vlastní šachtě
  ([KOK 3:22](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=202), [3:28](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=208)).
  To odpovídá autorovu rozhodnutí „jeden pás v desce s moduly kolem“.
- Panely mají perforované mřížky s kruhovými otvory, šrafy a malé skupiny tlačítek
  ([KOK 3:12](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=192), [2:10](https://www.youtube.com/watch?v=fwhcB5NOXnI&t=130)).

## 8. Audit zdrojů (co máme a co chybí)

| Potřeba z rozboru | Máme | Chybí / zdroj |
|---|---|---|
| Strukturní atlas (mřížky, šrouby, kryty, lišty) | `decal_library.json`, 4096 px, T_Decals_N/M/BC | — (rozšiřovat podle potřeby) |
| Informační atlas (nápisy, čísla, výstrahy) | tentýž atlas, text z fontů projektu | tištěné rámečky skupin, oblouky stupnic, emisní verze štítků |
| Textury šmouh a stékání pro velké karty špíny | nic | CC0: ambientCG Leaking / Grunge / Smear (bez klíče přes API) nebo procedurálně v `generate_decals.py` |
| Dlaždicová textura drsnosti (škrábance, šmouhy) | procedurální grunge v masteru | CC0: ambientCG Scratches / Smudges / Fingerprints; import jako maska drsnosti |
| Trim sheet interiéru (lišty, švy, obruby) | Quaternius kit (CC0, low-poly), trim textury kitu | vlastní trim sheet (procedurálně z knihovny decalů), krok 3 |
| Svítidla se světlem | lišty a bodovky v receptu, 35 světel | pravidlo „světlo u každého svítidla“ v `hs_interior` / kitu |
| Mlha pro objem světla | výšková mlha scény | lokální volumetrická mlha interiéru (ověřit cenu) |

Licence: ambientCG a Poly Haven jsou CC0 (záznam do `Docs/Credits.md` v tabulce CC0). Nic placeného.
