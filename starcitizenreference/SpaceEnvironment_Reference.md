# Vesmír a okolní prostředí — kompletní referenční rozbor

Rozbor toho, jak přední vesmírné hry (Elite Dangerous, No Man's Sky, Star
Citizen, Starfield) řeší okolní prostředí: strukturu systémů, obsah
vesmíru mezi planetami, škálu/vzdálenosti a jak vyvážit realismus proti
hratelnosti. Cíl: referenční podklad pro budoucí rozhodnutí, ne příkaz
k okamžité implementaci.

---

## 1. Základní problém: vesmír je příliš velký na to, aby byl "hratelný" doslovně

Každá z těchto her řeší stejné dilema jinak — realistické vzdálenosti ve
vesmíru jsou tak obrovské, že doslovný let by znamenal hodiny/dny prázdné
nudy. Tři hlavní přístupy:

- **Elite Dangerous**: 1:1 měřítko reálné Mléčné dráhy (miliardy systémů,
  reálná astronomická data). Řeší to přes "Supercruise" (vnitrosystémové
  zrychlené cestování) a hyperjumpy mezi systémy — fyzická vzdálenost je
  reálná, ale čas cestování je uměle stlačený vysokou rychlostí.
- **No Man's Sky**: taky "nekonečný" prakticky nekonečný vesmír, ale
  vzdálenosti uvnitř systému jsou herně zmenšené/stylizované, ne 1:1
  reálné. Důraz na rychlý přístup k obsahu (planeta je "blízko" ve hře,
  i když by reálně byla daleko).
- **Starfield**: kombinuje handcrafted klíčové lokace s procedurálně
  generovanými planetami, kam se cestuje přes loading/fast-travel mezi
  jednotlivými "bublinami" obsahu (orbit → povrch je samostatná scéna,
  ne kontinuální let).
- **Star Citizen**: nejblíž "žádnému kompromisu" — snaží se o seamless
  přechody (to, co jsme si vybrali jako cíl pro Veyru), ale i tak
  vzdálenosti mezi planetami řeší přes Quantum Travel (viz předchozí
  dokument), ne skutečný 1:1 let v reálném čase.

**Klíčový insight:** žádná z těchto her nenutí hráče doslova proletět
reálnou vzdálenost mezi planetami v reálném čase bez nějaké formy
zrychlení/kompresе. To, co dělá "hru o vesmíru" hratelnou, není realismus
vzdáleností, ale **věrohodný pocit** obrovského prostoru v kombinaci
s praktickým způsobem, jak se v něm rychle pohybovat.

**Náš stav:** Máme jednu planetu (Veyra) s reálně-škálovaným letem
k ní (76s cestovní rychlostí). To funguje pro jednu planetu. Jakmile
přidáme druhou/třetí, narazíme na stejné dilema — a budeme muset
zvolit jeden z výše uvedených přístupů (pravděpodobně kombinace:
seamless landing jako teď + nějaká forma zrychleného cestování mezi
planetami/systémy, podobně jako Quantum Travel z předchozího dokumentu).

---

## 2. Obsah vesmíru mezi planetami — co tam vlastně je

Prázdný vesmír mezi planetami rychle omrzí. Hry ho plní těmito typy
obsahu ("points of interest", zkráceně POI):

### Asteroidová pole / pásy
- Gameplay funkce: těžba (zdroj surovin), úkryt/cover v boji, navigační
  překážka (musíš proletět opatrně, ne jen tlačit W).
- Vizuálně: shluky různě velkých těles, ne rovnoměrná mřížka — hustota
  by měla mít "jádro" (hustší) a řídnoucí okraje.
- V Cosmoteer např. asteroidový pás obklopuje celý systém jako okraj
  hratelné oblasti — funguje i jako přirozená hranice mapy.

### Vraky lodí / "hulks" / debris fields
- No Man's Sky COSMOS update (2026) přidal prakticky přesně tenhle typ
  obsahu: procedurálně generované vraky, které se dají prohledávat/těžit
  za cenu rizika (vraky jsou nestabilní, mohou explodovat).
- Gameplay funkce: environmentální storytelling (co se tu stalo?),
  loot/salvage smyčka, volitelné riziko/odměna.

### Mlhoviny (nebulae)
- Primárně vizuální/atmosférický prvek (Elite Dangerous má desítky
  pojmenovaných mlhovin jako "sightseeing" cíle), ale dá se jim přidat
  i gameplay dopad: snížená viditelnost, rušení senzorů/radaru, bonus/
  malus na určité typy zbraní (viz Cosmoteer příklad: mlhovina snižuje
  dosah senzorů, ale zvyšuje škodu energetických zbraní a skrývá lodě).

### Deep-space outposty / stanice / anomálie
- Statické nebo pomalu se pohybující struktury sloužící jako herní huby
  (obchod, mise, craftění) uprostřed jinak prázdného prostoru.

### Signály / anomálie k prozkoumání
- "Unidentified signals" typu No Man's Sky — bodové markery na mapě
  systému, které lákají hráče prozkoumat něco konkrétního, ne jen
  létat naslepo.

