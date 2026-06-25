# product_scope.py
# The supported product boundary for FARSight v1. Keep this definition
# explicit and reviewable: the source PDFs include adjacent FAA material
# that v1 deliberately does not answer.

FARSIGHT_V1_SUPPORTED_SCOPE = """\
FARSight v1 answers study-aid questions for student and private pilots when
the answer can be grounded in:

- 14 CFR Part 61: certification, privileges, limitations, and currency.
- 14 CFR Part 67: medical certificate standards.
- 14 CFR Part 71: airspace designations included in the corpus.
- 14 CFR Part 91: general operating and flight rules included in the corpus.
- AIM guidance for ordinary pilot operations, airspace procedures,
  communication, airport operations, aeromedical factors, and other normal
  FAR/AIM study topics.

FARSight v1 does not answer questions whose authoritative source is outside
that boundary, even if a retrieved FAR/AIM chunk is topically nearby. Out of
scope areas include:

- Part 107 or UAS/drone operating rules.
- Part 47 aircraft registration process rules and FAA registration filing
  procedures.
- Parts 121, 135, and 141 commercial, charter, airline, and flight-school
  certification rules.
- Part 43 maintenance rules except where the available Part 91 corpus itself
  directly answers an operational equipment or inspection requirement.
- Live weather, NOTAMs, flight planning, personalized legal judgments, or
  other facts that are not static FAR/AIM text.

Important boundary cases:

- Questions about carrying or having an aircraft registration certificate,
  airworthiness certificate, or operating limitations on board are in scope
  when answered by 14 CFR § 91.203.
- Questions about how to register an aircraft with the FAA are out of scope
  because the authoritative registration process lives in Part 47/FAA filing
  procedures, not in the v1 corpus.
- AIM content about ordinary pilot operations is in scope. AIM UAS/drone
  advisory content is present in the PDFs but is outside the v1 product
  boundary.
"""
