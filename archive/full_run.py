import farm_config
import farm_common
import farm_megafarm
import farm_rotation
import farm_maze
import farm_dinosaurs
import farm_pumpkin


# ============================================================
# FULL AUTOMATION (FASTEST RESET) RUNNER
# ============================================================
#
# Leaderboards.Fastest_Reset: "Completely automate the game
# from a single farm plot to unlocking the leaderboards again."
#
# What a reset starts with (archive/lb_reset_probe.py):
#
#   - 1x1 world, 1 / 1 drone, no items
#   - every LANGUAGE unlock (loops, functions, import, lists,
#     dicts, senses, operators, debug, timing, costs, ...)
#   - every FARM unlock at 0 (Grass 1)
#   - goal: Unlocks.Leaderboard = 2M Bone + 1M Gold
#
# Level-1 costs: Speed 20 Hay, Expand 30 Hay, Plant 50 Hay,
# Carrots 50 Wood, Watering 50 Wood, Trees 50 Wood + 70 Carrot,
# Fertilizer 500 Wood, Pumpkins 500 Wood + 200 Carrot,
# Sunflowers 500 Carrot, Polyculture 3000 Pumpkin, Cactus 5000
# Pumpkin, Mazes 1000 Weird Substance, Megafarm 2000 Gold,
# Dinosaurs 2000 Cactus.
#
#
# Loop:
#
#     1. Buy every wanted, affordable upgrade in PRIORITY order
#        (restarting from the top after each purchase).
#
#     2. Pick the first wanted upgrade whose missing items can
#        all be produced with what's unlocked now.
#
#     3. Farm its first missing item, or the input that item
#        needs first (e.g. Hay / Wood for Carrots), for up to
#        STEP_SECONDS.
#
#     4. Stop once Leaderboard is unlocked (or after
#        MAX_SECONDS / STALL_SECONDS without a purchase).
#
# Gold and Bone use production farm_maze / farm_dinosaurs.
# Cactus uses production farm_rotation.farm_cactus. Everything
# else uses the simple crop sweep below, which works from a 1x1
# field and one drone upward.
#
# Every [FR] line goes to output.txt, so the same file shows
# the timeline in simulation (sim_full.py) and in the real run.
# ============================================================


MAX_SECONDS = 250000

# Stop when this many farming steps in a row gain nothing of
# the item they farm. (A time limit without purchases stopped
# sim round 4 while slow Pumpkin farming was still progressing.)
STALL_STEPS = 20

STEP_SECONDS = 60

INPUT_BATCH = 4

# farm_split clears the field, calibrates and builds mazes on
# every call, so Gold steps run longer than crop steps.
GOLD_STEP_SECONDS = 300


# Megafarm and Mazes come first: they become farming targets as
# soon as they can be produced (Weird Substance needs Fertilizer,
# Gold needs Mazes), and extra drones speed up everything. Sim
# round 5 instead ground Pumpkins for Expand (64,000, then
# 512,000) with one drone and never reached Mazes.
#
# Expand / Plant / Carrots / Trees come before Speed: a bigger
# field and better crops pay back faster than Speed levels
# (sim round 2 spent ~1,800 sec farming 500 Carrots for Speed 4
# while Expand cost 100 Wood + 50 Carrot).

#
# Mazes level 1 is bought before Expand (Gold for Megafarm);
# further Mazes levels come after Expand (see priority_order).
# Megafarm is only wanted while drones < world size (sim round
# 6 bought 8 drones for a 6x6 field, then ground 128,000 Gold
# for 16).

#
# Gold per treasure depends on the Mazes level, so Mazes (and
# Cactus, which pays for Mazes 2+) come before Megafarm and
# Expand: sim round 9 took ~52,000 sec for 128,000 Gold at Mazes
# 1, even with 8 drones on 16x16.

