# Kontrola: oprava `hs_decals.grid` na Wayfareru (27. 9. 2026)

Zadání autora: ověřit změnu v `hs_decals` (normála plochy decalu před otočením, WORKFLOW ct) hned na lodi –
přestavět decaly exteriéru Wayfareru a porovnat snímky před a po.

## Postup

1. Snímky „před“ ze zabaleného buildu se starou lodí: `hull_decals`, `wayfarer_interior` a nový preset
   `wayfarer_decal_fix` (záď zezadu, obě strany v záběru).
2. Přestavba: `hs_build_ship.py` (trup, interiér a jeho decaly) → `hs_assemble_ship.py` (decaly exteriéru) →
   `gamespace_ship_export.py` → `import_ship.py` → balení → stejné snímky „po“.
3. Přesné srovnání geometrie v Blenderu. `hs_assemble_ship` jsem na **stejném** `Wayfarer_HS.blend` pustil
   dvakrát, jednou se starou a jednou s novou verzí `Placer.grid`, a porovnal plochy decalů (poloha
   a směr normály každé plochy).

## Výsledek

| Mesh | Ploch | Změněná poloha | Otočená normála |
|---|---|---|---|
| `SM_Ship_Wayfarer_Decals` (exteriér) | 33 213 | 0 | **21** |
| `SM_Ship_Wayfarer_InteriorDecals` | 3 053 | 0 | 0 |
| `SM_Ship_Wayfarer` (trup) | 303 648 | 0 | 0 |

- Všech 21 ploch je jeden decal: stékající špína `streak_drip` (0,1 × 0,4 m) na zadní svislé ploše
  (x = −10,27 m, pod levou zadní mřížkou). Nové normály míří ven stejně jako trup (skalární součin 1,0), staré
  mířily do trupu. Decal tedy dosud ležel rubem k divákovi a UE ho ořízl. Na snímku „po“ je vidět:
  [rear_before_after.jpg](2026-09-27_hs_decals_wayfarer_check/rear_before_after.jpg) (dole zvětšeno se
  zvýšeným kontrastem).
- Snímky decalů trupu a interiéru se před a po liší jen na úrovni šumu snímání (druhé kolo „po“ proti
  prvnímu). Výjimkou je odraz ve skleněném zábradlí v interiéru: po přestavbě mají svítidla jiné pořadí jmen.
  S decaly to nesouvisí, geometrie decalů interiéru je identická.
- Vedlejší zjištění: `hs_build_ship.py` není úplně deterministický. Dvě stavby ze stejného receptu daly trup
  303 646 / 303 648 ploch, jiné pořadí jmen světel svítidel a jedno světlo posunuté o 0,2 mm (WORKFLOW cw).
  Porovnání opravy proto běželo na stejném trupu.

## Doplněk: zrcadlená textura (27. 9. 2026 večer)

`test_ship_geometry.py` po přestavbě hlásil `mirrored_decals (21)`: je to právě ten `streak_drip`. Ležel v zrcadleném
rámci (x × y proti normále), proto dřív mířil rubem dovnitř a test ho neviděl. Po opravě normály míří ven, ale
textura se četla zrcadlově. `Placer.place_at` teď zrcadlený rámec srovná otočením osy x. Test prochází, decal je
pod levou zadní mřížkou vidět a čte se správně (`Saved/Shots/20260927_181303_wayfarer_decal_fix`). Při dopoledním
commitu jsem geometrický test nespustil, proto chyba prošla (WORKFLOW ct doplněno).
