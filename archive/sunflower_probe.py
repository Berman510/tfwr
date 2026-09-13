# ============================================================
# SUNFLOWER RULES PROBE
# ============================================================
#
# Run through sim_sunflower.py (PROBE = True).
#
# Sunflower Master = "Farm 12000 power in 1 minute." (Steam
# SUNFLOWER_MASTER, stat "power"). Answers what a fast
# continuous Power farm depends on:
#
#   A. Single tile x SAMPLES (never 10 flowers -> no bonus):
#      petals at plant vs. at maturity, grow time, base Power
#      per harvest (does it depend on petals?).
#
#   B. Same loop with Fertilizer, and with pre-watered soil.
#
#   C. 20 mature flowers: harvest the SMALLEST first (not the
#      max), then largest -> smallest. Power per harvest vs.
#      petals, max remaining, count remaining.
#
#   D. 10 mature + 1 freshly planted flower: does an immature
#      flower count toward "10 sunflowers" and "max petals"?
#
#   E. Power spent and seconds per move.
#
# One drone only. Every line starts with [PROBE].
#
# This file intentionally imports nothing.
# ============================================================


SAMPLES = 20

BOOST_SAMPLES = 10


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


def plant_sunflower():

	if get_entity_type() != None:

		harvest()


	if get_ground_type() != Grounds.Soil:

		till()


	return plant(
		Entities.Sunflower
	)


def power():

	return num_items(
		Items.Power
	)


def wait_mature():
	# Stand still until the flower under the drone is ready.

	t0 = get_time()


	while not can_harvest():

		pass


	return get_time() - t0


def harvest_here():
	# Power gained by harvesting the tile under the drone, with
	# no movement between the two reads.

	p0 = power()

	harvest()

	return power() - p0


# ============================================================
# A / B. SINGLE TILE LOOPS
# ============================================================

def tile_loop(
	label,
	samples,
	fertilize,
	prewater
):

	go_to(
		0,
		0
	)


	grow_total = 0

	gain_by_petals = {}

	changed = 0


	for i in range(samples):

		if prewater:

			while get_water() < 0.99:

				if not use_item(Items.Water):

					break


		plant_sunflower()

		petals_at_plant = measure()


		t0 = get_time()


		if fertilize:

			while not can_harvest():

				if not use_item(Items.Fertilizer):

					break


		while not can_harvest():

			pass


		grow = get_time() - t0

		grow_total = grow_total + grow

		petals_mature = measure()


		if petals_mature != petals_at_plant:

			changed = changed + 1


		gain = harvest_here()


		if petals_mature not in gain_by_petals:

			gain_by_petals[petals_mature] = []


		gain_by_petals[petals_mature].append(
			gain
		)


		if i < 5:

			quick_print(
				"[PROBE]",
				label,
				"sample",
				i + 1,
				"| petals at plant:",
				petals_at_plant,
				"| at maturity:",
				petals_mature,
				"| grow sec:",
				grow,
				"| power gain:",
				gain
			)


	quick_print(
		"[PROBE]",
		label,
		"avg grow sec:",
		grow_total / samples,
		"| petal count changed while growing:",
		changed,
		"/",
		samples
	)


	for petals in range(7, 16):

		if petals in gain_by_petals:

			gains = gain_by_petals[petals]

			total = 0


			for g in gains:

				total = total + g


			quick_print(
				"[PROBE]",
				label,
				"petals",
				petals,
				"| harvests:",
				len(gains),
				"| avg power:",
				total / len(gains)
			)


# ============================================================
# FIELD HELPERS FOR C / D
# ============================================================

def plant_block(
	x0,
	y0,
	width,
	height
):
	# Returns list of (x, y, petals at plant).

	cells = []


	for y in range(y0, y0 + height):

		for x in range(x0, x0 + width):

			go_to(x, y)

			plant_sunflower()

			cells.append(
				(x, y, measure())
			)


	return cells


