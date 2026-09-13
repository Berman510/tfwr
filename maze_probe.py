# ============================================================
# MAZE RULES PROBE
# ============================================================
#
# Run through sim_maze.py (PROBE = True).
#
# Answers the questions a faster Gold solver depends on:
#
#   A. Fresh maze: is it a perfect maze (open edges =
#      cells - 1)? How long does a move take?
#
#   B. Reuse: does use_item(Weird_Substance) on the treasure
#      pay Gold? Does it change the walls?
#
#   C. Reuse cap: how many reuses before use_item fails, and
#      what does the final harvest pay? Uses a remembered wall
#      map + BFS shortest paths, so it also measures that
#      solver's speed per treasure.
#
#   D. Drones: can a spawned drone move inside the maze and
#      reuse / harvest the treasure?
#
#   E. Half-cost maze: what does use_item with half the usual
#      Weird Substance produce?
#
# Every line of output starts with [PROBE].
#
# This file intentionally imports nothing.
# ============================================================


DIRS = [
	North,
	East,
	South,
	West
]

REUSE_LIMIT_TEST = 310


# ============================================================
# GEOMETRY
# ============================================================

def opposite(
	d
):

	if d == North:

		return South

	if d == South:

		return North

	if d == East:

		return West

	return East


def step(
	x,
	y,
	d,
	size
):

	if d == North:

		return (x, (y + 1) % size)

	if d == South:

		return (x, (y - 1) % size)

	if d == East:

		return ((x + 1) % size, y)

	return ((x - 1) % size, y)


def substance_cost():

	return (
		get_world_size()
		* 2 ** (num_unlocked(Unlocks.Mazes) - 1)
	)


def plain_go_to(
	x,
	y
):
	# Only used outside mazes (normal farm wraps).

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
# CREATE MAZE
# ============================================================

def create_maze(
	amount
):

	clear()

	plain_go_to(
		0,
		0
	)


	if get_entity_type() == Entities.Grass:

		harvest()


	if get_ground_type() != Grounds.Grassland:

		till()


	plant(
		Entities.Bush
	)


	t0 = get_time()

	ok = use_item(
		Items.Weird_Substance,
		amount
	)


	return (
		ok,
		get_time() - t0
	)


# ============================================================
# MAP HELPERS
# ============================================================

# The wall map is a dict: (x, y, direction) -> True when open,
# False once a move there was blocked. Dicts avoid relying on
# set removal, which may not be supported.

def is_open(
	edges,
	key
):

	return (
		key in edges
		and
		edges[key]
	)


def open_count(
	edges
):

	count = 0


	for key in edges:

		if edges[key]:

			count = count + 1


	return count // 2


def scan_cell(
	x,
	y,
	edges,
	size
):
	# Record every open direction from (x, y), both ways.
	# Returns how many edges were new.

	new = 0


	for d in DIRS:

		if can_move(d):

			if not is_open(edges, (x, y, d)):

				new = new + 1

				edges[(x, y, d)] = True

				n = step(x, y, d, size)

				edges[(n[0], n[1], opposite(d))] = True


	return new


def explore_all(
	size
):
	# Full DFS over every reachable cell. Returns
	# (edges, cells visited, moves, seconds).

	t0 = get_time()

	edges = {}

	visited = set()

	scanned = set()

	stack = []


	x = get_pos_x()

	y = get_pos_y()

	visited.add(
		(x, y)
	)

	moves = 0


	while True:

		if (x, y) not in scanned:

			scanned.add(
				(x, y)
			)

			scan_cell(
				x,
				y,
				edges,
				size
			)


		moved = False


		for d in DIRS:

			if is_open(edges, (x, y, d)):

				n = step(x, y, d, size)


				if n not in visited:

					if move(d):

						moves = moves + 1

						stack.append(d)

						x = n[0]

						y = n[1]

						visited.add(n)

						moved = True

						break


		if moved:

			continue


		if len(stack) == 0:

			break


		back = opposite(
			stack.pop()
		)

		move(back)

		moves = moves + 1

		n = step(x, y, back, size)

		x = n[0]

		y = n[1]


	return (
		edges,
		len(visited),
		moves,
		get_time() - t0
	)


