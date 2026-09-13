# ============================================================
# CARROT A/B BENCHMARK
# ============================================================
#
# Goal: Carrot Master = "Farm 200 million carrots in 1 minute."
#       (Steam CARROT_MASTER, stat "carrot")
#
# Result = simulated seconds to gain TARGET Carrots, measured
# after setup (RUN=False baseline subtracted, like sim_wood).
# <= 60 sec wins the achievement.
#
#
# MODE (see carrot_ab.py):
#
#   1 = CURRENT              farm_carrots + farm_polyculture
#   2 = PAIR SWEEP           checkerboard carrots, re-roll until
#                            the companion request is on a
#                            companion tile, water, place it
#   3 = PAIR SWEEP NO WATER  mode 2 without watering
#   4 = PAIR SWEEP NO REROLL keep unsafe requests (no bonus)
#
#
# Probe results (carrot_probe.py, 32x32, Carrots 10,
# Polyculture 5, Watering 9, Fertilizer 4, seed 1):
#
#   - Carrot costs 512 Hay + 512 Wood. Grass/Bush/Tree free.
#   - Harvest with no companion: 512 Carrots (12/12).
#   - Exact companion type on the exact requested tile: 81,920
#     (160x, 12/12), even when the companion is NOT mature
#     (6/12 were young).
#   - Wrong type on the right tile: 512. Right type one tile
#     off: 512.
#   - The request (Bush / Tree / Grass, within 3 tiles, never
#     the carrot tile) is fixed at planting (0/28 changed).
#   - Grow: ~5.9 sec plain, ~1.1 sec watered, ~0.03 sec with
#     Fertilizer, but Fertilizer HALVES the yield (256).
#
#   => 200M / 81,920 = ~2,442 bonus harvests per minute.
#
#
# Round 1 (200M Carrots, seeds 1-3, real Hay/Wood/Water,
# Fertilizer 317, carrots on a 1/2 checkerboard):
#
#   CURRENT               244.16 sec    49.1M/min   0/3 pass
#   PAIR SWEEP             52.10 sec   230.3M/min   3/3 pass
#   PAIR SWEEP NO WATER    58.75 sec   204.3M/min   3/3 pass
#   PAIR SWEEP NO REROLL   50.02 sec   239.9M/min   3/3 pass  WINNER
#
#   Only ~61% (PAIR SWEEP) / ~69% (NO REROLL) of placed
#   companions paid the bonus: neighbouring carrots' requests
#   overwrote companions still in use. Watering is worth it.
#   CURRENT also fertilizes carrots (farm_config.FERTILIZE),
#   which halves their yield while Fertilizer lasts.
#
# Round 2: lower carrot density to cut companion collisions.
#
#   NO REROLL density 1/2    50.03 sec   239.9M/min   3/3
#   NO REROLL density 1/4    43.66 sec   274.8M/min   3/3
#   NO REROLL density 1/8    46.86 sec   256.1M/min   3/3
#   PAIR SWEEP density 1/4   40.87 sec   293.6M/min   3/3  WINNER
#
#   1/4 density: ~87% of placed companions paid (vs ~70% at
#   1/2). 1/8 placed every companion but drones walked and
#   waited more. PAIR SWEEP 1/4 re-rolls ~0.32x per carrot,
#   gives every carrot a companion, and needs ~2,890 harvests
#   per 200M. 6x faster than CURRENT (244.16 sec).
#
#
# Inventory: everything 1e9 EXCEPT Hay, Wood, Water and
# Fertilizer, which copy the REAL inventory, and Carrot, which
# starts at 0.
#
#
# PROBE = True re-runs carrot_probe.py instead.
#
#
# Output:
#
#   output.txt, between
#
#       <<< CARROT_BENCH_BEGIN >>>
#       <<< CARROT_BENCH_END >>>
#
# Does NOT modify the real farm.
# ============================================================


PROBE = False


TARGET = 200000000

GOAL_SECONDS = 60


SEEDS = [
	1,
	2,
	3
]


