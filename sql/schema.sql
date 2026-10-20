-- Raw row identity is retained. Validation flags are set before SQL aggregation.
CREATE TABLE expected (
    site_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    PRIMARY KEY (site_id, week_start)
);
CREATE TABLE reports (
    source_row INTEGER PRIMARY KEY,
    site_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    positive_tests INTEGER,
    tests_performed INTEGER,
    delay_days INTEGER,
    usable INTEGER NOT NULL CHECK (usable IN (0, 1))
);
