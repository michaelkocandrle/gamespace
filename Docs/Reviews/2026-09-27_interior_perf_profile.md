# Profil výkonu interiéru s MegaLights C (27. 9. 2026)

Zadání autora: cíl je 60 FPS v interiéru na RTX 2060 v 1080p. Po zapnutí MegaLights změřit chodbu a křižovatku.
Pod cílem udělat profil (světla, stíny, Lumen, průsvitnost, geometrie) a navrhnout úspory dřív, než přibudou
další světla. Předvolba v zadání nebyla vyplněná. Měřeno ve výchozím nastavení hry: epická kvalita, TSR 75 %
(1440×810 → 1920×1080).

## Stav

- **MegaLights C je zapojená:** při vstupu do interiéru (I, U, `space.Interior`, `space.Showroom`) C++ nastaví
  `r.MegaLights.EnableForProject 1`, při návratu do lodi 0. Všechna světla ukázky kitu mají stíny (138 světel),
  při letu lodí se nic nemění.
- **Měření:** ustálené `stat unit` po 6 s ve stejných záběrech jako v recenzích kitu (chodba od okna, křižovatka
  zatáčky). Presety `Tools/Shots/kit_perf_profile.json` a `kit_perf_lumen.json`.

| Varianta (vždy jen jedna změna proti C) | GPU chodba | GPU křižovatka | Úspora |
|---|---|---|---|
| **C: MegaLights + RT stíny (nový stav)** | **18,1 ms** | **18,0 ms** | – |
| bez stínů (MegaLights B) | 17,0 | 16,9 | 1,1 |
| **bez odrazů Lumenu** | **15,8** | **15,2** | **2,3–2,8** |
| bez Lumen GI (obraz zčerná, jen pro řád) | 14,5 | 14,2 | 3,6–3,8 |
| bez průsvitnosti | 17,9 | 17,4 | 0,2–0,6 |
| rozlišení 67 % místo 75 % | 16,5 | 15,5 | 1,6–2,5 |
| bez motion bluru, bloomu a DOF | 18,2 | 17,8 | ~0 |
| dnešní stav A (bez MegaLights, bez stínů) | 17,2 | 16,1 | – |
| odrazy Lumenu v ½ rozlišení | ~17,0 | ~16,7 | ~0,7 |
| odrazy jen do drsnosti 0,3 / 0,2; hrubší sběr sond (32) | beze změny | beze změny | 0 (v šumu ±0,4 ms) |

- Rozpad C v chodbě (`stat gpu`): odložené osvětlení 8,4–8,9 ms (z toho MegaLights 3,6–4,0), postprocess 4,2,
  TSR 3,6, odrazy Lumenu 2,7–2,8, sběr sond Lumenu 1,5, stíny (hloubky a projekce) 1,1, základní průchod 0,4–0,5.
- **Geometrie není problém:** základní průchod 0,4 ms, 500–2 700 volání kreslení, CPU (Game) 2,7–6,8 ms. Hra je
  vázaná na GPU.
- **Snímek:** C má 17,5–18,1 ms GPU, tedy ~52–57 FPS. K 60 FPS (16,7 ms na snímek, GPU ≤ ~16,2 ms) chybí ~1,5–2 ms.

## Návrh úspor (čeká na autora, nic z toho není zapnuté)

1. **Odrazy Lumenu v interiérech vypnout** (`r.Lumen.Reflections.Allow 0` při vstupu do interiéru, spolu
   s MegaLights): −2,3 až −2,8 ms, tím je cíl splněný. Na snímcích chodby je rozdíl skoro nepostřehnutelný
   (lak kitu je matný, lesklé lišty jsou zdrsněné). Ztratí se ostré odrazy na skle a lesklém kovu. Až přibudou
   lesklé plochy (sklo, displeje), je potřeba to přeměřit.
2. **Pokud se odrazy mají zachovat:** poloviční rozlišení odrazů (−0,7 ms) a k tomu rozlišení 70 % (asi −1 ms,
   obraz o něco měkčí). Samo o sobě to na 60 FPS nestačí.
3. **Stíny MegaLights (C) nechat:** stojí ~1,1 ms, ale dávají kontrast, který chtěl kritik.
4. **Nepomáhá:** vypnutí motion bluru, bloomu a DOF, omezení průsvitnosti, hrubší sběr sond, nižší práh drsnosti
   odrazů.

Vedlejší zjištění: s RT stíny je ukázka tmavší. Průměrný jas chodby klesl z 0,20 na 0,13, p90 z 0,42 na 0,25
(spodní hrana rozsahu SC). Světla už neprosvítají geometrií. Jestli má být interiér světlejší, přidá se
intenzita svítidlům; to výkon s MegaLights skoro nemění.
