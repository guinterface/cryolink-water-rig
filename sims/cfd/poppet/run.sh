#!/bin/bash
# Preserve prior case files: refuse an existing decomposition instead of removing it.
set -e
source ./coldfit_foam_env.sh
export FOAM_MPI=mpich-3.3 LD_LIBRARY_PATH=$FOAM_LIBBIN/mpich-3.3:$LD_LIBRARY_PATH
cd $1; NP=$(grep numberOfSubdomains system/decomposeParDict | grep -o '[0-9]*')
decomposePar > log.decompose 2>&1
$FOAM_MPIEXEC -np $NP -env LD_PRELOAD $FOAM_LIBBIN/mpich-3.3/libPstream.so simpleFoam -parallel > log.simpleFoam 2>&1; echo "DONE $?" >> log.simpleFoam
reconstructPar -latestTime > log.reconstruct 2>&1