def bfs_path(
	sx,
	sy,
	tx,
	ty,
	edges,
	size
):

	start = (sx, sy)

	goal = (tx, ty)


	if start == goal:

		return []


	prev = {}

	prev[start] = None

	queue = [start]

	head = 0


	while head < len(queue):

		c = queue[head]

		head = head + 1


		if c == goal:

			break


		for d in DIRS:

			if is_open(edges, (c[0], c[1], d)):

				n = step(c[0], c[1], d, size)


				if n not in prev:

					prev[n] = (c[0], c[1], d)

					queue.append(n)


	if goal not in prev:

		return None


	path = []

	c = goal


	while prev[c] != None:

		p = prev[c]

		path.append(p[2])

		c = (p[0], p[1])


	result = []

	i = len(path) - 1


	while i >= 0:

		result.append(path[i])

		i = i - 1


	return result


STATS = {
	"moves": 0,
	"blocked": 0,
	"new_edges": 0,
	"replans": 0
}


def walk_to(
	tx,
	ty,
	edges,
	size,
	discover
):
	# Walk a BFS path on the known map. A blocked move removes
	# that edge and replans. With discover=True, every cell on
	# the way is scanned for newly opened edges.

	for attempt in range(50):

		x = get_pos_x()

		y = get_pos_y()


		if x == tx and y == ty:

			return True


		path = bfs_path(
			x,
			y,
			tx,
			ty,
			edges,
			size
		)


		if path == None:

			return False


		blocked = False


		for d in path:

			if discover:

				STATS["new_edges"] = (
					STATS["new_edges"]
					+ scan_cell(
						get_pos_x(),
						get_pos_y(),
						edges,
						size
					)
				)


			if move(d):

				STATS["moves"] = STATS["moves"] + 1

			else:

				STATS["blocked"] = STATS["blocked"] + 1

				cx = get_pos_x()

				cy = get_pos_y()

				n = step(cx, cy, d, size)

				edges[(cx, cy, d)] = False

				edges[(n[0], n[1], opposite(d))] = False


				STATS["replans"] = STATS["replans"] + 1

				blocked = True

				break


		if not blocked:

			return (
				get_pos_x() == tx
				and
				get_pos_y() == ty
			)


	return False


def edge_diff(
	old,
	new
):

	opened = 0

	closed = 0


	for e in new:

		if new[e] and not is_open(old, e):

			opened = opened + 1


	for e in old:

		if old[e] and not is_open(new, e):

			closed = closed + 1


	return (
		opened // 2,
		closed // 2
	)


# ============================================================
# A. FRESH MAZE
# ============================================================

size = get_world_size()

area = size * size

cost = substance_cost()


quick_print(
	"[PROBE] world:",
	size,
	"| Mazes level:",
	num_unlocked(Unlocks.Mazes),
	"| substance per maze:",
	cost,
	"| drones:",
	max_drones()
)


created = create_maze(
	cost
)


quick_print(
	"[PROBE] A create ok:",
	created[0],
	"| seconds:",
	created[1],
	"| entity under drone:",
	get_entity_type(),
	"| treasure at:",
	measure()
)


scan = explore_all(
	size
)

edges = scan[0]


quick_print(
	"[PROBE] A explore | cells:",
	scan[1],
	"/",
	area,
	"| open edges:",
	open_count(edges),
	"| perfect (edges = cells-1):",
	open_count(edges) == scan[1] - 1,
	"| moves:",
	scan[2],
	"| seconds:",
	scan[3],
	"| sec/move:",
	scan[3] / scan[2]
)


# ============================================================
# B. REUSE: GOLD + WALL CHANGES
# ============================================================

for reuse_round in range(2):

	target = measure()


	walk_to(
		target[0],
		target[1],
		edges,
		size,
		False
	)


	g0 = num_items(Items.Gold)

	ok = use_item(
		Items.Weird_Substance,
		cost
	)

	g1 = num_items(Items.Gold)


	quick_print(
		"[PROBE] B reuse",
		reuse_round + 1,
		"| use_item ok:",
		ok,
		"| gold delta:",
		g1 - g0,
		"| entity under drone:",
		get_entity_type(),
		"| new treasure:",
		measure()
	)


	rescan = explore_all(
		size
	)

	diff = edge_diff(
		edges,
		rescan[0]
	)


	quick_print(
		"[PROBE] B rescan after reuse",
		reuse_round + 1,
		"| open edges:",
		open_count(rescan[0]),
		"| walls removed:",
		diff[0],
		"| walls added:",
		diff[1],
		"| moves:",
		rescan[2]
	)


	edges = rescan[0]


# ============================================================
# C. REUSE CAP WITH REMEMBERED MAP + BFS
# ============================================================

STATS["moves"] = 0

STATS["blocked"] = 0