#
# Entries are (upgrade, highest level this entry buys); None
# means only CAPS applies. Mazes is staged: up to 3 early, 4-6
# only after Expand / Dinosaurs. Cactus pays per sorted field,
# so on a small field high Mazes levels are very slow (sim round
# 10: Mazes 4 -> 5 took ~42,000 sec on 6x6).

#
# Leaderboard is last: as a target it only makes sense once the
# farm is fully grown (sim round 12 made it the target on 6x6
# with 4 drones as soon as Dinosaurs was bought). buy_pass still
# buys it the moment it's affordable.

PRIORITY = [
	(Unlocks.Mazes, 3),
	(Unlocks.Cactus, None),
	(Unlocks.Megafarm, None),
	# Before Expand: Expand always has a next level, so anything
	# after it waits forever (sim round 11 never bought Dinosaurs).
	(Unlocks.Dinosaurs, None),
	(Unlocks.Expand, None),
	(Unlocks.Mazes, None),
	(Unlocks.Plant, None),
	(Unlocks.Carrots, None),
	(Unlocks.Trees, None),
	(Unlocks.Watering, None),
	(Unlocks.Fertilizer, None),
	(Unlocks.Speed, None),
	(Unlocks.Pumpkins, None),
	(Unlocks.Grass, None),
	(Unlocks.Leaderboard, None)
]


# Highest level to buy. Upgrades not listed have no cap.

CAPS = {
	# Uncapped, these become endless farming targets as their
	# cost climbs (sim round 8 farmed Wood for Watering levels
	# for ~51,500 sec before it unlocked Pumpkins).
	Unlocks.Watering: 5,
	Unlocks.Speed: 5,

	Unlocks.Plant: 1,
	Unlocks.Fertilizer: 1,
	Unlocks.Pumpkins: 1,
	Unlocks.Cactus: 1,
	Unlocks.Mazes: 6,
	Unlocks.Dinosaurs: 1,
	# Level 3 of these cost thousands (Carrots 3: 6,250 Wood, ~1,850
	# sec of farming in sim round 6).
	Unlocks.Grass: 2,
	Unlocks.Trees: 2,
	Unlocks.Carrots: 2
}


# A purchase only has to leave the current target's items alone
# when it spends at least this much of one. Smaller purchases
# (Watering, Speed, ...) pay back quickly; sim round 6 held them
# back for ~2,000 sec.
PROTECT_MIN = 1000


STATE = {
	"start": 0,
	"last_buy": 0,
	"last_farm": None,
	"field": None,
	"idle_steps": 0
}


# ============================================================
# LOGGING
# ============================================================

def log_status(
	label
):

	quick_print(
		"[FR] t=",
		get_time(),
		label,
		"| world",
		get_world_size(),
		"| drones",
		max_drones()
	)


def log_inventory():

	for item in Items:

		if num_items(item) > 0:

			quick_print(
				"[FR]   item",
				item,
				num_items(item)
			)


	for entry in PRIORITY:

		quick_print(
			"[FR]   unlock",
			entry[0],
			num_unlocked(entry[0]),
			"next cost",
			get_cost(entry[0])
		)


# ============================================================
# UPGRADES
# ============================================================

def can_produce(
	item
):

	if item == Items.Hay:

		return True


	if item == Items.Wood:

		return num_unlocked(Unlocks.Plant) > 0


	if item == Items.Carrot:

		return num_unlocked(Unlocks.Carrots) > 0


	if item == Items.Pumpkin:

		return num_unlocked(Unlocks.Pumpkins) > 0


	if item == Items.Cactus:

		return num_unlocked(Unlocks.Cactus) > 0


	if item == Items.Weird_Substance:

		return (
			num_unlocked(Unlocks.Fertilizer) > 0
			and
			num_unlocked(Unlocks.Plant) > 0
		)


	if item == Items.Gold:

		return num_unlocked(Unlocks.Mazes) > 0


	if item == Items.Bone:

		return (
			num_unlocked(Unlocks.Dinosaurs) > 0
			and
			num_unlocked(Unlocks.Cactus) > 0
			and
			get_world_size() % 2 == 0
		)


	return False


