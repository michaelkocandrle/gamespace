# Kit: interiér s Nanite, znovu ověřeno (26. 9. 2026)

Zadání kitu, krok 2: „Interiér bez Nanite (nástraha 9.2a), pokud to mezitím neplatí, ověř a zapiš.“

- **Test:** Wayfarer s dílem Interior jednou bez Nanite (současný stav) a jednou s Nanite (`no_nanite_parts`
  bez Interior). Preset `display_sharpness`, pohled pilota za rychlého letu (400 m/s s přídavným spalováním,
  zatáčení s boostem, NAV 900 m/s, pomalý let), TSR, třesení kamery.
- **Výsledek:** s Nanite interiér v pohledu pilota přišel o tenké díly: rámy displejů, pouzdra ovládacích modulů
  a obruby zmizely a tvary desky se zhrubly. Rozpad textu v rychlém letu (původní 9.2a) se na těchto snímcích
  výrazně neprojevil, ale rozbitá geometrie stačí.
- **Další důvody pro „bez Nanite“:**
  - stíny MegaLights přes ray tracing počítají s přesnou geometrií; Nanite mesh jde do ray tracingu jako
    zjednodušená záloha;
  - interiér letí s kamerou (9.2a).
- **Pravidlo platí.** Díky rozpočtům trojúhelníků v `ArtSource/Kit/kit_rules.json` zůstane interiér bez Nanite
  v rozumném výkonu (dnes ~300 tisíc trojúhelníků na 67 m² bez pláště trupu).

Snímek: `2026-09-26_kit_nanite_check/bez_nanite_vs_nanite_400ms.jpg` (vlevo bez Nanite, vpravo s Nanite).
