# ============================================================
# PUMPKIN A/B BENCHMARK
# ============================================================
#
# Goal: Pumpkin Master = "Farm 20 million pumpkins in 1 minute."
#       (Steam PUMPKIN_MASTER, stat "pumpkin")
#
# Result = simulated seconds to gain TARGET Pumpkins, measured
# after setup (RUN=False baseline subtracted, like sim_wood).
# <= 60 sec wins the achievement.
#
#
# MODE (see pumpkin_ab.py):
#
#   1 = CURRENT                 farm_pumpkins, Fertilizer ON
#   2 = TILE 6                  25 x 6x6 blocks, 1 drone each
#   3 = TILE 8                  16 x 8x8 blocks, 1 drone each
#
#
# Probe results (pumpkin_probe.py, 32x32, Pumpkins 10,
# Watering 9, Fertilizer 4, seed 1):
#
#   - Pumpkin costs 512 Carrots.
#   - Single pumpkin: 512. Fertilizer HALVES it (256).
#   - Grow: ~2.05 sec plain, ~0.41 sec watered, ~0.04 sec
#     fertilized. 20-30% of unfertilized pumpkins die.
#   - Mega pumpkin yield = 512 x pumpkins x min(side, 6):
#
#       side 2   4,096  (1,024 each)   2.25 sec, 1 drone
#       side 3  13,824  (1,536 each)   3.29 sec
#       side 4  32,768  (2,048 each)   5.38 sec
#       side 6 110,592  (3,072 each)  17.81 sec
#       side 8 196,608  (3,072 each)  31.23 sec
#
#   => every pumpkin in a mega of side >= 6 pays 3,072.
#      20M / 3,072 = ~6,510 pumpkins harvested per minute.
#
#
# Round 1 (20M Pumpkins, seeds 1-3, real Carrot/Water,
# Fertilizer 1,607; repair re-scanned every tile each pass):
#
#   CURRENT   153.86 sec    7.80M/min   0/3  (8 field cycles)
#   TILE 6    104.23 sec   11.51M/min   0/3
#   TILE 8    147.53 sec    8.13M/min   0/3
#
#   Edge-to-edge blocks merged with their neighbours: TILE 6
#   paid ~550k per harvest (a lone 6x6 pays 110,592) and
#   replanted ~180 pumpkins per harvest, as one drone's harvest
#   took neighbouring blocks with it.
#
# Round 2: bare-soil gaps between blocks, and each drone only
# revisits unfinished tiles (a grown live pumpkin can't die).
#
#   TILE 6 GAP   82.77 sec   14.5M/min   0/3   16 drones
#   TILE 5 GAP   65.21 sec   18.4M/min   0/3   25 drones
#   TILE 4 GAP   63.16 sec   19.0M/min   0/3   32 drones
#
#   Every harvest paid exactly a lone block (110,592 / 64,000
#   / 32,768): gaps work. ~1.2 plantings per tile. Still ~5%
#   short.
#
# Round 3: no corner check (harvest as soon as every tile is
# grown and alive), and less watering per planting.
#
#   8 = TILE 4 GAP, no check, water to 0.9
#   9 = TILE 4 GAP, no check, water to 0.5
#  10 = TILE 4 GAP, no check, no water
#  11 = TILE 5 GAP, no check, water to 0.5
#
#   8   54.74 sec   21.9M/min   3/3   32 x 4x4
#   9   60.40 sec   19.9M/min   1/3
#  10  136.25 sec    8.8M/min   0/3
#  11   58.39 sec   20.6M/min   3/3   25 x 5x5
#
#   Watering to 0.9 matters. 5x5 beat 4x4 at equal watering.
#
# Round 4: use the whole field. Mega pumpkins only form squares
# and the field wraps, so leftover rows become bands of bigger
# square blocks (still gapped, one drone per block, water 0.9):
#
#  12 = BANDS 5,5,4,4,4,4   10 x 5x5 + 22 x 4x4
#  13 = TILE 5 GAP, no check, water to 0.9   25 x 5x5
#  14 = BANDS 6,4,4,4,4,4    4 x 6x6 + 28 x 4x4
#
#  12   51.60 sec   23.3M/min   3/3   WINNER (~505 megas)
#  13   58.04 sec   20.7M/min   3/3
#  14   52.37 sec   22.9M/min   3/3
#
#   Filling spare rows with bigger square blocks beat the plain
#   4x4 grid (54.74) by ~6%. -> pumpkin_run.py uses mode 12.
#
#   Real game (pumpkin_run): +23.8M Pumpkins in the first 60
#   sec (+25.1M in 64.83 sec). Pumpkin Master unlocked.
#
# Round 5: verify the production port (farm_pumpkin) only. Its
# time includes its own soil / planting.
#
#  15 = PRODUCTION (farm_pumpkin, incl. setup)
#
#  15   60.99 sec (60.59 / 61.60 / 60.78), incl. ~8-9 sec of
#       soil / planting: ~52 sec of harvesting, matching mode 12.
#
#
# Inventory: everything 1e9 EXCEPT Carrot, Water and Fertilizer,
# which copy the REAL inventory, and Pumpkin, which starts at 0.
#
#
# PROBE = True re-runs pumpkin_probe.py instead.
#
#
# Output:
#
#   output.txt, between
#
#       <<< PUMPKIN_BENCH_BEGIN >>>
#       <<< PUMPKIN_BENCH_END >>>
#
# Does NOT modify the real farm.
# ============================================================


