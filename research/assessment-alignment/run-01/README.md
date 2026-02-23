# Run 1: Schema Audit & Data Quality

**Date:** Feb 21-22, 2026
**Analyst:** Eli Vance
**Study:** Assessment Alignment Deep Dive — Do internal assessments predict LEAP outcomes?

## Summary

This run verified the actual schema of every assessment table needed for the alignment study, tested all cross-system join paths, and documented coverage rates.

### Top-Line Results

| Finding | Detail |
|---|---|
| Analyzable student population | **1,784 students** have LEAP + anet + MAP + PM data (94.4% of all LEAP students) |
| Best join key | LASID (State Student Number) — STRING in all systems, no casting needed |
| Weakest link | MAP at 95.7% LEAP coverage; PM is strongest at 99.4% |
| Biggest gotcha | anet is item-level (13-16 rows per student per test) — must aggregate before analysis |
| School correction | 399005 = Langston Hughes Charter Academy (not GW Carver as assumed in Run 0) |
| Schools covered | 4: Ashe (534), LHA (519), Wheatley (499), Green (338) |
| LEAP grades | 3-8 across all four schools |

### Critical Gotchas for Run 2+

1. **anet**: Item-level grain. Aggregate with `SUM(points_received)/SUM(points_possible) GROUP BY sas_id, assessment_id`
2. **PM results_raw**: Standard-level grain. Use `SELECT DISTINCT student, test, Overall_Test_Score`
3. **PM results_by_test**: School-level only. **Dead end** for student analysis.
4. **Grades**: No LASID. Bridge through roster (`Student_Number` -> `State_StudentNumber`)
5. **LEAP SchoolName**: Has trailing whitespace. Always `TRIM()`
6. **School names**: LHA has 3 different strings across systems. Use `LIKE '%Hughes%'` pattern.
7. **MAP**: Subject = "Language Arts" (not "ELA"), "Mathematics" (not "Math"). No Grade column.

## Files

| File | Description |
|---|---|
| `schema-audit.html` | Full HTML artifact with coverage matrix, schema reference, and join paths |
| `tmp/` | Raw JSON query results (14 schema samples + counting/overlap queries) |

## What's Needed for Run 2

Run 2 should aggregate anet and PM to student-level scores, then begin the actual alignment analysis:
- Compute anet percent correct per student per assessment window (BOY/MOY/EOY) per subject
- Extract MAP RIT scores and percentiles per student per window
- Extract PM test scores per student for ELA and Math assessments
- Extract course grades (ELA/Math) from grades table
- Join all to LEAP achievement levels
- Produce concordance tables: what % of students at each internal assessment level hit Mastery+ on LEAP?
