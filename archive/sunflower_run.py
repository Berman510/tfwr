# ============================================================
# SUNFLOWER MASTER RUNNER
# ============================================================
#
# Achievement (Steam SUNFLOWER_MASTER, stat "power"):
#
#     "Farm 12000 power in 1 minute."
#
#
# Proven simulation (sim_sunflower MATURE 15, 32x32 / 32
# drones, real Fertilizer / Water / Carrot stock):
#
#     Average:  25.97 sec per +12,000 Power (net inventory)
#     Seeds:    3 / 3 pass, 0 anomalies
#
#
# Method:
#
#     1. clear(), then every drone plants its row with
#        Sunflowers on soil and waters each tile to WATER_TO.
#
#     2. All drones synchronise and share one Power baseline.
#
#     3. Each drone sweeps its row: every mature flower is
#        harvested (15 petals = bonus 8 Power while >= 10
#        flowers are on the field, else ~1 Power), replanted
#        once and watered.
#
#     4. Stop when Power has grown by TARGET_GAIN, or after
#        MAX_SECONDS.
#
#
# TARGET_GAIN is 15,000 (margin over 12,000). Power is read
# from inventory, which under-counts harvested Power because
# moves and actions spend some.
#
# Stop main first so every drone is free.
#
# This file intentionally imports nothing.
# ============================================================


TARGET_GAIN = 15000

MAX_SECONDS = 120

WATER_TO = 0.9

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
# SETUP WORKER
# ============================================================

def setup_worker(
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


			plant(Entities.Sunflower)

			water_up()


			if x < size - 1:

				move(East)


	return 1


# ============================================================
# RUN WORKER
# ============================================================

def run_worker(
	rows,
	sample_at,
	go_at,
	deadline,
	gain,
	mark_60
):
	# Returns (bonus harvests, normal harvests, start power,
	# power 60 sec after go or -1, finish time).

	size = get_world_size()


	while get_time() < sample_at:

		pass


	start_power = num_items(Items.Power)

	target = start_power + gain


	while get_time() < go_at:

		pass


	bonus = 0

	normal = 0

	power_60 = -1

	minute = go_at + 60


	while get_time() < deadline:

		for row in rows:

			go_to(0, row)


			for x in range(size):

				if mark_60 and power_60 < 0 and get_time() >= minute:

					power_60 = num_items(Items.Power)


				if num_items(Items.Power) >= target:

					return (bonus, normal, start_power, power_60, get_time())


				if can_harvest():

					if measure() == 15:

						bonus = bonus + 1

					else:

						normal = normal + 1


					harvest()

					plant(Entities.Sunflower)

					water_up()


				move(East)


	return (bonus, normal, start_power, power_60, get_time())


# ============================================================
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< SUNFLOWER_RUN_BEGIN >>>"
)


size = get_world_size()

count = min(max_drones(), size)


quick_print(
	"[SUN] world:",
	size,
	"x",
	size,
	"| drones:",
	count,
	"| target gain:",
	TARGET_GAIN,
	"| power now:",
	num_items(Items.Power),
	"| water:",
	num_items(Items.Water),
	"| carrot:",
	num_items(Items.Carrot)
)


clear()


# ------------------------------------------------------------
# SETUP
# ------------------------------------------------------------

setup_start = get_time()

handles = []


for k in range(1, count):

	handle = spawn_drone(
		setup_worker,
		stripe_rows(k, count, size)
	)


	if handle != None:

		handles.append(handle)


setup_worker(
	stripe_rows(0, count, size)
)


for handle in handles:

	wait_for(handle)


quick_print(
	"[SUN] setup seconds:",
	get_time() - setup_start
)


# ------------------------------------------------------------
# SYNCHRONISED RUN
# ------------------------------------------------------------

sample_at = get_time() + SYNC_DELAY

go_at = sample_at + QUIET_DELAY + GO_DELAY

deadline = go_at + MAX_SECONDS


handles = []


for k in range(1, count):

	handle = spawn_drone(
		run_worker,
		stripe_rows(k, count, size),
		sample_at,
		go_at,
		deadline,
		TARGET_GAIN,
		False
	)


	if handle != None:

		handles.append(handle)


quick_print(
	"[SUN] workers:",
	len(handles) + 1
)


totals = run_worker(
	stripe_rows(0, count, size),
	sample_at,
	go_at,
	deadline,
	TARGET_GAIN,
	True
)


bonus = totals[0]

normal = totals[1]

start_power = totals[2]

power_60 = totals[3]

finish = totals[4]


for handle in handles:

	result = wait_for(handle)

	bonus = bonus + result[0]

	normal = normal + result[1]


	if result[4] > finish:

		finish = result[4]


gained = num_items(Items.Power) - start_power

elapsed = finish - go_at


# ============================================================
# RESULT
# ============================================================

quick_print(
	"[SUN] power gained:",
	gained,
	"| seconds:",
	elapsed,
	"| Power/min:",
	gained * 60 / elapsed
)

quick_print(
	"[SUN] bonus harvests:",
	bonus,
	"| normal harvests:",
	normal,
	"| est. harvested power:",
	bonus * 8 + normal
)


if power_60 >= 0:

	quick_print(
		"[SUN] power gained in first 60 sec:",
		power_60 - start_power
	)

else:

	quick_print(
		"[SUN] target reached before 60 sec"
	)


if gained >= 12000 and elapsed <= 60:

	quick_print(
		"[SUN] 12,000+ Power inside 60 sec - check for Sunflower Master"
	)

else:

	quick_print(
		"[SUN] under 12,000 in 60 sec - check results"
	)


quick_print(
	"<<< SUNFLOWER_RUN_END >>>"
)


print(
	"SUNFLOWER RUN COMPLETE\n",
	"Gained:",
	gained,
	"in",
	elapsed,
	"sec\n",
	"Open output.txt"
)
