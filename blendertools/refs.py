"""Digitized reference data. Provenance is the whole point: each entry says
which photo, which convention, and how confident. Derived targets EXPIRE --
re-digitize when the reference or the framing convention changes.
"""

# Boy, front view (boy1.jpg), 30x30 occupancy spans, row 0 = crown of hair,
# row 29 = collar bottom; col 0/29 = left/right silhouette extremes.
# Visual estimate, +-1 cell. Digitized during the 30x30 session; note the
# ear rows (14-17) were later found to UNDER-read ear extent -- the model's
# "excess" there was the ear, correctly placed. Treat those rows as +-2.
BOY_FRONT_SPANS_30 = [
    None, (13, 17), (11, 19), (9, 21), (7, 22), (5, 24), (4, 25), (3, 26), (2, 27), (2, 27),
    (2, 27), (2, 26), (3, 26), (3, 25), (4, 25), (4, 24), (5, 24), (5, 23), (6, 23), (7, 22),
    (7, 21), (8, 20), (9, 19), (10, 18), (11, 18), (12, 17), (12, 17), (12, 17), (12, 17), (10, 19),
]

# Boy, profile (boy5.jpg), (u=Y forward-negative, v=Z) landmarks in model units,
# crown z=1.10 -> chin z=-1.15. Used by the profile-diff drawing studies.
BOY_PROFILE_LANDMARKS = [
    (-0.05, 1.10), (-0.55, 0.90), (-0.85, 0.55), (-0.93, 0.25), (-0.95, -0.12),
    (-1.10, -0.30), (-0.90, -0.44), (-0.96, -0.60), (-0.92, -0.72), (-0.86, -0.92),
    (-0.60, -1.10), (-0.28, -1.15),
]
