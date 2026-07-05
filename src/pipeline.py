"""
LogiTrackPipeline — LogiTrack India capstone (Days 189-190)
Extracted from the actual submitted Day189/Day190 notebooks.
Generates its own locked raw dataset (seed=181) if no CSV is supplied,
so this file runs standalone in CI (GitHub Actions) without a notebook.
"""
import pandas as pd
import numpy as np
import os
import io
import json
from datetime import datetime, timedelta

os.environ.setdefault('AWS_DEFAULT_REGION', 'ap-south-1')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'testing')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'testing')
os.environ.setdefault('AWS_SECURITY_TOKEN', 'testing')
os.environ.setdefault('AWS_SESSION_TOKEN', 'testing')

import boto3
from moto import mock_aws

CONFORMANCE_THRESHOLD = 80.0
RAW_PATH = 'capstone_raw/logitrack_raw.csv'


def generate_raw_data(path=RAW_PATH, seed=181, n=530):
    """Locked raw-data generator — DO NOT MODIFY. Same logic as Days 189-190."""
    np.random.seed(seed)

    carriers = ['BlueDart', 'Delhivery', 'DTDC', 'XpressBees', 'Ecom Express']
    cities_origin = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 'Kolkata', 'Pune', 'Ahmedabad']
    cities_dest = ['Jaipur', 'Lucknow', 'Bhopal', 'Patna', 'Surat', 'Nagpur', 'Visakhapatnam', 'Indore']
    statuses = ['Delivered', 'In Transit', 'Delayed', 'Returned']

    shipment_ids = [f'LT{str(i).zfill(5)}' for i in range(1, n + 1)]
    carrier_col = np.random.choice(carriers, n)
    origin_col = np.random.choice(cities_origin, n)
    destination_col = np.random.choice(cities_dest, n)
    weight_col = np.round(np.random.uniform(0.5, 50.0, n), 2)
    days_col = np.random.randint(1, 25, n)
    status_col = np.random.choice(statuses, n, p=[0.6, 0.2, 0.15, 0.05])
    revenue_col = np.round(weight_col * np.random.uniform(20, 80, n), 2)

    base_date = datetime(2024, 1, 1)
    ship_dates = [base_date + timedelta(days=int(x)) for x in np.random.randint(0, 365, n)]
    ship_date_col = [d.strftime('%Y-%m-%d') for d in ship_dates]

    df_base = pd.DataFrame({
        'shipment_id': shipment_ids, 'carrier': carrier_col, 'origin': origin_col,
        'destination': destination_col, 'weight_kg': weight_col, 'days_in_transit': days_col,
        'status': status_col, 'revenue_inr': revenue_col, 'ship_date': ship_date_col
    })

    # inject 8 duplicate rows — same corruption pattern as Days 181/186
    dup_indices = np.random.choice(range(n), 8, replace=False)
    dups = df_base.iloc[dup_indices].copy()
    df_raw = pd.concat([df_base, dups], ignore_index=True)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df_raw.to_csv(path, index=False)
    return df_raw


