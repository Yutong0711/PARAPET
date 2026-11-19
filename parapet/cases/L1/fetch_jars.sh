#!/usr/bin/env bash
# Fetch the L1 dependency jars from Maven Central into $PARAPET_JARS_DIR
# (default ~/parapet-work/jars) and verify them against the SHA-256 pinned in
# case.yaml. Network is needed only for this step; builds are offline after it.
set -euo pipefail
DEST="${PARAPET_JARS_DIR:-$HOME/parapet-work/jars}"
mkdir -p "$DEST"
fetch() {  # path-in-repo1 file sha256
  local url="https://repo1.maven.org/maven2/$1"
  [ -f "$DEST/$2" ] || curl -sSf -o "$DEST/$2" "$url"
  echo "$3  $DEST/$2" | sha256sum -c -
}
fetch net/iharder/base64/2.3.8/base64-2.3.8.jar base64-2.3.8.jar bbf41fda22877a538f6bc2d5ad0aa372a7ddf4a756af3386aa09d3d4eea84f7f
fetch junit/junit/4.11/junit-4.11.jar junit-4.11.jar 90a8e1603eeca48e7e879f3afbc9560715322985f39a274f6f6070b43f9d06fe
fetch org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar hamcrest-core-1.3.jar 66fdef91e9739348df7a096aa384a5685f4e875584cce89386a7a47251c4d8e9
