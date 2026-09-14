# ============================================================
# PUMPKIN MASTER RUNNER
# ============================================================
#
# Achievement (Steam PUMPKIN_MASTER, stat "pumpkin"):
#
#     "Farm 20 million pumpkins in 1 minute."
#
#
# Proven simulation (sim_pumpkin round 4, mode 12 BANDS
# 5,5,4,4,4,4, 32x32 / 32 drones, real Carrot / Water stock):
#
#     Average:  51.60 sec per +20M Pumpkins after setup
#     Seeds:    3 / 3 pass (51.45 / 51.72 / 51.65)
#
#
# Rules (pumpkin_probe.py, Pumpkins 10, Watering 9):
#
#   - A Pumpkin costs 512 Carrots.
#   - Mega pumpkin yield = 512 x pumpkins x min(side, 6):
#     4x4 = 32,768, 5x5 = 64,000. Fertilizer halves yield:
#     never used.
#   - 20-30% of pumpkins die when they grow; a grown live
#     pumpkin stays alive.
#   - Grown pumpkins merge with any grown neighbours, so
#     blocks need a bare-soil gap between them (the field
#     wraps, so the far edges need one too).
#
#
# Method:
#
#     1. clear(). The field is cut into horizontal bands of
#        heights 5, 5, 4, 4, 4, 4 (+1 gap row each = 32). Each
#        band is a row of square blocks of its height with
#        1-tile gaps: 10 x 5x5, then 4x4 blocks, one drone each.
#
#     2. Every drone tills its block, plants pumpkins and
#        waters each tile to 0.9.
#
#     3. All drones synchronise and share one Pumpkin baseline.
#
#     4. Each drone keeps a list of its block's unfinished
#        tiles and revisits only those: plant + water empty or
#        dead tiles, skip growing ones, drop grown ones. When
#        none are left, the block is one mega pumpkin: harvest
#        and start again.
#
#     5. Stop when Pumpkins have grown by TARGET_GAIN, or after
#        MAX_SECONDS.
#
#
# Stop main first so every drone is free.
#
# This file intentionally imports nothing.
# ============================================================


TARGET_GAIN = 25000000

MAX_SECONDS = 120

WATER_TO = 0.9

BAND_HEIGHTS = [5, 5, 4, 4, 4, 4]

SYNC_DELAY = 4

QUIET_DELAY = 1

GO_DELAY = 1


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


def water_up():

	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			return


# ============================================================
# LAYOUT
# ============================================================

def band_anchors(
	heights
):
	# [(x, y, side), ...]: each band of height h holds
	# size // (h + 1) blocks of side h, with a 1-tile gap after
	# every block and after every band.

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


def block_cells(
	ox,
	oy,
	side
):
	# Serpentine order, so consecutive cells are adjacent.

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
# SETUP WORKER
# ============================================================

def setup_block(
	ox,
	oy,
	side
):

	for cell in block_cells(ox, oy, side):

		go_to(cell[0], cell[1])


		if get_entity_type() != None:

			harvest()


		if get_ground_type() != Grounds.Soil:

			till()


		plant(Entities.Pumpkin)

		water_up()


	return 1


# ============================================================
# RUN WORKER
# ============================================================

def block_worker(
	ox,
	oy,
	side,
	sample_at,
	go_at,
	deadline,
	gain,
	mark_60
):
	# Returns (mega harvests, plantings, start pumpkins,
	# pumpkins 60 sec after go or -1, finish time).

	while get_time() < sample_at:

		pass


	start_pumpkins = num_items(Items.Pumpkin)

	target = start_pumpkins + gain


	while get_time() < go_at:

		pass


	megas = 0

	plantings = 0

	pumpkins_60 = -1

	minute = go_at + 60


	all_cells = block_cells(ox, oy, side)

	pending = all_cells


	while get_time() < deadline:

		if mark_60 and pumpkins_60 < 0 and get_time() >= minute:

			pumpkins_60 = num_items(Items.Pumpkin)


		if num_items(Items.Pumpkin) >= target:

			return (megas, plantings, start_pumpkins, pumpkins_60, get_time())


		still = []


		for cell in pending:

			go_to(cell[0], cell[1])


			if get_entity_type() == Entities.Pumpkin:

				if not can_harvest():

					still.append(cell)

			else:

				plant(Entities.Pumpkin)

				water_up()

				plantings = plantings + 1

				still.append(cell)


		pending = still


		if len(pending) > 0:

			continue


		# Every tile grown and alive: one mega pumpkin.

		harvest()

		megas = megas + 1

		pending = all_cells


	return (megas, plantings, start_pumpkins, pumpkins_60, get_time())


