import farm_config
import farm_common
import farm_telemetry


# ============================================================
# MOVE WITH TELEMETRY
# ============================================================

def dino_move(
	direction
):

	farm_telemetry.add_counter(
		"dinosaur move attempts",
		1
	)


	if move(
		direction
	):

		farm_telemetry.add_counter(
			"dinosaur successful moves",
			1
		)

		return True


	farm_telemetry.add_counter(
		"dinosaur blocked moves",
		1
	)


	return False


# ============================================================
# ONE HAMILTONIAN CYCLE
# ============================================================

def cycle_once(
	width,
	height
):

	for i in range(
		height - 1
	):

		if not dino_move(
			North
		):

			return False


	for x in range(
		1,
		width
	):

		if not dino_move(
			East
		):

			return False


		if x % 2 == 1:

			for i in range(
				height - 2
			):

				if not dino_move(
					South
				):

					return False


		else:

			for i in range(
				height - 2
			):

				if not dino_move(
					North
				):

					return False


	if not dino_move(
		South
	):

		return False


	for i in range(
		width - 1
	):

		if not dino_move(
			West
		):

			return False


	return True


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

		farm_telemetry.phase_end(
			"dinosaur run",
			phase
		)

		return False


	width = size
	height = size

	usable_tiles = (
		width
		* height
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


	if not farm_common.wear_hat(
		Hats.Dinosaur_Hat
	):

		farm_telemetry.phase_end(
			"dinosaur run",
			phase
		)

		return False


	circuits = 0


	for circuit in range(
		usable_tiles
	):

		circuits = (
			circuits + 1
		)


		if not cycle_once(
			width,
			height
		):

			break


	farm_telemetry.add_counter(
		"dinosaur cycle attempts",
		circuits
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