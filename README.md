# TFWR — The Farmer Was Replaced automation

Scripts from my `Save0` save of [The Farmer Was Replaced](https://store.steampowered.com/app/2060160/The_Farmer_Was_Replaced/).
The game has you program a drone in a Python-like language. This repo holds a
fully automated farm that runs forever: it buys upgrades, keeps Gold and Bone
stocked, and cycles through every crop across the whole field using parallel
drones. It also includes benchmark and simulation scripts used to tune it.

> **Language note:** the in-game language only *looks* like Python. There are no
> classes, no real imports beyond other save files, and only the game's
> builtins are available. `__builtins__.py` (not tracked) is a community-made
> set of type stubs so VS Code can autocomplete. It is never executed.

---

## Quick start

1. Open the save in game (the files in this folder are the in-game code windows).
2. Run **`main`**. It loops forever.
3. To change behaviour, edit [`farm_config.py`](farm_config.py) first. Most
   tuning knobs live there.

This folder **is** the live save. Checking out a git branch changes the code
the game loads, so switch back to `main` before playing normally.

---

## How the main loop works

[`main.py`](main.py) repeats four steps:

| Step | Module | What it does |
|---|---|---|
| 1 | [`farm_unlocks`](farm_unlocks.py) | Spends only **surplus** resources on upgrades, in priority order |
| 2 | [`farm_maze`](farm_maze.py) | If Gold < `gold_floor`, tiles the field with small mazes (one per drone) until it's reached |
| 3 | [`farm_dinosaurs`](farm_dinosaurs.py) | If Bone < `bone_floor`, runs a dinosaur snake run |
| 4 | [`farm_rotation`](farm_rotation.py) | Runs one full-field crop rotation |

Auto-unlocks happen **only between rotations**. Buying `Expand` clears the
farm, so an unlock in the middle of a crop phase would destroy it.

### Crop rotation (`farm_rotation.run_cycle`)

Each phase checks up front that it can pay for a whole field. If it can't, it
skips the phase instead of starting a field it can't finish. The one exception
is Hay: each companion tile uses the first affordable Bush/Tree/Carrot. Wood,
Hay, Carrots, Sunflowers and Pumpkins run until their gain target, with
`continuous_phase_max_seconds` as a safety cap.

1. **Wood** ([`farm_wood`](farm_wood.py), the `wood_run` achievement method):
   plant a Tree/Bush checkerboard (no two Trees touch, even across the world
   wrap on odd sizes) and water every tile to 0.99. Then every drone loops over
   its own rows, harvesting and replanting whatever is ready, until Wood has
   grown by `wood_gain_target`.
2. **Hay** ([`farm_hay`](farm_hay.py), the `hay_run` achievement method): Grass
   sources on one checkerboard parity, fixed Bush/Tree/Carrot companions on the
   other (with affordable fallbacks). Every drone loops over its rows,
   harvesting ready Grass two tiles apart, until Hay has grown by
   `hay_gain_target`.
3. **Carrots** ([`farm_carrot`](farm_carrot.py), the `carrot_run` Carrot Master
   method): till every tile to soil. Put a carrot on one tile in four
   (`(x + 2y) % 4 == 0`); every other tile is for companions. Each carrot is
   replanted until its companion request lands on a companion tile, watered,
   and its requested companion is planted there. Every drone then loops over
   its rows' carrots, harvesting and re-planting the same way, until Carrots
   have grown by `carrot_gain_target`. Rules confirmed by
   [`carrot_probe.py`](archive/carrot_probe.py):
   - A Carrot costs 512 Hay + 512 Wood. Grass, Bush and Tree are free.
   - A harvest pays 512, or **81,920 (160×)** with the exact requested type on
     the exact requested tile (Bush/Tree/Grass within 3 tiles, fixed at
     planting). The companion may be young. Wrong type or wrong tile: 512.
   - Growth takes ~5.9 s plain, ~1.1 s watered. **Fertilizer halves carrot
     yield**, so it's off for Carrots.

   One carrot in four beat one in two (neighbours overwrite each other's
   companions) and one in eight (drones walk and wait more).
4. **Sunflowers** ([`farm_sunflower`](farm_sunflower.py), the `sunflower_run`
   Sunflower Master method): plant and water every tile. Then every drone loops
   over its rows, harvesting any mature flower, replanting once and watering,
   until Power has grown by `sunflower_gain_target`. Rules confirmed by
   [`sunflower_probe.py`](archive/sunflower_probe.py):
   - Petals (7–15) are fixed at planting.
   - A harvest pays ~1 Power, or **8** when the flower has the max petals on
     the field and at least 10 sunflowers are on it (young ones count).
     Tied flowers all pay 8.
   - Growth takes ~6.8 s plain, ~1.3 s watered, ~0.13 s fertilized.

   About 1 in 9 replanted flowers has 15 petals, so the field keeps paying
   bonuses without spending actions on re-rolls. Drones spend Power to move
   and act faster, so the inventory gain slightly under-counts harvested Power.
5. **Pumpkins** ([`farm_pumpkin`](farm_pumpkin.py), the `pumpkin_run` Pumpkin
   Master method): cut the field into horizontal bands of heights 5, 5, 4, 4,
   4, 4, each followed by a bare-soil gap row. Each band is a row of square
   blocks of its height with 1-tile gaps: 10 × 5×5 and 22 × 4×4, one drone
   each. Every drone plants and waters its block to 0.9. It then revisits only
   unfinished tiles (plant + water empty or dead ones, skip growing ones) until
   the whole block is grown, harvests the mega pumpkin, and starts over, until
   Pumpkins have grown by `pumpkin_gain_target`. Rules confirmed by
   [`pumpkin_probe.py`](archive/pumpkin_probe.py):
   - A Pumpkin costs 512 Carrots. A mega pumpkin pays
     **512 × pumpkins × min(side, 6)**: 4×4 = 32,768, 5×5 = 64,000.
   - Growth takes ~2.05 s plain, ~0.41 s watered. 20–30% die when they grow;
     a grown live pumpkin stays alive. **Fertilizer halves pumpkin yield**, so
     it's off for Pumpkins.
   - Grown pumpkins merge with every grown neighbour, and only into squares.
     Blocks placed edge to edge merge with each other, so they need gaps,
     including across the world wrap.

   Using the spare rows for bigger square blocks beat a plain 4×4 grid, a 6×6
   band and a 5×5 grid.
6. **Cactus**: parallel cocktail-shaker sort of every row, then every column
   ([`cact_sort`](cact_sort.py)), then one chain harvest at (0,0).

Growth boost everywhere: water below `water_level`, then fertilize until the
plant is harvestable.

### Dinosaurs (`farm_dinosaurs.farm`)

Rules confirmed by [`dino_probe.py`](archive/dino_probe.py) (32×32, Dinosaurs level 6):

- Putting on the Dinosaur Hat spawns an Apple under the drone. While the
  drone stands on an Apple, `measure()` returns where the **next** Apple will
  spawn.
- Each Apple grows the tail by one and costs 64 Cactus. The field edge is a
  wall, and a move into the tail just fails (`can_move` predicts it).
- Removing the hat pays **32 × apples²** Bones. A full field is 1023 Apples
  = 33,488,928 Bones.
- Moves get **cheaper** as the tail grows (~0.06 s early, ~0.01 s by 60
  Apples).
- **Code between moves costs game time too.** A first shortcut version made
  38% fewer moves but took 50% *longer* (3042 s vs. 2028 s), because
  per-move work outweighed the moves saved once moves were cheap.

The drone follows a Hamiltonian cycle that covers every tile. With
`dinosaur_shortcuts` on, it skips ahead along the cycle toward the next Apple
while the tail covers less than `dinosaur_shortcut_max_fill` of the field. It
never skips past the Apple, and never to within `SHORTCUT_BUFFER` (8) steps of
the tail. The tail always lies in cycle order behind the head, so the plain
cycle path stays open. The shortcut loop is kept lean: precomputed cycle and
neighbour tables, `head == apple` instead of `get_entity_type()`, no
`can_move`, and no per-move telemetry. After the shortcut phase, the drone
returns to (0,0) along the cycle and runs the bare `cycle_once` loop until the
field is full.

One caveat: skipped tiles stay as gaps inside the body until the tail passes
them, and the tail pauses while an Apple is eaten. Trapping the head would take
about 8 Apples spawning almost exactly in its path in a row. If a planned move is ever
blocked anyway, the drone takes any open neighbour, stops taking shortcuts for
the rest of the run, and counts an emergency move. In `sim_dino` (archived),
every benchmark run filled the whole field with 0 emergency moves.

### Gold (`farm_maze.farm`)

Rules confirmed by [`maze_probe.py`](archive/maze_probe.py) (32×32, Mazes level 6):

- A fresh maze is **perfect**: exactly one route between any two tiles. A move
  takes about 0.05 s.
- Reusing the maze (`use_item(Weird_Substance)` on the treasure) pays
  **side² × 32** Gold immediately, moves the treasure, and removes one wall.
  Walls are never added.
- Reuse fails after **300** reuses; `harvest()` then pays once more and turns
  the maze back to Grass, so each maze gives **301 treasures**.
- A maze costs **side × 32** Weird Substance, so its size is chosen by how much
  you use. Spawned drones can move and reuse inside mazes.
- Mazes are **not** built from the Bush's corner. Placement has to be measured
  (see below), or edge mazes shift into their neighbours' squares.

Gold per treasure grows with side², but walking distance only grows with the
side. One big maze has a single treasure at a time, so extra drones can barely
help. With `maze_method = "split"`, the field is tiled with
`maze_split_side` × `maze_split_side` mazes, one per drone:

1. **Calibrate:** build one maze with its Bush mid-field, map it, and measure
   where its lower corner lands relative to the Bush. Then clear it.
2. **Deploy:** each drone walks to its square's Bush spot (corner + offset),
   and all start together.
3. **Per maze:** plant the Bush, create the maze, and map it once into a
   spanning tree (verifying it fills exactly the drone's square). Then walk
   tree paths (up to the common ancestor, then down) to each treasure: 300
   reuses, then the final harvest, then back to the Bush for a new maze.
   Removed walls never break tree paths.
4. **Stop** when Gold reaches `gold_floor` or `maze_max_seconds` runs out, then
   `clear()` so the rotation starts clean.

With only one free drone it uses one full-field maze instead. `maze_method =
"single"` keeps the original solver (DFS toward the treasure from scratch on
every trip). Hot loops follow the dinosaur lesson: bare `move()`, tables, and
no per-move telemetry.

---

## Script structure

Every script falls into one of three groups:

- **Production:** what `main` runs. Proven methods live here.
- **Tools:** run by hand to profile, simulate, or debug production code. They
  call production modules directly, so they always test the real thing.
- **Experiments:** standalone scripts used to find a better method (`*_ab`
  targets, `sim_*` drivers, achievement runners). Once a winner is built into
  production, the experiment is retired to an archive subfolder. The game
  doesn't show subfolders, but it doesn't delete them either.

```
main
├── farm_unlocks        auto-research with operating reserves
├── farm_maze           Gold top-up (split small mazes)
├── farm_dinosaurs      Bone top-up
└── farm_rotation       one full crop rotation
    ├── farm_wood       continuous Wood phase   (from wood_run)
    ├── farm_hay        continuous Hay phase    (from hay_run)
    ├── farm_carrot     continuous Carrot phase (from carrot_run)
    ├── farm_sunflower  continuous Sunflower phase (from sunflower_run)
    ├── farm_pumpkin    continuous Pumpkin phase (from pumpkin_run)
    └── cact_sort       Cactus sorter

shared by all:  farm_config · farm_common · farm_megafarm · farm_telemetry

tools:  simulate_rotation → benchmark_rotation → farm_rotation
        benchmark_full_cycle → farm_maze, farm_dinosaurs, farm_rotation
        debug_rotation → farm_rotation
```

---

## File map

### Production code (used by `main`)

| File | Purpose |
|---|---|
| [`main.py`](main.py) | Top-level forever loop (see above) |
| [`farm_config.py`](farm_config.py) | `SETTINGS`, per-crop hat toggles, per-crop fertilizer toggles |
| [`farm_common.py`](farm_common.py) | Shared helpers: wraparound `go_to`, cost checks, water/fertilizer, soil/grassland, hat state, timing prints |
| [`farm_megafarm.py`](farm_megafarm.py) | Parallel drone helpers (see below) |
| [`farm_rotation.py`](farm_rotation.py) | The six-phase crop rotation |
| [`farm_wood.py`](farm_wood.py) | Continuous Wood phase: Tree/Bush checkerboard, pre-watered, drones harvest/replant their rows until `wood_gain_target` |
| [`farm_hay.py`](farm_hay.py) | Continuous Hay phase: Grass + fixed companions, drones harvest their rows until `hay_gain_target` |
| [`farm_carrot.py`](farm_carrot.py) | Continuous Carrot phase: one carrot per four tiles, each replanted until its companion request is on a companion tile, companions placed, drones harvest/replant until `carrot_gain_target` |
| [`farm_unlocks.py`](farm_unlocks.py) | Auto-research with operating reserves |
| [`farm_maze.py`](farm_maze.py) | Gold: split method (calibrated small mazes, one per drone, spanning-tree paths) plus the original single-maze DFS solver |
| [`farm_dinosaurs.py`](farm_dinosaurs.py) | Bones: Hamiltonian-cycle dinosaur run with safe shortcuts |
| [`farm_telemetry.py`](farm_telemetry.py) | Profiler: phase/sub-phase timing, resource deltas, drone utilisation, counters |
| [`cact_sort.py`](cact_sort.py) | Parallel cactus row/column sorter |
| [`farm_sunflower.py`](farm_sunflower.py) | Continuous Sunflower phase: plant + water, drones harvest mature flowers, replant and water their rows until `sunflower_gain_target` |
| [`farm_pumpkin.py`](farm_pumpkin.py) | Continuous Pumpkin phase: gapped square blocks in bands (10 × 5×5 + 22 × 4×4), one drone per block, repair unfinished tiles, harvest each mega pumpkin until `pumpkin_gain_target` |

### Benchmarking and debugging (run manually)

| File | Purpose |
|---|---|
| [`benchmark_rotation.py`](benchmark_rotation.py) | Profiles one crop rotation (no unlocks, mazes, or dinosaurs) and prints a telemetry report |
| [`benchmark_full_cycle.py`](benchmark_full_cycle.py) | Profiles maze + dinosaurs (if needed) + rotation |
| [`simulate_rotation.py`](simulate_rotation.py) | Runs `benchmark_rotation` in `simulate()` with a fixed seed and the current unlocks and inventory. The real farm is not touched |
| [`debug_rotation.py`](debug_rotation.py) | Runs one rotation on a small world (default 6×6) at adjustable speed so you can watch it (continuous phases capped at 20 s) |

### Archived experiments (`archive/`)

**Retired.** The winning methods now run in `main` (`farm_wood`, `farm_hay`,
`farm_sunflower`, `farm_carrot`, `farm_pumpkin`, `farm_dinosaurs`, `farm_maze`), and these scripts are kept in
[`archive/`](archive/) for reference. The game doesn't show subfolders, so they
can't be run from there. To re-run one, create its code window in the game
first, then copy it back to the top level. Each `sim_*` driver ran its target
through `simulate()` over several seeds and reported a `=== RESULT ===` winner.
Most targets stand alone and import nothing. `dino_ab` and `maze_ab` are the
exceptions: they switch settings and call production `farm_dinosaurs` /
`farm_maze`, so re-running them measures the current code.

| Driver | Target | Question it answers |
|---|---|---|
| [`sim_h2.py`](archive/sim_h2.py) | [`hay_ab.py`](archive/hay_ab.py) | Best static Grass layout for 200M Hay in 60 s (checkerboard vs. alternating rows vs. every 4th row) |
| [`sim_bo.py`](archive/sim_bo.py) | [`hay_bo.py`](archive/hay_bo.py) | Harvest all sources vs. only boosted ones vs. wait on boosted ones |
| [`sim_fc.py`](archive/sim_fc.py) | [`hay_fc.py`](archive/hay_fc.py) | Sparse vs. full vs. fixed companion layout, steady-state throughput |
| [`sim_wood.py`](archive/sim_wood.py) | [`wood_ab.py`](archive/wood_ab.py) | Wood layout (Bush / Tree-Bush mix / Tree-poly / Bush-poly) × dry/wet for 1B Wood in 60 s |
| [`sim_sun.py`](archive/sim_sun.py) | [`sun_ab.py`](archive/sun_ab.py) | Sunflower harvest order for the old whole-field sweep: current vs. serpentine vs. nearest-neighbour route. Serpentine won (`sun_sort`, now also retired in favour of `farm_sunflower`) |
| — | [`hay_run.py`](archive/hay_run.py) | The real 200M-Hay achievement run (fixed-companion checkerboard). **Method now in `farm_hay`** |
| — | [`wood_run.py`](archive/wood_run.py) | The real 1B-Wood achievement run (pre-watered Tree/Bush checkerboard, avg 53.98 s in sim). **Method now in `farm_wood`** |
| [`sim_dino.py`](archive/sim_dino.py) | [`dino_ab.py`](archive/dino_ab.py) | Dinosaur run time: plain cycle vs. shortcuts until 10% / 25% / 50% fill, with Bones kept at full-field yield. **25% won; now `farm_dinosaurs`' default** |
| [`sim_dino.py`](archive/sim_dino.py) (`PROBE = True`) | [`dino_probe.py`](archive/dino_probe.py) | Confirms dinosaur rules: next-Apple `measure()`, walls, tail collisions, Bone formula, move time vs. tail length |
| [`sim_maze.py`](archive/sim_maze.py) | [`maze_ab.py`](archive/maze_ab.py) | Gold: time to +10M. Modes: original solver, full-maze tree paths, split 16/8/6/5/4/3, and 9 = production `farm_maze.farm()`. The header records all four rounds. **Split 5×5 won; now `farm_maze`' default** |
| [`sim_maze.py`](archive/sim_maze.py) (`PROBE = True`) | [`maze_probe.py`](archive/maze_probe.py) | Confirms maze rules: perfect maze, reuse Gold and wall changes, the 300-reuse cap, drones in mazes, and maze size vs. Weird Substance |
| — | [`acrobat_run.py`](archive/acrobat_run.py) | **Master Acrobat** ("Do 1000 flips"): `do_a_flip()` always takes 1 s, so it splits 1,050 flips across all free drones. Flips by spawned drones count: 1,056 flips in 34.04 s unlocked it |
| [`sim_sunflower.py`](archive/sim_sunflower.py) | [`sunflower_ab.py`](archive/sunflower_ab.py) | Power: time to +12,000 after setup, with real Fertilizer/Water/Carrot stock. Field sweep 86.07 s (0/3), re-roll to 15 37.96 s, re-roll + Fertilizer 48.76 s, **mature 15 25.97 s (winner)**. Mode 5 = production `farm_sunflower`: 35.61 s including setup. **Now `farm_sunflower`** |
| [`sim_sunflower.py`](archive/sim_sunflower.py) (`PROBE = True`) | [`sunflower_probe.py`](archive/sunflower_probe.py) | Confirms Sunflower rules: fixed petals, base vs. bonus Power, the ≥10-flower rule (young flowers count), growth with water/Fertilizer, Power per move |
| — | [`sunflower_run.py`](archive/sunflower_run.py) | **Sunflower Master** ("Farm 12000 power in 1 minute"): plant + water, then mature-15 harvesting on 32 drones. Real game: +15,006 Power in 32.63 s, and it unlocked |
| — | [`sun_sort.py`](archive/sun_sort.py) | Serpentine ordering of equal-petal points for the old whole-field sunflower sweep. Retired with that sweep |
| [`sim_carrot.py`](archive/sim_carrot.py) | [`carrot_ab.py`](archive/carrot_ab.py) | Carrots: time to +200M after setup, with real Hay/Wood/Water stock. Round 1: old `farm_carrots` 244.16 s (0/3), pair sweep 52.10 s, no water 58.75 s, no re-roll 50.02 s. Round 2 (carrot density): ½ 50.03 s, ¼ no re-roll 43.66 s, ⅛ 46.86 s, **¼ pair sweep 40.87 s (winner)**. Mode 8 = production `farm_carrot`. **Now `farm_carrot`** |
| [`sim_carrot.py`](archive/sim_carrot.py) (`PROBE = True`) | [`carrot_probe.py`](archive/carrot_probe.py) | Confirms Carrot rules: cost, base vs. companion yield (exact type + tile, young companion OK), fixed requests, growth with water, Fertilizer halving yield |
| — | [`carrot_run.py`](archive/carrot_run.py) | **Carrot Master** ("Farm 200 million carrots in 1 minute"): ¼-density pair sweep on 32 drones. Real game: +251M Carrots in 50.95 s, and it unlocked |
| — | [`farm_polyculture.py`](archive/farm_polyculture.py) | The old Carrot companion harvest (scan → plan → fused execute → reject cleanup), used only by the old `farm_carrots`. Retired with it |
| [`sim_pumpkin.py`](archive/sim_pumpkin.py) | [`pumpkin_ab.py`](archive/pumpkin_ab.py) | Pumpkins: time to +20M after setup, with real Carrot/Water stock. Round 1: old whole-field `farm_pumpkins` 153.86 s, edge-to-edge 6×6 / 8×8 blocks 104.23 / 147.53 s (neighbouring blocks merged). Round 2 (gapped blocks): 6×6 82.77 s, 5×5 65.21 s, 4×4 63.16 s. Round 3 (no corner check): 4×4 water 0.9 54.74 s, water 0.5 60.40 s, no water 136.25 s, 5×5 water 0.5 58.39 s. Round 4 (use the whole field): **bands 5,5,4,4,4,4 51.60 s (winner)**, bands 6,4,4,4,4,4 52.37 s, 5×5 water 0.9 58.04 s. Mode 15 = production `farm_pumpkin`: 60.99 s including setup. **Now `farm_pumpkin`** |
| [`sim_pumpkin.py`](archive/sim_pumpkin.py) (`PROBE = True`) | [`pumpkin_probe.py`](archive/pumpkin_probe.py) | Confirms Pumpkin rules: cost, single vs. fertilized yield, growth with water/Fertilizer, death rate, mega-pumpkin yield by side |
| — | [`misc_achievements.py`](archive/misc_achievements.py) | **Healer** (Fertilizer then Weird Substance on a Tree, plus Weird Substance twice on another), **Fashion Show** (5 unlocked hats on 5 drones for 5 s), **Wrong Order** (full 32×32 cactus field bubble-sorted descending in 70.17 s, then harvested) and **Stack Overflow** (endless recursion, run last). All four unlocked |
| — | [`cycle_a.py`](archive/cycle_a.py) + [`cycle_b.py`](archive/cycle_b.py) | **Circular Import**: each imports the other. The game runs the loop (a → b → a) without an error, and it unlocked |
| — | [`lb_start.py`](archive/lb_start.py) + [`lb_probe.py`](archive/lb_probe.py) | Leaderboard probe: `leaderboard_run()` starts a fresh 32×32 farm at time 0 with 1 / 32 drones and every upgrade at max. The Sunflowers board starts with 1B Carrots and nothing else; the Hay board with no items at all |
| — | [`lb_start.py`](archive/lb_start.py) + [`lb_hay_run.py`](archive/lb_hay_run.py) | **Competitive Farming**: the Hay board (2B Hay) with production `farm_hay`. ~340 s per run (the game ran it 4 times: 341.66 / 339.15 / 342.15 / 339.44 s). Rank #555, and it unlocked. (Run from the top level as `lb_probe`) |
| — | [`pumpkin_run.py`](archive/pumpkin_run.py) | **Pumpkin Master** ("Farm 20 million pumpkins in 1 minute"): 5,5,4,4,4,4 gapped block bands on 32 drones. Real game: +23.8M Pumpkins in the first 60 s (+25.1M in 64.83 s), and it unlocked |

Most experiment scripts use **`RUN=False`** for a setup-only baseline. The
driver subtracts that time from the `RUN=True` time, so the result measures
farming alone and not setup or drone spawning.

---

## Megafarm helpers

[`farm_megafarm.py`](farm_megafarm.py) is the only place drones are spawned.
Every helper follows the same pattern:

- `worker_count(n)` = `min(free drones + 1, n)`. The calling drone also does
  work.
- **Row helpers** (`run_rows`, `run_rows_bool`, `collect_rows`, `sum_rows`, and
  the `_with_arg` variants) split rows into stripes. Worker `k` handles rows
  `k, k+count, k+2·count, …`.
- **Item helpers** (`run_items`, `sum_items`) split a list into contiguous
  chunks.
- **Continuous helper** (`run_stripes_with_arg`) hands each drone its whole
  stripe of rows once, as `worker(rows, arg)`, for workers that loop until a
  shared stop condition (Wood/Hay gain target or deadline). If a spawn fails,
  that stripe's rows go to the coordinator. Running them afterward would be
  pointless, because the target would already be met.
- If `spawn_drone` fails, that stripe or chunk runs serially on the
  coordinator.
- Results are combined on the coordinator with `wait_for`: AND for bool,
  concatenation for lists, and addition for sums.

**Gotchas:**
- Each drone has **its own module state**, so telemetry only counts on the
  coordinator drone.
- Inventory is **shared**. `shared_item_available` makes sure at least one
  item per active drone is in stock before using Water or Fertilizer, which
  avoids races where two drones spend the same last item.
- Row workers must start with `go_to(0, row)` and must not assume where the
  drone is.

---

## Configuration

All in [`farm_config.py`](farm_config.py):

| Setting | Default | Meaning |
|---|---|---|
| `water_level` | `0.5` | Water a tile when its water is below this |
| `wood_gain_target` | `1000000000` | The Wood phase keeps harvesting until Wood has grown by this much |
| `hay_gain_target` | `200000000` | The Hay phase keeps harvesting until Hay has grown by this much |
| `sunflower_gain_target` | `20000` | The Sunflower phase keeps harvesting until Power has grown by this much (~27,700 Power/min on 32×32) |
| `carrot_gain_target` | `200000000` | The Carrot phase keeps harvesting until Carrots have grown by this much (~294M Carrots/min on 32×32) |
| `pumpkin_gain_target` | `20000000` | The Pumpkin phase keeps harvesting until Pumpkins have grown by this much (~23M Pumpkins/min on 32×32) |
| `continuous_phase_max_seconds` | `180` | Safety cap on each continuous phase's harvest loop |
| `timing_enabled` | `True` | Print `[TIMING]` lines from `main` |
| `auto_unlock_enabled` | `True` | Allow `farm_unlocks.manage()` to buy upgrades |
| `unlock_farm_reserve_multiplier` | `2.0` | Keep this many rotations' worth of planting costs before buying upgrades |
| `mazes_enabled` / `gold_floor` | `True` / `100000000` | Run mazes while Gold is below the floor (100M = the last upgrades' cost) |
| `maze_method` | `"split"` | `"split"`: small mazes, one per drone. `"single"`: original one-maze solver |
| `maze_split_side` | `5` | Maze side for `"split"` (5×5 won on 32×32 with 32 drones) |
| `maze_max_seconds` | `3600` | Return to the crop rotation after this long even if `gold_floor` isn't reached |
| `dinosaurs_enabled` / `bone_floor` | `True` / `100000000` | Run dinosaurs while Bone is below the floor |
| `dinosaur_shortcuts` | `True` | Take safe shortcuts along the dinosaur cycle (`False` = plain cycle) |
| `dinosaur_shortcut_max_fill` | `0.25` | Stop taking shortcuts once the tail covers this fraction of the field, then run the plain cycle |

`HAT_ENABLED` (all off) and `FERTILIZE` (on for everything except Carrots and
Pumpkins, where Fertilizer halves the yield) are per-crop toggles.

### Upgrade priority

`Speed → Megafarm → Expand → Fertilizer → Watering → Polyculture → Mazes →
Dinosaurs → Sunflowers → Trees → Grass → Carrots → Pumpkins → Cactus`

Each unlock appears only once. `unlock(Unlocks.Expand)` buys whatever the next
level is. After every purchase the manager rebuilds all reserves and starts
again from the top, because an upgrade can change world size, costs, or drone
count.

Reserves kept before any purchase:
- 2× one rotation's planting cost (pumpkins count as 12 fields: the
  continuous phase replants every block after each harvest)
- the Gold and Bone floors, **except** for an upgrade that costs at least the
  whole floor. The floor is the savings for that upgrade, so it isn't reserved
  on top of the cost (otherwise a 100M-Gold upgrade would need 200M).
- Weird Substance for one small maze per drone (`"split"`) or one full maze
  (`"single"`), when Gold is low
- a full board of Apples, when Bone is low

---

## Benchmark results recorded in code

| Change | Setup | Before | After |
|---|---|---|---|
| Skip cactus verification pass | 22×22, 8 drones | 68.98 s | 65.44 s (−5.1%) |
| Serpentine sunflower order | fixed seeds ×5 | 30.01 s | 25.99 s (−13.4%, 5/5 wins) |
| Fixed-companion Hay checkerboard | 32 drones, 200M Hay | — | avg ~33.36 s, worst ~33.71 s |
| Lean dinosaur loop (no per-move overhead) | 32×32 full field, seeds 1–3 | 2027.67 s | 1676.04 s (−17%) |
| Dinosaur shortcuts until 25% fill | 32×32 full field, seeds 1–3 | 2027.67 s | **976.46 s (−52%)**; 10% fill: 1049.87 s, 50% fill: 1314.99 s |
| Continuous Wood phase in `main` (`farm_wood`) | 32×32, 32 drones, `simulate_rotation` seed 1 | — | 1B Wood in 54.12 s harvest (+8.93 s plant / pre-water) |
| Continuous Hay phase in `main` (`farm_hay`) | 32×32, 32 drones, `simulate_rotation` seed 1 | — | 200M Hay in 34.64 s harvest (+3.63 s companions) |
| Full six-phase rotation | 32×32, 32 drones, `simulate_rotation` seed 1 | — | 245.23 s (Wood 63.08, Cactus 57.23, Sunflowers 41.60, Hay 38.30, Carrots 26.14, Pumpkins 17.11) |
| Gold: full maze with tree paths (1 drone) | 32×32, +10M Gold, seed 1 | 3369.77 s (original solver) | 2122.77 s (1.59×) |
| Gold: split 4×4 / 6×6 (calibrated) | 32×32, 32 drones, +10M Gold, seeds 1–3 | 3369.77 s | 146.83 s (22.95×) / 156.19 s with 25 drones (21.58×) |
| **Gold: split 5×5 (production `farm_maze`)** | 32×32, 32 drones, +10M Gold, seeds 1–3 | 3369.77 s | **127.54 s (26.42×)**, 78,409 Gold/s, 0 anomalies |
| Power: mature-15 continuous harvest (`sim_sunflower`) | 32×32, 32 drones, +12,000 Power after setup, seeds 1–3 | 86.07 s (old whole-field sweep) | **25.97 s (3.3×)**, 27,726 Power/min |
| **Power: production `farm_sunflower`** | same, time includes its own planting/watering | 86.07 s | **35.61 s**, 3/3 under 60 s. Real game: +15,006 Power in 32.63 s |
| Carrots: ¼-density pair sweep (`sim_carrot`) | 32×32, 32 drones, +200M Carrots after setup, seeds 1–3 | 244.16 s (old `farm_carrots` + Polyculture) | **40.87 s (6.0×)**, 293.6M Carrots/min. Real game: +251M in 50.95 s |
| **Carrots: production `farm_carrot`** | same, time includes its own soil/planting | 244.16 s | **50.95 s**, 3/3 under 60 s |
| Pumpkins: 5,5,4,4,4,4 gapped block bands (`sim_pumpkin`) | 32×32, 32 drones, +20M Pumpkins after setup, seeds 1–3 | 153.86 s (old single mega pumpkin) | **51.60 s (3.0×)**, 23.3M Pumpkins/min. Real game: +23.8M in the first 60 s |
| **Pumpkins: production `farm_pumpkin`** | same, time includes its own soil/planting (~8–9 s) | 153.86 s | **60.99 s** (60.59 / 61.60 / 60.78), ~52 s of harvesting |

When a new experiment wins, record the numbers in the module header comment
and in this table.

---

## Profiling workflow

1. Run `simulate_rotation` (fixed seed, fast) or `benchmark_rotation` (real).
2. Read the report between `<<< FARM_PROFILE_BEGIN >>>` and
   `<<< FARM_PROFILE_END >>>` in the game's `output.txt`. It includes a phase
   ranking, drone utilisation, sub-phase ranking, the bottleneck, counters,
   and resource rates.

   `output.txt` is **not** in this folder. The game writes it two levels up,
   at `…\TheFarmerWasReplaced\TheFarmerWasReplaced\output.txt`, and replaces
   it on every run.
3. Change the code, re-run with the **same seed**, and compare. Lower
   simulated time wins.

---

## Repository conventions

- **`main` is always what the farm should run.** Every change goes on a
  feature branch (`feat/…`, `fix/…`, `perf/…`, `docs/…`). Test it in game or in
  simulation, then merge through a pull request.
- **Keep this README current.** Any PR that adds or removes a file, changes
  settings or the upgrade priority, or produces new benchmark numbers should
  update the matching section here.
- **Not tracked** (see [`.gitignore`](.gitignore)): `save.json`, which the game
  rewrites constantly (inventory, unlocks, editor layout), and
  `__builtins__.py`, the editor type stubs.
- **New script files:** create the code window in the game *before* the file
  is written from outside (or close the game first). Otherwise the game deletes
  any `.py` it doesn't know about the next time it saves.
- **Retiring scripts:** copy them into `archive/` first, then close their
  windows *in the game* (which deletes the top-level files) and exit normally.
  Files deleted while the game is closed come back on the next launch, because
  Steam Cloud syncs this save folder.
- **Simulation drivers** report like [`sim_wood.py`](archive/sim_wood.py):
  `quick_print` to `output.txt` between `<<< NAME_BENCH_BEGIN/END >>>`
  markers, a header, per-mode AVG/MIN/MAX, and a final `=== RESULT ===`.
- **Code style:** tabs, generous vertical spacing, `# ===` section banners, and
  one argument per line in calls. New code should match.
