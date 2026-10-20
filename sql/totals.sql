-- Pool counts; do not average site percentages. NULL represents an undefined ratio.
SELECT COALESCE(SUM(positive_tests), 0) AS pooled_positive_tests,
       COALESCE(SUM(tests_performed), 0) AS pooled_tests_performed,
       1.0 * SUM(positive_tests) / NULLIF(SUM(tests_performed), 0) AS pooled_positivity
FROM reports WHERE usable = 1;
