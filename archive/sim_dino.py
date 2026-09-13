# ============================================================
# DINOSAUR A/B/C BENCHMARK
# ============================================================
#
# MODE:
#
#   1 = CYCLE
#       Plain Hamiltonian cycle.
#
#   2 = SHORTCUT 10%
#   3 = SHORTCUT 25%
#   4 = SHORTCUT 50%
#       Safe cycle shortcuts until the tail covers that
#       fraction of the field, then plain cycle.
#
#
# First attempt (heavy per-move loop, seeds 1-3):
#
#   CYCLE           2027.67 sec
#   SHORTCUT 50%    3042.29 sec
#   SHORTCUT 100%   8095.38 sec
#
#   All runs filled the field with 0 emergency moves. Per-move
#   code overhead outweighed the moves saved.
#
#
# Second attempt (lean loop, shortcuts early only, seeds 1-3):
#
#   CYCLE           1676.04 sec
#   SHORTCUT 10%    1049.87 sec
#   SHORTCUT 25%     976.46 sec   <- WINNER, production default
#   SHORTCUT 50%    1314.99 sec
#
#   All runs: 33,488,928 Bones (full field), 0 emergency moves.
#
#
# Target:
#
#   dino_ab.py
#
#   Each run prints one line: Apples and moves when shortcuts
#   ended, shortcut moves, emergency moves, Bones, and whether
#   the whole field was filled.
#
#
# PROBE = True runs dino_probe.py instead, to re-confirm the
# dinosaur rules (see farm_dinosaurs.py header).
#
#
# Output:
#
#   output.txt, between
#
#       <<< DINO_BENCH_BEGIN >>>
#       <<< DINO_BENCH_END >>>
#
# Does NOT modify the real farm.
# ============================================================


PROBE = False


SEEDS = [
	1,
	2,
	3
]


MODES = [
	1,
	2,
	3,
	4
]


NAMES = {
	1: "CYCLE",
	2: "SHORTCUT 10%",
	3: "SHORTCUT 25%",
	4: "SHORTCUT 50%"
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
# We are measuring dinosaur run time, not stockpile
# constraints.
#
# Bones start at 0 so every Bone in the simulation came from
# the dinosaur run.

sim_items = {}


for item in Items:

	sim_items[
		item
	] = 1000000000


sim_items[
	Items.Bone
] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< DINO_BENCH_BEGIN >>>"
)

quick_print(
	"DINOSAUR"
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
	"Dinosaurs:",
	num_unlocked(
		Unlocks.Dinosaurs
	)
)

quick_print(
	"Apple cost:",
	get_cost(
		Entities.Apple
	)
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
		"dino_probe",
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
# A/B/C
# ============================================================

else:

	best_avg = -1

	best_mode = -1

	cycle_avg = -1


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
				"dino_ab",
				sim_unlocks,
				sim_items,
				{
					"MODE": mode
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
					run_time
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


			if mode == 1:

				cycle_avg = avg


			elif cycle_avg > 0:

				quick_print(
					"vs CYCLE:",
					(
						(cycle_avg - avg)
						* 100
						/ cycle_avg
					),
					"% faster"
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


		if cycle_avg > 0:

			quick_print(
				"vs CYCLE:",
				(
					(cycle_avg - best_avg)
					* 100
					/ cycle_avg
				),
				"% faster"
			)


quick_print(
	"<<< DINO_BENCH_END >>>"
)


print(
	"DINO BENCH DONE\n",
	"Open output.txt"
)
