import farm_config
import farm_pumpkin


# ============================================================
# PUMPKIN BENCHMARK TARGET
# ============================================================
#
# Run through sim_pumpkin.py. Measures time to gain TARGET
# Pumpkins after setup (RUN=False = setup + sync only).
#
# MODE:
#
#   1 = CURRENT (retired)
#       The old farm_rotation.farm_pumpkins() (one 32x32 mega
#       pumpkin, Fertilizer ON) was replaced by farm_pumpkin.
#       Its result is recorded in sim_pumpkin.py: 153.86 sec.
#
#  15 = PRODUCTION
#       farm_pumpkin.farm() with TARGET as its gain target.
#       Its time includes its own soil / planting.
#
#   Tiled modes: one drone per block. Each drone keeps a list
#   of its block's unfinished tiles; every pass it visits only
#   those (plant + water empty / dead ones, skip ones still
#   growing, drop grown live ones). When none are left it
#   checks two opposite corners share a mega-pumpkin id,
#   harvests, and starts the next block.
#
#   2 = TILE 6        25 x 6x6, edge to edge  (round 1 layout)
#   3 = TILE 8        16 x 8x8, edge to edge  (round 1 layout)
#   5 = TILE 6 GAP    16 x 6x6, 1-tile gaps (pitch 7)
#   6 = TILE 5 GAP    25 x 5x5, 1-tile gaps (pitch 6)
#   7 = TILE 4 GAP    32 x 4x4, 1-tile gaps (pitch 5)
#   8-11, 13          no corner check, varied watering
#   12, 14            mixed bands (see LAYOUTS)
#
#
# Round 1 (full re-scan every pass, edge-to-edge blocks):
# edge-to-edge blocks merged with their neighbours. TILE 6
# paid ~550k per "6x6" harvest (a lone 6x6 pays 110,592) and
# replanted ~180 per harvest, because one drone's harvest took
# neighbouring blocks with it. Bare-soil gaps keep every block
# its own mega pumpkin.
#
#
# Rules this relies on (pumpkin_probe.py, Pumpkins 10,
# Watering 9, Fertilizer 4):
#
#   - A Pumpkin costs 512 Carrots.
#   - Single pumpkin: 512. Fertilizer halves it (256).
#   - Grow ~2.05 sec plain, ~0.41 sec watered. 20-30% of
#     unfertilized pumpkins die at the moment they grow; a
#     grown live pumpkin stays alive.
#   - Mega pumpkin yield = 512 x pumpkins x min(side, 6).
#
# Prints one summary line per run.
# ============================================================


SYNC_DELAY = 4

QUIET_DELAY = 1

GO_DELAY = 1

MAX_SECONDS = 600

WATER_TO = 0.9


# mode: (block side, pitch, water to, check corners).
# pitch > side leaves bare-soil gaps. water to 0 = never water.
# check corners False = harvest as soon as every tile is grown
# and alive (a gapped block of grown live pumpkins has merged).

BLOCKS = {
	2: (6, 6, 0.9, True),
	3: (8, 8, 0.9, True),
	5: (6, 7, 0.9, True),
	6: (5, 6, 0.9, True),
	7: (4, 5, 0.9, True),
	8: (4, 5, 0.9, False),
	9: (4, 5, 0.5, False),
	10: (4, 5, 0.0, False),
	11: (5, 6, 0.5, False),
	13: (5, 6, 0.9, False)
}


# mode: (band heights, water to, check corners).
#
# Mixed layout: horizontal bands, each band a row of square
# blocks of that height with 1-tile gaps. Heights plus one gap
# per band must add up to the field size so the wrap-around
# seam also gets a gap. Mega pumpkins only form squares, and the
# field wraps, so leftover space is used by making whole bands
# of bigger square blocks rather than stretching edge blocks.
#
#   [5, 5, 4, 4, 4, 4] on 32x32 -> 10 x 5x5 + 24 x 4x4 slots
#   [6, 4, 4, 4, 4, 4] on 32x32 ->  4 x 6x6 + 30 x 4x4 slots
#   (the first 32 are used, one per drone).

