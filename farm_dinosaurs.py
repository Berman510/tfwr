import farm_config
import farm_common
import farm_telemetry


# ============================================================
# DINOSAUR RULES
# ============================================================
#
# Confirmed by dino_probe.py (32x32, Dinosaurs level 6):
#
#   - Wearing the Dinosaur Hat spawns an Apple under the drone.
#
#   - Standing on an Apple, measure() returns where the NEXT
#     Apple will spawn. Anywhere else it returns None.
#
#   - Every Apple eaten grows the tail by one.
#
#   - The field edge is a wall. There is no wraparound.
#
#   - A move into the tail fails harmlessly.
#
#   - Removing the hat pays 32 x apples^2 Bones at level 6.
#     A full 32x32 field is 1023 Apples = 33,488,928 Bones.
#
#   - Moves get CHEAPER as the tail grows:
#
#         ~0.06 sec with a short tail
#         ~0.01 sec by 60 Apples
#
#
# PERFORMANCE LESSON (sim_dino, first attempt)
#
#     Code between moves costs game time too. Once moves are
#     cheap, per-move overhead dominates:
#
#         plain cycle          ~194k moves   2028 sec
#         heavy shortcut loop  ~120k moves   3042 sec
#
#     38% fewer moves, 50% MORE time.
#
#     So:
#
#         - hot loops use bare move() with no telemetry calls
#         - cycle order and neighbours are precomputed tables
#         - an Apple is detected by head == apple, not by
#           get_entity_type()
#         - no can_move(); a failed move() triggers the
#           emergency fallback instead
#         - shortcuts only run in the early game, where moves
#           are expensive, then the bare cycle_once loop takes
#           over
#
#
# STRATEGY
#
#     Follow a Hamiltonian cycle that covers every tile.
#
#     Until the tail covers dinosaur_shortcut_max_fill of the
#     field, skip ahead along the cycle toward the next Apple
#     whenever it is safe:
#
#         - never skip past the Apple
#         - never skip to within SHORTCUT_BUFFER steps of
#           the tail
#
#     The tail always lies in cycle order behind the head, so
#     the plain cycle path stays open.
#
#     One caveat: skipped tiles remain as gaps inside the body
#     until the tail passes them, and the tail pauses whenever
#     an Apple is eaten. If Apples kept spawning directly in
#     front of the head, it could catch the tail before those
#     gaps clear. SHORTCUT_BUFFER makes that astronomically
#     unlikely, and an emergency fallback keeps the run alive
#     if it ever happens.
#
#     Then return to (0, 0) along the cycle and run the plain
#     cycle until the field is full.
# ============================================================


DIRECTIONS = [
	North,
	East,
	South,
	West
]


# Never jump to within this many cycle steps of the tail.
#
# Trapping the head would need roughly this many Apples to
# spawn almost exactly in its path, one after another.

SHORTCUT_BUFFER = 8


# ============================================================
# LAST RUN STATS
# ============================================================
#
# Read by dino_ab.py. Module state is per drone, and the
# dinosaur run only ever uses the coordinator.

LAST_RUN = {
	"apples_at_switch": 0,
	"shortcut_phase_moves": 0,
	"shortcut_moves": 0,
	"emergency_moves": 0
}


# ============================================================
# ONE HAMILTONIAN CYCLE (PLAIN MODE)
# ============================================================
#
# Starts and ends at (0, 0). Bare move() calls only.

def cycle_once(
	size
):

	for i in range(
		size - 1
	):

		if not move(
			North
		):

			return False


	for x in range(
		1,
		size
	):

		if not move(
			East
		):

			return False


		if x % 2 == 1:

			for i in range(
				size - 2
			):

				if not move(
					South
				):

					return False


		else:

			for i in range(
				size - 2
			):

				if not move(
					North
				):

					return False


	if not move(
		South
	):

		return False


	for i in range(
		size - 1
	):

		if not move(
			West
		):

			return False


	return True


def run_plain_cycle(
	size
):
	# Ends when the field is full and the next move is blocked.

	for circuit in range(
		size * size
	):

		if not cycle_once(
			size
		):

			break


# ============================================================
# CYCLE SUCCESSOR
# ============================================================
#
# Same cycle as cycle_once:
#
#     column 0 northward
#     columns 1 .. size-1 serpentine over rows 1 .. size-1
#     row 0 westward back to (0, 0)
#
# Requires an even size.

