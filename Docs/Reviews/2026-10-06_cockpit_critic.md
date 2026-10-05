# Kokpit a holo MFD v3: kritik (5.–6. 10. 2026, práh step)

Hodnocené kategorie:
1. holo vzhled a čitelnost MFD;
2. rozvržení a písmo proti SC;
3. křeslo;
4. konzole, středový sloupek, klávesy a středové displeje;
5. panel dveří a hasicí přístroj;
6. celková soudržnost.

| Kolo | 1 | 2 | 3 | 4 | 5 | 6 | Průměr | Verdikt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6,0 | 5,5 | 6,5 | 4,5 | 5,5 | 5,5 | 5,58 | FAIL |
| 2 | 6,0 | 5,5 | 6,5 | 5,5 | 6,5 | 6,0 | 6,0 | FAIL |
| 3 | 6,0 | 6,5 | 6,5 | 5,5 | 6,5 | 6,0 | 6,17 | FAIL (bez bodů „musí se opravit“) |

Snímky jednotlivých kol:
- **Kolo 1:** `shots:20261005_232951_mfd_pages`, `shots:20261005_191320_cockpit_audit`, `shots:20261005_195945_doors`
- **Kolo 2:** `shots:20261005_233811_mfd_pages`, `shots:20261005_233833_cockpit_audit`, `shots:20261005_233906_doors`
- **Kolo 3:** `shots:20261005_235539_mfd_pages`, `shots:20261005_235601_cockpit_audit`, `shots:20261005_235634_doors`, `shots:20261005_235731_extinguisher`

## Body „musí se opravit“ a reakce

| Bod | Reakce | Stav |
| --- | --- | --- |
| NAVIGATION: popisky daleko od hodnot, KETH v liště, hodnoty o řádek vedle | Kompaktní blok SPEED / LIMIT / QUANTUM vpravo, seznam bez hlavičky, pevné linky (`c795871b`) | vyřešeno v kole 3 |
| Popisky záložek useknuté | Záložky 48 px (`3e7f71cd`) | vyřešeno |
| Oranžová lišta kokpitu za daty | `HoloSmoke` 0,3 → 0,46 → 0,6 | přeřazeno na „měl by se opravit“, pořád prosvítá |
| Pastelová tlačítka na sloupku | Tmavé podsvícené klávesy (`f3df1e32`) | vyřešeno |
| Text panelu dveří a překryv nápisu | TAP TO OPEN / CLOSE, panel níž a blíž dveřím | vyřešeno |

## Otevřené body „měl by se opravit“ (do dalšího kroku)

- **Horní plochy konzolí** jsou z kamer pořád moc holé:
  - nové moduly ve vnější polovině nejsou na snímcích vidět;
  - plochu před HOTAS je potřeba dál rozbít;
  - do sady snímků přidat záběr modulů.
- **Šedá deska s „mlhavou“ texturou** nahoře vlevo v `cockpit_audit/05`.
- **Středové displeje RADAR / SELF STATUS** jsou malé a mají zrnité pozadí. Zvětšit je, nebo dát čisté tmavé pozadí.
- **Drátěný model lodi na SELF STATUS** je tenká hrubá kresba.
- **Oranžová lišta za holo daty** dál prosvítá.
- **Ikona zámku u CLOSED** na panelu dveří čte jako „zamčeno“. Nahradit ikonou dveří nebo šipek.
- **Drobnosti:**
  - na hasicím přístroji štítek a záběr i se dnem;
  - textura na madle dveří;
  - tloušťka popruhů křesla.
