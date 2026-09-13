import farm_config
import farm_common
import farm_telemetry


# ============================================================
# GOLD FARMING
# ============================================================
#
# farm_config.SETTINGS["maze_method"]:
#
#   "split" (default)
#       Tile the field with small mazes, one per drone
#       (maze_split_side x maze_split_side). Each drone maps its
#       maze once into a spanning tree, walks tree paths to all
#       301 treasures (300 reuses + final harvest), then
#       rebuilds. With only one free drone, it runs one
#       full-field maze instead.
#
#   "single"
#       The original solver: one full maze, one drone,
#       target-guided DFS from scratch for every treasure.
#
#
# Maze rules (maze_probe.py, 32x32, Mazes 6):
#
#   - A fresh maze is perfect (a tree). A move takes ~0.05 sec.
#   - Reusing (use_item on the treasure) pays side^2 x 32 Gold
#     at once, moves the treasure and removes one wall. Walls
#     are never added, so tree paths stay valid.
#   - use_item fails after 300 reuses; harvest() pays once
#     more and clears the maze to Grass.
#   - A maze costs side x 32 Weird Substance.
#   - Spawned drones can move and reuse inside mazes.
#   - Mazes are NOT built from the Bush's corner; placement is
#     calibrated once per run so every maze fills exactly its
#     own square.
#
#
# sim_maze, 32x32 / 32 drones, time to +10M Gold:
#
#   single (original)       3369.77 sec     2,968 Gold/sec
#   full maze, tree paths   2122.77 sec     4,711 Gold/sec
#   split 4x4                146.83 sec    68,105 Gold/sec
#   split 5x5                132.42 sec    75,520 Gold/sec  25.45x
#   split 6x6 (25 drones)    156.19 sec    64,026 Gold/sec
# ============================================================


SPLIT_SYNC_DELAY = 5


DIRS = [
	North,
	East,
	South,
	West
]

OPPOSITE = {
	North: South,
	South: North,
	East: West,
	West: East
}


LAST_RUN = {
	"method": "",
	"drones": 0,
	"treasures": 0,
	"mazes": 0,
	"anomalies": 0
}


# ============================================================
# MAZE COST
# ============================================================

def substance_cost():

	return (
		get_world_size()
		* 2 ** (
			num_unlocked(
				Unlocks.Mazes
			)
			- 1
		)
	)


# ============================================================
# TREASURE VALUE
# ============================================================

def treasure_value():

	size = get_world_size()

	multiplier = (
		2 ** (
			num_unlocked(
				Unlocks.Mazes
			)
			- 1
		)
	)


	return (
		size
		* size
		* multiplier
	)


# ============================================================
# DIRECTIONS
# ============================================================

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


