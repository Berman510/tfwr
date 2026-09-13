import farm_config
import farm_maze


# ============================================================
# MAZE / GOLD BENCHMARK TARGET
# ============================================================
#
# Run through sim_maze.py. Measures time to gain TARGET Gold.
#
# MODE:
#
#   1 = CURRENT
#       Production farm_maze.farm(): one full maze, one drone,
#       target-guided DFS from scratch for every treasure.
#
#   2 = FULL TREE
#       One full maze, one drone. Explore the maze once into a
#       spanning tree, then walk tree paths (up to the common
#       ancestor, then down) to every treasure.
#
#   3 = SPLIT 16   4 x 16x16 mazes,  4 drones
#   4 = SPLIT 8   16 x  8x8  mazes, 16 drones
#   5 = SPLIT 4   32 x  4x4  mazes, 32 drones (checkerboard)
#   6 = SPLIT 5   32 x  5x5  mazes, 32 drones (of 36 slots)
#   7 = SPLIT 6   25 x  6x6  mazes, 25 drones
#   8 = SPLIT 3   32 x  3x3  mazes, 32 drones (of 100 slots)
#   9 = PRODUCTION  farm_maze.farm() with its default
#                   "split" settings (verifies the port)
#
#       Every drone owns one maze and runs the FULL TREE
#       method on it independently.
#
#
# Rules this relies on (confirmed by maze_probe.py):
#
#   - A fresh maze is perfect (a tree).
#   - Reusing (use_item on the treasure) pays side^2 x 32 Gold,
#     moves the treasure, and removes one wall. Walls are
#     never added, so tree paths stay valid for all reuses.
#   - use_item fails after 300 reuses; harvest() then pays once
#     more and clears the maze to Grass.
#   - A maze costs side x 32 Weird Substance. Spawned drones
#     can move and reuse inside mazes.
#
# Anchors are spaced exactly one maze side apart, so mazes
# can't overlap wherever the game places a maze relative to
# its Bush.
#
# Prints one summary line per run.
# ============================================================


SYNC_DELAY = 10

MAX_SECONDS = 20000


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


# ============================================================
# PLAIN MOVEMENT (no mazes on the field yet)
# ============================================================