STATS["new_edges"] = 0

STATS["replans"] = 0


deltas = {}

reuses = 2

t_start = get_time()

treasures = 0


while reuses < REUSE_LIMIT_TEST:

	target = measure()


	if target == None:

		quick_print(
			"[PROBE] C measure() returned None at reuse",
			reuses
		)

		break


	if not walk_to(
		target[0],
		target[1],
		edges,
		size,
		True
	):

		quick_print(
			"[PROBE] C could not reach treasure at reuse",
			reuses
		)

		break


	g0 = num_items(Items.Gold)


	if not use_item(
		Items.Weird_Substance,
		cost
	):

		quick_print(
			"[PROBE] C use_item FAILED after",
			reuses,
			"reuses | entity under drone:",
			get_entity_type()
		)

		break


	delta = num_items(Items.Gold) - g0

	treasures = treasures + 1

	reuses = reuses + 1


	if delta in deltas:

		deltas[delta] = deltas[delta] + 1

	else:

		deltas[delta] = 1


	if reuses in [3, 10, 50, 100, 200, 299, 300, 301]:

		quick_print(
			"[PROBE] C reuse",
			reuses,
			"| gold delta:",
			delta,
			"| open edges known:",
			open_count(edges),
			"| avg moves/treasure:",
			STATS["moves"] / treasures,
			"| avg sec/treasure:",
			(get_time() - t_start) / treasures
		)


quick_print(
	"[PROBE] C totals | reuses:",
	reuses,
	"| treasures walked:",
	treasures,
	"| gold deltas seen:",
	deltas,
	"| moves:",
	STATS["moves"],
	"| blocked moves:",
	STATS["blocked"],
	"| new edges discovered:",
	STATS["new_edges"],
	"| seconds:",
	get_time() - t_start
)


target = measure()


if target != None:

	walk_to(
		target[0],
		target[1],
		edges,
		size,
		False
	)


g0 = num_items(Items.Gold)

harvested = harvest()


quick_print(
	"[PROBE] C final harvest | ok:",
	harvested,
	"| gold delta:",
	num_items(Items.Gold) - g0,
	"| entity under drone after:",
	get_entity_type(),
	"| measure() after:",
	measure()
)


# ============================================================
# D. SPAWNED DRONE INSIDE THE MAZE
# ============================================================

def child_task(
	child_edges,
	child_size,
	child_cost
):

	target = measure()

	start = (get_pos_x(), get_pos_y())

	arrived = walk_to(
		target[0],
		target[1],
		child_edges,
		child_size,
		False
	)

	g0 = num_items(Items.Gold)

	reused = use_item(
		Items.Weird_Substance,
		child_cost
	)

	return (
		start,
		target,
		arrived,
		reused,
		num_items(Items.Gold) - g0,
		(get_pos_x(), get_pos_y())
	)


created = create_maze(
	cost
)

scan = explore_all(
	size
)

edges = scan[0]


handle = spawn_drone(
	child_task,
	edges,
	size,
	cost
)


if handle == None:

	quick_print(
		"[PROBE] D spawn_drone returned None inside maze"
	)

else:

	result = wait_for(
		handle
	)

	quick_print(
		"[PROBE] D child | start:",
		result[0],
		"| target:",
		result[1],
		"| arrived:",
		result[2],
		"| reuse ok:",
		result[3],
		"| gold delta:",
		result[4],
		"| end:",
		result[5]
	)


target = measure()


if target != None:

	walk_to(
		target[0],
		target[1],
		edges,
		size,
		False
	)

	g0 = num_items(Items.Gold)

	harvest()

	quick_print(
		"[PROBE] D coordinator harvest after child | gold delta:",
		num_items(Items.Gold) - g0
	)


# ============================================================
# E. HALF-COST MAZE
# ============================================================

created = create_maze(
	cost // 2
)


quick_print(
	"[PROBE] E half-cost create ok:",
	created[0],
	"| treasure at:",
	measure(),
	"| entity under drone:",
	get_entity_type()
)


if created[0]:

	scan = explore_all(
		size
	)

	quick_print(
		"[PROBE] E explore | reachable cells:",
		scan[1],
		"| open edges:",
		open_count(scan[0])
	)


	target = measure()


	if target != None:

		walk_to(
			target[0],
			target[1],
			scan[0],
			size,
			False
		)

		g0 = num_items(Items.Gold)

		harvest()

		quick_print(
			"[PROBE] E harvest | gold delta:",
			num_items(Items.Gold) - g0
		)