LAYOUTS = {
	12: ([5, 5, 4, 4, 4, 4], 0.9, False),
	14: ([6, 4, 4, 4, 4, 4], 0.9, False)
}


# ============================================================
# MOVEMENT (normal farm wraps)
# ============================================================

def go_to(
	x,
	y
):

	size = get_world_size()


	while get_pos_x() != x:

		if (x - get_pos_x()) % size <= size // 2:

			move(East)

		else:

			move(West)


	while get_pos_y() != y:

		if (y - get_pos_y()) % size <= size // 2:

			move(North)

		else:

			move(South)


def water_up(
	level
):

	while get_water() < level:

		if not use_item(Items.Water):

			return


def block_cells(
	ox,
	oy,
	side
):
	# Serpentine order over the block: row by row, alternating
	# direction, so consecutive cells are adjacent.

	cells = []


	for dy in range(side):

		for i in range(side):

			dx = i


			if dy % 2 == 1:

				dx = side - 1 - i


			cells.append(
				(ox + dx, oy + dy)
			)


	return cells


# ============================================================
# BLOCK SETUP (before the synchronised start)
# ============================================================

def setup_block(
	ox,
	oy,
	side,
	water_to
):

	for cell in block_cells(ox, oy, side):

		go_to(cell[0], cell[1])


		if get_entity_type() != None:

			harvest()


		if get_ground_type() != Grounds.Soil:

			till()


		plant(Entities.Pumpkin)

		water_up(water_to)


	return 1


# ============================================================
# BLOCK RUN WORKER
# ============================================================

def block_worker(
	ox,
	oy,
	side,
	water_to,
	check_corners,
	sample_at,
	go_at,
	deadline,
	gain,
	do_run
):
	# Returns (mega harvests, plantings, pumpkins at sample).

	while get_time() < sample_at:

		pass


	start_pumpkins = num_items(Items.Pumpkin)

	target = start_pumpkins + gain


	while get_time() < go_at:

		pass


	megas = 0

	plantings = 0


	if not do_run:

		return (megas, plantings, start_pumpkins)


	all_cells = block_cells(ox, oy, side)

	pending = all_cells


	while get_time() < deadline:

		if num_items(Items.Pumpkin) >= target:

			return (megas, plantings, start_pumpkins)


		# ----------------------------------------------------
		# ONE PASS OVER UNFINISHED TILES ONLY
		# ----------------------------------------------------

		still = []


		for cell in pending:

			go_to(cell[0], cell[1])


			if get_entity_type() == Entities.Pumpkin:

				if not can_harvest():

					still.append(cell)

			else:

				# Empty (after harvest) or dead: plant again.

				plant(Entities.Pumpkin)

				water_up(water_to)

				plantings = plantings + 1

				still.append(cell)


		pending = still


		if len(pending) > 0:

			continue


		# ----------------------------------------------------
		# EVERY TILE GROWN AND ALIVE: MERGED? HARVEST
		# ----------------------------------------------------

		if check_corners:

			go_to(ox, oy)

			first = measure()

			go_to(ox + side - 1, oy + side - 1)

			last = measure()


			if first == None or first != last:

				pending = all_cells

				continue


		# The drone stands on a grown tile of this block either
		# way; harvesting any tile harvests the merged pumpkin.

		harvest()

		megas = megas + 1

		pending = all_cells


	return (megas, plantings, start_pumpkins)


# ============================================================
# TILED MODES
# ============================================================

def grid_anchors(
	side,
	pitch
):
	# Uniform grid of side x side blocks every `pitch` tiles.
	# Returns [(x, y, side), ...].

	size = get_world_size()

	per_row = 0


	while per_row * pitch + side <= size:

		per_row = per_row + 1


	anchors = []


	for i in range(per_row):

		for j in range(per_row):

			anchors.append(
				(i * pitch, j * pitch, side)
			)


	return anchors


