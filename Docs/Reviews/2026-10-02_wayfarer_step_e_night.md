# Wayfarer – krok e: noc a červené poziční světlo (analýza), 2. 10. 2026

Jen analýza (zadání autora 1. 10.), nic se neopravuje. Podnět: kritik kola 1 bod 4 a kola 4 bod 3 (`2026-10-01_wayfarer_kit_pilot.md`).
Preset `Tools/Shots/wayfarer_night_analysis.json`, snímky `shots:20261002_222005_wayfarer_night_analysis/` a
`shots:20261002_222255_wayfarer_night_analysis/` (editor, 1920 × 1080). Měřen průměrný jas středu záběru zádě
(30–80 % výšky, 30–70 % šířky, lineární jas 0–1 ze sRGB).

## 1. Proč se trup v noci neztmaví

| Snímek (stejná kamera na záď) | Jas středu |
|---|---:|
| den (slunce 33° nad obzorem) | 0,505 |
| noc podle presetu (slunce 10° **pod** obzorem lodi, obloha 0,03) | 0,451 |
| noc, slunce vypnuté (`space.Sun Intensity 0`) | 0,004 |
| noc, slunce i obloha vypnuté | 0,004 |
| totéž a navíc bez Lumen GI | 0,003 |
| noc a `bPerPixelAtmosphereTransmittance` slunce zapnuté | 0,452 |

![zdroje světla v noci](2026-10-02_wayfarer_step_e_night/night_sources.jpg)

**Příčina: slunce pod obzorem dál svítí na loď skoro plnou silou (89 % denního jasu).** Obloha, GI ani světla lodi
v tom roli nehrají: bez slunce je záď černá (0,004).
- Směrové světlo nic nezastíní, protože planeta (Veyra, poloměr 120 km) nevrhá stín na loď 3 km nad sebou. Kaskádové
  stíny pokrývají jen okolí kamery.
- Atmosféra (`atmosphere_sun_light`) ztlumí slunce podle propustnosti, kterou UE počítá pro jeden referenční bod
  „vrchol planety“. Loď ale stojí na straně −X planety (její „nahoru“ je −X světa), takže slunce pod obzorem lodi je
  pro ten bod vysoko nad obzorem. Obloha se přitom vykreslí správně tmavá, protože se počítá z pohledu kamery.
- Per-pixel propustnost slunce (`bPerPixelAtmosphereTransmittance`) nic nezměnila (0,452), přepínač světla tedy
  nestačí.

**Návrh opravy (k rozhodnutí autora):** „stín planety“ v C++. Sílu slunce násobit podle výšky slunce nad obzorem
v místě kamery (normála planety z `USpaceCelestialRegistrySubsystem`, `FindNearest`): plná síla nad +3°, plynulý
přechod do nuly do −2°, k tomu zabarvení soumraku. Úprava má desítky řádků, běží jednou za snímek a platí pro všechny
planety a místa. Bez ní je noc na planetě jen tmavá obloha nad lodí osvětlenou jako ve dne. Ověření: tento preset,
střed v noci pod 0,05.

Druhé zjištění: když slunce nesvítí, světla lodi trup skoro neosvětlí (0,004 se zapnutými světly lodi). Pracovní
světlo nad rampou je vidět jen jako bod a nedělá kužel na rampě (kritik kola 4 bod 3). Po opravě noci je potřeba
světla lodi vyladit: pracovní světlo jako bodové světlo (spot) s viditelnou stopou.

## 2. Přepálené červené poziční světlo

![noc](2026-10-02_wayfarer_step_e_night/red_night.jpg)
![den](2026-10-02_wayfarer_step_e_night/red_day.jpg)

Červené světlo `nav_L` (pravobok gondoly vpředu, x 5,0 m) je bodové světlo **3 cd s dosahem 1 m** a čočka svítí
emisí 25 (`MI_Ship_Wayfarer_LightRed`). Scéna je ale kalibrovaná na slunce 11 lx a pevnou expozici EV100 3
(`build_space_scene.py`). Pro srovnání: 3 cd ve vzdálenosti 1 m dají 3 lx, tedy zhruba čtvrtinu osvětlení od slunce.
Proto světlo dělá ve dne na křídle a spodku gondoly sytou červenou skvrnu a v noci velkou červenou louži s odleskem.
Čočka sama je malá a v pořádku. Přepaluje se osvětlení okolí, ne čočka.

**Návrh opravy:** bodové světlo navigačních světel (červené i zelené) snížit asi 10× (0,3 cd) a dosah na 0,6 m;
čočku nechat. Měřítko pro všechna světla lodi: intenzita v cd ≈ skutečná intenzita × 11 / 100 000 (poměr slunce
hry ke skutečnému), u svítidel trupu pak doladit podle snímku. Je to levná změna dat (`hs_lights`, `Wayfarer_lights.json`).

## 3. Vedlejší nález

V noci je na tmavém laku gondoly zrnitý šum (jiskření, `red_night.jpg` vpravo). Je to šum Lumenu při velmi
nízkém osvětlení. Po opravě noci ověřit znovu. Pokud zůstane, patří k odloženým odrazům Lumenu (optimalizace na konec).

## Rozhodnutí autora
- Stín planety v C++ (bod 1): ano / ne.
- Navigační světla 10× slabší (bod 2): ano / ne.