class LogiTrackPipeline:
    def __init__(self, raw_path=RAW_PATH):
        self.raw_path = raw_path
        if not os.path.exists(raw_path):
            generate_raw_data(raw_path)
        self.df_raw = pd.read_csv(raw_path)
        self.df_clean = None
        self.df_events = None
        self.run_log = {}

    # ---- Day 189: extract / transform / test / load ----
    def extract(self):
        self.run_log['rows_in'] = len(self.df_raw)
        print(f"Extracted rows: {self.run_log['rows_in']}")
        return self.df_raw

    def transform(self):
        self.df_clean = self.df_raw.drop_duplicates().reset_index(drop=True)
        self.df_clean['delay_flag'] = self.df_clean['days_in_transit'].apply(
            lambda x: 'High Delay' if x > 14 else 'On Track'
        )
        self.df_clean['high_delay'] = self.df_clean['delay_flag'] == 'High Delay'
        return self.df_clean

    def run_tests(self):
        checks = [
            ('raw_row_count', len(self.df_raw) == 538),
            ('clean_row_count', len(self.df_clean) == 530),
            ('no_duplicates', self.df_clean.duplicated().sum() == 0),
            ('no_nulls', self.df_clean.isnull().sum().sum() == 0),
            ('shipment_id_unique', self.df_clean['shipment_id'].is_unique),
            ('revenue_non_negative', (self.df_clean['revenue_inr'] >= 0).all()),
        ]
        all_passed = True
        for name, passed in checks:
            print(f"  {'✓ PASS' if passed else '✗ FAIL'}: {name}")
            if not passed:
                all_passed = False
        return all_passed, checks

    def load(self):
        with mock_aws():
            s3 = boto3.client('s3', region_name='ap-south-1')
            bucket_name = 'logitrack-capstone-bucket'
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
            )
            for carrier, group_df in self.df_clean.groupby('carrier'):
                key = f"processed/carrier={carrier}/data.csv"
                buf = io.BytesIO()
                group_df.to_csv(buf, index=False)
                buf.seek(0)
                s3.put_object(Bucket=bucket_name, Key=key, Body=buf.getvalue())
            resp = s3.list_objects_v2(Bucket=bucket_name, Prefix='processed/')
            objects = resp.get('Contents', [])
            self.run_log['s3_objects_written'] = len(objects)
        return True

    # ---- Day 190: process-mining monitor ----
    def generate_event_log(self):
        np.random.seed(190)
        canonical = ['Order Placed', 'Picked Up', 'In Transit Scan', 'Out for Delivery', 'Delivered']
        middle = canonical[1:-1]
        events = []
        for _, row in self.df_clean.iterrows():
            case_id = row['shipment_id']
            carrier = row['carrier']
            break_prob = 0.45 if row['high_delay'] else 0.15
            timestamp = datetime.strptime(row['ship_date'], '%Y-%m-%d')
            sequence = canonical.copy()
            if np.random.random() < break_prob:
                break_type = np.random.choice(['skip', 'reorder'])
                if break_type == 'skip':
                    idx = np.random.randint(0, len(middle))
                    sequence.remove(middle[idx])
                else:
                    idx = np.random.randint(0, len(middle) - 1)
                    p1, p2 = sequence.index(middle[idx]), sequence.index(middle[idx + 1])
                    sequence[p1], sequence[p2] = sequence[p2], sequence[p1]
            for activity in sequence:
                timestamp += timedelta(hours=np.random.uniform(2, 30))
                events.append({'case_id': case_id, 'carrier': carrier, 'activity': activity, 'timestamp': timestamp})
        self.df_events = pd.DataFrame(events)
        return self.df_events

    def check_conformance(self):
        canonical = ['Order Placed', 'Picked Up', 'In Transit Scan', 'Out for Delivery', 'Delivered']
        conformant, non_conformant = [], []
        for case_id, group in self.df_events.groupby('case_id'):
            activities = group.sort_values('timestamp')['activity'].tolist()
            if set(activities) != set(canonical):
                non_conformant.append(case_id)
                continue
            order = [canonical.index(a) for a in activities]
            (conformant if all(order[i] < order[i + 1] for i in range(len(order) - 1)) else non_conformant).append(case_id)
        total = len(conformant) + len(non_conformant)
        rate = round(len(conformant) / total * 100, 2) if total else 0.0
        print(f"Conformance rate: {rate}%")
        print(f"Non-conformant cases: {len(non_conformant)}")
        return rate, non_conformant

    def monitor(self):
        rate, non_conformant = self.check_conformance()
        gate_passed = rate >= CONFORMANCE_THRESHOLD
        self.run_log['conformance_rate'] = rate
        self.run_log['non_conformant_case_count'] = len(non_conformant)
        self.run_log['conformance_threshold'] = CONFORMANCE_THRESHOLD
        self.run_log['conformance_gate_passed'] = gate_passed
        return gate_passed

    # ---- orchestration ----
    def run(self):
        print("=== LogiTrack Pipeline Execution ===")
        self.extract()
        self.transform()
        data_quality_pass, _ = self.run_tests()
        if data_quality_pass:
            self.load()
        self.generate_event_log()
        conformance_pass = self.monitor()

        total_rows = len(self.df_clean)
        high_delay_count = int(self.df_clean['high_delay'].sum())
        self.run_log.update({
            'run_timestamp': datetime.now().isoformat(),
            'raw_row_count': int(len(self.df_raw)),
            'clean_row_count': int(total_rows),
            'high_delay_count': high_delay_count,
            'high_delay_pct': round(high_delay_count / total_rows * 100, 2),
            'data_quality_gate_passed': bool(data_quality_pass),
            'overall_gate_passed': bool(data_quality_pass and conformance_pass),
        })
        os.makedirs('capstone_raw', exist_ok=True)
        with open('capstone_raw/run_summary.json', 'w') as f:
            json.dump(self.run_log, f, indent=2, default=str)
        print("=== Pipeline finished ===")
        return self.run_log


if __name__ == '__main__':
    pipeline = LogiTrackPipeline()
    summary = pipeline.run()
    print(json.dumps(summary, indent=2, default=str))
