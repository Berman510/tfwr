# ============================================================
# DINOSAUR RULES PROBE
# ============================================================
#
# Run through sim_dino.py (PROBE = True).
#
# Answers the questions the shortcut algorithm depends on:
#
#   1. Does measure() give the next Apple position?
#   2. Is an Apple eaten on arrival, and does a move into
#      the tail fail (rather than ending the run)?
#   3. How do Bones scale with Apples eaten?
#   4. Does move time grow with tail length?
#
# Plus: does movement wrap around the field edge while
# wearing the Dinosaur Hat?
#
#
# Run A: eat K_SMALL Apples, with wrap + collision tests.
# Run B: eat K_LONG Apples, with move-time buckets.
#
# Every line of output starts with [PROBE].
#
# This file intentionally imports nothing.
# ============================================================


K_SMALL = 4

K_LONG = 60

TIME_BUCKET = 10


# ============================================================
# HAMILTONIAN CYCLE SUCCESSOR
# ============================================================
#
# Same cycle as farm_dinosaurs.cycle_once:
#
#     column 0 northward
#     columns 1 .. w-1 serpentine over rows 1 .. h-1
#     row 0 westward back to (0, 0)
#
# Requires an even width.

def cycle_dir(
	x,
	y,
	w,
	h
):

	if y == 0:

		if x > 0:

			return West

		return North


	if x == 0:

		if y < h - 1:

			return North

		return East


	if x % 2 == 1:

		if y > 1:

			return South

		if x < w - 1:

			return East

		return South


	if y < h - 1:

		return North

	return East


def opposite(
	direction
):

	if direction == North:

		return South

	if direction == South:

		return North

	if direction == East:

		return West

	return East


# ============================================================
# APPLE COST ITEM
# ============================================================

def cost_item():

	cost = get_cost(
		Entities.Apple
	)


	if cost == None:

		return None


	for item in cost:

		return item


	return None


# ============================================================
# ONE PROBE RUN
# ============================================================

