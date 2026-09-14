import farm_config
import farm_common
import farm_megafarm
import farm_telemetry


# ============================================================
# CONTINUOUS PUMPKIN PHASE
# ============================================================
#
# Production version of pumpkin_run.py (Pumpkin Master
# achievement: 20M Pumpkins in 1 minute).
#
# sim_pumpkin round 4, BANDS 5,5,4,4,4,4, 32x32 / 32 drones,
# seeds 1-3:
#
#     51.60 sec per +20M Pumpkins (23.3M/min)
#     vs 153.86 sec for the old single 32x32 mega pumpkin
#
# Real game: +23.8M Pumpkins in the first 60 sec, unlocked it.
#
# This production port (sim_pumpkin mode 15): 60.99 sec per
# +20M including ~8-9 sec of soil / planting.
#
#
# Rules (pumpkin_probe.py, Pumpkins 10, Watering 9):
#
#   - A Pumpkin costs 512 Carrots.
#   - Mega pumpkin yield = 512 x pumpkins x min(side, 6):
#     4x4 = 32,768, 5x5 = 64,000.
#   - Grow ~2.05 sec plain, ~0.41 sec watered. 20-30% die when
#     they grow; a grown live pumpkin stays alive.
#   - Fertilizer halves the yield, so it is never used (and is
#     off for Pumpkins in farm_config.FERTILIZE).
#   - Grown pumpkins merge with every grown neighbour, and only
#     into squares, so blocks need bare-soil gaps between them
#     (including across the wrap-around edges).
#
#
# Process:
#
#     1. clear(). The field is cut into horizontal bands of
#        BAND_HEIGHTS (+1 gap row each). Each band is a row of
#        square blocks of its height with 1-tile gaps. One drone
#        per block.
#
#     2. Every drone tills its block, plants pumpkins and waters
#        each tile to WATER_TO.
#
#     3. Each drone keeps a list of its block's unfinished tiles
#        and revisits only those: plant + water empty or dead
#        tiles, skip growing ones, drop grown ones. When none are
#        left the block is one mega pumpkin: harvest, start over.
#
#     4. Stop when Pumpkins have grown by pumpkin_gain_target, or
#        continuous_phase_max_seconds have passed, or Carrots run
#        out.
#
#
# Bands 5,5,4,4,4,4 (10 x 5x5 + 22 x 4x4) beat a plain 4x4 grid
# (54.74 sec, spare rows unused), bands 6,4,4,4,4,4 (52.37) and
# a 5x5 grid (58.04).
# ============================================================


WATER_TO = 0.9

BAND_HEIGHTS = [5, 5, 4, 4, 4, 4]


# ============================================================
# LAYOUT
# ============================================================

def band_blocks(
	heights,
	limit
):
	# [(x, y, side), ...], at most `limit` blocks. Each band of
	# height h holds size // (h + 1) blocks of side h, with a
	# 1-tile gap after every block and after every band.

	size = get_world_size()

	blocks = []

	y = 0


	for h in heights:

		if y + h + 1 > size:

			break


		for i in range(size // (h + 1)):

			if len(blocks) < limit:

				blocks.append(
					(i * (h + 1), y, h)
				)


		y = y + h + 1


	return blocks


def block_cells(
	block
):
	# Serpentine order, so consecutive cells are adjacent.

	cells = []

	side = block[2]


	for dy in range(side):

		for i in range(side):

			dx = i


			if dy % 2 == 1:

				dx = side - 1 - i


			cells.append(
				(block[0] + dx, block[1] + dy)
			)


	return cells


# ============================================================
# PLANT ONE PUMPKIN
# ============================================================

def plant_pumpkin():
	# Returns False when a pumpkin can no longer be afforded.

	if not farm_common.can_afford(
		Entities.Pumpkin,
		1
	):

		return False


	plant(Entities.Pumpkin)


	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			break


	return True


# ============================================================
# SETUP BLOCK
# ============================================================

def setup_block(
	block
):

	for cell in block_cells(block):

		farm_common.go_to(
			cell[0],
			cell[1]
		)


		if get_entity_type() != None:

			harvest()


		farm_common.make_soil()


		if not plant_pumpkin():

			return


# ============================================================
# CONTINUOUS HARVEST WORKER
# ============================================================

def harvest_block(
	block,
	target,
	deadline
):

	cells = block_cells(block)

	pending = cells


	while get_time() < deadline:

		if num_items(Items.Pumpkin) >= target:

			return


		still = []


		for cell in pending:

			farm_common.go_to(
				cell[0],
				cell[1]
			)


			if get_entity_type() == Entities.Pumpkin:

				if not can_harvest():

					still.append(cell)

			else:

				# Empty (after harvest) or dead: plant again.

				if not plant_pumpkin():

					return


				still.append(cell)


		pending = still


		if len(pending) > 0:

			continue


		# Every tile grown and alive: one mega pumpkin.

		harvest()

		pending = cells


# ============================================================
# PUMPKIN PHASE
# ============================================================

def farm():

	size = get_world_size()


	if not farm_common.can_afford(
		Entities.Pumpkin,
		size * size * 2
	):

		farm_telemetry.add_counter(
			"crop phases skipped for cost",
			1
		)

		return False


	# One drone per block, so no drone ever owns two blocks.

	blocks = band_blocks(
		BAND_HEIGHTS,
		max_drones() - num_drones() + 1
	)


	# --------------------------------------------------------
	# SOIL + PLANT
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"soil / plant blocks"
	)


	farm_common.clear_field()


	farm_megafarm.run_items(
		setup_block,
		blocks
	)


	farm_telemetry.subphase_end(
		"soil / plant blocks",
		start
	)


	# --------------------------------------------------------
	# CONTINUOUS HARVEST
	# --------------------------------------------------------

	gain = farm_config.SETTINGS["pumpkin_gain_target"]

	start_pumpkins = num_items(
		Items.Pumpkin
	)

	target = start_pumpkins + gain

	deadline = (
		get_time()
		+ farm_config.SETTINGS["continuous_phase_max_seconds"]
	)


	def worker(
		block
	):

		harvest_block(
			block,
			target,
			deadline
		)


	start = farm_telemetry.subphase_start(
		"continuous harvest"
	)


	farm_megafarm.run_items(
		worker,
		blocks
	)


	farm_telemetry.subphase_end(
		"continuous harvest",
		start
	)


	gained = (
		num_items(Items.Pumpkin)
		- start_pumpkins
	)


	farm_telemetry.add_counter(
		"pumpkins gained in continuous harvest",
		gained
	)


	if gained < gain:

		farm_telemetry.add_counter(
			"pumpkin phases stopped by time cap or cost",
			1
		)


	return True
