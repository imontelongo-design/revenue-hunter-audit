import os
import pandas as pd
import json
from dotenv import load_dotenv

# --- 0. SECURITY & KEYS ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    print("✅ Google API Key loaded successfully.")
else:
    print("❌ Error: API Key not found. Check your .env file.")

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.json')
data_path = os.path.join(current_dir, 'billing_export.csv')
export_path = os.path.join(current_dir, 'dashboard_data.json')

# --- 2. LOAD DATA & CONFIG ---
with open(config_path) as f:
    config = json.load(f)

df = pd.read_csv(data_path)
df['Date'] = pd.to_datetime(df['Date'])

# --- 3. FORENSIC AUDIT LOGIC ---
def forensic_audit(row):
    # Determine the "Contractual Truth"
    # 2025 is the base year; 2026 requires a 5% escalation
    if row['Date'].year == 2025:
        expected_local = row['BilledAmount'] 
    else:
        # If it's 2026, we check if the 5% escalation was applied
        # We assume the 'BilledAmount' should have increased by the escalation %
        # Logic: If current billed is same as 2025, we have a leak.
        base_fee_est = row['BilledAmount'] / 1.05 if row['Date'].year == 2026 else row['BilledAmount']
        expected_local = base_fee_est * (1 + config['contract_terms']['annual_escalation'])
    
    # Apply SLA Penalty if Uptime falls below threshold
    if row['Uptime'] < config['contract_terms']['sla_threshold']:
        expected_local *= (1 - config['contract_terms']['sla_penalty'])

    # FX Analysis: Convert everything to EUR for unified reporting
    actual_rate = config['actual_fx_rates'].get(row['Currency'], 1.0)
    budget_rate = config['budget_fx_rates'].get(row['Currency'], 1.0)
    
    billed_eur_actual = row['BilledAmount'] * actual_rate
    expected_eur_budget = expected_local * budget_rate
    
    # Categorization of Variances
    # Price Leak: Difference between what we should have billed vs actual in today's money
    price_leak_eur = (expected_local - row['BilledAmount']) * actual_rate
    
    # FX Impact: The variance caused strictly by currency fluctuations
    fx_impact_eur = (expected_eur_budget - billed_eur_actual) - price_leak_eur
    
    return pd.Series([price_leak_eur, fx_impact_eur])

# Apply calculations to every row
df[['Price_Leak_EUR', 'FX_Impact_EUR']] = df.apply(forensic_audit, axis=1)

# --- 4. PREPARE DASHBOARD DATA (Customer & Segment Level) ---
dashboard_summary = df.groupby(['Customer_Name', 'Entity', 'Segment', 'Currency']).agg({
    'Price_Leak_EUR': 'sum',
    'FX_Impact_EUR': 'sum',
    'BilledAmount': 'sum'
}).reset_index()

# Risk Level Logic (Using absolute value to catch negative leakage)
def get_risk(val):
    if abs(val) > 15000: return 'High'
    if abs(val) > 5000: return 'Medium'
    return 'Low'

dashboard_summary['Risk_Level'] = dashboard_summary['Price_Leak_EUR'].apply(get_risk)

# --- 5. WHAT-IF SCENARIO: 10% DEVALUATION ---
devaluation = config.get('stress_test', {}).get('currency_devaluation_pct', 0.10)

def calculate_stress(row):
    if row['Currency'] == 'EUR': return 0.0
    actual_rate = config['actual_fx_rates'].get(row['Currency'], 1.0)
    # Potential loss if the currency drops another 10%
    return (row['BilledAmount'] * actual_rate) * devaluation

dashboard_summary['Stress_Loss_EUR'] = dashboard_summary.apply(calculate_stress, axis=1)

# --- 6. NARRATIVE GENERATION ---
def generate_insight(row):
    leak = abs(row['Price_Leak_EUR'])
    if leak > 10000:
        return f"CRITICAL: {row['Customer_Name']} ({row['Entity']}) shows €{leak:,.0f} leakage. Escalation clause likely bypassed."
    elif row['FX_Impact_EUR'] < -5000:
        return f"FX RISK: Significant currency headwind for {row['Customer_Name']} in {row['Entity']}."
    else:
        return f"Account stable. Minor variances within threshold for {row['Customer_Name']}."

dashboard_summary['AI_Insight'] = dashboard_summary.apply(generate_insight, axis=1)

# --- 7. EXPORT ---
# Main Dashboard Export
dashboard_summary.to_json(export_path, orient='records', indent=4)
print(f"✅ Dashboard data exported to: {export_path}")

# Detailed Drill-Down Export (The Top 15 worst leaks for the side panel)
drill_down = df[df['Price_Leak_EUR'] > 0].sort_values(by='Price_Leak_EUR', ascending=False).head(15)
drill_down.to_json(os.path.join(current_dir, 'audit_details.json'), orient='records', indent=4)

print("✅ Drill-down details exported to: audit_details.json")