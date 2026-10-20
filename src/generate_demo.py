"""Write deterministic invented fixtures; no person-level records are involved."""
import csv
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write(name, rows, fields):
    with (ROOT / "data" / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    weeks = [date(2026, 1, 5) + timedelta(weeks=i) for i in range(4)]
    sites = ["demo_A", "demo_B", "demo_C"]
    values = [(0,100,2),(0,0,1),(3,60,12),(5,80,3),(4,50,2),(2,30,2),(2,40,1),(7,50,3),(1,20,2),(4,90,0),(2,60,1),(1,20,2)]
    clean = []
    for (week, site), (positive, tests, delay) in zip([(w,s) for w in weeks for s in sites], values):
        clean.append({"site_id":site,"week_start":week.isoformat(),"positive_tests":str(positive),"tests_performed":str(tests),"reported_on":(week+timedelta(days=6+delay)).isoformat()})
    dirty = [dict(row) for i,row in enumerate(clean) if i != 5]
    dirty.insert(4, dict(clean[3]))
    for row in dirty:
        if (row["site_id"], row["week_start"]) == ("demo_B", "2026-01-19"):
            row["positive_tests"] = "70"
        if (row["site_id"], row["week_start"]) == ("demo_C", "2026-01-26"):
            row["tests_performed"] = "twenty"
        if (row["site_id"], row["week_start"]) == ("demo_B", "2026-01-26"):
            row["reported_on"] = "2026-01-27"
    fields=["site_id","week_start","positive_tests","tests_performed","reported_on"]
    write("reports.csv", dirty, fields)
    write("reports_clean.csv", clean, fields)
    write("calendar.csv", [{"site_id":s,"week_start":w.isoformat()} for w in weeks for s in sites], ["site_id","week_start"])

if __name__ == "__main__":
    main()