def cycle_dir(
	x,
	y,
	size
):

	if y == 0:

		if x > 0:

			return West

		return North


	if x == 0:

		if y < size - 1:

			return North

		return East


	if x % 2 == 1:

		if y > 1:

			return South

		if x < size - 1:

			return East

		return South


	if y < size - 1:

		return North

	return East


def neighbor(
	x,
	y,
	direction
):

	if direction == North:

		return (
			x,
			y + 1
		)

	if direction == South:

		return (
			x,
			y - 1
		)

	if direction == East:

		return (
			x + 1,
			y
		)

	return (
		x - 1,
		y
	)


# ============================================================
# PRECOMPUTED CYCLE TABLES
# ============================================================
#
# index[x][y]      cycle position of tile (x, y); (0, 0) = 0
# next_dir[i]      direction from cycle position i to i + 1
# neighbors[i]     [(direction, cycle position), ...] for every
#                  in-bounds neighbour of cycle position i

def build_tables(
	size
):

	total = (
		size
		* size
	)


	index = []


	for x in range(size):

		column = []


		for y in range(size):

			column.append(
				0
			)


		index.append(
			column
		)


	xs = []

	ys = []

	next_dir = []


	x = 0

	y = 0


	for i in range(
		total
	):

		index[x][y] = i

		xs.append(
			x
		)

		ys.append(
			y
		)


		direction = cycle_dir(
			x,
			y,
			size
		)

		next_dir.append(
			direction
		)


		step = neighbor(
			x,
			y,
			direction
		)

		x = step[0]

		y = step[1]


	neighbors = []


	for i in range(
		total
	):

		options = []


		for direction in DIRECTIONS:

			step = neighbor(
				xs[i],
				ys[i],
				direction
			)


			if (
				step[0] >= 0
				and
				step[0] < size
				and
				step[1] >= 0
				and
				step[1] < size
			):

				options.append(
					(
						direction,
						index[step[0]][step[1]]
					)
				)


		neighbors.append(
			options
		)


	return (
		index,
		next_dir,
		neighbors
	)


# ============================================================
# EMERGENCY FALLBACK
# ============================================================
#
# Should never trigger (see header). Take any open neighbour.

def emergency_move():

	for direction in DIRECTIONS:

		if move(
			direction
		):

			LAST_RUN["emergency_moves"] = (
				LAST_RUN["emergency_moves"] + 1
			)

			return True


	return False


# ============================================================
# SHORTCUT RUN
# ============================================================

def run_shortcuts(
	size,
	max_fill
):

	total = (
		size
		* size
	)


	tables = build_tables(
		size
	)

	index = tables[0]

	next_dir = tables[1]

	neighbors = tables[2]


	head = index[
		get_pos_x()
	][
		get_pos_y()
	]


	# --------------------------------------------------------
	# HEAD HISTORY RING
	# --------------------------------------------------------
	#
	# history[moves % total] = head cycle position after that
	# move. With N tail pieces, the oldest piece sits where the
	# head was N moves ago.

	history = []


	for i in range(
		total
	):

		history.append(
			head
		)


	# --------------------------------------------------------
	# FIRST APPLE
	# --------------------------------------------------------
	#
	# The hat spawns an Apple under the drone, so we already
	# stand on Apple 1 and can measure Apple 2.

	apple = -1

	pieces = 1


	if get_entity_type() == Entities.Apple:

		target = measure()


		if target != None:

			apple = index[
				target[0]
			][
				target[1]
			]


	stop_pieces = min(
		total * max_fill,
		total - 2
	)


	moves = 0

	shortcuts = 0

	on_cycle = True


	# --------------------------------------------------------
	# SHORTCUT PHASE
	# --------------------------------------------------------

	while (
		apple >= 0
		and
		pieces < stop_pieces
	):

		tail = history[
			(moves - pieces) % total
		]


		free = total


		if tail != head:

			free = (
				(tail - head)
				% total
			)


		direction = next_dir[head]

		destination = (
			(head + 1)
			% total
		)


		reach = min(
			(apple - head) % total,
			free - SHORTCUT_BUFFER - 1
		)


		if reach > 1:

			best = 1


			for option in neighbors[head]:

				distance = (
					(option[1] - head)
					% total
				)


				if (
					distance > best
					and
					distance <= reach
				):

					best = distance

					direction = option[0]

					destination = option[1]


			if best > 1:

				shortcuts = (
					shortcuts + 1
				)


		if not move(
			direction
		):

			on_cycle = False

			break


		head = destination

		moves = (
			moves + 1
		)

		history[
			moves % total
		] = head


		if head == apple:

			pieces = (
				pieces + 1
			)


			target = measure()


			if target == None:

				apple = -1

			else:

				apple = index[
					target[0]
				][
					target[1]
				]


	LAST_RUN["apples_at_switch"] = pieces

	LAST_RUN["shortcut_phase_moves"] = moves

	LAST_RUN["shortcut_moves"] = shortcuts


	# --------------------------------------------------------
	# RETURN TO (0, 0) ALONG THE CYCLE
	# --------------------------------------------------------

	if not on_cycle:

		if not emergency_move():

			return


		head = index[
			get_pos_x()
		][
			get_pos_y()
		]


	steps = 0


	while (
		head != 0
		and
		steps < total * 2
	):

		if move(
			next_dir[head]
		):

			head = (
				(head + 1)
				% total
			)

		else:

			if not emergency_move():

				return


			head = index[
				get_pos_x()
			][
				get_pos_y()
			]


		steps = (
			steps + 1
		)


	if head != 0:

		return


	# --------------------------------------------------------
	# PLAIN PHASE
	# --------------------------------------------------------

	run_plain_cycle(
		size
	)


