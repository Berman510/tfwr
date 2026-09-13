# ============================================================
# CARROT RULES PROBE
# ============================================================
#
# Run through sim_carrot.py (PROBE = True).
#
# Carrot Master = "Farm 200 million carrots in 1 minute."
# (Steam CARROT_MASTER, stat "carrot"). Answers what a fast
# continuous Carrot farm depends on:
#
#   A. Isolated tile x SAMPLES (no plants nearby): planting
#      cost, base yield per harvest, grow time, and what
#      get_companion() asks for (type, offset) at planting vs.
#      at maturity.
#
#   B. Same loop with pre-watered soil, and with Fertilizer.
#
#   C. Companion bonus, SAMPLES each:
#      C1 exact type at the exact requested tile
#      C2 wrong type at the requested tile
#      C3 exact type one tile away from the requested tile
#      Also records whether the companion was mature.
#
# One drone only. Every line starts with [PROBE].
#
# This file intentionally imports nothing.
# ============================================================


SAMPLES = 12

BOOST_SAMPLES = 8

CX = 16

CY = 16

CLEAR_RADIUS = 4


COMPANION_TYPES = [
	Entities.Grass,
	Entities.Bush,
	Entities.Tree,
	Entities.Carrot
]


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


def empty_soil():
	# Leave the tile under the drone as bare soil.

	if get_entity_type() != None:

		harvest()


	if get_ground_type() != Grounds.Soil:

		till()


def carrots():

	return num_items(
		Items.Carrot
	)


def offset(
	a,
	b
):
	# Signed shortest offset from b to a on the wrapping farm.

	size = get_world_size()

	d = (a - b) % size


	if d > size // 2:

		d = d - size


	return d


def clear_area():

	for y in range(CY - CLEAR_RADIUS, CY + CLEAR_RADIUS + 1):

		for x in range(CX - CLEAR_RADIUS, CX + CLEAR_RADIUS + 1):

			go_to(x, y)

			empty_soil()


def other_type(
	entity
):

	for t in COMPANION_TYPES:

		if t != entity:

			return t


	return Entities.Bush


def place(
	entity,
	x,
	y
):

	go_to(x, y)

	empty_soil()

	return plant(entity)


def count_into(
	table,
	key
):

	if key in table:

		table[key] = table[key] + 1

	else:

		table[key] = 1


# ============================================================
# A / B. ISOLATED TILE LOOPS
# ============================================================

def tile_loop(
	label,
	samples,
	prewater,
	fertilize
):

	gains = []

	grow_total = 0

	changed = 0

	types = {}

	offsets = {}


	for i in range(samples):

		go_to(CX, CY)

		empty_soil()


		if prewater:

			while get_water() < 0.99:

				if not use_item(Items.Water):

					break


		c0 = carrots()

		plant(Entities.Carrot)

		spent = c0 - carrots()

		request = get_companion()


		t0 = get_time()


		if fertilize:

			while not can_harvest():

				if not use_item(Items.Fertilizer):

					break


		while not can_harvest():

			pass


		grow = get_time() - t0

		grow_total = grow_total + grow

		request_mature = get_companion()


		if request != request_mature:

			changed = changed + 1


		c1 = carrots()

		harvest()

		gain = carrots() - c1

		gains.append(gain)


		if request != None:

			count_into(types, request[0])

			count_into(
				offsets,
				(
					offset(request[1][0], CX),
					offset(request[1][1], CY)
				)
			)


		if i < 4:

			quick_print(
				"[PROBE]",
				label,
				"sample",
				i + 1,
				"| carrot spent on plant:",
				spent,
				"| request at plant:",
				request,
				"| at maturity:",
				request_mature,
				"| grow sec:",
				grow,
				"| gain (no companion):",
				gain
			)


	total = 0


	for g in gains:

		total = total + g


	quick_print(
		"[PROBE]",
		label,
		"avg gain:",
		total / samples,
		"| min:",
		min(gains),
		"| max:",
		max(gains),
		"| avg grow sec:",
		grow_total / samples,
		"| request changed while growing:",
		changed,
		"/",
		samples
	)

	quick_print(
		"[PROBE]",
		label,
		"requested types:",
		types,
		"| requested offsets:",
		offsets
	)


	return total / samples