def saving_for_leaderboard():
	# Keep Gold and Bone for the Leaderboard only once the field
	# is fully expanded. Earlier, Megafarm (Gold) still pays back
	# (sim round 12 blocked it on 6x6 as soon as Dinosaurs was
	# bought).

	expand_cost = get_cost(Unlocks.Expand)


	if expand_cost != None and len(expand_cost) > 0:

		return False


	return (
		can_produce(Items.Gold)
		and
		can_produce(Items.Bone)
	)


def priority_order():

	order = []


	for upgrade in PRIORITY:

		order.append(upgrade)


	return order


def wanted(
	entry
):

	upgrade = entry[0]

	cost = get_cost(upgrade)


	if cost == None or len(cost) == 0:

		return False


	if entry[1] != None and num_unlocked(upgrade) >= entry[1]:

		return False


	# Each Megafarm level doubles the drones. Only buy one whose
	# drones still fit the field width (sim round 7 had 4 drones
	# on 6x6 and would have ground 32,000 Gold for 8).

	if upgrade == Unlocks.Megafarm and max_drones() * 2 > get_world_size():

		return False


	if upgrade in CAPS and num_unlocked(upgrade) >= CAPS[upgrade]:

		return False


	if upgrade != Unlocks.Leaderboard and saving_for_leaderboard():

		if Items.Gold in cost or Items.Bone in cost:

			return False


	return True


def affordable(
	cost
):

	for item in cost:

		if num_items(item) < cost[item]:

			return False


	return True


def competes(
	cost,
	target
):
	# True when buying `cost` would leave less of some item than
	# `target` still needs (sim round 5: Cactus took 5,000 of the
	# Pumpkins being saved for Expand).

	if target == None:

		return False


	target_cost = get_cost(target)


	for item in cost:

		if item in target_cost and cost[item] >= PROTECT_MIN:

			if num_items(item) - cost[item] < target_cost[item]:

				return True


	return False


def buy_pass():

	bought = 0

	progress = True


	while progress:

		progress = False

		target = choose_target()


		for entry in priority_order():

			if not wanted(entry):

				continue


			upgrade = entry[0]

			cost = get_cost(upgrade)


			if not affordable(cost):

				continue


			if upgrade != target and competes(cost, target):

				continue


			if unlock(upgrade):

				bought = bought + 1

				progress = True


				log_status(
					"BUY " + str(upgrade) + " -> " + str(num_unlocked(upgrade))
				)


				break


	return bought


def choose_target():

	for entry in priority_order():

		if not wanted(entry):

			continue


		upgrade = entry[0]

		cost = get_cost(upgrade)

		producible = True


		for item in cost:

			if num_items(item) < cost[item] and not can_produce(item):

				producible = False


		if producible:

			return upgrade


	return None


# ============================================================
# WHAT FARMING AN ITEM NEEDS FIRST
# ============================================================

def crop_entity(
	item
):

	if item == Items.Carrot:

		return Entities.Carrot


	if item == Items.Pumpkin:

		return Entities.Pumpkin


	if item == Items.Wood or item == Items.Weird_Substance:

		return Entities.Bush


	return None


def weird_from_cactus(
	item
):
	# Weird Substance comes from harvesting infected (fertilized)
	# plants. farm_cactus fertilizes every cactus and harvests the
	# whole sorted field at once, which pays far more than the
	# Bush / Tree sweep (sim round 10 banked 167,203 while farming
	# Cactus; round 11's sweep gained ~2-17 per step and starved
	# the mazes for ~49,000 sec).

	return (
		item == Items.Weird_Substance
		and
		num_unlocked(Unlocks.Cactus) > 0
	)


