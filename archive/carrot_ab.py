import farm_config
import farm_carrot


# ============================================================
# CARROT BENCHMARK TARGET
# ============================================================
#
# Run through sim_carrot.py. Measures time to gain TARGET
# Carrots after setup (RUN=False = setup + sync only).
#
# MODE:
#
#   1 = CURRENT
#       Production farm_rotation.farm_carrots() (full soil
#       field + farm_polyculture), repeated.
#
#   2 = PAIR SWEEP
#       Carrots on one checkerboard parity, companions on the
#       other. Each drone sweeps its rows; every mature carrot
#       is harvested, replanted (re-rolled until its companion
#       request lands on a companion-parity tile), watered,
#       and its requested companion is planted if missing.
#
#   3 = PAIR SWEEP, NO WATER
#       Mode 2 without watering.
#
#   4 = PAIR SWEEP, NO RE-ROLL
#       Mode 2, but if the request lands on a carrot tile the
#       carrot keeps it and gets no companion (512 instead of
#       81,920).
#
#   5 = NO RE-ROLL, carrot density 1/4
#   6 = NO RE-ROLL, carrot density 1/8
#   7 = PAIR SWEEP (re-roll), carrot density 1/4
#
#       Round 1 showed ~30-40% of placed companions were
#       overwritten by neighbouring carrots' requests on the
#       1/2-density checkerboard. Fewer carrots per row keep the
#       drone just as busy (sweep time was ~5x the watered grow
#       time) while making companion collisions rarer.
#
#
# Rules this relies on (carrot_probe.py, Carrots 10,
# Polyculture 5, Watering 9):
#
#   - A Carrot costs 512 Hay + 512 Wood. Grass/Bush/Tree are
#     free.
#   - Harvest: 512, or 81,920 (160x) with the exact requested
#     type on the exact requested tile. The companion does NOT
#     need to be mature. Wrong type or wrong tile = 512.
#   - The request (Bush / Tree / Grass, within 3 tiles) is
#     fixed at planting.
#   - Grow ~5.9 sec plain, ~1.1 sec watered. Fertilizer halves
#     the yield, so it is never used.
#
# Prints one summary line per run.
# ============================================================


SYNC_DELAY = 4

QUIET_DELAY = 1

GO_DELAY = 1

MAX_SECONDS = 600

WATER_TO = 0.9

MAX_REROLLS = 20

CARROT_PARITY = 0


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


# ============================================================
# TILE HELPERS
# ============================================================

# Carrot density per mode: one carrot tile in every DENSITY
# tiles, laid out as (x + STEP * y) % DENSITY == 0 so carrots
# are spread evenly. Every other tile is a companion tile.

DENSITY = {
	2: 2,
	3: 2,
	4: 2,
	5: 4,
	6: 8,
	7: 4
}

STEP = {
	2: 1,
	4: 2,
	8: 3
}

REROLL_MODES = [2, 3, 7]


def is_carrot_tile(
	x,
	y,
	mode
):
	# mode is passed explicitly: spawned drones have their own
	# memory, so they may not see simulation-injected globals.

	k = DENSITY[mode]

	return (
		(x + STEP[k] * y) % k
		== 0
	)


def water_up():

	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			return


def plant_carrot_pair(
	x,
	y,
	mode
):
	# Drone stands on carrot tile (x, y). Plant a carrot whose
	# companion request is on a companion tile (re-rolling in
	# modes 2/3), water it, then make sure the requested
	# companion stands on the requested tile.
	#
	# Returns (companion placed or already present, re-rolls).

	rolls = 0

	request = None


	while True:

		if get_entity_type() != None:

			harvest()


		plant(Entities.Carrot)

		request = get_companion()


		if request == None:

			break


		if not is_carrot_tile(request[1][0], request[1][1], mode):

			break


		if mode not in REROLL_MODES or rolls >= MAX_REROLLS:

			request = None

			break


		rolls = rolls + 1


	if mode != 3:

		water_up()


	if request == None:

		return (False, rolls)


	want = request[0]


	go_to(
		request[1][0],
		request[1][1]
	)


	if get_entity_type() != want:

		if get_entity_type() != None:

			harvest()


		plant(want)


	go_to(
		x,
		y
	)


	return (True, rolls)


# ============================================================
# STRIPES
# ============================================================

def stripe_rows(
	start,
	count,
	size
):

	rows = []

	row = start


	while row < size:

		rows.append(row)

		row = row + count


	return rows


# ============================================================
# SETUP WORKERS
# ============================================================

def soil_worker(
	rows
):

	size = get_world_size()


	for row in rows:

		go_to(0, row)


		for x in range(size):

			if get_entity_type() != None:

				harvest()


			if get_ground_type() != Grounds.Soil:

				till()


			if x < size - 1:

				move(East)


	return 0


def plant_worker(
	rows,
	mode
):

	size = get_world_size()

	placed = 0


	for row in rows:

		for x in range(size):

			if is_carrot_tile(x, row, mode):

				go_to(x, row)

				result = plant_carrot_pair(x, row, mode)


				if result[0]:

					placed = placed + 1


	return placed


