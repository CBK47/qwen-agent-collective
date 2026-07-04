"""Legacy demo shim for the Track 3 multi-agent reviewer.

The original prototype used stale imports. Keep this file as a small sample
runner that exercises the canonical ``review.py`` pipeline.
"""

from __future__ import annotations

import json

from review import review_diff


SAMPLE_DIFF = """\
diff --git a/billing.py b/billing.py
--- a/billing.py
+++ b/billing.py
@@ -1,4 +1,6 @@
 def calculate_total(price, tax):
-    return price + (price * tax)
+    password = "secret123"
+    if price < 0: return 0
+    return float(price * (1 + tax))
"""


if __name__ == "__main__":
    print(json.dumps(review_diff(SAMPLE_DIFF), indent=2))
