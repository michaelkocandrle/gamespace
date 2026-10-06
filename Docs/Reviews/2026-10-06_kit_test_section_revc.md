# KF-PORTAL-01 – list rev. C a kalibrace světla zkušebního úseku (6. 10. 2026)

**Stav:** STOP. Autor posoudí výřezy rev. C, tabulku jasu a 4 listy. Blockout (krok 4) až potom.

**Proč:** autor schválil krok 3 (materiálový základ). Zbylé rozdíly proti SC jsou v návrhu a světle, proto návrat
do kroku 2 (list rev. C) a kalibrace světla. Kritik nespouštěn (hodnotí až díl v kroku 8).

## List rev. C

`ArtSource/Kit/Design/KF-PORTAL-01.png`, změněné výřezy `_01_pohled`, `_02_rez`, `_03_profil`, `_04_podlaha`,
`_05_napojeni` (patka). Data jsou v `KF-PORTAL-01.json` (`revisions`, `boot`, `floor.lip_network`).

1. **Rám je jeden plný tvar v jednom laku**, stupně 40 / 70 / 100 mm bez spár, čitelné jen stínem a odleskem.
   - Leštěný lem je jen na hraně koruny: perlička 12 × 12 mm, jedna světlá linka z každé strany.
   - Pryžová manžeta (80 mm, žebra 7 / 15) je na vnitřní straně koruny, tedy na ploše do průchodu.
2. **Patka L1 je osmiboká bota** kolem paty pilíře a vrůstá do podlahy.
   - Rozměry 300 × 170 × 230 mm, ke chodbě zkosená 60 mm, nahoře zkosení 45° do pilíře.
   - Světlo je ve štěrbině 60 × 20 mm, zapuštěné 25 mm. Zdroj Ø12 mm míří 30° dolů na podlahu a lem.
   - Z oka je vidět jen jako malý jasný bod.
   - Nakresleno v pohledu (1), řezu podél chodby (2), půdorysu (4) a v řezu boty 1:5 (5).
3. **Podlaha je souvislá síť leštěného lemu 18 mm** přes chodník, rohové trojúhelníky u zkosení, boční desky,
   příčný pás i práh pod portálem. Pole jsou 6 mm pod sítí. Půdorys teď ukazuje dvě rozteče 1,2 m (výchozí).

**Hrubá geometrie zkušebního úseku** je podle rev. C (`Tools/Kit/kit_factory.py`).
- Rám se staví bez zkosení, takže mezi stupni nejsou spáry; otěr hran přijde až s dílem.
- Bota se štěrbinou a bodem zdroje, práh v síti lemu.
- L1 je teď bodový reflektor ze štěrbiny (30° dolů ven), aby nesvítil na vlastní botu.

## Kalibrace světla

**Měření:** `Tools/Shots/measure_look.py` (nově podíl tmavých < 0,08 a světlých > 0,45 pixelů, `--all` pro složku
referencí). Kotevní záběry SC proti našim snímkům ze stejných úhlů.

| Úhel | | průměr | p10 | medián | p90 | tmavé | světlé |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 z oka do hloubky | SC `ram_portal_1` | 0,24 | 0,13 | 0,22 | 0,37 | 1 % | 4 % |
| | před (rev. B, L2 40 / L3 25 cd) | 0,31 | 0,07 | 0,26 | 0,70 | 12 % | 20 % |
| | **po** | **0,19** | 0,03 | **0,14** | **0,49** | 26 % | **11 %** |
| 2 pata pilíře | SC `ram_portal_2` | 0,28 | 0,14 | 0,26 | 0,42 | 1 % | 7 % |
| | před | 0,35 | 0,12 | 0,32 | 0,58 | 7 % | 31 % |
| | **po** | **0,25** | 0,06 | **0,22** | **0,42** | 12 % | **8 %** |
| 3 podlaha 35° | SC `podlaha_1` | 0,28 | 0,19 | 0,25 | 0,40 | 0 % | 6 % |
| | před | 0,33 | 0,11 | 0,27 | 0,60 | 6 % | 27 % |
| | **po** | **0,23** | 0,06 | **0,17** | **0,44** | 17 % | **8 %** |
| 4 lak a tmavá třetina | SC `ram_portal_3` | 0,23 | 0,13 | 0,19 | 0,37 | 1 % | 6 % |
| | před | 0,32 | 0,16 | 0,28 | 0,69 | 4 % | 15 % |
| | **po** | **0,21** | 0,06 | **0,16** | 0,55 | 25 % | **11 %** |

- **Před** = snímky schváleného kroku 3: `shots:20261006_192907_kit_test_section`.
- **Po** = `shots:20261006_200718_kit_test_section`.

**Kola kalibrace:**

| Kolo | L1 | L2 | L3 | Grafit | Výsledek |
|---|---|---|---|---|---|
| 1 (geometrie rev. C) | bod 2,5 cd | 40 cd | 25 cd | 0,07 | světlé 19–33 %; L1 jako bod svítil na vlastní botu |
| 2 | reflektor 4 cd ze štěrbiny | 14 cd | 6 cd | 0,07 | příliš tmavé: tmavé 40–47 %, průměr 0,14 |
| 3 | 4 cd | 24 cd / 100° | 10 cd | 0,095 | podlaha světle šedá, světlé 29–34 % |
| 4 = stav | **4 cd** | **18 cd / 100°** | **8 cd** | **0,06** | tabulka „po“ |

**Splněno:**
- Průměr, medián a p90 jsou v rozsahu etalonu nebo těsně pod ním.
- Světlé plochy klesly z 15–31 % na 8–11 % (SC 4–7 %).
- Strop je tmavší než stěny.
- Jas dělají ostrůvky pod botami a linky lemu.
- Lak rámu jsem neměnil (autor).

**Zbývá:** tmavé plochy jsou 12–26 % proti 1 % v SC; SC nemá skoro nic černého (p10 0,13 proti našim 0,03–0,06).
- Část dělá tónová křivka SC (zvednuté černé, opar), část naše černé plochy: manžeta, konec chodby, stíny u stropu.
- Další zesílení světla tuhle mezeru nezavřelo: kolo 3 přidalo světlé plochy, tmavé nevyrovnalo, protože se k tomu
  přidává automatická expozice.
- Návrh na další krok: lehce zvednout černé v tónové křivce interiéru, nebo dát úseku opar podle SC. Až po
  autorově posouzení.

**Grafit Halcyonu** je teď 0,06 (dřív 0,07). Ve hře ho zatím žádný díl nepoužívá, týká se jen dílů továrny.

## Listy

Složka `2026-10-06_kit_test_section_revc/`: `sheet_00_etalon.jpg` a `sheet_01` až `sheet_04`, stejné úhly jako
v kroku 3 (FOV 90, 2560 × 1440).
