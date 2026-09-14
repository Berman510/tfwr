# ============================================================
# HAY FULL-COMPANION A/B/C
# ============================================================
#
# MODE:
#
#   0 = SPARSE
#       Optimized first-generation companions only.
#
#   1 = FULL
#       Optimized first generation, then fill every unused
#       companion checkerboard tile.
#
#   2 = FIXED
#       No companion scan.
#       Fully-populated deterministic companion checkerboard.
#
#
# IMPORTANT:
#
# Every simulation warms up for WARMUP seconds before the
# inventory baseline is recorded.
#
# Therefore this measures STEADY-STATE Hay throughput.
# ============================================================


TARGET = 200000000


WARMUP = 10


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
	2
]


NAMES = {
	0: "SPARSE",
	1: "FULL",
	2: "FIXED"
}


SIM_SPEEDUP = 10000


# ============================================================
# CURRENT REAL-SAVE UNLOCK LEVELS
# ============================================================

sim_unlocks = {}


for unlock_type in Unlocks:

	sim_unlocks[
		unlock_type
	] = num_unlocked(
		unlock_type
	)


# ============================================================
# LARGE TEST INVENTORY
# ============================================================
#
# Companion setup is outside the measured window.
#
# Give it enough resources that setup affordability never
# becomes part of this algorithm test.
# ============================================================

sim_items = {}


for item in Items:

	sim_items[
		item
	] = 1000000000


# Start Hay at zero simply to make the simulated inventory
# easier to reason about.

sim_items[
	Items.Hay
] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< HAY_FC_BEGIN >>>"
)

quick_print(
	"HAY FULL-COMPANION TEST"
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
	"Warmup:",
	WARMUP,
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
	"Grass:",
	num_unlocked(
		Unlocks.Grass
	)
)

quick_print(
	"Polyculture:",
	num_unlocked(
		Unlocks.Polyculture
	)
)

quick_print(
	"Leaderboard:",
	num_unlocked(
		Unlocks.Leaderboard
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


# ============================================================
# TEST EACH LAYOUT
# ============================================================

for mode in MODES:

	name = NAMES[
		mode
	]


	total = 0

	min_time = -1

	max_time = 0

	pass_count = 0

	completed = 0


	quick_print(
		"---",
		name,
		"---"
	)


	for seed in SEEDS:

		# ====================================================
		# BASELINE
		# ====================================================
		#
		# Identical:
		#
		#   clear
		#   setup
		#   spawn
		#   position
		#   warmup
		#   quiet period
		#   inventory snapshot
		#   final synchronization
		#
		# Then terminate.

		base = simulate(
			"hay_fc",
			sim_unlocks,
			sim_items,
			{
				"TARGET": TARGET,
				"WARMUP": WARMUP,
				"MODE": mode,
				"RUN": False
			},
			seed,
			SIM_SPEEDUP
		)


		if base == None:

			quick_print(
				"ERROR baseline",
				name,
				seed
			)


		else:

			# ================================================
			# FULL RUN
			# ================================================

			full = simulate(
				"hay_fc",
				sim_unlocks,
				sim_items,
				{
					"TARGET": TARGET,
					"WARMUP": WARMUP,
					"MODE": mode,
					"RUN": True
				},
				seed,
				SIM_SPEEDUP
			)


			if full == None:

				quick_print(
					"ERROR run",
					name,
					seed
				)


			else:

				# ============================================
				# PURE STEADY-STATE FARM TIME
				# ============================================

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


	# ========================================================
	# SUMMARY
	# ========================================================

	if completed > 0:

		avg = (
			total
			/ completed
		)


		hay_per_second = (
			TARGET
			/ avg
		)


		hay_per_minute = (
			TARGET
			* 60
			/ avg
		)


		margin = (
			60 - avg
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
			"Hay/sec:",
			hay_per_second
		)

		quick_print(
			"Hay/min:",
			hay_per_minute
		)

		quick_print(
			"60s margin:",
			margin
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


		elif avg < best_avg:

			best_avg = avg

			best_mode = mode


	quick_print(
		""
	)


# ============================================================
# FINAL RESULT
# ============================================================

quick_print(
	"=== RESULT ==="
)


if best_mode >= 0:

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
		"Hay/min:",
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
			"HAY MASTER:",
			"PASS CAPABLE"
		)


	else:

		quick_print(
			"HAY MASTER:",
			"MORE WORK NEEDED"
		)


quick_print(
	"<<< HAY_FC_END >>>"
)


print(
	"HAY FULL-COMPANION TEST DONE\n",
	"Open output.txt"
)
