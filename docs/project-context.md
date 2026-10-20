# Why this project exists

## The background

A weekly surveillance table can look ready for analysis even when reports are missing, duplicated, revised, or built from different denominators. Before interpreting a curve, it helps to ask two questions: **what does each number represent, and when was that number available?**

This project brings those questions into a small, reproducible workflow. Its real-data example uses public national laboratory aggregates from [CDC NREVSS](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb). A separate synthetic example makes reporting delays and revisions easy to inspect without inventing a history for the CDC data.

## What it does

The public-data audit checks a pinned 123-record extract covering 41 weeks and three laboratory categories. It verifies counts, matches records to the expected weekly calendar, preserves missing or suppressed values, and checks whether reported percentages agree with their numerators and denominators. It then shows how pooled summaries change when recent weeks are left out.

The version-history tool answers a different question: which reports could an analyst have used by a particular date? It selects the latest available version, keeps future revisions out, and distinguishes reports that are not yet due from reports that are overdue. Another tool compares two saved public releases when a later capture becomes available.

## Why it matters

The benefit is a more inspectable analysis: readers can see the source, exclusions, denominators, and timing assumptions before deciding what a result supports. [Mellor and colleagues’ 2026 review](https://doi.org/10.1371/journal.pdig.0001759) explains how reporting delays and revisions can make retrospective surveillance analyses look more useful than their real-time counterparts. That motivates these checks; it does not establish that this software is validated for operational surveillance.

The [2026 MMWR respiratory-surveillance report](https://doi.org/10.15585/mmwr.mm7506a2) also discusses NREVSS participation and representativeness limits. Complete rows in this extract do not mean complete coverage of laboratories, patients, or infections. Test positivity is not population prevalence.

## Key themes to look for

- **Data provenance:** fixed inputs, source links, and file fingerprints.
- **Denominator awareness:** separate test pools and explicit coverage measures.
- **Time-aware analysis:** observation dates, availability dates, and revisions.
- **Reproducible engineering:** Python, SQLite, automated checks, and readable outputs.

Start with the [real-data results](../results_public/report.md), then compare the [synthetic version-history example](../results_vintages/report.md).
