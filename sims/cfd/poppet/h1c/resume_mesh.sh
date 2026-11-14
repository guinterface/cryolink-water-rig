#!/bin/bash
# Run from sims/cfd/poppet after successful final CAD export and seals checks.
set -euo pipefail
python -I mesh.py 1.0 h1c/mesh.msh > h1c/log.mesh 2>&1
NP=16 ./mkcase.sh h1c > h1c/log.mkcase 2>&1
grep -q "Mesh OK" h1c/log.checkMesh
./run.sh h1c > h1c/log.run 2>&1
grep -q 'DONE 0' h1c/log.simpleFoam
./post.sh h1c > h1c/log.post_driver 2>&1
python3 -I summarize_h1c.py > h1c/log.summary 2>&1
