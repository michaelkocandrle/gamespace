# Verdikt: FAIL

První dojem: Pět listů ve schváleném stylu E-01, data v nich z velké většiny sedí, ale koncové pohledy mají záblesk ploutve na ose trupu místo na ploutvi a dva z pěti detailů E-07 jsou jen zvětšené obálky bez kót a bez obsahu.

| Kategorie | Skóre | Proč |
|---|---|---|
| 1. Čitelnost | 6 | Písmo, šrafy a tečky jsou ostré, ale svazky 4–12 odkazů do jedné svislice (E-05 střed, E-06 B oba rohy) a červené kříže kreslené přes nové modré prvky na témže místě se nedají rozplést. |
| 2. Úplnost | 6 | Všech šest pohledů i pět detailů existuje a každý list vypisuje svá ID, ale E-07 nemá jedinou kótu, detaily D a E neukazují nic navíc proti 1:30, rám rampy chybí a legenda slíbená v poznámce na E-05/E-06 není. |
| 3. Soulad s daty | 7 | Přes dvacet kontrolovaných prvků (RCS plán 8 ks, desky P-B ×, podvozek, písty, nápisy, změny Δ) sedí na ±0,1 m; nesedí L-STROBE-FIN na obou koncových pohledech, obsah detailu D a skrytý popisek P-S-K04. |
| 4. Konvence | 7 | Orientace všech pohledů podle třetího úhlu, razítko, měřítko, skryté hrany čárkovaně a seznam listů v pořádku; kóta 21,50 leží přes číslici měřítka, detaily bez kót, dvě měřítka čel na jednom listu bez důvodu. |
| 5. Návrh povrchu | 6 | Boky (E-06) navazují na E-01 jedna ku jedné a břicho drží gunmetal koncept C, ale hřbet je od x 3 po kabinu holý gunmetal s třemi osiřelými krémovými záplatami, bez pásu desek i bez slíbených rozvodů. |
| 6. Srozumitelnost pro autora | 6 | České poznámky a stavové barvy jsou jasné, ale u prvků Δ není z listu vidět, co se mění (F-RCS-01 Δ je modrý blok a nic víc), a 90 svislých odkazů přes gondoly a křídla nutí hledat, u které tečky odkaz končí. |

Průměr: 6,3

## Musí se opravit

1. **E-05, výřezy 11 a 13 (zezadu i zepředu), vrchol trupu na ose** – `L-STROBE-FIN +` je nakreslen hvězdičkou a odkazem na ose trupu (y = 0, z 3,3). Podle návrhu je světlo `on: fin_tip` (x 1,6, z 3,3) a ploutev sedí na gondole (čelní obrys ploutve špička y 3,56–3,81). Na E-06 i E-07 F je správně na špičce ploutve. – Na obou koncových pohledech hvězdičku i odkaz posunout na špičky ploutví (y ≈ ±3,7, z 3,3, obě kopie); nepopsané modré obdélníčky na špičkách ploutví popsat jako pouzdro XK-STROBE, nebo odstranit.
2. **E-07, detail D (23) a detail E (25)** – detaily bez obsahu a bez kót. D je jeden šedý T-blok s jediným popiskem `F-GEAR-MAIN`, přestože data stavby popisují nohu jako tlumič, nůžky, vzpěru, hydrauliku, dvířka s pruhem a patku (hs.json `gear._comment`); poznámka slibuje „nápisy u šachty“, ale žádný D-H na výřezu není. E je pruh zbraně se třemi objímkami – nic o tom, jak objímky drží zbraň u křídla, chybí značka konce křídla `D-H-47`. Na žádném detailu E-07 není jediná kóta. – Detail má přinést, co 1:30 neumí: dílčí prvky a kóty. Co to nepřinese, vypustit.

## Mělo by se opravit

1. **E-03, záď trupu** – tmavá zóna záďového krytu je v půdorysu trojúhelník s diagonálou; podle dat jsou `Z-B-02` (x 0–3, z > 2,2) i `P-B-01` (x 0,1–2,9, `centre`) přes celou šířku. – Ověřit kreslení zóny; je-li diagonála záměr (promítnutí sklonu zádi), napsat to do poznámky.
2. **E-05, výřez 11, horní střed** – čtyři odkazy (`P-HULL Δ`, `D-T-05`, `L-RAMP +`, `L-STROBE-FIN +`) sbíhají do jedné svislice. – Rozvést do samostatných svislic.
3. **E-06 B, výřezy 18 a 19** – svazky 8–12 šikmých odkazů přes sebe; červené kříže `F-RCS-05 ×`, `G-VT-03 ×` přes novou mřížku `F-GRILLE-02 +`, `F-GRILLE-01 +` vypadá jako odstraněný. – Starý díl kreslit tenkým obrysem s malým křížem v rohu.
4. **E-03, celý hřbet** – od x ≈ 3 po kabinu holý gunmetal rám s osiřelými krémovými deskami P-B-04/16/17. – Doplnit pás desek hřbetu, nebo rozhodnout a do poznámky napsat, že hřbet je záměrně holý.
5. **E-05 a E-06, poznámka 1** – tvrdí „legenda … zde zopakovaná“, legenda tam není. – Doplnit legendu, nebo opravit poznámku.
6. **E-07 detail C a E-05, rampa** – zadání žádá „rampu s písty a rámem“; rám rampy není v datech ani na výkresu. – Doplnit prvek rámu s ID a kitem, nebo v poznámce říct, co je rám.
7. **E-04, výřez 07** – `P-S-K04` je v JSON „labelled“, ale popisek není vidět (pod blokem hlavního podvozku). – Popisek vedle s odkazem.
8. **E-06 A** – desky P-S s popiskem v ploše bez „+“, odkazy u skrytých desek s „+“. – „+“ všude, nebo nikde.

## Drobnosti

1. E-03 a E-04 – text kóty „21,50 …“ leží přes číslici „10“ měřítka.
2. E-05 – zezadu 1:20 a zepředu 1:30 na jednom listu, dolní polovina listu prázdná; obě čela by se vešla v 1:20.
3. E-07 detail F – název „Gondola s tryskou shora“, ale tryska shora vidět není; přejmenovat na „Gondola shora“.
4. Nápisy jako jména textur – „Hazard_Ramp“, „Hazard_Exhaust“; nahradit obsahem nebo ID.
5. E-06 B – kříže `G-VT-01/02 ×` přes nápis „Wayfarer“ – zmenšit.
6. E-03 – odkazy `D-H-21`, `D-H-23` procházejí obdélníky s tečkou, než skončí; koncovou tečku zvýraznit.

## Namátková kontrola dat (výběr)

Sedí: F-RCS-13 +, F-RCS-12 Δ, F-RCS-07 ×, F-RCS-03 ×, F-RCS-10/11 ×, F-RCS-04/08 ×, plán RCS celkem 8 = spec, L-STROBE-WING +,
L-LANDING +, F-GEAR-NOSE, F-RAMP-PISTON +, P-B-07/08/09, D-H-54, D-H-57 Δ, F-CONN-01 Δ a D-H-58 Δ, G-VT-01/02 ×,
F-RCS-09/06 ×, Z-B-03 Δ, P-B-02/03/14/15 ×, P-B-05/06/18 a G-HTL-02, F-FIN Δ, L-MARKER-HULL a L-TAIL, G-POD-VT-01 a D-T-01,
tabulka nápisů levoboku.
Nesedí: L-STROBE-FIN (E-05 na ose), obsah detailu D, P-S-K04 (popisek není vidět), D-H-47 v detailu E; obdélník
D-LOGO-L v nové poloze na E-06 B nenalezen.
