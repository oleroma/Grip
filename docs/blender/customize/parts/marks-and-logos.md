# Marks and logos

There are two kinds of lettering on the parts:

- **marks**: small identification letters on button shafts, triggers and bumpers, probably meant to tell printed variants apart;
- **logos**: the symbols engraved on the ABXY caps and the Home cap.

## Marks

| Parts | Switched by |
|---|---|
| button shafts, triggers | global `marks` (off as saved) |
| bumpers | the `marks` input on the `L1`/`R1` modifier (on as saved) |

What is written is set on the `marks parameters` node in each part's preset:

| `type` | What is printed |
|---|---|
| `custom` | a letter: `R` or `L` for left and right parts when `L-R side` is on, otherwise a fixed letter (`T`) |
| `parameter` | the values named in `parameters`, for example the tolerance the part was made with, with `Decimals` digits |
| `curve` | the Grip logo curves |

The other inputs place and size the text: `font size`, `bump` (raised height), `mark depth` (engraving depth), `insertion`, and `translate`, `rotate`, `axis`, `side` for which face it goes on.

**To label tolerance variants**, set `type` to `parameter`. The `parameters` field on each part already names the right values (`button tolerance`, `trigger x tolerance, button press tolerance`, …). The `custom` letter does not change with the tolerance, so as saved every part prints `T` whatever tolerance it was exported with.

## Logos

The ABXY caps and the Home cap have a second modifier, `logo`, that engraves curves from a collection: `abxy logo up`, `abxy logo down`, `abxy logo left`, `abxy logo right` and `home logo` in the `source` scene. **To change a symbol, edit or replace the curves in that collection.** The global `button logo` turns all logos off. `depth` and `bump` set how deep the symbol is engraved.

The `logo` modifiers on the button shafts are disabled or have no font set; they do nothing.

## Fonts

All text uses Windows system fonts (marks use Segoe UI Bold). On macOS or Linux the marks are silently left out. The logos are curves, so they always work. Packing the fonts into the file (File › External Data › Pack Resources) would fix this.
