"""Default: read-only dry run. Apply only after explicit human approval of report."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from bookings.repair_tables import dry_run, apply_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--apply-approved-report', action='store_true')
    args = parser.parse_args()
    if args.apply_approved_report:
        changed = apply_report(json.loads(args.report.read_text()))
        print(f'Assegnate {len(changed)} prenotazioni: {changed}')
    else:
        report = dry_run()
        # Do not silently replace a previously reviewed report.
        with os.fdopen(os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as output:
            json.dump(report, output, indent=2, ensure_ascii=False)
        print(f"DRY RUN: {report['involved']} coinvolte; {report['assignable']} assegnabili; {report['unassigned']} senza tavolo.")
        for row in report['bookings']:
            print(f"#{row['id']} | {row['date']} {row['time']} | {row['name']} | {row['party_size']} persone | "
                  + ('+'.join(row['proposed_tables']) or 'TAVOLO DA ASSEGNARE'))

if __name__ == '__main__':
    main()