**Náš stav:** Máme jen 16 asteroidů jako čistě vizuální/kolizní
referenční body (žádná gameplay funkce — netěží se, nejsou zdrojem
ničeho). To je v pořádku jako placeholder, ale až budeme řešit
gameplay smyčku, tohle je seznam, odkud brát inspiraci na "co dát
mezi planety, aby to nebyla prázdnota".

---

## 3. Procedurální vs. ručně dělaný obsah — kde je hranice

Starfield řeší tohle nejsystematičtěji ze všech čtyř her:
- Algoritmus generuje planetu podle **biome metrik** (typ terénu, historie
  osídlení, atd.) — planeta s historií inteligentního života dostane
  pravděpodobněji umělé ruiny, odlehlé světy nemají nic.
- I na procedurálně generovaných planetách jsou POI **ručně navržené
  šablony**, jen se vybírají/umisťují algoritmicky — ne, že by každý
  POI byl čistě náhodný shluk geometrie.
- Klíčové/příběhové lokace (třeba hlavní město) jsou 100% ručně dělané,
  bez procedurální generace vůbec.

**Praktický důsledek pro nás:** i když budeme chtít víc než jednu planetu,
nemusíme (a nemělo by to smysl) stavět "nekonečný" procedurální vesmír
jako Elite/NMS. Mnohem realističtější a udržitelnější cíl pro sólo projekt
je **malý, ale ručně navržený sluneční systém** (pár planet, pár POI,
možná jedna stanice) — stejný přístup, jaký jsme zvolili u Veyry (ručně
umístěná, ne procedurálně vygenerovaná pozice).

---

## 4. Environmentální hazardy — vesmír není jen prázdnota k proletění

Napříč hrami se opakuje vzorec: prostředí samo o sobě představuje riziko,
ne jen NPC/nepřátelé:

- Radiační zóny kolem hvězd (Cosmoteer "sun zone")
- Mlhoviny rušící senzory/navigaci
- Debris fields poškozující loď při rychlém průletu
- Nestabilní vraky, co explodují při prohledávání
- (Ze Star Citizen dokumentu) — interdikce, EMP rušení během quantum
  spoolu

**Náš stav:** Máme jen samotnou planetu jako "hazard" (kolize, HEAT při
rychlém atmosférickém vstupu). Až budeme mít víc objektů ve vesmíru,
tohle je seznam k inspiraci na to, jak z prázdného prostoru udělat
místo, které vyžaduje pozornost, ne jen tlačit W.

---

## 5. Vizuální technika — skybox a renderování dálky

Nešel jsem hluboko do rendering-specifické literatury (mimo scope tohohle
rozboru), ale klíčový princip, který se opakuje:

- Vzdálené hvězdy/mlhoviny se typicky renderují jako statický/pomalu
  rotující skybox (to už máme — náš `ASkyDome`), ne jako simulovaná
  geometrie v reálné vzdálenosti.
- Blízké objekty (asteroidy, vraky, jiné lodě) jsou skutečná herní
  geometrie s kolizemi.
- Přechod mezi "vzdálený skybox prvek" a "blízký herní objekt" (např.
  vzdálená planeta, která se postupně stává herním objektem, jak k ní
  letíš) je přesně to, co jsme řešili u Veyry (World Origin Rebasing +
  postupné LOD zjemňování).

**Náš stav:** Tohle už máme vyřešené líp než spousta jednodušších her —
náš floating origin + skydome systém je přesně ten správný technický
základ pro cokoliv z výše popsaného.

---

## Shrnutí — co z tohohle dává smysl pro gamespace a kdy

1. **Rozhodnutí o škále vesmíru** — než přidáme druhou planetu, musíme
   se rozhodnout: realistické vzdálenosti + nějaká forma zrychleného
   cestování (Quantum Travel styl, navazuje na předchozí dokument), NEBO
   uměle zmenšené vzdálenosti (NMS styl, jednodušší implementačně).
   Doporučení: vzhledem k tomu, že už máme funkční seamless landing na
   reálné škále, dává smysl zůstat u **realistických vzdáleností +
   Quantum Travel** — je to konzistentní s tím, co jsme už postavili.

2. **Asteroidové pole s gameplay funkcí** — snadné rozšíření současných
   16 dekorativních asteroidů o těžbu/zdroje, jakmile budeme řešit
   ekonomiku/inventář (zatím nemáme).

3. **Druhá planeta/měsíc jako další cíl** — přirozený další krok pro
   "obsah vesmíru", než budeme řešit POI/vraky/mlhoviny.

4. **Vraky lodí, mlhoviny, deep-space POI** — pozdější fáze, dává smysl
   až s existující gameplay smyčkou (těžba/mise/obchod), jinak je to
   jen dekorace bez účelu.

5. **Environmentální hazardy** — polish fáze, navazuje na existující
   HEAT systém, ne prioritní teď.

Stejně jako u letového systému — nejde o seznam úkolů k okamžité
implementaci, ale o mapu, ze které vytáhneme konkrétní další krok, až
na něj budeme mít připravenou půdu (typicky: až budeme řešit druhou
planetu nebo ekonomiku/těžbu).
