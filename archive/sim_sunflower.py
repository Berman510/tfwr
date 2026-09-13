# ============================================================
# SUNFLOWER / POWER A/B BENCHMARK
# ============================================================
#
# Goal: Sunflower Master = "Farm 12000 power in 1 minute."
#       (Steam SUNFLOWER_MASTER, stat "power")
#
# Result = simulated seconds to gain TARGET Power, measured
# after setup (RUN=False baseline subtracted, like sim_wood).
# <= 60 sec wins the achievement.
#
#
# MODE (see sunflower_ab.py):
#
#   1 = FIELD SWEEP       production farm_sunflowers, repeated
#   2 = REROLL 15         keep every tile a 15-petal flower:
#                         harvest mature 15s, replant and
#                         re-roll young flowers until 15, water
#   3 = REROLL 15 + FERT  mode 2, plus Fertilizer while it lasts
#   4 = MATURE 15         plant once, water; harvest mature 15s
#                         (8 Power) and mature non-15s (1 Power)
#
#
# Probe results (sunflower_probe.py, 32x32, Sunflowers 1,
# Speed 5, Fertilizer 4, Watering 9, seed 1):
#
#   - Sunflower costs 1 Carrot.
#   - Petals (7-15) are fixed at planting: measure() works on
#     a young flower and never changed while growing (0/40).
#   - Base harvest: ~1 Power at any petal count.
#   - Bonus harvest: 8 Power (not 5x) when the flower has the
#     max petals on the field AND >= 10 sunflowers are on the
#     field, counting the one harvested. Ties all get it.
#   - Young flowers count toward the 10.
#   - Grow: ~6.8 sec plain, ~1.3 sec pre-watered, ~0.13 sec
#     with Fertilizer.
#   - Move: 0.03 sec and 0.03 Power.
#   - Readings of ~0.77-0.8 instead of 1 are small Power costs
#     taken between the two inventory reads.
#
#   => ~1,500 bonus harvests (8 Power) per minute.
#
#
# Round 1 (12,000 Power, seeds 1-3, real Fertilizer 869):
#
#   FIELD SWEEP        86.07 sec    8,366 Power/min   0/3 pass
#   REROLL 15          37.96 sec   18,968 Power/min   3/3 pass
#   REROLL 15 + FERT   48.76 sec   14,767 Power/min   3/3 pass
#   MATURE 15          25.97 sec   27,726 Power/min   3/3 pass  WINNER
#
#   0 anomalies everywhere: harvesting a young flower clears
#   its tile. REROLL spends ~8 unpaid re-rolls per 15. FERT
#   harvested ~30% more but spent ~5,100 Power on actions
#   (vs ~1,200). MATURE 15 wastes no actions: ~800 bonus
#   (8) + ~6,500 normal (1) harvests per run, ~16 sec setup,
#   no Fertilizer.
#
#
# Inventory: everything 1e9 EXCEPT Fertilizer, Water and
# Carrot, which copy the REAL inventory so the result holds
# in the real game (Fertilizer is scarce). Power starts at
# 1,000,000 so moves never run dry.
#
#
# PROBE = True re-runs sunflower_probe.py instead.
#
#
# Output:
#
#   output.txt, between
#
#       <<< SUNFLOWER_BENCH_BEGIN >>>
#       <<< SUNFLOWER_BENCH_END >>>
#
# Does NOT modify the real farm.
# ============================================================


PROBE = False


TARGET = 12000

GOAL_SECONDS = 60


SEEDS = [
	1,
	2,
	3
]


# Round 2: verify the production port only. Its time
# includes farm_sunflower's own planting / watering (~16 sec),
# so expect ~42 sec (vs MATURE 15's 25.97 sec run-only).
#
# Round 2 result (seeds 1-3):
#
#   PRODUCTION  35.61 sec incl. setup   3/3 pass   0 anomalies
#   (35.43 / 35.68 / 35.72). Reported gain ~11,710 because it
#   is measured from before planting; farm_sunflower counts
#   its gain target from after planting.
#
# Real game (sunflower_run): +15,006 Power in 32.63 sec and
# +15,007 in 32.25 sec. Sunflower Master unlocked.

MODES = [
	5
]


NAMES = {
	1: "FIELD SWEEP",
	2: "REROLL 15",
	3: "REROLL 15 + FERT",
	4: "MATURE 15",
	5: "PRODUCTION (farm_sunflower, incl. setup)"
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


# Real amounts for the consumables the strategies depend on.

for item in [Items.Fertilizer, Items.Water, Items.Carrot]:

	sim_items[
		item
	] = num_items(
		item
	)


sim_items[
	Items.Power
] = 1000000


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< SUNFLOWER_BENCH_BEGIN >>>"
)

quick_print(
	"SUNFLOWER / POWER"
)

quick_print(
	"Target:",
	TARGET,
	"Power within",
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
	"Sunflowers:",
	num_unlocked(Unlocks.Sunflowers),
	"| Watering:",
	num_unlocked(Unlocks.Watering),
	"| Fertilizer:",
	num_unlocked(Unlocks.Fertilizer)
)

quick_print(
	"Real stock | Fertilizer:",
	sim_items[Items.Fertilizer],
	"| Water:",
	sim_items[Items.Water],
	"| Carrot:",
	sim_items[Items.Carrot]
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
		"sunflower_probe",
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
				"sunflower_ab",
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
				"sunflower_ab",
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
				"Power/min:",
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
				"Power/min:",
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
			"Power/min:",
			TARGET * 60 / best_avg
		)

		quick_print(
			"60s margin:",
			GOAL_SECONDS - best_avg
		)


		if best_avg <= GOAL_SECONDS:

			quick_print(
				"SUNFLOWER MASTER:",
				"PASS CAPABLE"
			)

		else:

			quick_print(
				"SUNFLOWER MASTER:",
				"MORE WORK NEEDED"
			)


quick_print(
	"<<< SUNFLOWER_BENCH_END >>>"
)


print(
	"SUNFLOWER BENCH DONE\n",
	"Open output.txt"
)
