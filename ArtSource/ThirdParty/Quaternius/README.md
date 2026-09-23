# Quaternius — Modular Sci-Fi MegaKit (Standard / free)

**Licence: CC0 1.0 Universal** (public domain, bez povinné atribuce) — potvrzeno v
`License_Standard.txt` uvnitř archivu, 23. 9. 2026. Autor: @Quaternius, https://quaternius.com.

Zip sám **není v gitu** (48 MB třetí strany, volně stažitelné). V repozitáři je jen tenhle README
a později ty konkrétní modely, které skutečně použijeme.

## Jak ho získat znovu

1. https://quaternius.itch.io/modular-sci-fi-megakit
2. „Download Now“ → „No thanks, just take me to the downloads“ → „Download“
   (itch.io generuje podepsanou URL platnou 60 s, přímý odkaz proto nejde uložit)
3. Ulož jako `ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip`

## Co v něm je (volná Standard verze)

1 195 souborů, 190 modelů v glTF (a totéž v FBX a OBJ), textury v PNG:

| Kategorie | Kusů | Co z toho |
| --- | --- | --- |
| Walls | 84 | stěnové panely, rohy, pásy — chodby a přepážky |
| Platforms | 38 | podlahy, rampy, zábradlí, **dveře a zárubně** |
| Decals | 29 | nálepky, šipky, značení |
| Props | 28 | **ventilace** (3 velikosti), kabely, rošty, bedny, terminál, světla, madla |
| Columns | 8 | nosníky, sloupy s potrubím |
| Aliens | 3 | mimo náš žánr, nepoužívat |

**Placená PRO/SOURCE verze** má modelů víc; Standard je jen výběr. Zatím nekupovat, dokud
nenarazíme na konkrétní chybějící kus.

## K čemu se hodí u Steadfastu

Chodby, nákladový prostor, strojovna — tedy všechno, co je „prostředí“. **Kokpit z toho
nepostavíme**: kit nemá dashboardy, sedačky pilota ani panely s přepínači. Ty zůstávají
procedurální (přesný technický detail) podle `Docs/AssetPipeline_Modular.md`.

## Měřítko: kit je stavěný na 4m grid (zjištěno 23. 9. 2026)

Naměřeno po importu do Blenderu:

| Díl | Nativní rozměr |
| --- | --- |
| `ShortWall_*_Straight` | 4,0 × 2,0 m (plochý quad, detail je v textuře) |
| `Platform_Metal` | 4,0 × 4,0 m |
| `Door_Frame_Square` | 4,85 × 5,0 m |
| `Column_Pipes` | 5,0 m vysoký |
| `Prop_Crate4` | 1,12 m |
| `Prop_Computer` | 1,59 m |
| `Prop_Vent_Wide` | 1,94 m |

**Architektura je pro prochozí základnu, ne pro loď.** Pro Steadfast (30 m dlouhý, 9,5 m vysoký)
se stěny, podlahy a dveře škálují **×0,5** — pak vyjde chodba 2 m široká se stropem ve 2 m,
což je na loď správně. **Propy (bedny, ventilace, terminál, kabely) se nechávají 1:1**, ty mají
reálnou velikost rovnou.

Zkouška chodby: 8 m chodby = **5 727 trojúhelníků** i s podlahou, stropem a propy, což je na
interiér lodi velmi levné. Render `Saved/Kitbash/steadfast_corridor.png`.

**Pozor na textury:** glTF soubory odkazují textury holým jménem, ale ty leží ve sdílené složce
`Textures/`. Před importem je nutné je nakopírovat vedle modelů, jinak Blender importuje materiály
bez textur (všechno růžové).
