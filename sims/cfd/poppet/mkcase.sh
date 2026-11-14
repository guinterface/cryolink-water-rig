#!/bin/bash
# usage: mkcase.sh <case dir containing mesh.msh> ; incompressible LOX 90.19 K 4 bar, 0.28 kg/s, k-omega SST
set -e
C=$1
source ./coldfit_foam_env.sh
U=${U:-0.6457}; NU=1.71e-07; D=0.022
I=0.05; K=$(python3 -c "print(1.5*($U*$I)**2)"); OM=$(python3 -c "k=1.5*($U*$I)**2; print(k**0.5/(0.09**0.25*0.07*$D))")
mkdir -p $C/0 $C/constant $C/system
H='FoamFile{version 2.0;format ascii;class'
cat > $C/system/controlDict <<E
$H dictionary;object controlDict;}
application simpleFoam;startFrom latestTime;startTime 0;stopAt endTime;endTime 4000;deltaT 1;
writeControl timeStep;writeInterval 500;purgeWrite 0;writeFormat binary;writePrecision 8;runTimeModifiable true;
functions{
 pIn{type surfaceFieldValue;libs (fieldFunctionObjects);regionType patch;name inlet;operation areaAverage;fields (p);writeFields false;writeControl timeStep;writeInterval 25;log true;}
 pOut{type surfaceFieldValue;libs (fieldFunctionObjects);regionType patch;name outlet;operation areaAverage;fields (p);writeFields false;writeControl timeStep;writeInterval 25;log true;}
 phiOut{type surfaceFieldValue;libs (fieldFunctionObjects);regionType patch;name outlet;operation sum;fields (phi);writeFields false;writeControl timeStep;writeInterval 25;log true;}
 pMin{type fieldMinMax;libs (fieldFunctionObjects);fields (p U);writeControl timeStep;writeInterval 25;log true;}
}
E
cat > $C/system/fvSchemes <<E
$H dictionary;object fvSchemes;}
ddtSchemes{default steadyState;}gradSchemes{default cellLimited Gauss linear 1;}
divSchemes{default none;div(phi,U) bounded Gauss linearUpwind grad(U);div(phi,k) bounded Gauss upwind;div(phi,omega) bounded Gauss upwind;div((nuEff*dev2(T(grad(U))))) Gauss linear;}
laplacianSchemes{default Gauss linear limited 0.5;}interpolationSchemes{default linear;}snGradSchemes{default limited 0.5;}wallDist{method meshWave;}
E
cat > $C/system/fvSolution <<E
$H dictionary;object fvSolution;}
solvers{p{solver GAMG;smoother GaussSeidel;tolerance 1e-8;relTol 0.05;}"(U|k|omega)"{solver smoothSolver;smoother symGaussSeidel;tolerance 1e-8;relTol 0.1;}}
SIMPLE{nNonOrthogonalCorrectors 1;consistent yes;residualControl{p 1e-5;U 1e-6;"(k|omega)" 1e-6;}}
relaxationFactors{equations{U 0.7;".*" 0.7;}fields{p 0.5;}}
E
cat > $C/system/decomposeParDict <<E
$H dictionary;object decomposeParDict;}
numberOfSubdomains ${NP:-16};method scotch;
E
for f in physicalProperties transportProperties; do printf "$H dictionary;object $f;}\ntransportModel Newtonian;viscosityModel constant;nu $NU;\n" > $C/constant/$f; done
for f in momentumTransport turbulenceProperties; do printf "$H dictionary;object $f;}\nsimulationType RAS;RAS{model kOmegaSST;turbulence on;printCoeffs on;}\n" > $C/constant/$f; done
cat > $C/0/U <<E
$H volVectorField;object U;}
dimensions [0 1 -1 0 0 0 0];internalField uniform (0 0 0);
boundaryField{inlet{type fixedValue;value uniform (0 0 $U);}outlet{type zeroGradient;}wall{type noSlip;}}
E
cat > $C/0/p <<E
$H volScalarField;object p;}
dimensions [0 2 -2 0 0 0 0];internalField uniform 0;
boundaryField{inlet{type zeroGradient;}outlet{type fixedValue;value uniform 0;}wall{type zeroGradient;}}
E
for fld in k omega; do v=$K; dim="[0 2 -2 0 0 0 0]"; wf=kqRWallFunction; if [ $fld = omega ]; then v=$OM; dim="[0 0 -1 0 0 0 0]"; wf=omegaWallFunction; fi
cat > $C/0/$fld <<E
$H volScalarField;object $fld;}
dimensions $dim;internalField uniform $v;
boundaryField{inlet{type fixedValue;value uniform $v;}outlet{type zeroGradient;}wall{type $wf;value uniform $v;}}
E
done
cat > $C/0/nut <<E
$H volScalarField;object nut;}
dimensions [0 2 -1 0 0 0 0];internalField uniform 0;
boundaryField{inlet{type calculated;value uniform 0;}outlet{type calculated;value uniform 0;}wall{type nutkWallFunction;value uniform 0;}}
E
cd $C
gmshToFoam mesh.msh > log.gmshToFoam 2>&1
transformPoints "scale=(0.001 0.001 0.001)" > log.transform 2>&1 || transformPoints -scale "(0.001 0.001 0.001)" > log.transform 2>&1
sed -i '/wall/,/}/ s/type *patch;/type wall;/' constant/polyMesh/boundary
checkMesh > log.checkMesh 2>&1 || true
grep -E "Mesh OK|Failed|cells:|Max non-orth|skewness" log.checkMesh | head -6