def wait_block_mature(
	cells
):

	t0 = get_time()

	ready = False


	while not ready:

		ready = True


		for cell in cells:

			go_to(cell[0], cell[1])


			if not can_harvest():

				ready = False


	return get_time() - t0


def remove_cell(
	cells,
	target
):

	result = []


	for cell in cells:

		if cell != target:

			result.append(cell)


	return result


def max_petals(
	cells
):

	best = -1


	for cell in cells:

		best = max(best, cell[2])


	return best


# ============================================================
# RUN
# ============================================================

size = get_world_size()


quick_print(
	"[PROBE] world:",
	size,
	"| Sunflowers level:",
	num_unlocked(Unlocks.Sunflowers),
	"| Speed:",
	num_unlocked(Unlocks.Speed),
	"| Fertilizer:",
	num_unlocked(Unlocks.Fertilizer),
	"| sunflower cost:",
	get_cost(Entities.Sunflower),
	"| power start:",
	power()
)


clear()


tile_loop("A plain", SAMPLES, False, False)

tile_loop("B fertilizer", BOOST_SAMPLES, True, False)

tile_loop("B prewater", BOOST_SAMPLES, False, True)


# ------------------------------------------------------------
# C. BONUS RULE ON 20 MATURE FLOWERS
# ------------------------------------------------------------

clear()


cells = plant_block(
	2,
	2,
	5,
	4
)


quick_print(
	"[PROBE] C planted 20 | petals:",
	cells,
	"| mature after sec:",
	wait_block_mature(cells)
)


# Smallest first (deliberately NOT the max).

smallest = cells[0]


for cell in cells:

	if cell[2] < smallest[2]:

		smallest = cell


go_to(smallest[0], smallest[1])

gain = harvest_here()


quick_print(
	"[PROBE] C smallest-first | petals:",
	smallest[2],
	"| max on field:",
	max_petals(cells),
	"| flowers before:",
	len(cells),
	"| power gain:",
	gain
)


cells = remove_cell(
	cells,
	smallest
)


# Then largest -> smallest.

while len(cells) > 0:

	best = cells[0]


	for cell in cells:

		if cell[2] > best[2]:

			best = cell


	before = len(cells)

	top = max_petals(cells)

	go_to(best[0], best[1])

	gain = harvest_here()


	quick_print(
		"[PROBE] C harvest | petals:",
		best[2],
		"| max on field:",
		top,
		"| flowers before:",
		before,
		"| power gain:",
		gain
	)


	cells = remove_cell(
		cells,
		best
	)


# ------------------------------------------------------------
# D. DOES AN IMMATURE FLOWER COUNT?
# ------------------------------------------------------------

clear()


mature = plant_block(
	2,
	8,
	10,
	1
)

wait_block_mature(mature)


go_to(2, 10)

plant_sunflower()

young_petals = measure()


quick_print(
	"[PROBE] D 10 mature + 1 young | mature petals:",
	mature,
	"| young petals:",
	young_petals,
	"| young ready yet:",
	can_harvest()
)


while len(mature) > 0:

	best = mature[0]


	for cell in mature:

		if cell[2] > best[2]:

			best = cell


	before = len(mature)

	top = max_petals(mature)

	go_to(best[0], best[1])

	gain = harvest_here()


	quick_print(
		"[PROBE] D harvest | petals:",
		best[2],
		"| max among mature:",
		top,
		"| young petals:",
		young_petals,
		"| mature before:",
		before,
		"| power gain:",
		gain
	)


	mature = remove_cell(
		mature,
		best
	)


# ------------------------------------------------------------
# E. MOVEMENT COST
# ------------------------------------------------------------

clear()

go_to(0, 0)


p0 = power()

t0 = get_time()


for i in range(64):

	move(East)


quick_print(
	"[PROBE] E 64 moves | power spent per move:",
	(p0 - power()) / 64,
	"| sec per move:",
	(get_time() - t0) / 64
)
