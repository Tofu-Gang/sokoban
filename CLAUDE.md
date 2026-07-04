# Sokoban — Claude Code Guide

## Project overview

A browser-based Sokoban game with a built-in solver. No backend. Pure client-side React app.

## Tech stack

- React 19 + Vite 8 + Tailwind CSS 4
- Web Workers for the solver (keeps UI responsive)
- Vite `?raw` imports for `.sok` level files
- Additional libraries: none yet — add here as introduced

## Commands

```bash
npm run dev       # start dev server (localhost:5173)
npm run build     # production build
npm run lint      # ESLint
npm run preview   # preview production build
```

## Directory structure

```
src/
  assets/           # Tile images (see Tile assets section)
  levels/           # Phase 1 — .sok level files (XSB format), imported via ?raw
  engine/           # Pure JS, zero React, fully testable
    parser.js       # Phase 1 — Parse .sok files → Level[]
    state.js        # Phase 2 — GameState: Uint8Array grid + player pos + box Set<number>
    moves.js        # Phase 2 — Move validation, push execution, reachability BFS
    deadlock.js     # Phase 4 — Dead-square precomputation (once per level load) + per-node freeze deadlock check
  solver/
    worker.js       # Phase 3 — Web Worker entry — receives state, posts results
    bfs.js          # Phase 3 — BFS over push-state space with transposition table
    iddfs.js        # Phase 5 — IDDFS (lower memory, better for deep levels)
    heuristic.js    # Phase 5 — Lower-bound: min matching of boxes to goals
    pi-corral.js    # Phase 5 — PI-corral pruning — see docs/pi-corral.md
  components/
    LevelSelect.jsx   # Phase 1
    GameBoard.jsx     # Phase 2 — CSS grid + tile <img> elements
    GameControls.jsx  # Phase 2 — Undo, reset, move counter
    SolverPanel.jsx   # Phase 3 — Algorithm selector, start/stop, progress, playback
  hooks/
    useGame.js      # Phase 2 — useReducer: MOVE, UNDO, RESET, LOAD_LEVEL
    useSolver.js    # Phase 3 — Worker lifecycle, solution receipt, playback
    useSwipe.js     # Phase 6 — Touch swipe detection for mobile controls
  App.jsx           # Phase 1
  main.jsx          # Phase 1
  index.css         # Phase 1
docs/               # Algorithm and format reference docs
```

## Implementation phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Level system — parser, .sok files, LevelSelect | not started |
| 2 | Playable game — state, moves, GameBoard, useGame | not started |
| 3 | Solver baseline — BFS in Web Worker, useSolver | not started |
| 4 | Static deadlock detection | not started |
| 5 | IDA* with heuristic + PI-corral pruning | not started |
| 6 | Touch/swipe controls | not started |

Update the Status column as phases complete.

## Level format (XSB)

Plain text, one character per cell:

| Char | Meaning |
|------|---------|
| `#`  | Wall |
| ` `  | Floor |
| `@`  | Player |
| `+`  | Player on goal |
| `$`  | Box |
| `*`  | Box on goal |
| `.`  | Goal |

Level sets bundled in `src/levels/`:
- `xsokoban.sok` — 90 puzzles (standard benchmark)
- `microban.sok` — 155 small puzzles by David Skinner (easier, good for solver testing)

## Tile assets

All tiles are in `src/assets/`. Mapping from XSB cell type to filename:

| Cell | File |
|------|------|
| Wall | `wall.png` |
| Floor | `floor.png` |
| Player | `player.png` |
| Player on goal | `player-on-goal.png` |
| Box | `box.png` |
| Box on goal | `box-on-goal.png` |
| Goal | `goal.png` |
| Out of bounds / background | `background.png` |

## Key design decisions

- **Solver in Web Worker** — solver can run for minutes; blocking the main thread is not acceptable.
- **State as `Uint8Array` + `Set<number>`** — fast to copy, compact, serializable across the Worker boundary.
- **Push-space search** — exponentially smaller than move-space; player routing is a sub-problem solved by BFS.
- **Canonical state = sorted box positions + player reachable region** — avoids re-exploring equivalent positions.
- **Static dead squares precomputed at load** — free pruning with zero per-node cost.
- **XSB text format + Vite `?raw` import** — standard, human-readable, no custom binary format needed.

## Responsivity and mobile

- **Responsive layout** is a continuous requirement — build all components with fluid sizing from the start, never hardcode pixel dimensions.
- **Touch/swipe controls** are added after Phase 2 (once the game is playable). Swipe direction is detected via `touchstart`/`touchend` delta — no drag library needed since no element physically follows the finger. Implemented in a small `useSwipe.js` hook alongside the keyboard handler.

## Out of scope

- No backend, server, or database
- No level editor
- No multiplayer or leaderboard

## Reference

`docs/Timo-Virkkala-Solving-Sokoban-Masters-Thesis.pdf` — primary algorithmic reference for the solver.