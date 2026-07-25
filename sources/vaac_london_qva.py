"""Source: Met Office VAAC London — Quantitative Volcanic Ash (QVA) feed.

QVA became operational 27 Nov 2025. Access requires a written email request to
QVA@metoffice.gov.uk (free but access-gated). Until Harry has completed onboarding
this module is a stub — it raises a clear diagnostic so the runner marks it "failed"
with an actionable next step in the manifest notes column.

Onboarding email template (send from harryevans15@icloud.com):

    To:   QVA@metoffice.gov.uk
    Subj: QVA subscription request — DefendAble Ltd (EC261/UK261 defence tool)

    Please add DefendAble Ltd to the QVA distribution list. We use volcanic-ash
    evidence in EC261/UK261 airline-defence cases (McDonagh C-12/11 pattern).
    We will consume the feed via authenticated pull. Delivery preference: HTTPS
    endpoint with API key. Contact: Harry Evans, harryevans15@icloud.com.
    Organisation website: (add when available).

Once onboarding completes, replace pull() body with the real fetch and set
VAAC_QVA_KEY as a GitHub Actions secret.
"""

from pull_common import wrap
import time

ID = "vaac-london-qva"
ENDPOINT = "QVA@metoffice.gov.uk"
AUTH_MODE = "written request (pending)"


def pull() -> dict:
    raise RuntimeError(
        "VAAC QVA access not yet onboarded — email QVA@metoffice.gov.uk with the "
        "subscription template in this file's docstring. Free but access-gated."
    )
