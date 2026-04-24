# Level System

## XSB format

XSB is a plain-text format where each character represents one grid cell.

| Char | Meaning |
|------|---------|
| `#`  | Wall |
| ` `  | Floor (space) |
| `@`  | Player |
| `+`  | Player on goal |
| `$`  | Box |
| `*`  | Box on goal |
| `.`  | Goal |

Rules:
- Each level must contain exactly one player (`@` or `+`).
- Number of boxes must equal number of goals.
- Rows may differ in length — short rows are padded with floor on the right.
- Lines outside the wall border are treated as out-of-bounds (not rendered as floor).

## .sok file structure

A `.sok` file contains multiple levels separated by blank lines. Each level may optionally be preceded by a metadata header:

```
; comment line (ignored)
Title: Level name
Author: Author name

#####
# @ #
#$. #
#####

Title: Next level
...
```

- Lines starting with `;` are comments — skip entirely.
- `Title:` and `Author:` metadata lines precede the grid.
- A blank line signals the end of a level's grid rows.
- A line that starts with `#` or contains XSB characters is a grid row.

## Level sets

Both files live in `src/levels/` and are imported in JS via Vite's `?raw` import:

```js
import xsokobanRaw from "./levels/xsokoban.sok?raw";
import microbanRaw from "./levels/microban.sok?raw";
```

### XSokoban (`xsokoban.sok`)
- 90 puzzles, the quasi-standard benchmark set.
- Referenced as [Mye01] in the Virkkala thesis.
- Used for solver benchmarking (Phases 3–6).

### Microban (`microban.sok`)
- 155 small puzzles by David Skinner.
- Easier and smaller than XSokoban — good for rapid solver testing.
- Used as the primary test set during Phase 3 baseline.

## Parser contract (`src/engine/parser.js`)

### Input
Raw string from a `?raw` import of a `.sok` file.

### Output
Array of `Level` objects:

```js
{
  title: string,        // from "Title:" header, or "" if absent
  author: string,       // from "Author:" header, or "" if absent
  width: number,        // max row length across all grid rows
  height: number,       // number of grid rows
  grid: string[],       // raw grid rows, length-normalized to `width`
}
```

### Parsing steps
1. Split file into lines.
2. Accumulate metadata (`Title:`, `Author:`) until the first grid row appears.
3. Accumulate grid rows until a blank line (or EOF) is reached.
4. Normalize row lengths: pad shorter rows with spaces to match `width`.
5. Emit a `Level` object; reset state and repeat.

### Validation (parser should throw on)
- No player found in grid.
- Box count ≠ goal count.
- Empty file or no valid levels parsed.

### Notes
- The parser does not convert the grid to a numeric representation — that is `state.js`'s responsibility.
- Rows containing only spaces (empty floor rows) are valid grid rows; do not treat them as separators.