import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
entities = {
    'DE_Berlin': 'EUR', 'PL_Krakow': 'PLN', 'UK_London': 'GBP', 'US_Chicago': 'USD',
    'SG_Singapore': 'SGD', 'BR_SaoPaulo': 'BRL', 'FR_Paris': 'EUR', 'JP_Tokyo': 'JPY'
}

customers = [
    {'name': 'Siemens AG', 'segment': 'Enterprise', 'region': 'DE_Berlin'},
    {'name': 'CD Projekt', 'segment': 'Enterprise', 'region': 'PL_Krakow'},
    {'name': 'HSBC Holdings', 'segment': 'Enterprise', 'region': 'UK_London'},
    {'name': 'Boeing Co.', 'segment': 'Enterprise', 'region': 'US_Chicago'},
    {'name': 'DBS Bank', 'segment': 'Enterprise', 'region': 'SG_Singapore'},
    {'name': 'Petrobras', 'segment': 'Enterprise', 'region': 'BR_SaoPaulo'},
    {'name': 'LVMH Group', 'segment': 'Enterprise', 'region': 'FR_Paris'},
    {'name': 'SoftBank Group', 'segment': 'Enterprise', 'region': 'JP_Tokyo'},
    {'name': 'N26 Bank', 'segment': 'SMB', 'region': 'DE_Berlin'},
    {'name': 'Revolut Ltd', 'segment': 'SMB', 'region': 'UK_London'}
]

services = ['SaaS_Subscription', 'Managed_Services', 'Support_Gold']
data_rows = []
start_date = datetime(2025, 1, 1)

for cust in customers:
    entity = cust['region']
    currency = entities[entity]
    base_fee = np.random.randint(8000, 15000) if cust['segment'] == 'Enterprise' else np.random.randint(2000, 5000)
    
    for month_idx in range(24): # 2 years
        current_month = start_date + timedelta(days=30 * month_idx)
        for service in services:
            is_leaking = (current_month.year == 2026 and np.random.random() < 0.15)
            
            # Logic: In 2026, it SHOULD be base_fee * 1.05. If leaking, it stays at base_fee.
            expected = base_fee if current_month.year == 2025 else base_fee * 1.05
            actual = base_fee if is_leaking else expected
            
            data_rows.append({
                'Date': current_month.strftime('%Y-%m-%d'),
                'Customer_Name': cust['name'],
                'Segment': cust['segment'],
                'Entity': entity,
                'Currency': currency,
                'Service_Type': service,
                'BilledAmount': actual,
                'Uptime': np.random.uniform(98.5, 99.9),
                'Invoice_ID': f"INV-{cust['name'][:3].upper()}-{np.random.randint(1000, 9999)}"
            })

pd.DataFrame(data_rows).to_csv('billing_export.csv', index=False)
print("✅ New customer-centric billing_export.csv generated.")