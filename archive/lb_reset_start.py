# ============================================================
# LEADERBOARD LAUNCHER
# ============================================================
#
# Starts a timed leaderboard run with FILE as its starting
# file.
#
#   Fastest_Reset: "Completely automate the game from a single
#   farm plot to unlocking the leaderboards again."
#
# FILE = "lb_probe" for now: a staged probe of what a reset
# starts with. SPEEDUP only sets the starting playback speed.
# ============================================================


LEADERBOARD = Leaderboards.Fastest_Reset

FILE = "lb_probe"

SPEEDUP = 1


leaderboard_run(
	LEADERBOARD,
	FILE,
	SPEEDUP
)
