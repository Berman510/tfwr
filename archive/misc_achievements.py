import farm_common
import farm_megafarm


# ============================================================
# MISC ACHIEVEMENTS RUNNER
# ============================================================
#
#   Healer          "Cure an infected plant."
#   Fashion Show    "Equip 5 different hats on 5 drones."
#   Wrong Order     "Sort a full field of cacti the wrong way
#                    around."
#   Stack Overflow  "Cause a stack overflow."
#
# Stack Overflow runs last, because it crashes the script.
# Each step can be switched off below.
#
# Stop main first so every drone is free.
# ============================================================


DO_HEALER = True

DO_FASHION = True

DO_WRONG_ORDER = True

DO_STACK_OVERFLOW = True


FASHION_SECONDS = 5


# ============================================================
# HEALER
# ============================================================
#
# Weird Substance "toggles the infection status" of a plant.
# Fertilizer is believed to infect plants, so:
#
#   A. Tree + Fertilizer (infect?), then Weird Substance (cure).
#   B. Tree + Weird Substance (infect), then again (cure).
#
# Trees, not Bushes: Weird Substance on a Bush grows a maze.

def healer():

	farm_common.clear_field()


	farm_common.go_to(0, 0)

	plant(Entities.Tree)


	quick_print(
		"[HEALER] A fertilizer:",
		use_item(Items.Fertilizer),
		"| weird substance (cure):",
		use_item(Items.Weird_Substance)
	)


	farm_common.go_to(2, 0)

	plant(Entities.Tree)


	quick_print(
		"[HEALER] B weird substance (infect):",
		use_item(Items.Weird_Substance),
		"| weird substance (cure):",
		use_item(Items.Weird_Substance)
	)


# ============================================================
# FASHION SHOW
# ============================================================

def wear_hat_until(
	hat,
	x,
	until
):

	farm_common.go_to(x, 0)

	change_hat(hat)


	while get_time() < until:

		do_a_flip()


	return 1


def fashion_show():

	hats = []


	for hat in Hats:

		# The Dinosaur Hat starts the dinosaur game.

		if hat == Hats.Dinosaur_Hat:

			continue


		if len(hats) < 5 and num_unlocked(hat) > 0:

			hats.append(hat)


	quick_print(
		"[FASHION] hats:",
		hats,
		"| max drones:",
		max_drones()
	)


	if len(hats) < 5 or max_drones() < 5:

		quick_print(
			"[FASHION] need 5 unlocked hats and 5 drones - skipped"
		)

		return


	until = get_time() + FASHION_SECONDS

	handles = []


	for k in range(1, 5):

		handle = spawn_drone(
			wear_hat_until,
			hats[k],
			k * 2,
			until
		)


		if handle != None:

			handles.append(handle)


	wear_hat_until(
		hats[0],
		0,
		until
	)


	for handle in handles:

		wait_for(handle)


	quick_print(
		"[FASHION] drones with hats:",
		len(handles) + 1
	)


	change_hat(Hats.Straw_Hat)


# ============================================================
# WRONG ORDER
# ============================================================
#
# Normal cactus sorting is ascending West -> East and
# South -> North. This sorts the whole field DESCENDING in both
# directions, then harvests.

def plant_cactus_row(
	row
):

	size = get_world_size()


	farm_common.go_to(0, row)


	for x in range(size):

		if get_entity_type() != None:

			harvest()


		farm_common.make_soil()

		plant(Entities.Cactus)


		if x < size - 1:

			move(East)


def reverse_row(
	y
):
	# Bubble sort, largest first (West).

	size = get_world_size()

	right = size - 1

	swapped = True


	while swapped and right > 0:

		swapped = False

		farm_common.go_to(0, y)


		for i in range(right):

			if measure() < measure(East):

				swap(East)

				swapped = True


			move(East)


		right = right - 1


def reverse_column(
	x
):
	# Bubble sort, largest first (South).

	size = get_world_size()

	top = size - 1

	swapped = True


	while swapped and top > 0:

		swapped = False

		farm_common.go_to(x, 0)


		for i in range(top):

			if measure() < measure(North):

				swap(North)

				swapped = True


			move(North)


		top = top - 1


def wrong_order():

	size = get_world_size()

	start = get_time()


	farm_common.clear_field()


	farm_megafarm.run_rows(
		plant_cactus_row,
		size
	)


	farm_megafarm.run_rows(
		reverse_row,
		size
	)


	farm_megafarm.run_rows(
		reverse_column,
		size
	)


	farm_common.go_to(0, 0)


	while not can_harvest():

		pass


	cactus = num_items(Items.Cactus)

	harvest()


	quick_print(
		"[WRONG ORDER] field",
		size,
		"x",
		size,
		"sorted descending in",
		get_time() - start,
		"sec | cactus from harvest:",
		num_items(Items.Cactus) - cactus
	)


# ============================================================
# STACK OVERFLOW
# ============================================================

def dive(
	depth
):

	return dive(depth + 1) + 1


# ============================================================
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< MISC_ACHIEVEMENTS_BEGIN >>>"
)


if DO_HEALER:

	healer()


if DO_FASHION:

	fashion_show()


if DO_WRONG_ORDER:

	wrong_order()


quick_print(
	"<<< MISC_ACHIEVEMENTS_END >>>"
)


if DO_STACK_OVERFLOW:

	quick_print(
		"[STACK] diving - the script should now crash"
	)

	dive(0)
