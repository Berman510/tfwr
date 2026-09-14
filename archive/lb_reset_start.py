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
# FILE = "full_run": sim_full round 13 unlocked the Leaderboard
# in 91,502 simulated sec. SPEEDUP only sets the starting
# playback speed.
# ============================================================


LEADERBOARD = Leaderboards.Fastest_Reset

FILE = "full_run"

SPEEDUP = 256


leaderboard_run(
	LEADERBOARD,
	FILE,
	SPEEDUP
)
