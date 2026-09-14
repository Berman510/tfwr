# ============================================================
# LEADERBOARD LAUNCHER
# ============================================================
#
# Starts a timed leaderboard run with FILE as its starting
# file.
#
#   Hay: "Farm 2_000_000_000 hay with multiple drones."
#   lb_probe.py runs production farm_hay with a 2B target.
#
# SPEEDUP only sets the starting playback speed.
# ============================================================


LEADERBOARD = Leaderboards.Hay

FILE = "lb_probe"

SPEEDUP = 64


leaderboard_run(
	LEADERBOARD,
	FILE,
	SPEEDUP
)
