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
| 2 | [`farm_maze`](farm_maze.py) | If Gold < `gold_floor`, runs maze batches until it's restored |
| 3 | [`farm_dinosaurs`](farm_dinosaurs.py) | If Bone < `bone_floor`, runs a dinosaur snake run |
| 4 | [`farm_rotation`](farm_rotation.py) | Runs one full-field crop rotation |

Auto-unlocks happen **only between rotations**. Buying `Expand` clears the
farm, so an unlock in the middle of a crop phase would destroy it.

### Crop rotation (`farm_rotation.run_cycle`)

Each phase checks up front that it can pay for a whole field. If it can't, it
skips the phase instead of starting a field it can't finish. The one exception
is Hay: each companion tile uses the first affordable Bush/Tree/Carrot. Wood and
Hay run until their gain target, with `continuous_phase_max_seconds` as a
safety cap.

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
3. **Carrots**: full soil field, then Polyculture harvest.
4. **Sunflowers**: measure every flower and sort them into buckets by petal
   count (15 → 7). Each bucket is harvested in parallel, largest first,
   keeping the ≥10-sunflowers-remaining bonus rule. Inside a bucket, points
   are visited in serpentine order ([`sun_sort`](sun_sort.py)).
5. **Pumpkins**: plant the whole field and replant dead pumpkins until
   the pumpkin at (0,0) and the one at (n-1,n-1) have the same `measure()` id
   (one merged mega-pumpkin). Then harvest once.
6. **Cactus**: parallel cocktail-shaker sort of every row, then every column
   ([`cact_sort`](cact_sort.py)), then one chain harvest at (0,0).

Growth boost everywhere: water below `water_level`, then fertilize until the
plant is harvestable.

### Dinosaurs (`farm_dinosaurs.farm`)

Rules confirmed by [`dino_probe.py`](dino_probe.py) (32×32, Dinosaurs level 6):

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
the rest of the run, and counts an emergency move. `sim_dino` reports that count
and whether each run filled the whole field.

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
├── farm_maze           Gold top-up
├── farm_dinosaurs      Bone top-up
└── farm_rotation       one full crop rotation
    ├── farm_wood       continuous Wood phase   (from wood_run)
    ├── farm_hay        continuous Hay phase    (from hay_run)
    ├── farm_polyculture  Carrot companion harvest
    ├── sun_sort        Sunflower harvest order (from sun_ab)
    └── cact_sort       Cactus sorter

shared by all:  farm_config · farm_common · farm_megafarm · farm_telemetry

tools:  simulate_rotation → benchmark_rotation → farm_rotation
        benchmark_full_cycle → farm_maze, farm_dinosaurs, farm_rotation
        debug_rotation → farm_rotation
        sim_dino → dino_ab → farm_dinosaurs
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
| [`farm_polyculture.py`](farm_polyculture.py) | Carrot companion-planting harvest: scan → plan → fused execute → reject cleanup |
| [`farm_unlocks.py`](farm_unlocks.py) | Auto-research with operating reserves |
| [`farm_maze.py`](farm_maze.py) | Gold: maze creation, target-guided DFS solver, maze reuse |
| [`farm_dinosaurs.py`](farm_dinosaurs.py) | Bones: Hamiltonian-cycle dinosaur run with safe shortcuts |
| [`farm_telemetry.py`](farm_telemetry.py) | Profiler: phase/sub-phase timing, resource deltas, drone utilisation, counters |
| [`cact_sort.py`](cact_sort.py) | Parallel cactus row/column sorter |
| [`sun_sort.py`](sun_sort.py) | Serpentine ordering for sunflower harvest points |

### Benchmarking and debugging (run manually)

| File | Purpose |
|---|---|
| [`benchmark_rotation.py`](benchmark_rotation.py) | Profiles one crop rotation (no unlocks, mazes, or dinosaurs) and prints a telemetry report |
| [`benchmark_full_cycle.py`](benchmark_full_cycle.py) | Profiles maze + dinosaurs (if needed) + rotation |
| [`simulate_rotation.py`](simulate_rotation.py) | Runs `benchmark_rotation` in `simulate()` with a fixed seed and the current unlocks and inventory. The real farm is not touched |
| [`debug_rotation.py`](debug_rotation.py) | Runs one rotation on a small world (default 6×6) at adjustable speed so you can watch it (continuous phases capped at 20 s) |
| [`sim_dino.py`](sim_dino.py) → [`dino_ab.py`](dino_ab.py) | Dinosaur run time: plain cycle vs. shortcuts until 10% / 25% / 50% fill. `dino_ab` calls production `farm_dinosaurs` directly; Bones must stay at full-field yield |
| [`sim_dino.py`](sim_dino.py) (`PROBE = True`) → [`dino_probe.py`](dino_probe.py) | Confirms dinosaur rules: next-Apple `measure()`, walls, tail collisions, Bone formula, move time vs. tail length |

