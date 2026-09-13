import farm_common
import farm_unlocks
import farm_rotation
import farm_maze
import farm_dinosaurs


# ============================================================
# MAIN CONTROLLER
# ============================================================
#
# Every main cycle:
#
#     1. Invest surplus resources in upgrades
#
#     2. Restore Gold reserve if necessary
#
#     3. Restore Bone reserve if necessary
#
#     4. Run one complete normal crop rotation
#
#
# AUTO UNLOCKS ONLY RUN HERE.
#
# They are deliberately never called in the middle of a crop
# phase.
#
# This is especially important because upgrading Expand clears
# the farm.
# ============================================================


while True:

	# ========================================================
	# 1. AUTOMATIC RESEARCH / UPGRADES
	# ========================================================

	start = farm_common.timing_start()


	upgrades = farm_unlocks.manage()


	if upgrades > 0:

		farm_common.timing_end(
			"AUTO UNLOCK",
			start
		)

		quick_print(
			"[UNLOCK]",
			"purchased:",
			upgrades,
			"world:",
			get_world_size(),
			"x",
			get_world_size(),
			"drones:",
			max_drones()
		)


	# ========================================================
	# 2. MAZES / GOLD
	# ========================================================

	start = farm_common.timing_start()


	maze_ran = farm_maze.manage()


	if maze_ran:

		farm_common.timing_end(
			"MAZE BATCH",
			start
		)


	# ========================================================
	# 3. DINOSAURS / BONES
	# ========================================================

	start = farm_common.timing_start()


	dinosaur_ran = farm_dinosaurs.manage()


	if dinosaur_ran:

		farm_common.timing_end(
			"DINOSAUR RUN",
			start
		)


	# ========================================================
	# 4. NORMAL FULL-FIELD ROTATION
	# ========================================================

	farm_rotation.run_cycle()