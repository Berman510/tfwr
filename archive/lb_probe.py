# ============================================================
# LEADERBOARD PROBE
# ============================================================
#
# Started by lb_start.py through leaderboard_run(). Prints what
# a leaderboard run starts with (world, drones, items, unlocks)
# and then stops, so the real leaderboard script can be planned.
# ============================================================


quick_print(
	""
)

quick_print(
	"<<< LB_PROBE_BEGIN >>>"
)

quick_print(
	"[LB] time:",
	get_time(),
	"| world:",
	get_world_size(),
	"| drones:",
	num_drones(),
	"/",
	max_drones()
)


for item in Items:

	quick_print(
		"[LB] item",
		item,
		num_items(item)
	)


for unlock_type in Unlocks:

	quick_print(
		"[LB] unlock",
		unlock_type,
		num_unlocked(unlock_type)
	)


quick_print(
	"<<< LB_PROBE_END >>>"
)
