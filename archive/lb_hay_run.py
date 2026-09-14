import farm_config
import farm_hay


# ============================================================
# LEADERBOARD RUN BODY: HAY
# ============================================================
#
# Started by lb_start.py through
# leaderboard_run(Leaderboards.Hay, "lb_probe", ...).
#
# Board: "Farm 2_000_000_000 hay with multiple drones."
#
# The first version of this file (archive/lb_probe.py) showed
# what a leaderboard run starts with, on the Sunflowers board:
#
#   - time 0, 32x32, 1 / 32 drones
#   - every upgrade at its max level
#   - 1B Carrots, every other item 0 (no Water / Fertilizer)
#
# Hay needs nothing to buy: farm_hay plants free Bush / Tree
# companions and harvests Grass (~200M per ~33 sec on 32x32 /
# 32 drones), so this just runs it with a 2B target.
# ============================================================


TARGET = 2000000000


quick_print(
	""
)

quick_print(
	"<<< LB_RUN_BEGIN >>>"
)

quick_print(
	"[LB] time:",
	get_time(),
	"| world:",
	get_world_size(),
	"| drones:",
	num_drones(),
	"/",
	max_drones(),
	"| hay:",
	num_items(Items.Hay),
	"| wood:",
	num_items(Items.Wood),
	"| carrot:",
	num_items(Items.Carrot),
	"| water:",
	num_items(Items.Water)
)


farm_config.SETTINGS["hay_gain_target"] = TARGET

farm_config.SETTINGS["continuous_phase_max_seconds"] = 1800


phases = 0


while num_items(Items.Hay) < TARGET:

	farm_hay.farm()

	phases = phases + 1


	quick_print(
		"[LB] phase",
		phases,
		"| time:",
		get_time(),
		"| hay:",
		num_items(Items.Hay)
	)


quick_print(
	"[LB] done | time:",
	get_time(),
	"| hay:",
	num_items(Items.Hay)
)

quick_print(
	"<<< LB_RUN_END >>>"
)