def neighbor_position(
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
# TARGET-GUIDED DIRECTION ORDER
# ============================================================

def preferred_directions(
	x,
	y,
	target_x,
	target_y
):

	directions = []


	dx = (
		target_x - x
	)

	dy = (
		target_y - y
	)


	if abs(dx) >= abs(dy):

		if dx > 0:

			directions.append(
				East
			)

		elif dx < 0:

			directions.append(
				West
			)


		if dy > 0:

			directions.append(
				North
			)

		elif dy < 0:

			directions.append(
				South
			)


	else:

		if dy > 0:

			directions.append(
				North
			)

		elif dy < 0:

			directions.append(
				South
			)


		if dx > 0:

			directions.append(
				East
			)

		elif dx < 0:

			directions.append(
				West
			)


	all_directions = [
		North,
		East,
		South,
		West
	]


	for direction in all_directions:

		if direction not in directions:

			directions.append(
				direction
			)


	return directions


# ============================================================
# SOLVE
# ============================================================

def solve():

	solve_start = get_time()


	target = measure()


	if target == None:

		return False


	target_x = target[0]
	target_y = target[1]


	start = (
		get_pos_x(),
		get_pos_y()
	)


	visited = {}

	parent = {}


	size = get_world_size()


	while True:

		x = get_pos_x()
		y = get_pos_y()


		if (
			x == target_x
			and
			y == target_y
		):

			farm_telemetry.add_counter(
				"maze solve seconds",
				get_time() - solve_start
			)


			return (
				get_entity_type()
				== Entities.Treasure
			)


		current = (
			x,
			y
		)


		if current not in visited:

			farm_telemetry.add_counter(
				"maze nodes visited",
				1
			)


		visited[
			current
		] = True


		directions = preferred_directions(
			x,
			y,
			target_x,
			target_y
		)


		moved_forward = False


		for direction in directions:

			next_position = neighbor_position(
				x,
				y,
				direction
			)

			next_x = next_position[0]
			next_y = next_position[1]


			if (
				next_x < 0
				or
				next_x >= size
				or
				next_y < 0
				or
				next_y >= size
			):

				continue


			if next_position in visited:

				continue


			farm_telemetry.add_counter(
				"maze move attempts",
				1
			)


			if move(
				direction
			):

				farm_telemetry.add_counter(
					"maze successful forward moves",
					1
				)


				parent[
					next_position
				] = opposite(
					direction
				)

				moved_forward = True

				break


			else:

				farm_telemetry.add_counter(
					"maze blocked moves",
					1
				)


		if moved_forward:

			continue


		if current == start:

			farm_telemetry.add_counter(
				"maze solve failures",
				1
			)

			return False


		if current not in parent:

			farm_telemetry.add_counter(
				"maze solve failures",
				1
			)

			return False


		back = parent[
			current
		]


		farm_telemetry.add_counter(
			"maze backtracks",
			1
		)

		farm_telemetry.add_counter(
			"maze move attempts",
			1
		)


		if move(
			back
		):

			farm_telemetry.add_counter(
				"maze successful backtrack moves",
				1
			)

		else:

			farm_telemetry.add_counter(
				"maze blocked moves",
				1
			)

			farm_telemetry.add_counter(
				"maze solve failures",
				1
			)

			return False


# ============================================================
# CREATE MAZE
# ============================================================

def create():

	create_start = get_time()


	clear()

	farm_common.reset_hat_after_clear()


	farm_common.go_to(
		0,
		0
	)


	farm_common.harvest_reset_grass()

	farm_common.make_grassland()


	if not farm_common.plant_if_affordable(
		Entities.Bush
	):

		return False


	needed = substance_cost()


	if num_items(
		Items.Weird_Substance
	) < needed:

		return False


	if not use_item(
		Items.Weird_Substance,
		needed
	):

		return False


	farm_telemetry.add_counter(
		"fresh mazes created",
		1
	)

	farm_telemetry.add_counter(
		"maze creation seconds",
		get_time() - create_start
	)


	return True


# ============================================================
# REUSE MAZE
# ============================================================

def reuse():

	needed = substance_cost()


	if num_items(
		Items.Weird_Substance
	) < needed:

		return False


	result = use_item(
		Items.Weird_Substance,
		needed
	)


	if result:

		farm_telemetry.add_counter(
			"maze reuses",
			1
		)


	return result


# ============================================================
# FARM MAZES
# ============================================================

def farm_single():

	phase = farm_telemetry.phase_start(
		"maze batch"
	)


	needed = substance_cost()


	if num_items(
		Items.Weird_Substance
	) < needed:

		farm_telemetry.phase_end(
			"maze batch",
			phase
		)

		return False


	if not create():

		farm_telemetry.phase_end(
			"maze batch",
			phase
		)

		return False


	completed = 0

	reuses_on_current_maze = 0


	while (
		num_items(
			Items.Gold
		)
		<
		farm_config.SETTINGS["gold_floor"]
	):

		if not solve():

			clear()

			farm_common.reset_hat_after_clear()

			break


		will_reach_goal = (
			num_items(
				Items.Gold
			)
			+
			treasure_value()
			>=
			farm_config.SETTINGS["gold_floor"]
		)


		can_reuse = (
			reuses_on_current_maze < 300
			and
			num_items(
				Items.Weird_Substance
			) >= needed
		)


		if (
			will_reach_goal
			or
			not can_reuse
		):

			harvest()

			completed = (
				completed + 1
			)


			farm_telemetry.add_counter(
				"maze treasures collected",
				1
			)


			if (
				num_items(
					Items.Gold
				)
				>=
				farm_config.SETTINGS["gold_floor"]
			):

				break


			if num_items(
				Items.Weird_Substance
			) < needed:

				break


			if not create():

				break


			reuses_on_current_maze = 0


		else:

			if reuse():

				completed = (
					completed + 1
				)

				reuses_on_current_maze = (
					reuses_on_current_maze + 1
				)

				farm_telemetry.add_counter(
					"maze treasures collected",
					1
				)


			else:

				harvest()

				completed = (
					completed + 1
				)

				farm_telemetry.add_counter(
					"maze treasures collected",
					1
				)

				break


	farm_telemetry.phase_end(
		"maze batch",
		phase
	)


	return (
		completed > 0
	)


# ============================================================
# SPLIT METHOD: COSTS
# ============================================================

def maze_cost(
	side
):

	return (
		side
		* 2 ** (
			num_unlocked(
				Unlocks.Mazes
			)
			- 1
		)
	)


def available_drones():

	count = (
		max_drones()
		- num_drones()
		+ 1
	)


	if count < 1:

		return 1


	return count


def split_side():

	side = farm_config.SETTINGS["maze_split_side"]

	size = get_world_size()


	if side > size:

		return size


	return side


def substance_reserve():
	# Weird Substance to keep so Gold farming can start: one
	# maze per drone for "split", one full maze for "single".

	if farm_config.SETTINGS["maze_method"] == "single":

		return substance_cost()


	return (
		maze_cost(
			split_side()
		)
		* max_drones()
	)


def substance_to_start():

	if farm_config.SETTINGS["maze_method"] == "single":

		return substance_cost()


	return maze_cost(
		split_side()
	)


# ============================================================
# SPLIT METHOD: SPANNING TREE
# ============================================================
#
# Cell ids are x * size + y. parent / parent_dir / depth are
# field-sized lists owned by the caller. Hot loops use bare
# move() and no telemetry: code between moves costs game time.

def new_tree_lists():

	area = (
		get_world_size()
		* get_world_size()
	)


	parent = []

	parent_dir = []

	depth = []


	for i in range(area):

		parent.append(-1)

		parent_dir.append(North)

		depth.append(-1)


	return (
		parent,
		parent_dir,
		depth
	)


def build_tree(
	size,
	parent,
	parent_dir,
	depth
):
	# DFS over the maze the drone stands in. Returns the list
	# of visited cell ids.

	x = get_pos_x()

	y = get_pos_y()

	root = x * size + y

	depth[root] = 0

	parent[root] = -1


	visited = [root]

	stack = []


	while True:

		here = x * size + y

		moved = False


		for d in DIRS:

			if not can_move(d):

				continue


			if d == North:

				nx = x

				ny = (y + 1) % size

			elif d == South:

				nx = x

				ny = (y - 1) % size

			elif d == East:

				nx = (x + 1) % size

				ny = y

			else:

				nx = (x - 1) % size

				ny = y


			n = nx * size + ny


			if depth[n] != -1:

				continue


			move(d)

			parent[n] = here

			parent_dir[n] = OPPOSITE[d]

			depth[n] = depth[here] + 1

			visited.append(n)

			stack.append(d)

			x = nx

			y = ny

			moved = True

			break


		if moved:

			continue


		if len(stack) == 0:

			return visited


		back = OPPOSITE[stack.pop()]

		move(back)


		if back == North:

			y = (y + 1) % size

		elif back == South:

			y = (y - 1) % size

		elif back == East:

			x = (x + 1) % size

		else:

			x = (x - 1) % size


def walk_tree(
	a,
	b,
	parent,
	parent_dir,
	depth
):
	# Drone stands on cell a. Walk to cell b through their
	# lowest common ancestor.

	down = []


	while depth[a] > depth[b]:

		move(parent_dir[a])

		a = parent[a]


	while depth[b] > depth[a]:

		down.append(parent_dir[b])

		b = parent[b]


	while a != b:

		move(parent_dir[a])

		a = parent[a]

		down.append(parent_dir[b])

		b = parent[b]


	i = len(down) - 1


	while i >= 0:

		move(OPPOSITE[down[i]])

		i = i - 1


def plant_maze(
	cost
):

	if get_entity_type() == Entities.Grass:

		harvest()


	if get_ground_type() != Grounds.Grassland:

		till()


	if not plant(Entities.Bush):

		return False


	return use_item(
		Items.Weird_Substance,
		cost
	)


# ============================================================
# SPLIT METHOD: PLACEMENT CALIBRATION
# ============================================================
#
# Build one maze with its Bush mid-field, map it, and measure
# where its lower corner lands. Then clear it by harvesting.
#
# Returns (offset_x, offset_y): Bush = square corner + offset,
# or None if the maze couldn't be built.

def calibrate(
	side
):

	size = get_world_size()

	lists = new_tree_lists()

	parent = lists[0]

	parent_dir = lists[1]

	depth = lists[2]


	bx = size // 2

	by = size // 2


	farm_common.go_to(
		bx,
		by
	)


	if not plant_maze(
		maze_cost(side)
	):

		return None


	visited = build_tree(
		size,
		parent,
		parent_dir,
		depth
	)


	min_x = size

	min_y = size


	for cell in visited:

		min_x = min(min_x, cell // size)

		min_y = min(min_y, cell % size)


	spot = measure()


	if spot != None:

		walk_tree(
			bx * size + by,
			spot[0] * size + spot[1],
			parent,
			parent_dir,
			depth
		)

		harvest()


	return (
		bx - min_x,
		by - min_y
	)


# ============================================================
# SPLIT METHOD: ONE DRONE'S MAZE LOOP
# ============================================================
#
# (ax, ay) = Bush position. (ox, oy) = lower corner of the
# side x side square this drone's maze must fill.
#
# Returns (treasures, mazes, anomalies).

def split_worker(
	ax,
	ay,
	ox,
	oy,
	side,
	target,
	start_at,
	deadline
):

	size = get_world_size()

	lists = new_tree_lists()

	parent = lists[0]

	parent_dir = lists[1]

	depth = lists[2]

	cost = maze_cost(side)


	farm_common.go_to(
		ax,
		ay
	)


	while get_time() < start_at:

		pass


	anchor = ax * size + ay

	treasures = 0

	mazes = 0

	anomalies = 0

	visited = []


	while (
		num_items(Items.Gold) < target
		and
		get_time() < deadline
	):

		if not plant_maze(cost):

			# Out of Weird Substance, or the tile is blocked.
			return (treasures, mazes, anomalies)


		mazes = mazes + 1


		for cell in visited:

			depth[cell] = -1


		visited = build_tree(
			size,
			parent,
			parent_dir,
			depth
		)


		# The maze must fill exactly this drone's square.

		min_x = size

		min_y = size

		max_x = -1

		max_y = -1


		for cell in visited:

			cx = cell // size

			cy = cell % size

			min_x = min(min_x, cx)

			min_y = min(min_y, cy)

			max_x = max(max_x, cx)

			max_y = max(max_y, cy)


		if (
			min_x != ox
			or
			min_y != oy
			or
			max_x != ox + side - 1
			or
			max_y != oy + side - 1
		):

			anomalies = anomalies + 1


		here = get_pos_x() * size + get_pos_y()


		while True:

			spot = measure()


			if spot == None:

				anomalies = anomalies + 1

				return (treasures, mazes, anomalies)


			goal = spot[0] * size + spot[1]


			if depth[goal] == -1:

				anomalies = anomalies + 1

				return (treasures, mazes, anomalies)


			walk_tree(
				here,
				goal,
				parent,
				parent_dir,
				depth
			)

			here = goal


			if (
				num_items(Items.Gold) >= target
				or
				get_time() >= deadline
			):

				return (treasures, mazes, anomalies)


			if use_item(Items.Weird_Substance, cost):

				treasures = treasures + 1

				continue


			# Reuse cap (or out of substance): the final harvest
			# clears the maze. Hedges are gone, so the tree path
			# back to the Bush stays inside this drone's square.

			harvest()

			treasures = treasures + 1


			walk_tree(
				here,
				anchor,
				parent,
				parent_dir,
				depth
			)

			break


	return (treasures, mazes, anomalies)


# ============================================================
# SPLIT METHOD: RUN
# ============================================================

def farm_split(
	target,
	max_seconds
):

	size = get_world_size()

	side = split_side()

	workers = available_drones()


	clear()

	farm_common.reset_hat_after_clear()


	# --------------------------------------------------------
	# ONE FREE DRONE: a single full-field maze beats a small
	# maze per drone-trip.
	# --------------------------------------------------------

	if workers < 2:

		side = size


	offset = (0, 0)


	if side < size:

		offset = calibrate(
			side
		)


		if offset == None:

			return False


	# --------------------------------------------------------
	# SQUARES: checkerboard first, then the rest, up to the
	# number of free drones.
	# --------------------------------------------------------

	per_row = size // side

	first = []

	second = []


	for i in range(per_row):

		for j in range(per_row):

			slot = (
				i * side + offset[0],
				j * side + offset[1],
				i * side,
				j * side
			)


			if (i + j) % 2 == 0:

				first.append(slot)

			else:

				second.append(slot)


	slots = []


	for slot in first:

		if len(slots) < workers:

			slots.append(slot)


	for slot in second:

		if len(slots) < workers:

			slots.append(slot)


	start_at = get_time() + SPLIT_SYNC_DELAY

	deadline = start_at + max_seconds


	handles = []


	for k in range(1, len(slots)):

		handle = spawn_drone(
			split_worker,
			slots[k][0],
			slots[k][1],
			slots[k][2],
			slots[k][3],
			side,
			target,
			start_at,
			deadline
		)


		if handle != None:

			handles.append(handle)


	totals = split_worker(
		slots[0][0],
		slots[0][1],
		slots[0][2],
		slots[0][3],
		side,
		target,
		start_at,
		deadline
	)


	treasures = totals[0]

	mazes = totals[1]

	anomalies = totals[2]


	for handle in handles:

		result = wait_for(handle)

		treasures = treasures + result[0]

		mazes = mazes + result[1]

		anomalies = anomalies + result[2]


	# Leave a clean field for the crop rotation.

	clear()

	farm_common.reset_hat_after_clear()


	LAST_RUN["method"] = "split " + str(side)

	LAST_RUN["drones"] = len(handles) + 1

	LAST_RUN["treasures"] = treasures

	LAST_RUN["mazes"] = mazes

	LAST_RUN["anomalies"] = anomalies


	farm_telemetry.add_counter(
		"maze treasures collected",
		treasures
	)

	farm_telemetry.add_counter(
		"maze mazes created",
		mazes
	)

	farm_telemetry.add_counter(
		"maze anomalies",
		anomalies
	)

	farm_telemetry.max_metric(
		"maze drones",
		len(handles) + 1
	)


	return treasures > 0


# ============================================================
# FARM GOLD
# ============================================================

def farm():

	if farm_config.SETTINGS["maze_method"] == "single":

		LAST_RUN["method"] = "single"

		return farm_single()


	phase = farm_telemetry.phase_start(
		"maze batch"
	)


	result = farm_split(
		farm_config.SETTINGS["gold_floor"],
		farm_config.SETTINGS["maze_max_seconds"]
	)


	farm_telemetry.phase_end(
		"maze batch",
		phase
	)


	return result


# ============================================================
# TRIGGER
# ============================================================

def manage():

	if not farm_config.SETTINGS["mazes_enabled"]:

		return False


	if num_items(
		Items.Gold
	) >= farm_config.SETTINGS["gold_floor"]:

		return False


	if num_items(
		Items.Weird_Substance
	) < substance_to_start():

		return False


	return farm()