# ============================================================
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< PUMPKIN_RUN_BEGIN >>>"
)


anchors = []


for block in band_anchors(BAND_HEIGHTS):

	if len(anchors) < max_drones():

		anchors.append(block)


quick_print(
	"[PUMPKIN] world:",
	get_world_size(),
	"x",
	get_world_size(),
	"| blocks:",
	len(anchors),
	"| target gain:",
	TARGET_GAIN,
	"| pumpkin cost:",
	get_cost(Entities.Pumpkin),
	"| carrots:",
	num_items(Items.Carrot),
	"| water:",
	num_items(Items.Water)
)


clear()


# ------------------------------------------------------------
# SETUP
# ------------------------------------------------------------

setup_start = get_time()


handles = []


for k in range(1, len(anchors)):

	handle = spawn_drone(
		setup_block,
		anchors[k][0],
		anchors[k][1],
		anchors[k][2]
	)


	if handle != None:

		handles.append(handle)


setup_block(
	anchors[0][0],
	anchors[0][1],
	anchors[0][2]
)


for handle in handles:

	wait_for(handle)


quick_print(
	"[PUMPKIN] setup seconds:",
	get_time() - setup_start
)


# ------------------------------------------------------------
# SYNCHRONISED RUN
# ------------------------------------------------------------

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
		sample_at,
		go_at,
		deadline,
		TARGET_GAIN,
		False
	)


	if handle != None:

		handles.append(handle)


quick_print(
	"[PUMPKIN] workers:",
	len(handles) + 1
)


totals = block_worker(
	anchors[0][0],
	anchors[0][1],
	anchors[0][2],
	sample_at,
	go_at,
	deadline,
	TARGET_GAIN,
	True
)


megas = totals[0]

plantings = totals[1]

start_pumpkins = totals[2]

pumpkins_60 = totals[3]

finish = totals[4]


for handle in handles:

	result = wait_for(handle)

	megas = megas + result[0]

	plantings = plantings + result[1]


	if result[4] > finish:

		finish = result[4]


gained = num_items(Items.Pumpkin) - start_pumpkins

elapsed = finish - go_at


# ============================================================
# RESULT
# ============================================================

quick_print(
	"[PUMPKIN] pumpkins gained:",
	gained,
	"| seconds:",
	elapsed,
	"| Pumpkins/min:",
	gained * 60 / elapsed
)

quick_print(
	"[PUMPKIN] mega harvests:",
	megas,
	"| plantings:",
	plantings,
	"| avg per mega:",
	gained / max(1, megas)
)


if pumpkins_60 >= 0:

	quick_print(
		"[PUMPKIN] pumpkins gained in first 60 sec:",
		pumpkins_60 - start_pumpkins
	)

else:

	quick_print(
		"[PUMPKIN] target reached before 60 sec"
	)


if gained >= 20000000 and elapsed <= 60:

	quick_print(
		"[PUMPKIN] 20M+ Pumpkins inside 60 sec - check for Pumpkin Master"
	)

else:

	quick_print(
		"[PUMPKIN] under 20M in 60 sec - check results"
	)


quick_print(
	"<<< PUMPKIN_RUN_END >>>"
)


print(
	"PUMPKIN RUN COMPLETE\n",
	"Gained:",
	gained,
	"in",
	elapsed,
	"sec\n",
	"Open output.txt"
)
