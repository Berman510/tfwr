import farm_config
import farm_common
import farm_telemetry


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

def farm():

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
	) < substance_cost():

		return False


	return farm()