# Round 3: verify the production port (farm_carrot) only. Its
# time includes its own soil / planting (~16 sec), so expect
# roughly ~57 sec (vs PAIR SWEEP 1/4's 40.87 sec run-only).
#
# Round 3 result (seeds 1-3):
#
#   PRODUCTION  50.95 sec incl. setup   3/3 pass
#   (50.70 / 51.16 / 50.99), +200.4M / +200.7M / +200.6M.
#
# Real game (carrot_run): +251M Carrots in 50.95 sec, 200M at
# ~41 sec. Carrot Master unlocked.

MODES = [
	8
]


NAMES = {
	1: "CURRENT",
	2: "PAIR SWEEP",
	3: "PAIR SWEEP NO WATER",
	4: "NO REROLL density 1/2",
	5: "NO REROLL density 1/4",
	6: "NO REROLL density 1/8",
	7: "PAIR SWEEP density 1/4",
	8: "PRODUCTION (farm_carrot, incl. setup)"
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
# TEST INVENTORY
# ============================================================

sim_items = {}


for item in Items:

	sim_items[
		item
	] = 1000000000


for item in [Items.Hay, Items.Wood, Items.Water, Items.Fertilizer]:

	sim_items[
		item
	] = num_items(
		item
	)


sim_items[
	Items.Carrot
] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< CARROT_BENCH_BEGIN >>>"
)

quick_print(
	"CARROT"
)

quick_print(
	"Target:",
	TARGET,
	"Carrots within",
	GOAL_SECONDS,
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
	"Carrots:",
	num_unlocked(Unlocks.Carrots),
	"| Polyculture:",
	num_unlocked(Unlocks.Polyculture),
	"| Watering:",
	num_unlocked(Unlocks.Watering)
)

quick_print(
	"Carrot cost:",
	get_cost(Entities.Carrot)
)

quick_print(
	"Real stock | Hay:",
	sim_items[Items.Hay],
	"| Wood:",
	sim_items[Items.Wood],
	"| Water:",
	sim_items[Items.Water],
	"| Fertilizer:",
	sim_items[Items.Fertilizer]
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
		"carrot_probe",
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


	for mode in MODES:

		label = NAMES[
			mode
		]


		total = 0

		min_time = -1

		max_time = 0

		completed = 0

		passes = 0


		quick_print(
			"---",
			label,
			"---"
		)


		for seed in SEEDS:

			base = simulate(
				"carrot_ab",
				sim_unlocks,
				sim_items,
				{
					"MODE": mode,
					"TARGET": TARGET,
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

				continue


			full = simulate(
				"carrot_ab",
				sim_unlocks,
				sim_items,
				{
					"MODE": mode,
					"TARGET": TARGET,
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

				continue


			run_time = (
				full - base
			)


			completed = (
				completed + 1
			)


			total = (
				total + run_time
			)


			if min_time < 0 or run_time < min_time:

				min_time = run_time


			if run_time > max_time:

				max_time = run_time


			if run_time <= GOAL_SECONDS:

				passes = (
					passes + 1
				)


			quick_print(
				"seed:",
				seed,
				"setup:",
				base,
				"time:",
				run_time,
				"Carrots/min:",
				TARGET * 60 / run_time,
				"pass:",
				run_time <= GOAL_SECONDS
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
				"Carrots/min:",
				TARGET * 60 / avg
			)

			quick_print(
				"Passing seeds:",
				passes,
				"/",
				completed
			)


			if best_avg < 0 or avg < best_avg:

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
			"Carrots/min:",
			TARGET * 60 / best_avg
		)

		quick_print(
			"60s margin:",
			GOAL_SECONDS - best_avg
		)


		if best_avg <= GOAL_SECONDS:

			quick_print(
				"CARROT MASTER:",
				"PASS CAPABLE"
			)

		else:

			quick_print(
				"CARROT MASTER:",
				"MORE WORK NEEDED"
			)


quick_print(
	"<<< CARROT_BENCH_END >>>"
)


print(
	"CARROT BENCH DONE\n",
	"Open output.txt"
)