def band_anchors(
	heights
):
	# Horizontal bands of square blocks. Each band of height h
	# holds size // (h + 1) blocks of side h, with a 1-tile gap
	# after every block and after every band.

	size = get_world_size()

	anchors = []

	y = 0


	for h in heights:

		per_row = size // (h + 1)


		for i in range(per_row):

			anchors.append(
				(i * (h + 1), y, h)
			)


		y = y + h + 1


	return anchors


def run_blocks(
	layout,
	water_to,
	check_corners
):
	# layout: [(x, y, side), ...], biggest blocks first. One
	# drone per block, up to max_drones().

	clear()


	anchors = []


	for block in layout:

		if len(anchors) < max_drones():

			anchors.append(
				block
			)


	# --------------------------------------------------------
	# SETUP (all drones)
	# --------------------------------------------------------

	handles = []


	for k in range(1, len(anchors)):

		handle = spawn_drone(
			setup_block,
			anchors[k][0],
			anchors[k][1],
			anchors[k][2],
			water_to
		)


		if handle != None:

			handles.append(handle)


	setup_block(
		anchors[0][0],
		anchors[0][1],
		anchors[0][2],
		water_to
	)


	for handle in handles:

		wait_for(handle)


	# --------------------------------------------------------
	# SYNCHRONISED RUN (or baseline)
	# --------------------------------------------------------

	sample_at = get_time() + SYNC_DELAY

	go_at = sample_at + QUIET_DELAY + GO_DELAY

	deadline = go_at + MAX_SECONDS


	handles = []


	for k in range(1, len(anchors)):

		handle = spawn_drone(
			block_worker,
			anchors[k][0],
			anchors[k][1],
			anchors[k][2],
			water_to,
			check_corners,
			sample_at,
			go_at,
			deadline,
			TARGET,
			RUN
		)


		if handle != None:

			handles.append(handle)


	totals = block_worker(
		anchors[0][0],
		anchors[0][1],
		anchors[0][2],
		water_to,
		check_corners,
		sample_at,
		go_at,
		deadline,
		TARGET,
		RUN
	)


	megas = totals[0]

	plantings = totals[1]

	start_pumpkins = totals[2]


	for handle in handles:

		result = wait_for(handle)

		megas = megas + result[0]

		plantings = plantings + result[1]


	return (
		len(handles) + 1,
		megas,
		plantings,
		num_items(Items.Pumpkin) - start_pumpkins
	)


# ============================================================
# CURRENT MODE (retired)
# ============================================================

def run_full_field():

	clear()


	if RUN:

		quick_print(
			"  MODE 1 retired: old farm_pumpkins no longer exists"
		)


	return (max_drones(), 0, 0, 0)


# ============================================================
# PRODUCTION MODE
# ============================================================

def run_production():
	# Production farm_pumpkin.farm() with TARGET as its gain
	# target. Its time includes its own soil / planting.

	clear()


	if not RUN:

		return (max_drones(), 0, 0, 0)


	farm_config.SETTINGS["pumpkin_gain_target"] = TARGET

	start_pumpkins = num_items(Items.Pumpkin)

	farm_pumpkin.farm()


	return (
		max_drones(),
		0,
		0,
		num_items(Items.Pumpkin) - start_pumpkins
	)


# ============================================================
# ENTRYPOINT
# ============================================================

if MODE == 1:

	stats = run_full_field()

elif MODE == 15:

	stats = run_production()

elif MODE in LAYOUTS:

	stats = run_blocks(
		band_anchors(LAYOUTS[MODE][0]),
		LAYOUTS[MODE][1],
		LAYOUTS[MODE][2]
	)

else:

	stats = run_blocks(
		grid_anchors(BLOCKS[MODE][0], BLOCKS[MODE][1]),
		BLOCKS[MODE][2],
		BLOCKS[MODE][3]
	)


quick_print(
	"  RUN:",
	RUN,
	"| drones:",
	stats[0],
	"| mega harvests (field cycles for mode 1):",
	stats[1],
	"| plantings:",
	stats[2],
	"| pumpkins gained:",
	stats[3],
	"| per mega:",
	stats[3] / max(1, stats[1])
)
