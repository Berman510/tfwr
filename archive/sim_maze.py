# ============================================================
# MAZE / GOLD A/B BENCHMARK
# ============================================================
#
# MODE (see maze_ab.py):
#
#   1 = CURRENT         production farm_maze, full maze, DFS
#   2 = FULL TREE       full maze, 1 drone, spanning-tree paths
#   3 = SPLIT 16         4 x 16x16 mazes,  4 drones
#   4 = SPLIT 8         16 x  8x8  mazes, 16 drones
#   5 = SPLIT 4         32 x  4x4  mazes, 32 drones
#   6 = SPLIT 5         32 x  5x5  mazes, 32 drones
#   7 = SPLIT 6         25 x  6x6  mazes, 25 drones
#   8 = SPLIT 3         32 x  3x3  mazes, 32 drones
#
# Result = simulated seconds to gain TARGET Gold (lower wins).
#
#
# Round 1 (10M Gold, seed 1):
#
#   CURRENT     3369.77 sec    2,968 Gold/sec
#   FULL TREE   2122.77 sec    4,711 Gold/sec   1.59x
#   SPLIT 16    2362.42 sec    4,233 Gold/sec   1.43x  (3 anomalies)
#   SPLIT 8      348.79 sec   28,671 Gold/sec   9.66x  (7 anomalies)
#   SPLIT 4      147.30 sec   67,887 Gold/sec  22.88x  (1 anomaly)
#
# A drone stops at its first anomaly, so split results with
# anomalies ran below full drone capacity. Round 2 records why.
#
#
# Round 2 (10M Gold, seeds 1-3, Bush at square corner):
#
#   SPLIT 3   175.44 sec   57,001 Gold/sec  19.21x   31/32 drones
#   SPLIT 4   148.38 sec   67,394 Gold/sec  22.71x   31/32 drones
#   SPLIT 5   180.63 sec   55,361 Gold/sec  18.66x   22/32 drones
#   SPLIT 6   225.96 sec   44,256 Gold/sec  14.91x   16/25 drones
#
#   Every anomaly: measure() None right after maze #1, same
#   squares on every seed (edge squares and their neighbours).
#   Mazes aren't built from the Bush's corner, so edge mazes
#   shifted into neighbouring squares and wiped treasures.
#   Gold/sec per WORKING drone rose with maze size
#   (~1,839 / 2,174 / 2,516 / 2,766).
#
#   Round 3 calibrates the Bush offset first, so every maze
#   fills exactly its own square.
#
#
# Round 3 (10M Gold, seeds 1-3, calibrated placement):
#
#   SPLIT 4   146.83 sec   68,105 Gold/sec  22.95x   32 drones
#   SPLIT 5   132.42 sec   75,520 Gold/sec  25.45x   32 drones  WINNER
#   SPLIT 6   156.19 sec   64,026 Gold/sec  21.58x   25 drones
#
#   0 anomalies on every run. SPLIT 5 is now farm_maze's
#   default ("split", side 5).
#
#
# Round 4: mode 9 runs the production farm_maze.farm() to
# confirm the port matches the benchmark.
#
#
# Probe results (maze_probe.py, 32x32, Mazes 6, seed 1):
#
#   - Fresh maze is perfect: 1024 cells, 1023 open edges.
#   - Move ~0.05 sec.
#   - Reuse pays 32,768 Gold immediately, moves the treasure,
#     removes exactly 1 wall, never adds walls.
#   - use_item fails after 300 reuses; harvest then pays
#     32,768 more and leaves Grass -> 301 treasures per maze.
#   - Remembered map + BFS: 40 moves but 8.74 sec per treasure
#     by reuse 300 (per-move code overhead dominates).
#   - A spawned drone can walk to and reuse the treasure.
#   - Half substance (512) -> 16x16 maze, 8,192 Gold per
#     treasure: value = side^2 x 32, cost = side x 32.
#
#
# PROBE = True re-runs maze_probe.py instead.
#
#
# Output:
#
#   output.txt, between
#
#       <<< MAZE_BENCH_BEGIN >>>
#       <<< MAZE_BENCH_END >>>
#
# Does NOT modify the real farm.
# ============================================================


PROBE = False


# About one full maze's worth of treasures (301 x 32,768).

TARGET = 10000000


SEEDS = [
	1,
	2,
	3
]


# Round 2: split sizes only. CURRENT (mode 1) takes ~3400 sim
# seconds per seed, so the round-1 result is used as the
# baseline unless mode 1 is added back here.

MODES = [
	9
]


CURRENT_BASELINE = 3369.77