# ============================================================
# C. COMPANION BONUS
# ============================================================

def bonus_loop(
	label,
	variant,
	samples
):
	# variant 1: exact type, exact tile
	# variant 2: wrong type, exact tile
	# variant 3: exact type, one tile away from the request

	gains = []

	mature_companions = 0


	for i in range(samples):

		go_to(CX, CY)

		empty_soil()


		while get_water() < 0.99:

			if not use_item(Items.Water):

				break


		plant(Entities.Carrot)

		request = get_companion()


		if request == None:

			continue


		want = request[0]

		tx = request[1][0]

		ty = request[1][1]

		kind = want


		if variant == 2:

			kind = other_type(want)


		if variant == 3:

			# Shift one tile away from the carrot along x,
			# keeping clear of the carrot tile itself.

			if offset(tx, CX) >= 0:

				tx = tx + 1

			else:

				tx = tx - 1


		placed = place(kind, tx, ty)


		go_to(CX, CY)


		while not can_harvest():

			pass


		# Record whether the companion has matured by now.

		go_to(tx, ty)

		companion_ready = can_harvest()


		if companion_ready:

			mature_companions = mature_companions + 1


		go_to(CX, CY)

		c1 = carrots()

		harvest()

		gain = carrots() - c1

		gains.append(gain)


		if i < 3:

			quick_print(
				"[PROBE]",
				label,
				"sample",
				i + 1,
				"| request:",
				request,
				"| placed:",
				kind,
				"at",
				(tx, ty),
				"ok:",
				placed,
				"| companion mature:",
				companion_ready,
				"| gain:",
				gain
			)


		go_to(tx, ty)

		empty_soil()


	if len(gains) == 0:

		quick_print("[PROBE]", label, "no samples")

		return 0


	total = 0


	for g in gains:

		total = total + g


	quick_print(
		"[PROBE]",
		label,
		"avg gain:",
		total / len(gains),
		"| min:",
		min(gains),
		"| max:",
		max(gains),
		"| companion mature at harvest:",
		mature_companions,
		"/",
		len(gains)
	)


	return total / len(gains)


# ============================================================
# RUN
# ============================================================

quick_print(
	"[PROBE] world:",
	get_world_size(),
	"| Carrots:",
	num_unlocked(Unlocks.Carrots),
	"| Polyculture:",
	num_unlocked(Unlocks.Polyculture),
	"| Watering:",
	num_unlocked(Unlocks.Watering),
	"| Fertilizer:",
	num_unlocked(Unlocks.Fertilizer),
	"| Speed:",
	num_unlocked(Unlocks.Speed)
)

quick_print(
	"[PROBE] costs | Carrot:",
	get_cost(Entities.Carrot),
	"| Grass:",
	get_cost(Entities.Grass),
	"| Bush:",
	get_cost(Entities.Bush),
	"| Tree:",
	get_cost(Entities.Tree)
)


clear()

clear_area()


base = tile_loop("A plain", SAMPLES, False, False)

tile_loop("B prewater", BOOST_SAMPLES, True, False)

tile_loop("B fertilizer", BOOST_SAMPLES, False, True)


exact = bonus_loop("C1 exact type + tile", 1, SAMPLES)

wrong = bonus_loop("C2 wrong type, exact tile", 2, SAMPLES)

near = bonus_loop("C3 exact type, 1 tile off", 3, SAMPLES)


if base > 0:

	quick_print(
		"[PROBE] multipliers vs plain | exact:",
		exact / base,
		"| wrong type:",
		wrong / base,
		"| one tile off:",
		near / base
	)
