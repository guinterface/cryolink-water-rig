#!/bin/bash
# Prefer original runtime; use the preserved OpenFOAM 2412 runtime if conda files are missing.
S=<scratch>/sim_env
if [ -f "$S/etc/conda/activate.d/openfoam_activate.sh" ] && [ -x "$S/bin/simpleFoam" ]; then
    export CONDA_PREFIX=$S PATH=$S/bin:$PATH
    source "$S/etc/conda/activate.d/openfoam_activate.sh"
    FOAM_MPIEXEC=$S/bin/mpiexec
else
    source cryolink/sims/video/foam_env.sh
    export PATH=$V/mpi/bin:$PATH
    export LD_LIBRARY_PATH=$V/ucx/lib:$V/mpi/lib:$LD_LIBRARY_PATH
    export UCX_TLS=self,sm,tcp UCX_WARN_UNUSED_ENV_VARS=n
    FOAM_MPIEXEC=$V/mpi/bin/mpiexec
fi
export FOAM_MPIEXEC FOAM_MPI=mpich-3.3
