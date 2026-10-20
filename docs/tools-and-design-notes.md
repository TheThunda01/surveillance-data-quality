# Related tools and design choices

A useful comparison is the Carnegie Mellon Delphi group's public [delphi-epidata repository](https://github.com/cmu-delphi/delphi-epidata). Its official documentation makes observation time and data availability explicit. The newer [V5 API](https://cmu-delphi.github.io/delphi-epidata/api/v5.html) distinguishes historical archives from snapshots of what was known at a point in time. That is closely related to the question our small version-history example teaches.

For the current review, the [V5 source documentation](https://github.com/cmu-delphi/delphi-epidata/blob/603969199277177c2e3c612b13fa732f1698f99c/docs/api/v5.md) and [MIT license](https://github.com/cmu-delphi/delphi-epidata/blob/603969199277177c2e3c612b13fa732f1698f99c/LICENSE) were inspected at commit `603969199277177c2e3c612b13fa732f1698f99c`. The local preflight borrows the general separation of snapshots and metadata as a design lesson; it is independently implemented and is not a Delphi client. See the [review and selection record](literature-review.md).

| Question | This project | Delphi documentation |
| --- | --- | --- |
| What was available by a date? | Selects local synthetic report versions by `issued_on` | V5 snapshot endpoints retrieve a dataset's state at a selected time |
| How are changes inspected? | Compares two user-saved public extracts | V5 archives expose records as values change |
| Where do the data come from? | One pinned direct CDC extract; synthetic version-history fixture | A hosted collection of epidemiological data streams |
| What is required to run? | Standard-library Python, offline by default | API access and attention to source-specific coverage, licensing, and endpoint behavior |

This is a design comparison, not an integration or claim of equivalence. No Delphi code or data were copied into the repository, and no dependency was added. A future historical-data extension should first confirm that the chosen source actually preserves the needed releases and that its time fields match the intended analysis.

The [legacy V4 query documentation](https://github.com/cmu-delphi/delphi-epidata/blob/dev/docs/api/covidcast_api_queries.md) also explains issue-date selection, but the project now directs new work toward V5. We do not recommend building a new integration against the legacy endpoint merely because an older example uses it. Documentation and repository metadata were checked on October 20, 2026.