def input_needs(
	item
):
	# Items (and amounts) one farming step for `item` should have
	# in stock before it starts.

	size = get_world_size()

	area = size * size

	needs = {}


	entity = crop_entity(item)


	if item == Items.Cactus or weird_from_cactus(item):

		entity = Entities.Cactus


	if entity != None:

		cost = get_cost(entity)


		if cost != None:

			# Two fields' worth: farm_pumpkin (like farm_carrot)
			# won't start with less (sim round 8 stalled with 170
			# Carrots on 12x12, never farming more).

			for need_item in cost:

				needs[need_item] = cost[need_item] * area * 2


	if item == Items.Gold:

		needs[Items.Weird_Substance] = max(
			farm_maze.maze_cost(size),
			farm_maze.substance_reserve()
		)


	if item == Items.Bone:

		apple = get_cost(Entities.Apple)


		if apple != None:

			for need_item in apple:

				needs[need_item] = apple[need_item] * area


	return needs


def resolve(
	item,
	amount,
	depth
):

	if depth > 6:

		return (item, amount)


	needs = input_needs(item)


	for need_item in needs:

		if num_items(need_item) < needs[need_item] and can_produce(need_item):

			# Farm INPUT_BATCH sweeps' worth, so the next step
			# doesn't run straight back out.

			return resolve(
				need_item,
				needs[need_item] * INPUT_BATCH,
				depth + 1
			)


	return (item, amount)


# ============================================================
# SIMPLE CROP SWEEP (1 drone / tiny fields upward)
# ============================================================

def tend(
	item,
	x,
	y
):

	if item == Items.Hay:

		if can_harvest():

			harvest()


		return


	if can_harvest():

		harvest()


	current = get_entity_type()


	# Harvested Grass shows as Grass again straight away, and a
	# dead pumpkin disappears when something is planted: plant
	# over both.

	if current == Entities.Grass or current == Entities.Dead_Pumpkin:

		current = None


	if current != None:

		# Still growing.

		return


	entity = crop_entity(item)


	if entity == None:

		return


	if (
		entity == Entities.Bush
		and
		num_unlocked(Unlocks.Trees) > 0
		and
		(x + y) % 2 == 0
	):

		entity = Entities.Tree


	if entity == Entities.Carrot or entity == Entities.Pumpkin:

		farm_common.make_soil()


	if not farm_common.plant_if_affordable(entity):

		return


	if item == Items.Weird_Substance:

		if num_items(Items.Fertilizer) > 0:

			use_item(Items.Fertilizer)

	elif num_unlocked(Unlocks.Watering) > 0:

		farm_common.water_if_needed()


def crop_worker(
	rows,
	arg
):

	item = arg[0]

	goal = arg[1]

	deadline = arg[2]


	size = get_world_size()


	while get_time() < deadline:

		for row in rows:

			farm_common.go_to(0, row)


			for x in range(size):

				if num_items(item) >= goal or get_time() >= deadline:

					return


				tend(item, x, row)


				if x < size - 1:

					move(East)


# ============================================================
# WHOLE-FIELD MEGA PUMPKIN (1 drone)
# ============================================================
#
# Harvesting pumpkins one by one never lets them merge (sim
# round 4: ~3,500 Pumpkins in ~1,800 sec on 8x8). Plant the
# whole field, replace empty / dead / other tiles until every
# tile is a grown pumpkin, then harvest the merged pumpkin once.

def pumpkin_step(
	goal,
	deadline
):

	size = get_world_size()


	while get_time() < deadline and num_items(Items.Pumpkin) < goal:

		complete = True


		for y in range(size):

			farm_common.go_to(0, y)


			for x in range(size):

				current = get_entity_type()


				if current != Entities.Pumpkin:

					complete = False


					if (
						current != None
						and
						current != Entities.Grass
						and
						current != Entities.Dead_Pumpkin
					):

						harvest()


					farm_common.make_soil()


					if not farm_common.plant_if_affordable(Entities.Pumpkin):

						return


					farm_common.water_if_needed()

				elif not can_harvest():

					complete = False

					farm_common.water_if_needed()


				if x < size - 1:

					move(East)


			if get_time() >= deadline:

				return


		if complete:

			harvest()