PROBE = False


TARGET = 20000000

GOAL_SECONDS = 60


SEEDS = [
	1,
	2,
	3
]


MODES = [
	15
]


NAMES = {
	1: "CURRENT",
	2: "TILE 6",
	3: "TILE 8",
	5: "TILE 6 GAP",
	6: "TILE 5 GAP",
	7: "TILE 4 GAP",
	8: "TILE 4 GAP NOCHECK W0.9",
	9: "TILE 4 GAP NOCHECK W0.5",
	10: "TILE 4 GAP NOCHECK NO WATER",
	11: "TILE 5 GAP NOCHECK W0.5",
	12: "BANDS 5,5,4,4,4,4 W0.9",
	13: "TILE 5 GAP NOCHECK W0.9",
	14: "BANDS 6,4,4,4,4,4 W0.9",
	15: "PRODUCTION (farm_pumpkin, incl. setup)"
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


for item in [Items.Carrot, Items.Water, Items.Fertilizer]:

	sim_items[
		item
	] = num_items(
		item
	)


sim_items[
	Items.Pumpkin
] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< PUMPKIN_BENCH_BEGIN >>>"
)

quick_print(
	"PUMPKIN"
)

quick_print(
	"Target:",
	TARGET,
	"Pumpkins within",
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
	"Pumpkins:",
	num_unlocked(Unlocks.Pumpkins),
	"| Watering:",
	num_unlocked(Unlocks.Watering),
	"| Fertilizer:",
	num_unlocked(Unlocks.Fertilizer)
)

quick_print(
	"Pumpkin cost:",
	get_cost(Entities.Pumpkin)
)

quick_print(
	"Real stock | Carrot:",
	sim_items[Items.Carrot],
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
		"pumpkin_probe",
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
				"pumpkin_ab",
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
				"pumpkin_ab",
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
				"Pumpkins/min:",
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
				"Pumpkins/min:",
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
			"Pumpkins/min:",
			TARGET * 60 / best_avg
		)

		quick_print(
			"60s margin:",
			GOAL_SECONDS - best_avg
		)


		if best_avg <= GOAL_SECONDS:

			quick_print(
				"PUMPKIN MASTER:",
				"PASS CAPABLE"
			)

		else:

			quick_print(
				"PUMPKIN MASTER:",
				"MORE WORK NEEDED"
			)


quick_print(
	"<<< PUMPKIN_BENCH_END >>>"
)


print(
	"PUMPKIN BENCH DONE\n",
	"Open output.txt"
)
