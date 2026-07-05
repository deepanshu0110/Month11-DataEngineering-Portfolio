
import json
import sys

def main():
    try:
        with open('capstone_raw/run_summary.json', 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        print("✗ FAIL: run_summary.json not found")
        sys.exit(1)

    checks = [
        ('raw_row_count', log.get('raw_row_count') == 538),
        ('clean_row_count', log.get('clean_row_count') == 530),
        ('data_quality_gate_passed', log.get('data_quality_gate_passed') is True),
        ('conformance_rate >= threshold', log.get('conformance_rate', 0) >= log.get('conformance_threshold', 0))
    ]
    all_pass = True
    for name, passed in checks:
        if passed:
            print(f"✓ PASS: {name}")
        else:
            print(f"✗ FAIL: {name}")
            all_pass = False
    if all_pass:
        print("GATE RESULT: PASS")
        sys.exit(0)
    else:
        print("GATE RESULT: FAIL")
        sys.exit(1)

if __name__ == '__main__':
    main()
