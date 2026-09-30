# Archiv: WORKFLOW kap. 10 „Kam dál (priority k 19. 9. 2026)“ (přesunuto 30. 9. 2026)

Doslovně přesunutá kapitola z `Docs/WORKFLOW.md`. Priority se týkaly odstraněné první stíhačky; aktuální
další kroky jsou v `Docs/CURRENT.md`.

## 10. Kam dál (priority k 19. 9. 2026)

Menší kroky, podle pořadí:

1. ~~Třetí displej ve středním sloupku~~ – hotovo 19. 9. 2026: RADAR nahoře, SELF STATUS dole
   (HANDOFF kapitola 5, bod 31).
2. ~~Přepínání stránek MFD~~ – hotovo 19. 9. 2026 (F1 / F2, HANDOFF kapitola 5, bod 32). Navazuje:
   přepínání myší jako v SC (režim interakce, klik na tlačítko displeje) a stránky zbraní, štítů a
   energie, až budou systémy.
3. ~~Detail lodi zblízka~~ – hotovo 20. 9. 2026 (detailní vrstva materiálu, trup 1 mil. trojúhelníků,
   HANDOFF bod 33). Navazuje: decaly a nápisy, lepší zdrojové modely z Meshy/Higgsfield.
4. ~~Hrany trupu (zkosení, vážené normály)~~ – změřeno 20. 9. 2026 a **zahozeno**: trup z Meshy má
   92 % hran pod 36° (organický sken, ne rovné panely), takže ostrejší úhel i 2mm bevel změnily jen 1 %
   pixelů. Hrany budou dávat smysl až u modelů s rovnými panely.
5. ~~Světlo a post scény~~ – hotovo 20. 9. 2026 (kapitola 11, HANDOFF bod 36).
6. ~~Okluze a kavita na trupu~~ – hotovo 20. 9. 2026 (HANDOFF bod 38): v pečených texturách žádná
   okluze nebyla, `Tools/Blender/bake_ship_ao.py` ji dopeče.
7. ~~Nápisy a výstražné pruhy~~ – hotovo 20. 9. 2026 (HANDOFF bod 39): decaly ze seznamu v setupu lodi.
   Navazuje: víc nápisů a další místa (zatím jich je sedm).
8. ~~Panelové spáry~~ – hotovo 20. 9. 2026 (HANDOFF bod 40): dlaždicový list triplanárně v prostoru lodi.
9. ~~První zóna materiálu~~ – hotovo 20. 9. 2026 (HANDOFF bod 41): spálený plech u trysek z polohy
   v prostoru lodi. Navazuje: další zóny (gondoly proti trupu, břicho po vstupu do atmosféry)
   a nakonec druhá sada UV, až bude třeba zóny kreslit ručně a ne odvozovat z tvaru.
10. ~~Hra běžela na Medium~~ – hotovo 20. 9. 2026 (HANDOFF bod 42): výchozí předvolba je Cinematic
    kromě global illumination, plus doostření po tonemapperu. **Než začneš hledat rozmazanost
    v modelu nebo materiálu, změř nastavení** – dvakrát za den to bylo ono (rozlišení 50 %, pak Medium).
11. **Odlesky a špína na skle canopy** (jemný fresnel, škrábance).
12. **Silnější záře displejů na rámu** a okolní desce.
13. Doladit zbývající „duchy“ čísel při afterburneru (9.2b).
14. **ambientCG.com** (sesterská stránka k Poly Havenu, stejná CC0 licence, volné API bez
    klíče, 2000+ materiálů) – zvážit `fetch_ambientcg.py` podle vzoru `fetch_polyhaven.py`
    pro variaci materiálu trupu (viz plastic_diag/plastic_mat) a pro interiér (kůže sedadel,
    guma, opotřebený kov na panelech). Nalezeno autorem 23. 9. 2026, zatím nezapojeno.

Velké celky:
- tělo pilota v sedadle;
- lepší model kokpitu (sedadlo, boční stěny);
- chybějící systémy SC HUD (palivo, zbraně, protiopatření);
- ~~SC-2b VTOL a zpětná vazba při visení~~ – hotovo 20. 9. 2026 (HANDOFF bod 43). Další v letové
  roadmapě je SC-3 (zbytek HUD a MFD) nebo SC-4 (quantum travel místo cruise).
- SC-4 quantum drive je hotový (HANDOFF bod 47). Z videa zbývá: **mapa systému (F2)** s výběrem
  cíle, **modré jiskry z hran trupu** ve skoku (zvenku), **modrá záře pod přídí** z kokpitu,
  doplňování quantum paliva.