# ============================================================
# EXACT CACTUS COST
# ============================================================

def cactus_required_for_run(
	usable_tiles
):

	cost = get_cost(
		Entities.Apple
	)


	if cost == None:

		return None


	if Items.Cactus not in cost:

		return None


	return (
		cost[
			Items.Cactus
		]
		* usable_tiles
	)


# ============================================================
# DINOSAUR FARM
# ============================================================

def farm():

	phase = farm_telemetry.phase_start(
		"dinosaur run"
	)


	size = get_world_size()


	if size % 2 != 0:

		farm_telemetry.add_counter(
			"dinosaur skipped odd world",
			1
		)

		farm_telemetry.phase_end(
			"dinosaur run",
			phase
		)

		return False


	usable_tiles = (
		size
		* size
	)


	farm_telemetry.set_metric(
		"dinosaur usable tiles",
		usable_tiles
	)


	required_cactus = cactus_required_for_run(
		usable_tiles
	)


	if required_cactus == None:

		farm_telemetry.phase_end(
			"dinosaur run",
			phase
		)

		return False


	farm_telemetry.set_metric(
		"dinosaur cactus reserve required",
		required_cactus
	)


	if num_items(
		Items.Cactus
	) < required_cactus:

		farm_telemetry.phase_end(
			"dinosaur run",
			phase
		)

		return False


	clear()

	farm_common.reset_hat_after_clear()


	LAST_RUN["apples_at_switch"] = 0

	LAST_RUN["shortcut_phase_moves"] = 0

	LAST_RUN["shortcut_moves"] = 0

	LAST_RUN["emergency_moves"] = 0


	if not farm_common.wear_hat(
		Hats.Dinosaur_Hat
	):

		farm_telemetry.phase_end(
			"dinosaur run",
			phase
		)

		return False


	if farm_config.SETTINGS["dinosaur_shortcuts"]:

		run_shortcuts(
			size,
			farm_config.SETTINGS["dinosaur_shortcut_max_fill"]
		)

	else:

		run_plain_cycle(
			size
		)


	# Telemetry is recorded once per run, never per move.

	farm_telemetry.add_counter(
		"dinosaur shortcut moves",
		LAST_RUN["shortcut_moves"]
	)

	farm_telemetry.add_counter(
		"dinosaur emergency moves",
		LAST_RUN["emergency_moves"]
	)


	farm_common.wear_hat(
		Hats.Straw_Hat
	)


	farm_telemetry.phase_end(
		"dinosaur run",
		phase
	)


	return True


# ============================================================
# TRIGGER
# ============================================================

def manage():

	if not farm_config.SETTINGS["dinosaurs_enabled"]:

		return False


	if num_items(
		Items.Bone
	) >= farm_config.SETTINGS["bone_floor"]:

		return False


	return farm()
