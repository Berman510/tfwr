# ============================================================
# CIRCULAR IMPORT (achievement: "Create an import cycle")
# ============================================================
#
# cycle_a imports cycle_b, and cycle_b imports cycle_a.
# Run cycle_a.
# ============================================================

import cycle_b


quick_print(
	"[CYCLE] cycle_a ran"
)
