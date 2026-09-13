import farm_config
import farm_sunflower


# ============================================================
# SUNFLOWER / POWER BENCHMARK TARGET
# ============================================================
#
# Run through sim_sunflower.py. Measures time to gain TARGET
# Power after setup (RUN=False = setup + sync only).
#
# MODE:
#
#   1 = FIELD SWEEP (retired)
#       The old farm_rotation.farm_sunflowers() whole-field
#       sweep, repeated. Replaced by farm_sunflower; result
#       kept in sim_sunflower.py (86.07 sec, 0/3 passed).
#
#   5 = PRODUCTION
#       farm_sunflower.farm() with TARGET as its gain target
#       (time includes its own planting / watering).
#
#   2 = REROLL 15
#       Setup: every tile gets a watered 15-petal sunflower
#       (replant young flowers until measure() == 15).
#       Run: each drone sweeps its rows. A mature 15 is
#       harvested (bonus), replanted and re-rolled to 15, then
#       watered.
#
#   3 = REROLL 15 + FERT
#       Mode 2, plus one Fertilizer per replant while stock
#       lasts (real stock is small).
#
#   4 = MATURE 15
#       Setup: plant every tile once and water. Run: harvest
#       any mature flower (15 = bonus, else 1 Power), replant
#       once and water. No re-rolling of young flowers.
#
#
# Only 15-petal flowers are harvested for the bonus, so the
# "max petals on the field" rule can never be missed, ties
# still pay, and a full field always has >= 10 flowers.
#
# Prints one summary line per run.
# ============================================================


SYNC_DELAY = 4

QUIET_DELAY = 1

GO_DELAY = 1

MAX_SECONDS = 600

WATER_TO = 0.9

MAX_REROLLS = 50

BONUS_PETALS = 15


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

def water_up():

	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			return


def reroll_to_bonus():
	# Tile must be empty or hold a young sunflower. Replant
	# until the flower shows BONUS_PETALS. Returns re-roll
	# count, or -1 if planting failed (tile not cleared).

	rolls = 0


	while True:

		if get_entity_type() != None:

			harvest()


		if not plant(Entities.Sunflower):

			return -1


		if measure() == BONUS_PETALS:

			return rolls


		rolls = rolls + 1


		if rolls >= MAX_REROLLS:

			return rolls


def fertilize_once():

	if num_items(Items.Fertilizer) >= max_drones():

		use_item(Items.Fertilizer)


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
# SETUP WORKER
# ============================================================

def setup_worker(
	rows,
	mode
):

	size = get_world_size()

	anomalies = 0


	for row in rows:

		go_to(0, row)


		for x in range(size):

			if get_entity_type() != None:

				harvest()


			if get_ground_type() != Grounds.Soil:

				till()


			if mode == 4:

				plant(Entities.Sunflower)

			else:

				if reroll_to_bonus() < 0:

					anomalies = anomalies + 1


			water_up()


			if x < size - 1:

				move(East)


	return anomalies


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
	# Returns (bonus harvests, normal harvests, re-rolls,
	# anomalies, power at sample time).

	size = get_world_size()


	while get_time() < sample_at:

		pass


	start_power = num_items(Items.Power)

	target = start_power + gain


	while get_time() < go_at:

		pass


	bonus = 0

	normal = 0

	rolls = 0

	anomalies = 0


	if not do_run:

		return (bonus, normal, rolls, anomalies, start_power)


	while get_time() < deadline:

		for row in rows:

			go_to(0, row)


			for x in range(size):

				if num_items(Items.Power) >= target:

					return (bonus, normal, rolls, anomalies, start_power)


				if can_harvest():

					petals = measure()

					harvest()


					if petals == BONUS_PETALS:

						bonus = bonus + 1

					else:

						normal = normal + 1


					if mode == 4:

						plant(Entities.Sunflower)

					else:

						result = reroll_to_bonus()


						if result < 0:

							anomalies = anomalies + 1

						else:

							rolls = rolls + result


						if mode == 3:

							fertilize_once()


					water_up()


				move(East)


	return (bonus, normal, rolls, anomalies, start_power)


# ============================================================
# CONTINUOUS MODES
# ============================================================

def run_continuous(
	mode
):

	size = get_world_size()

	count = min(max_drones(), size)


	clear()


	# --------------------------------------------------------
	# SETUP (all drones)
	# --------------------------------------------------------

	handles = []


	for k in range(1, count):

		handle = spawn_drone(
			setup_worker,
			stripe_rows(k, count, size),
			mode
		)


		if handle != None:

			handles.append(handle)


	anomalies = setup_worker(
		stripe_rows(0, count, size),
		mode
	)


	for handle in handles:

		anomalies = anomalies + wait_for(handle)


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


	bonus = totals[0]

	normal = totals[1]

	rolls = totals[2]

	anomalies = anomalies + totals[3]

	start_power = totals[4]


	for handle in handles:

		result = wait_for(handle)

		bonus = bonus + result[0]

		normal = normal + result[1]

		rolls = rolls + result[2]

		anomalies = anomalies + result[3]


	return (
		len(handles) + 1,
		bonus,
		normal,
		rolls,
		anomalies,
		num_items(Items.Power) - start_power
	)


# ============================================================
# FIELD SWEEP MODE
# ============================================================

def run_sweep():

	clear()


	if not RUN:

		return (max_drones(), 0, 0, 0, 0, 0)


	# The whole-field sweep (farm_rotation.farm_sunflowers) was
	# replaced by farm_sunflower. Its result is recorded in
	# sim_sunflower.py: 86.07 sec, 0/3 seeds passed.

	quick_print(
		"  MODE 1 retired: old field sweep no longer exists"
	)

	return (max_drones(), 0, 0, 0, 1, 0)


# ============================================================
# ENTRYPOINT
# ============================================================

def run_production():
	# Production farm_sunflower.farm() with TARGET as its gain
	# target. Its time includes its own planting / watering.

	clear()


	if not RUN:

		return (max_drones(), 0, 0, 0, 0, 0)


	farm_config.SETTINGS["sunflower_gain_target"] = TARGET

	start_power = num_items(Items.Power)

	farm_sunflower.farm()


	return (
		max_drones(),
		0,
		0,
		0,
		0,
		num_items(Items.Power) - start_power
	)


if MODE == 1:

	stats = run_sweep()

elif MODE == 5:

	stats = run_production()

else:

	stats = run_continuous(
		MODE
	)


quick_print(
	"  RUN:",
	RUN,
	"| drones:",
	stats[0],
	"| bonus harvests (sweeps for mode 1):",
	stats[1],
	"| normal harvests:",
	stats[2],
	"| re-rolls:",
	stats[3],
	"| anomalies:",
	stats[4],
	"| power gained:",
	stats[5]
)