def plain_go_to(
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
# SPANNING TREE OF THE CURRENT MAZE
# ============================================================
#
# Cells are ids: x * size + y. parent / parent_dir / depth are
# field-sized lists owned by the caller. Returns the list of
# visited ids so the caller can reset depth cheaply.

def build_tree(
	size,
	parent,
	parent_dir,
	depth
):

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


# ============================================================
# WALK A TREE PATH
# ============================================================

def walk_tree(
	a,
	b,
	parent,
	parent_dir,
	depth
):
	# Drone stands on cell a. Walk to cell b through their
	# lowest common ancestor. Returns b.

	down = []


	while depth[a] > depth[b]:

		move(parent_dir[a])

		a = parent[a]


	while depth[b] > depth[a]:

		down.append(parent_dir[b])

		b_up = parent[b]

		b = b_up


	while a != b:

		move(parent_dir[a])

		a = parent[a]

		down.append(parent_dir[b])

		b = parent[b]


	i = len(down) - 1


	while i >= 0:

		move(OPPOSITE[down[i]])

		i = i - 1


	return -1


# ============================================================
# ONE MAZE WORKER
# ============================================================

def worker(
	ax,
	ay,
	ox,
	oy,
	side,
	target,
	start_at,
	deadline
):
	# (ax, ay) = Bush position. (ox, oy) = the lower corner of
	# the side x side square this drone's maze must occupy.

	size = get_world_size()

	area = size * size


	parent = []

	parent_dir = []

	depth = []


	for i in range(area):

		parent.append(-1)

		parent_dir.append(North)

		depth.append(-1)


	cost = (
		side
		* 2 ** (num_unlocked(Unlocks.Mazes) - 1)
	)


	plain_go_to(
		ax,
		ay
	)


	while get_time() < start_at:

		pass


	anchor = ax * size + ay

	treasures = 0

	mazes = 0

	anomalies = 0

	reason = ""

	visited = []


	while (
		num_items(Items.Gold) < target
		and
		get_time() < deadline
	):

		# ----------------------------------------------------
		# CREATE MAZE AT ANCHOR
		# ----------------------------------------------------

		if get_entity_type() == Entities.Grass:

			harvest()


		if get_ground_type() != Grounds.Grassland:

			till()


		if not plant(Entities.Bush):

			anomalies = anomalies + 1

			reason = (
				"plant failed at "
				+ str((get_pos_x(), get_pos_y()))
				+ " entity "
				+ str(get_entity_type())
				+ " maze #"
				+ str(mazes + 1)
			)

			return (treasures, mazes, anomalies, reason)


		if not use_item(Items.Weird_Substance, cost):

			anomalies = anomalies + 1

			reason = (
				"create failed at "
				+ str((get_pos_x(), get_pos_y()))
				+ " maze #"
				+ str(mazes + 1)
			)

			return (treasures, mazes, anomalies, reason)


		mazes = mazes + 1


		for cell in visited:

			depth[cell] = -1


		visited = build_tree(
			size,
			parent,
			parent_dir,
			depth
		)


		# ----------------------------------------------------
		# VERIFY THE MAZE SITS EXACTLY IN THIS DRONE'S SQUARE
		# ----------------------------------------------------

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
			or
			len(visited) != side * side
		):

			anomalies = anomalies + 1

			reason = (
				"region mismatch for square "
				+ str((ox, oy))
				+ ": x "
				+ str(min_x)
				+ ".."
				+ str(max_x)
				+ " y "
				+ str(min_y)
				+ ".."
				+ str(max_y)
				+ " cells "
				+ str(len(visited))
			)


		here = get_pos_x() * size + get_pos_y()


		# ----------------------------------------------------
		# COLLECT UP TO 301 TREASURES
		# ----------------------------------------------------

		while True:

			spot = measure()


			if spot == None:

				anomalies = anomalies + 1

				reason = (
					"measure None at "
					+ str((get_pos_x(), get_pos_y()))
					+ " maze #"
					+ str(mazes)
				)

				return (treasures, mazes, anomalies, reason)


			goal = spot[0] * size + spot[1]


			if depth[goal] == -1:

				# Treasure outside this drone's maze.
				anomalies = anomalies + 1

				reason = (
					"treasure "
					+ str(spot)
					+ " outside maze of anchor "
					+ str((ax, ay))
					+ " at "
					+ str((get_pos_x(), get_pos_y()))
					+ " maze #"
					+ str(mazes)
					+ " cells "
					+ str(len(visited))
				)

				return (treasures, mazes, anomalies, reason)


			walk_tree(
				here,
				goal,
				parent,
				parent_dir,
				depth
			)

			here = goal


			if num_items(Items.Gold) >= target:

				return (treasures, mazes, anomalies, reason)


			if use_item(Items.Weird_Substance, cost):

				treasures = treasures + 1

				continue


			# Reuse cap reached: final harvest clears the maze.

			harvest()

			treasures = treasures + 1


			# Hedges are gone, so the tree path back to the
			# anchor stays inside this drone's own cells.

			walk_tree(
				here,
				anchor,
				parent,
				parent_dir,
				depth
			)

			break


	return (treasures, mazes, anomalies, reason)


# ============================================================
# CALIBRATE MAZE PLACEMENT
# ============================================================
#
# Round 2 showed mazes are NOT built from the Bush's corner:
# edge mazes shifted and overlapped their neighbours, wiping
# treasures. Build one maze with its Bush in the middle of the
# field, map it, and measure where its lower corner lands
# relative to the Bush. Then clear it by harvesting.
#
# Returns (offset_x, offset_y): Bush = square corner + offset.

