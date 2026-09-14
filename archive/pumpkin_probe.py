# ============================================================
# PUMPKIN RULES PROBE
# ============================================================
#
# Run through sim_pumpkin.py (PROBE = True).
#
# Pumpkin Master = "Farm 20 million pumpkins in 1 minute."
# (Steam PUMPKIN_MASTER, stat "pumpkin"). Answers what a fast
# Pumpkin farm depends on:
#
#   A. Single tile x SAMPLES: planting cost, grow time (plain /
#      watered / fertilized), how often a grown pumpkin dies,
#      and single-pumpkin yield (plain vs fertilized).
#
#   B. Square mega pumpkins of side 2, 3, 4, 6, 8: plant the
#      block, water, replant dead pumpkins until the block is
#      one merged pumpkin (same measure() id in opposite
#      corners), harvest. Records yield, seconds, replants, so
#      the yield formula (side^2? side^3? count^3?) and the
#      time cost per size are known.
#
# One drone only. Every line starts with [PROBE].
#
# This file intentionally imports nothing.
# ============================================================


SAMPLES = 20

SIDES = [
	2,
	3,
	4,
	6,
	8
]

ORIGIN_X = 4

ORIGIN_Y = 4

WATER_TO = 0.9

MAX_REPAIR_PASSES = 200


# ============================================================
# HELPERS
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


def pumpkins():

	return num_items(
		Items.Pumpkin
	)


def soil_empty():

	if get_entity_type() != None:

		harvest()


	if get_ground_type() != Grounds.Soil:

		till()


def water_up():

	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			return


# ============================================================
# A. SINGLE TILE
# ============================================================

def single_loop(
	label,
	samples,
	prewater,
	fertilize
):

	go_to(0, 0)


	grow_total = 0

	grown = 0

	died = 0

	gain_total = 0

	gains = 0


	for i in range(samples):

		soil_empty()


		if prewater:

			water_up()


		before = num_items(Items.Carrot)

		plant(Entities.Pumpkin)

		spent_carrot = before - num_items(Items.Carrot)


		t0 = get_time()


		if fertilize:

			while not can_harvest() and get_entity_type() == Entities.Pumpkin:

				if not use_item(Items.Fertilizer):

					break


		while get_entity_type() == Entities.Pumpkin and not can_harvest():

			pass


		grow_total = grow_total + (get_time() - t0)

		grown = grown + 1


		if get_entity_type() == Entities.Dead_Pumpkin:

			died = died + 1

			harvest()

			continue


		p0 = pumpkins()

		harvest()

		gain = pumpkins() - p0

		gain_total = gain_total + gain

		gains = gains + 1


		if i < 3:

			quick_print(
				"[PROBE]",
				label,
				"sample",
				i + 1,
				"| carrot spent on plant:",
				spent_carrot,
				"| seconds to grow/die:",
				get_time() - t0,
				"| gain:",
				gain
			)


	average = 0


	if gains > 0:

		average = gain_total / gains


	quick_print(
		"[PROBE]",
		label,
		"avg sec:",
		grow_total / grown,
		"| died:",
		died,
		"/",
		grown,
		"| avg single-pumpkin gain:",
		average
	)


# ============================================================
# B. SQUARE MEGA PUMPKIN
# ============================================================

def mega(
	side
):

	x0 = ORIGIN_X

	y0 = ORIGIN_Y

	x1 = x0 + side - 1

	y1 = y0 + side - 1


	clear()


	t0 = get_time()

	planted = 0


	for y in range(y0, y1 + 1):

		for x in range(x0, x1 + 1):

			go_to(x, y)

			soil_empty()

			water_up()

			plant(Entities.Pumpkin)

			planted = planted + 1


	passes = 0

	replants = 0

	merged = False


	while passes < MAX_REPAIR_PASSES:

		passes = passes + 1

		all_ready = True


		for y in range(y0, y1 + 1):

			for x in range(x0, x1 + 1):

				go_to(x, y)

				entity = get_entity_type()


				if entity == Entities.Dead_Pumpkin or entity == None:

					plant(Entities.Pumpkin)

					water_up()

					replants = replants + 1

					all_ready = False


				elif not can_harvest():

					all_ready = False


		if all_ready:

			go_to(x0, y0)

			first = measure()

			go_to(x1, y1)

			last = measure()


			if first != None and first == last:

				merged = True

				break


	go_to(x0, y0)

	p0 = pumpkins()

	harvest()

	gain = pumpkins() - p0

	seconds = get_time() - t0


	count = side * side


	quick_print(
		"[PROBE] B side",
		side,
		"| merged:",
		merged,
		"| repair passes:",
		passes,
		"| replants:",
		replants,
		"| seconds:",
		seconds,
		"| gain:",
		gain,
		"| gain/count:",
		gain / count,
		"| gain/count^2:",
		gain / (count * count),
		"| gain/side^3:",
		gain / (side * side * side),
		"| gain/sec:",
		gain / seconds
	)


	return gain


# ============================================================
# RUN
# ============================================================

quick_print(
	"[PROBE] world:",
	get_world_size(),
	"| Pumpkins:",
	num_unlocked(Unlocks.Pumpkins),
	"| Watering:",
	num_unlocked(Unlocks.Watering),
	"| Fertilizer:",
	num_unlocked(Unlocks.Fertilizer),
	"| pumpkin cost:",
	get_cost(Entities.Pumpkin)
)


clear()


single_loop("A plain", SAMPLES, False, False)

single_loop("A watered", SAMPLES, True, False)

single_loop("A fertilized", SAMPLES, False, True)


for side in SIDES:

	mega(side)
