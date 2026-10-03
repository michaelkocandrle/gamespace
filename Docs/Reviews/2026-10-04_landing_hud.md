# Recenze: stavový rámeček přistání na HUD (SC-3), 4. 10. 2026

Listy: `Docs/Reviews/2026-10-04_landing_hud/` (brief, 4 listy). Práh `step`. Reference: snímky ze SC videa
(`starcitizenreference/Landing_VideoNotes.md`). Snímky kola 1 `shots:20261004_011931_landing_hud`, kola 2
`shots:20261004_012400_landing_hud`.

## Kolo 1 – FAIL, průměr 5,4

Skóre: silueta 6, hierarchie 5, materiály 6, decaly 5, světlo 5, čitelnost 4, geometrie 6, styl 6.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Písmo jako nejmenší popisky HUD | musí | opraveno: 13 → 22 px, rámeček 300 × 38 |
| 2 | Nízký kontrast proti obloze a trupu | musí | opraveno: tmavá krytá výplň, text v barvě stavu (azurová / jantarová) |
| 3 | Rámeček odtržený od HUD u výzvy [F], na hraně desky | musí | opraveno: přesun nad pásku kurzu, kde má SC stavová hlášení |
| 4 | V chase kameře přes trup | doporučeno | opraveno přesunem (nad loď) |
| 5 | Chybí koncové lišty | doporučeno | neplatné: lišty kreslí `StatusBox` odjakživa, byly jen tenké; v kole 2 je kritik vidí |
| 6 | TOUCHDOWN bez ukazatele průběhu | doporučeno | opraveno: lišta průběhu u spodní hrany (`USpaceHudSymbol::Progress`) |
| 7 | Kalná olivová jantarová | doporučeno | opraveno: výplň už není tónovaná barvou textu, čistší `LandingAmber` |

## Kolo 2 – PASS, průměr 6,75

Skóre: silueta 7, hierarchie 7, materiály 6, decaly 7, světlo 6, čitelnost 8, geometrie 7, styl 6.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Varování bez barevného obrysu, koncové lišty tyrkysové | doporučeno | lišty jsou jantarové (`evidence/r2_01_end_bars_amber.jpg`); jantarová výplň neopravena, kosmetika na později |
| 2 | Výplň příliš krytá a šedá | doporučeno | neopraveno: krytí zvoleno kvůli výtce 2 z kola 1 (čitelnost proti obloze); ladit se zbytkem HUD |
| 3 | FREE LOOK v jiném stylu | doporučeno | mimo rozsah: FREE LOOK kreslí textový debug HUD; sjednotí se s jeho náhradou |
| 4 | Text bez záře | doporučeno | neopraveno: ostatní texty HUD mají stejné písmo bez bloomu; záře celého HUD je samostatné téma |
| 5 | Umístění neodpovídá briefu | doporučeno | brief psán před přesunem (výtka 3 kola 1); umístění odpovídá SC |

Kola: 2 z 3. Po kole 2 se nic neměnilo, ověřovací kolo nebylo potřeba.