def calibrate(
	side
):

	size = get_world_size()

	area = size * size


	parent = []

	parent_dir = []

	depth = []


	for i in range(area):

		parent.append(-1)

		parent_dir.append(North)

		depth.append(-1)


	cost = (
		side
		* 2 ** (num_unlocked(Unlocks.Mazes) - 1)
	)


	bx = size // 2

	by = size // 2


	plain_go_to(
		bx,
		by
	)


	if get_entity_type() == Entities.Grass:

		harvest()


	if get_ground_type() != Grounds.Grassland:

		till()


	plant(
		Entities.Bush
	)

	use_item(
		Items.Weird_Substance,
		cost
	)


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
# SPLIT RUN
# ============================================================

def run_split(
	side
):

	size = get_world_size()

	clear()


	offset = calibrate(
		side
	)


	per_row = size // side

	first = []

	second = []


	# Slots are spaced exactly one side apart. When there are
	# more slots than drones, fill a checkerboard first so
	# active mazes are spread over the whole field.

	# Each slot: (bush x, bush y, square corner x, square corner y)

	for i in range(per_row):

		for j in range(per_row):

			slot = (
				i * side + offset[0],
				j * side + offset[1],
				i * side,
				j * side
			)


			if (i + j) % 2 == 0:

				first.append(
					slot
				)

			else:

				second.append(
					slot
				)


	anchors = []


	for slot in first:

		if len(anchors) < max_drones():

			anchors.append(
				slot
			)


	for slot in second:

		if len(anchors) < max_drones():

			anchors.append(
				slot
			)


	start_at = get_time() + SYNC_DELAY

	deadline = start_at + MAX_SECONDS


	handles = []


	for k in range(1, len(anchors)):

		handle = spawn_drone(
			worker,
			anchors[k][0],
			anchors[k][1],
			anchors[k][2],
			anchors[k][3],
			side,
			TARGET,
			start_at,
			deadline
		)


		if handle != None:

			handles.append(
				handle
			)


	totals = worker(
		anchors[0][0],
		anchors[0][1],
		anchors[0][2],
		anchors[0][3],
		side,
		TARGET,
		start_at,
		deadline
	)


	treasures = totals[0]

	mazes = totals[1]

	anomalies = totals[2]

	reasons = []


	if totals[3] != "":

		reasons.append(
			totals[3]
		)


	for handle in handles:

		result = wait_for(
			handle
		)

		treasures = treasures + result[0]

		mazes = mazes + result[1]

		anomalies = anomalies + result[2]


		if result[3] != "":

			reasons.append(
				result[3]
			)


	return (
		treasures,
		mazes,
		anomalies,
		len(handles) + 1,
		reasons
	)


# ============================================================
# ENTRYPOINT
# ============================================================

SIDES = {
	3: 16,
	4: 8,
	5: 4,
	6: 5,
	7: 6,
	8: 3
}


if MODE == 1:

	farm_config.SETTINGS["gold_floor"] = TARGET

	farm_config.SETTINGS["maze_method"] = "single"

	farm_maze.farm()

	stats = (-1, -1, 0, 1, [])


elif MODE == 9:

	# Production farm_maze with its default split settings.

	farm_config.SETTINGS["gold_floor"] = TARGET

	farm_config.SETTINGS["maze_method"] = "split"

	farm_maze.farm()

	stats = (
		farm_maze.LAST_RUN["treasures"],
		farm_maze.LAST_RUN["mazes"],
		farm_maze.LAST_RUN["anomalies"],
		farm_maze.LAST_RUN["drones"],
		[]
	)


elif MODE == 2:

	clear()

	result = worker(
		0,
		0,
		0,
		0,
		get_world_size(),
		TARGET,
		get_time(),
		get_time() + MAX_SECONDS
	)

	reasons = []


	if result[3] != "":

		reasons.append(
			result[3]
		)


	stats = (
		result[0],
		result[1],
		result[2],
		1,
		reasons
	)


else:

	stats = run_split(
		SIDES[MODE]
	)


quick_print(
	"  drones:",
	stats[3],
	"| treasures:",
	stats[0],
	"| mazes:",
	stats[1],
	"| anomalies:",
	stats[2],
	"| gold:",
	num_items(Items.Gold)
)


for anomaly in stats[4]:

	quick_print(
		"  anomaly:",
		anomaly
	)
