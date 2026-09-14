# FASTEST RESET PROBE
#
# Started by lb_start.py through
# leaderboard_run(Leaderboards.Fastest_Reset, "lb_probe", 1).
#
# A real reset may start with almost nothing unlocked, including
# language features. Each numbered step uses one more feature,
# so the last [FR] line (and the error after it) shows what is
# locked at the start. No loops, functions or imports until the
# end.

quick_print("[FR] 1 quick_print ok")

harvest()
quick_print("[FR] 2 harvest ok")

probe_value = 1
quick_print("[FR] 3 variables ok")

quick_print("[FR] 4 world", get_world_size(), "time", get_time())

quick_print("[FR] 5 drones", num_drones(), "/", max_drones())

quick_print("[FR] 6 hay", num_items(Items.Hay), "wood", num_items(Items.Wood), "carrot", num_items(Items.Carrot))

quick_print("[FR] 7 loops", num_unlocked(Unlocks.Loops), "speed", num_unlocked(Unlocks.Speed), "expand", num_unlocked(Unlocks.Expand), "plant", num_unlocked(Unlocks.Plant))

quick_print("[FR] 8 variables", num_unlocked(Unlocks.Variables), "functions", num_unlocked(Unlocks.Functions), "import", num_unlocked(Unlocks.Import), "lists", num_unlocked(Unlocks.Lists))

quick_print("[FR] 9 senses", num_unlocked(Unlocks.Senses), "operators", num_unlocked(Unlocks.Operators), "debug", num_unlocked(Unlocks.Debug), "megafarm", num_unlocked(Unlocks.Megafarm))

for unlock_type in Unlocks:
	quick_print("[FR] 10 unlock", unlock_type, num_unlocked(unlock_type), "cost", get_cost(unlock_type))

quick_print("[FR] 11 done")