NAMES = {
	1: "CURRENT",
	2: "FULL TREE",
	3: "SPLIT 16",
	4: "SPLIT 8",
	5: "SPLIT 4",
	6: "SPLIT 5",
	7: "SPLIT 6",
	8: "SPLIT 3",
	9: "PRODUCTION (farm_maze split 5)"
}


SIM_SPEEDUP = 10000


# ============================================================
# CURRENT UNLOCKS
# ============================================================

sim_unlocks = {}


for unlock_type in Unlocks:

	sim_unlocks[
		unlock_type
	] = num_unlocked(
		unlock_type
	)


# ============================================================
# HUGE TEST INVENTORY
# ============================================================
#
# We are measuring Gold throughput, not stockpile constraints.
#
# Gold starts at 0 so every Gold in the simulation came from
# the maze.

sim_items = {}


for item in Items:

	sim_items[
		item
	] = 1000000000


sim_items[
	Items.Gold
] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< MAZE_BENCH_BEGIN >>>"
)

quick_print(
	"MAZE / GOLD"
)

quick_print(
	"Target:",
	TARGET
)

quick_print(
	"World:",
	get_world_size(),
	"x",
	get_world_size()
)

quick_print(
	"Drones:",
	max_drones()
)

quick_print(
	"Mazes:",
	num_unlocked(
		Unlocks.Mazes
	)
)

quick_print(
	"Full-maze treasure value:",
	get_world_size()
	* get_world_size()
	* 2 ** (num_unlocked(Unlocks.Mazes) - 1)
)

quick_print(
	"Seeds:",
	len(SEEDS)
)

quick_print(
	""
)


# ============================================================
# PROBE
# ============================================================

if PROBE:

	quick_print(
		"--- PROBE ---"
	)


	run_time = simulate(
		"maze_probe",
		sim_unlocks,
		sim_items,
		{},
		SEEDS[0],
		SIM_SPEEDUP
	)


	quick_print(
		""
	)

	quick_print(
		"=== RESULT ==="
	)


	if run_time == None:

		quick_print(
			"ERROR probe"
		)

	else:

		quick_print(
			"Probe simulated seconds:",
			run_time
		)


# ============================================================
# A/B
# ============================================================

else:

	best_avg = -1

	best_mode = -1

	current_avg = CURRENT_BASELINE


	for mode in MODES:

		label = NAMES[
			mode
		]


		total = 0

		min_time = -1

		max_time = 0

		completed = 0


		quick_print(
			"---",
			label,
			"---"
		)


		for seed in SEEDS:

			run_time = simulate(
				"maze_ab",
				sim_unlocks,
				sim_items,
				{
					"MODE": mode,
					"TARGET": TARGET
				},
				seed,
				SIM_SPEEDUP
			)


			if run_time == None:

				quick_print(
					"ERROR run",
					label,
					seed
				)


			else:

				completed = (
					completed + 1
				)


				total = (
					total + run_time
				)


				if min_time < 0:

					min_time = run_time


				elif run_time < min_time:

					min_time = run_time


				if run_time > max_time:

					max_time = run_time


				quick_print(
					"seed:",
					seed,
					"time:",
					run_time,
					"Gold/sec:",
					TARGET / run_time
				)


		# ====================================================
		# SUMMARY
		# ====================================================

		if completed > 0:

			avg = (
				total
				/ completed
			)


			quick_print(
				"AVG:",
				avg
			)

			quick_print(
				"MIN:",
				min_time
			)

			quick_print(
				"MAX:",
				max_time
			)

			quick_print(
				"Gold/sec:",
				TARGET / avg
			)


			if mode == 1:

				current_avg = avg


			elif current_avg > 0:

				quick_print(
					"vs CURRENT:",
					current_avg / avg,
					"x faster"
				)


			if best_avg < 0:

				best_avg = avg

				best_mode = mode


			elif avg < best_avg:

				best_avg = avg

				best_mode = mode


		quick_print(
			""
		)


	# ========================================================
	# FINAL
	# ========================================================

	quick_print(
		"=== RESULT ==="
	)


	if best_mode < 0:

		quick_print(
			"No completed runs"
		)


	else:

		quick_print(
			"WINNER:",
			NAMES[
				best_mode
			]
		)

		quick_print(
			"Average:",
			best_avg
		)

		quick_print(
			"Gold/sec:",
			TARGET / best_avg
		)


		if current_avg > 0:

			quick_print(
				"vs CURRENT:",
				current_avg / best_avg,
				"x faster"
			)


quick_print(
	"<<< MAZE_BENCH_END >>>"
)


print(
	"MAZE BENCH DONE\n",
	"Open output.txt"
)