# ============================================================
# ONE FARMING STEP
# ============================================================

def farm_step(
	item,
	goal
):

	if item == Items.Gold:

		STATE["field"] = None

		farm_maze.farm_split(
			goal,
			GOLD_STEP_SECONDS
		)

		return


	if item == Items.Bone:

		STATE["field"] = None

		farm_dinosaurs.farm()

		return


	if item == Items.Cactus or weird_from_cactus(item):

		STATE["field"] = None

		farm_rotation.farm_cactus()

		return


	# Keep a planted field between steps when switching between
	# planted crops: the sweep harvests whatever is grown and
	# replants only empty tiles. Clear when the world size
	# changes, and when switching to or from Hay: Hay needs a
	# field of Grass (sim round 3 stalled with 0 Hay on a field
	# full of Bushes / Carrots).

	field = (
		get_world_size(),
		item == Items.Hay
	)


	if STATE["field"] != field:

		farm_common.clear_field()

		STATE["field"] = field


	if item == Items.Pumpkin:

		if max_drones() >= 2 and get_world_size() >= 6:

			# Production gapped mega-pumpkin blocks, one drone per
			# block (farm_pumpkin clears and replants on its own).

			STATE["field"] = None

			farm_config.SETTINGS["pumpkin_gain_target"] = max(1, goal - num_items(Items.Pumpkin))

			farm_config.SETTINGS["continuous_phase_max_seconds"] = STEP_SECONDS

			farm_pumpkin.farm()

			return


		pumpkin_step(
			goal,
			get_time() + STEP_SECONDS
		)

		return


	farm_megafarm.run_stripes_with_arg(
		crop_worker,
		get_world_size(),
		(
			item,
			goal,
			get_time() + STEP_SECONDS
		)
	)


# ============================================================
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< FULL_RUN_BEGIN >>>"
)


STATE["start"] = get_time()

STATE["last_buy"] = get_time()


log_status(
	"START"
)


while num_unlocked(Unlocks.Leaderboard) == 0:

	if buy_pass() > 0:

		STATE["last_buy"] = get_time()


	if num_unlocked(Unlocks.Leaderboard) > 0:

		break


	if get_time() - STATE["start"] > MAX_SECONDS:

		log_status("STOP max seconds")

		log_inventory()

		break


	if STATE["idle_steps"] >= STALL_STEPS:

		log_status("STOP stalled")

		log_inventory()

		break


	target = choose_target()


	if target == None:

		log_status("STOP no producible target")

		log_inventory()

		break


	cost = get_cost(target)

	short = None


	for item in cost:

		if short == None and num_items(item) < cost[item]:

			short = item


	if short == None:

		log_status("STOP could not buy affordable " + str(target))

		log_inventory()

		break


	plan = resolve(
		short,
		cost[short],
		0
	)


	if STATE["last_farm"] != (target, plan[0]):

		STATE["last_farm"] = (target, plan[0])


		quick_print(
			"[FR] t=",
			get_time(),
			"FARM",
			plan[0],
			"to",
			plan[1],
			"(have",
			num_items(plan[0]),
			") for",
			target
		)


	before = num_items(plan[0])


	farm_step(
		plan[0],
		plan[1]
	)


	if num_items(plan[0]) > before:

		STATE["idle_steps"] = 0

	else:

		STATE["idle_steps"] = STATE["idle_steps"] + 1


if num_unlocked(Unlocks.Leaderboard) > 0:

	log_status(
		"DONE Leaderboard unlocked in " + str(get_time() - STATE["start"]) + " sec"
	)


quick_print(
	"<<< FULL_RUN_END >>>"
)
