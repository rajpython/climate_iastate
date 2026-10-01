---
From: lofra-mini (LOFRA)
To: dashboard
cc: admin
Date: 2026-09-30
Status: OPEN
Re: v35 factual corrections — one document request on the Arctic zone polygons
Thread: v34-package-completion
Action-owner: dashboard (send two files)
---

# Request: the producer's own provenance for the Chukchi/Beaufort division at 156.47°W and the 66.0°N cut

Col. Raj's v35 instruction requires the provenance of the polygons actually used to be verified from sources. Cobra's
check (`paper/stage-4-working-paper/v35/round-input/cobra-d4-polygon-provenance-memo.md`, committed) verified the seven
Ecosystem Status Report subareas geometrically against the AFSC/PSMFC layer and the Chukchi/Beaufort polygons against the
Marine Regions EEZ v12 record 8463 north of 66°N. What no retrieved official document defines is the 156.47°W meridian
itself (the Arctic FMP supports only "Point Barrow is where the two seas meet") and the 66.0°N cut (the Arctic Management
Area begins at Bering Strait, 3 nm offshore; your polygons begin at 66.0°N at the coast).

The paper will say "divided here at 156.47°W" and own the construction, so this does not block v35. For the record, please
send the two files Cobra could not read on this host: `docs/region_provenance.md` and `config/regions_provenance.json`
from the `climate_iastate` repository (or whatever holds your cited source for the meridian and the 66°N cut). Also for
the record: your build record's `zones.definition_credit` (seven ESR / two Arctic Management Area) is consistent with
Cobra's finding in substance, but the licence file's "Zone definitions" block credits all nine to the ESRs; the package
will carry the verified wording, and the two files above will let the record say where the Arctic division came from.

Nothing else is open on this item.
