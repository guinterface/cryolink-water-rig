#!/bin/bash
# Run only after h1c CFD post-processing/summarization, preserving the original proof outputs.
set -e
cd cryolink/sims/fea/coupling_p/coldfit_1106
COUPLING_PROOF_OUT=cryolink/sims/fea/coupling_p/coldfit_1106 H=1.0 LD_LIBRARY_PATH=<scratch>/cryolink_video/arpack/lib python -u ../coupling_proof.py > log.proof 2>&1
cp results.json ../results.json