def run(
	label,
	apples,
	edge_tests
):

	size = get_world_size()

	item = cost_item()


	clear()


	# --------------------------------------------------------
	# BASELINE MOVE TIME WITHOUT HAT
	# --------------------------------------------------------

	t0 = get_time()

	move(
		East
	)

	move(
		West
	)

	quick_print(
		"[PROBE]",
		label,
		"no-hat avg move seconds:",
		(get_time() - t0) / 2,
		"pos:",
		get_pos_x(),
		get_pos_y()
	)


	# --------------------------------------------------------
	# HAT ON
	# --------------------------------------------------------

	bones_start = num_items(
		Items.Bone
	)

	c_before = num_items(
		item
	)


	change_hat(
		Hats.Dinosaur_Hat
	)


	predicted = measure()


	quick_print(
		"[PROBE]",
		label,
		"hat on | cost item delta:",
		num_items(item) - c_before,
		"| entity under drone:",
		get_entity_type(),
		"| measure():",
		predicted
	)


	# --------------------------------------------------------
	# WRAP TEST
	# --------------------------------------------------------

	if edge_tests:

		c0 = num_items(
			item
		)

		can_wrap = can_move(
			South
		)

		wrapped = move(
			South
		)


		quick_print(
			"[PROBE]",
			label,
			"wrap test from (0,0) | can_move(South):",
			can_wrap,
			"| move(South):",
			wrapped,
			"| pos now:",
			get_pos_x(),
			get_pos_y(),
			"| cost item delta:",
			num_items(item) - c0
		)


		if wrapped:

			move(
				North
			)


	# --------------------------------------------------------
	# WALK THE CYCLE
	# --------------------------------------------------------

	eaten = 0

	moves = 0

	last_dir = None

	collision_tested = False

	other_entities_logged = 0

	bucket_seconds = 0

	bucket_moves = 0


	cap = (
		size
		* size
		* (apples + 2)
	)


	while (
		eaten < apples
		and
		moves < cap
	):

		x = get_pos_x()

		y = get_pos_y()


		# ----------------------------------------------------
		# COLLISION TEST (move back into the tail)
		# ----------------------------------------------------

		if (
			edge_tests
			and
			not collision_tested
			and
			eaten >= 3
			and
			last_dir != None
		):

			back = opposite(
				last_dir
			)

			can_back = can_move(
				back
			)

			t0 = get_time()

			moved_back = move(
				back
			)


			quick_print(
				"[PROBE]",
				label,
				"collision test, tail after",
				eaten,
				"apples | can_move:",
				can_back,
				"| move:",
				moved_back,
				"| pos:",
				get_pos_x(),
				get_pos_y(),
				"| seconds:",
				get_time() - t0
			)


			collision_tested = True


			if moved_back:

				last_dir = back


			continue


		# ----------------------------------------------------
		# NORMAL CYCLE STEP
		# ----------------------------------------------------

		direction = cycle_dir(
			x,
			y,
			size,
			size
		)


		c0 = num_items(
			item
		)

		t0 = get_time()


		if not move(
			direction
		):

			quick_print(
				"[PROBE]",
				label,
				"BLOCKED cycle move at",
				x,
				y,
				direction,
				"after",
				eaten,
				"apples"
			)

			break


		bucket_seconds = (
			bucket_seconds
			+ get_time()
			- t0
		)

		bucket_moves = (
			bucket_moves + 1
		)

		moves = (
			moves + 1
		)

		last_dir = direction


		entity = get_entity_type()


		if (
			entity != None
			and
			entity != Entities.Dinosaur
			and
			other_entities_logged < 5
		):

			other_entities_logged = (
				other_entities_logged + 1
			)

			quick_print(
				"[PROBE]",
				label,
				"entity under head after move:",
				entity,
				"at",
				get_pos_x(),
				get_pos_y(),
				"| measure():",
				measure()
			)


		c1 = num_items(
			item
		)


		if c1 < c0:

			eaten = (
				eaten + 1
			)


			nx = get_pos_x()

			ny = get_pos_y()

			m = measure()


			quick_print(
				"[PROBE]",
				label,
				"eat",
				eaten,
				"at",
				nx,
				ny,
				"| predicted:",
				predicted,
				"| match:",
				predicted == (nx, ny),
				"| cost delta:",
				c1 - c0,
				"| entity:",
				entity,
				"| measure() now:",
				m,
				"| moves:",
				moves
			)


			predicted = m


			if eaten % TIME_BUCKET == 0:

				quick_print(
					"[PROBE]",
					label,
					"avg move seconds, apples",
					eaten - TIME_BUCKET,
					"to",
					eaten,
					":",
					bucket_seconds / bucket_moves
				)

				bucket_seconds = 0

				bucket_moves = 0


	# --------------------------------------------------------
	# HAT OFF
	# --------------------------------------------------------

	c_hat = num_items(
		item
	)


	change_hat(
		Hats.Straw_Hat
	)


	bones = (
		num_items(Items.Bone)
		- bones_start
	)


	quick_print(
		"[PROBE]",
		label,
		"hat off | apples:",
		eaten,
		"| moves:",
		moves,
		"| bones:",
		bones,
		"| cost item delta:",
		num_items(item) - c_hat,
		"| entity under drone:",
		get_entity_type()
	)


	return (
		bones,
		eaten
	)


# ============================================================
# RUN
# ============================================================

quick_print(
	"[PROBE] world:",
	get_world_size(),
	"| Dinosaurs level:",
	num_unlocked(Unlocks.Dinosaurs),
	"| Apple cost:",
	get_cost(Entities.Apple)
)


a = run(
	"A",
	K_SMALL,
	True
)

b = run(
	"B",
	K_LONG,
	False
)


for result in [a, b]:

	if result[1] > 0:

		quick_print(
			"[PROBE] apples:",
			result[1],
			"| bones:",
			result[0],
			"| bones/apples:",
			result[0] / result[1],
			"| bones/apples^2:",
			result[0] / (result[1] * result[1])
		)
