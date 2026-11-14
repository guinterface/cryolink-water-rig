#!/bin/bash
# usage: post.sh <case>  -> area-averaged p, mass flow, on cutting planes along the axis + patches; min p
source ./coldfit_foam_env.sh
cd $1
ZS="200 250 258 265 272 280 286 289 292 300 310 320 328 333 340 348 352.5 360 380 410"
{ echo 'FoamFile{version 2.0;format ascii;class dictionary;object planes;}'
echo 'functions{'
for z in $ZS; do n=z${z/./_}
cat <<E
$n {type surfaceFieldValue;libs (fieldFunctionObjects);regionType sampledSurface;name $n;
 sampledSurfaceDict {type cuttingPlane;planeType pointAndNormal;pointAndNormalDict {point (0 0 $(python3 -c "print($z/1000)"));normal (0 0 1);} interpolate false;}
 operation areaAverage;fields (p U);writeFields false;}
${n}q {type surfaceFieldValue;libs (fieldFunctionObjects);regionType sampledSurface;name ${n}q;
 sampledSurfaceDict {type cuttingPlane;planeType pointAndNormal;pointAndNormalDict {point (0 0 $(python3 -c "print($z/1000)"));normal (0 0 1);} interpolate false;}
 operation areaIntegrate;fields (U);writeFields false;}
E
done
cat <<E
pin {type surfaceFieldValue;libs (fieldFunctionObjects);regionType patch;name inlet;operation areaAverage;fields (p);writeFields false;}
pout {type surfaceFieldValue;libs (fieldFunctionObjects);regionType patch;name outlet;operation areaAverage;fields (p);writeFields false;}
mm {type fieldMinMax;libs (fieldFunctionObjects);fields (p U);location true;}
}
E
} > system/planes
if [ -n "$T" ]; then TA="-time $T"; else TA=-latestTime; fi
simpleFoam -postProcess -dict system/planes $TA > log.post 2>&1
echo exit $?
