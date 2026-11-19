Summary of D.3, from the tables above: under the declared long-context
variant the default local generator reached L4 on L1 for 3 of 5 candidates
(G2, G3, G5). Each costs about +81% to +84% latency against the unpatched
library (upper bounds 84.91% to 89.75%), about +63% to +65% against R2 (the
reference with the same mechanism, measured in the same session), and fits
neither budget. In the same session the upstream fix R1 costs +40.51% and the
OWASP fix R2 +11.13%; nothing fits the strict budget and only R2 fits the
lenient one. Generation took about 80 to 88 s per candidate on the GPU for
about 10,000 completion tokens each.
