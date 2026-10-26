# Why this project exists

## The background

Before interpreting a surveillance curve, establish **what each number represents and when it was available**. A weekly table may contain missing, duplicated, or revised reports, or combine different denominators.

This project checks those details in a small, reproducible workflow. Its real-data example uses public national laboratory aggregates from the [Centers for Disease Control and Prevention (CDC) National Respiratory and Enteric Virus Surveillance System (NREVSS)](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb). A separate synthetic example makes reporting delays and revisions easy to inspect without inventing a history for the CDC data.

## What it does

The public-data audit checks a pinned 123-record extract covering 41 weeks and three laboratory categories. It verifies counts, matches records to the expected weekly calendar, preserves missing or suppressed values, and checks whether reported percentages agree with their numerators and denominators. It then shows how pooled summaries change when recent weeks are left out.

The version-history tool answers a different question: which reports could an analyst have used by a particular date? It selects the latest available version, keeps future revisions out, and distinguishes reports that are not yet due from reports that are overdue. Another tool compares two saved public releases when a later capture becomes available.

## Why it matters

Readers can inspect the source, exclusions, denominators, and timing assumptions before deciding what a result supports. [Mellor et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/42832413/) explain how reporting delays and revisions can make retrospective surveillance analyses look more useful than their real-time counterparts. Their work motivates these checks; it does not validate this software for operational surveillance.

The respiratory-surveillance report by [Silk et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/41712508/) also discusses NREVSS participation and representativeness limits. Complete rows in this extract do not mean complete coverage of laboratories, patients, or infections. Test positivity is not population prevalence.

## Key themes to look for

- **Data provenance:** fixed inputs, source links, and file fingerprints.
- **Denominator awareness:** separate test pools and explicit coverage measures.
- **Time-aware analysis:** observation dates, availability dates, and revisions.
- **Reproducible engineering:** Python, SQLite, automated checks, and readable outputs.

Start with the [real-data results](../results_public/report.md), then compare the [synthetic version-history example](../results_vintages/report.md).

The [glossary](glossary.md) explains the vocabulary, and the [assumption register](assumptions.md) explains which choices the data cannot establish. Complete citations are in [references](references.md).
