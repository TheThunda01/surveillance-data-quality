-- The expected calendar, not the submitted file, defines the denominator.
SELECT e.site_id, e.week_start, COUNT(r.source_row) AS received_rows,
    CASE WHEN COUNT(r.source_row) = 0 THEN 'missing'
         WHEN COUNT(r.source_row) = 1 AND MAX(r.usable) = 1 THEN 'usable'
         ELSE 'invalid' END AS status,
    CASE WHEN COUNT(r.source_row) = 1 AND MAX(r.usable) = 1 THEN MAX(r.positive_tests) END AS positive_tests,
    CASE WHEN COUNT(r.source_row) = 1 AND MAX(r.usable) = 1 THEN MAX(r.tests_performed) END AS tests_performed,
    CASE WHEN COUNT(r.source_row) = 1 AND MAX(r.usable) = 1 AND MAX(r.tests_performed) > 0
         THEN 1.0 * MAX(r.positive_tests) / MAX(r.tests_performed) END AS positivity,
    CASE WHEN COUNT(r.source_row) = 1 AND MAX(r.usable) = 1 THEN MAX(r.delay_days) END AS delay_days
FROM expected AS e
LEFT JOIN reports AS r ON e.site_id = r.site_id AND e.week_start = r.week_start
GROUP BY e.site_id, e.week_start
ORDER BY e.week_start, e.site_id;