# ============================================================
# RUN WORKER
# ============================================================

def run_worker(
	rows,
	mode,
	sample_at,
	go_at,
	deadline,
	gain,
	do_run
):
	# Returns (harvests, companions placed, re-rolls, carrots
	# at sample time).

	size = get_world_size()


	while get_time() < sample_at:

		pass


	start_carrots = num_items(Items.Carrot)

	target = start_carrots + gain


	while get_time() < go_at:

		pass


	harvests = 0

	placed = 0

	rolls = 0


	if not do_run:

		return (harvests, placed, rolls, start_carrots)


	while get_time() < deadline:

		for row in rows:

			for x in range(size):

				if not is_carrot_tile(x, row, mode):

					continue


				if num_items(Items.Carrot) >= target:

					return (harvests, placed, rolls, start_carrots)


				go_to(x, row)


				if can_harvest():

					harvest()

					harvests = harvests + 1


					result = plant_carrot_pair(x, row, mode)


					if result[0]:

						placed = placed + 1


					rolls = rolls + result[1]


	return (harvests, placed, rolls, start_carrots)


# ============================================================
# PAIR SWEEP MODES
# ============================================================

def run_pairs(
	mode
):

	size = get_world_size()

	count = min(max_drones(), size)


	clear()


	# --------------------------------------------------------
	# SETUP PASS 1: every tile to bare soil (all drones)
	# --------------------------------------------------------

	handles = []


	for k in range(1, count):

		handle = spawn_drone(
			soil_worker,
			stripe_rows(k, count, size)
		)


		if handle != None:

			handles.append(handle)


	soil_worker(
		stripe_rows(0, count, size)
	)


	for handle in handles:

		wait_for(handle)


	# --------------------------------------------------------
	# SETUP PASS 2: carrots + companions (all drones)
	# --------------------------------------------------------

	handles = []


	for k in range(1, count):

		handle = spawn_drone(
			plant_worker,
			stripe_rows(k, count, size),
			mode
		)


		if handle != None:

			handles.append(handle)


	setup_placed = plant_worker(
		stripe_rows(0, count, size),
		mode
	)


	for handle in handles:

		setup_placed = setup_placed + wait_for(handle)


	# --------------------------------------------------------
	# SYNCHRONISED RUN (or baseline)
	# --------------------------------------------------------

	sample_at = get_time() + SYNC_DELAY

	go_at = sample_at + QUIET_DELAY + GO_DELAY

	deadline = go_at + MAX_SECONDS


	handles = []


	for k in range(1, count):

		handle = spawn_drone(
			run_worker,
			stripe_rows(k, count, size),
			mode,
			sample_at,
			go_at,
			deadline,
			TARGET,
			RUN
		)


		if handle != None:

			handles.append(handle)


	totals = run_worker(
		stripe_rows(0, count, size),
		mode,
		sample_at,
		go_at,
		deadline,
		TARGET,
		RUN
	)


	harvests = totals[0]

	placed = totals[1]

	rolls = totals[2]

	start_carrots = totals[3]


	for handle in handles:

		result = wait_for(handle)

		harvests = harvests + result[0]

		placed = placed + result[1]

		rolls = rolls + result[2]


	return (
		len(handles) + 1,
		harvests,
		placed,
		rolls,
		setup_placed,
		num_items(Items.Carrot) - start_carrots
	)


# ============================================================
# CURRENT MODE
# ============================================================

def run_current():

	clear()


	if not RUN:

		return (max_drones(), 0, 0, 0, 0, 0)


	# The old farm_rotation.farm_carrots() + farm_polyculture
	# phase was replaced by farm_carrot. Its result is recorded
	# in sim_carrot.py: 244.16 sec, 0/3 seeds passed.

	quick_print(
		"  MODE 1 retired: old farm_carrots no longer exists"
	)

	return (max_drones(), 0, 0, 0, 0, 0)


# ============================================================
# PRODUCTION MODE
# ============================================================

def run_production():
	# Production farm_carrot.farm() with TARGET as its gain
	# target. Its time includes its own soil / planting.

	clear()


	if not RUN:

		return (max_drones(), 0, 0, 0, 0, 0)


	farm_config.SETTINGS["carrot_gain_target"] = TARGET

	start_carrots = num_items(Items.Carrot)

	farm_carrot.farm()


	return (
		max_drones(),
		0,
		0,
		0,
		0,
		num_items(Items.Carrot) - start_carrots
	)


# ============================================================
# ENTRYPOINT
# ============================================================

if MODE == 1:

	stats = run_current()

elif MODE == 8:

	stats = run_production()

else:

	stats = run_pairs(
		MODE
	)


quick_print(
	"  RUN:",
	RUN,
	"| drones:",
	stats[0],
	"| harvests (field cycles for mode 1):",
	stats[1],
	"| companions placed:",
	stats[2],
	"| re-rolls:",
	stats[3],
	"| setup companions:",
	stats[4],
	"| carrots gained:",
	stats[5]
)