### Archived experiments (`archive/`)

**Retired.** The winning methods now run in `main` (`farm_wood`, `farm_hay`,
`sun_sort`), and these scripts are kept in [`archive/`](archive/) for
reference. The game doesn't show subfolders, so they can't be run from there;
copy one back to the top level (and create its code window first) to re-run
it. Each `sim_*` driver ran its target through `simulate()` over several seeds
and reported a `=== RESULT ===` winner; the targets stand alone and import
nothing.

| Driver | Target | Question it answers |
|---|---|---|
| [`sim_h2.py`](archive/sim_h2.py) | [`hay_ab.py`](archive/hay_ab.py) | Best static Grass layout for 200M Hay in 60 s (checkerboard vs. alternating rows vs. every 4th row) |
| [`sim_bo.py`](archive/sim_bo.py) | [`hay_bo.py`](archive/hay_bo.py) | Harvest all sources vs. only boosted ones vs. wait on boosted ones |
| [`sim_fc.py`](archive/sim_fc.py) | [`hay_fc.py`](archive/hay_fc.py) | Sparse vs. full vs. fixed companion layout, steady-state throughput |
| [`sim_wood.py`](archive/sim_wood.py) | [`wood_ab.py`](archive/wood_ab.py) | Wood layout (Bush / Tree-Bush mix / Tree-poly / Bush-poly) × dry/wet for 1B Wood in 60 s |
| [`sim_sun.py`](archive/sim_sun.py) | [`sun_ab.py`](archive/sun_ab.py) | Sunflower harvest order: current vs. serpentine vs. nearest-neighbour route. **Serpentine won; now in `sun_sort`** |
| — | [`hay_run.py`](archive/hay_run.py) | The real 200M-Hay achievement run (fixed-companion checkerboard). **Method now in `farm_hay`** |
| — | [`wood_run.py`](archive/wood_run.py) | The real 1B-Wood achievement run (pre-watered Tree/Bush checkerboard, avg 53.98 s in sim). **Method now in `farm_wood`** |

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
| `continuous_phase_max_seconds` | `180` | Safety cap on each continuous phase's harvest loop |
| `timing_enabled` | `True` | Print `[TIMING]` lines from `main` |
| `auto_unlock_enabled` | `True` | Allow `farm_unlocks.manage()` to buy upgrades |
| `unlock_farm_reserve_multiplier` | `2.0` | Keep this many rotations' worth of planting costs before buying upgrades |
| `mazes_enabled` / `gold_floor` | `True` / `100000` | Run mazes while Gold is below the floor |
| `dinosaurs_enabled` / `bone_floor` | `True` / `100000` | Run dinosaurs while Bone is below the floor |
| `dinosaur_shortcuts` | `True` | Take safe shortcuts along the dinosaur cycle (`False` = plain cycle) |
| `dinosaur_shortcut_max_fill` | `0.25` | Stop taking shortcuts once the tail covers this fraction of the field, then run the plain cycle |

`HAT_ENABLED` (all off) and `FERTILIZE` (all on) are per-crop toggles.

### Upgrade priority

`Speed → Megafarm → Expand → Fertilizer → Watering → Polyculture → Mazes →
Dinosaurs → Sunflowers → Trees → Grass → Carrots → Pumpkins → Cactus`

Each unlock appears only once. `unlock(Unlocks.Expand)` buys whatever the next
level is. After every purchase the manager rebuilds all reserves and starts
again from the top, because an upgrade can change world size, costs, or drone
count.

Reserves kept before any purchase:
- 2× one rotation's planting cost (pumpkins count as 3 fields for replants)
- the Gold and Bone floors
- Weird Substance for one maze, when Gold is low
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
- **Simulation drivers** report like [`sim_wood.py`](archive/sim_wood.py):
  `quick_print` to `output.txt` between `<<< NAME_BENCH_BEGIN/END >>>`
  markers, a header, per-mode AVG/MIN/MAX, and a final `=== RESULT ===`.
- **Code style:** tabs, generous vertical spacing, `# ===` section banners, and
  one argument per line in calls. New code should match.
