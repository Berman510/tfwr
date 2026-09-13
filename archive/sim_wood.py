# ============================================================
# WOOD MASTER A/B BENCHMARK
# ============================================================
#
# Achievement:
#
#     1,000,000,000 Wood
#     within 60 seconds
#
#
# Layouts:
#
#     BUSH
#     MIX
#     TREEPOLY
#     BUSHPOLY
#
#
# Each layout is tested:
#
#     DRY
#     WET
#
#
# The timed result excludes:
#
#     clear
#     field preparation
#     initial planting
#     pre-watering
#     spawning
#     positioning
#     warmup
#     synchronization
# ============================================================


TARGET = 1000000000


SEEDS = [
	1,
	2,
	3,
	4,
	5
]


MODES = [
	0,
	1,
	2,
	3
]


NAMES = {
	0: "BUSH",
	1: "MIX",
	2: "TREEPOLY",
	3: "BUSHPOLY"
}


WATER = [
	False,
	True
]


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
# We are measuring throughput, not stockpile constraints.
#
# Once we know the winning architecture we'll calculate what
# the real run needs.

sim_items = {}


for item in Items:

	sim_items[
		item
	] = 1000000000


sim_items[
	Items.Wood
] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< WOOD_BENCH_BEGIN >>>"
)

quick_print(
	"WOOD MASTER"
)

quick_print(
	"Target:",
	TARGET
)

quick_print(
	"Goal:",
	60,
	"seconds"
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
	"Trees:",
	num_unlocked(
		Unlocks.Trees
	)
)

quick_print(
	"Polyculture:",
	num_unlocked(
		Unlocks.Polyculture
	)
)

quick_print(
	"Watering:",
	num_unlocked(
		Unlocks.Watering
	)
)

quick_print(
	""
)


# ============================================================
# GLOBAL WINNER
# ============================================================

best_avg = -1

best_mode = -1

best_wet = False


# ============================================================
# TEST
# ============================================================

for mode in MODES:

	for wet in WATER:

		name = NAMES[
			mode
		]


		if wet:

			label = (
				name
				+ " WET"
			)

		else:

			label = (
				name
				+ " DRY"
			)


		total = 0

		min_time = -1

		max_time = 0

		pass_count = 0

		completed = 0


		quick_print(
			"---",
			label,
			"---"
		)


		for seed in SEEDS:

			# ================================================
			# IDENTICAL WARM BASELINE
			# ================================================

			base = simulate(
				"wood_ab",
				sim_unlocks,
				sim_items,
				{
					"TARGET": TARGET,
					"MODE": mode,
					"WET": wet,
					"RUN": False
				},
				seed,
				SIM_SPEEDUP
			)


			if base == None:

				quick_print(
					"ERROR baseline",
					label,
					seed
				)


			else:

				# ============================================
				# FULL RUN
				# ============================================

				full = simulate(
					"wood_ab",
					sim_unlocks,
					sim_items,
					{
						"TARGET": TARGET,
						"MODE": mode,
						"WET": wet,
						"RUN": True
					},
					seed,
					SIM_SPEEDUP
				)


				if full == None:

					quick_print(
						"ERROR run",
						label,
						seed
					)


				else:

					# ========================================
					# PURE TIMED THROUGHPUT
					# ========================================

					run_time = (
						full - base
					)


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


					if run_time <= 60:

						pass_count = (
							pass_count + 1
						)


					quick_print(
						"seed:",
						seed,
						"time:",
						run_time,
						"pass:",
						(
							run_time <= 60
						)
					)


		# ====================================================
		# SUMMARY
		# ====================================================

		if completed > 0:

			avg = (
				total
				/ completed
			)


			wood_per_second = (
				TARGET
				/ avg
			)


			wood_per_minute = (
				TARGET
				* 60
				/ avg
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
				"Wood/sec:",
				wood_per_second
			)

			quick_print(
				"Wood/min:",
				wood_per_minute
			)

			quick_print(
				"60s margin:",
				(
					60 - avg
				)
			)

			quick_print(
				"Passing seeds:",
				pass_count,
				"/",
				completed
			)


			if best_avg < 0:

				best_avg = avg

				best_mode = mode

				best_wet = wet


			elif avg < best_avg:

				best_avg = avg

				best_mode = mode

				best_wet = wet


		quick_print(
			""
		)


# ============================================================
# FINAL
# ============================================================

quick_print(
	"=== RESULT ==="
)


quick_print(
	"WINNER:",
	NAMES[
		best_mode
	],
	"WET:",
	best_wet
)


quick_print(
	"Average:",
	best_avg
)


quick_print(
	"Wood/min:",
	(
		TARGET
		* 60
		/ best_avg
	)
)


quick_print(
	"60s margin:",
	(
		60 - best_avg
	)
)


if best_avg <= 60:

	quick_print(
		"WOOD MASTER:",
		"PASS CAPABLE"
	)


else:

	quick_print(
		"WOOD MASTER:",
		"MORE WORK NEEDED"
	)


quick_print(
	"<<< WOOD_BENCH_END >>>"
)


print(
	"WOOD BENCH DONE\n",
	"Open output.txt"
)