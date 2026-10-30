"""Campus Energy Audit and Carbon Footprint Reduction
IMPORTANT: dataset is synthetic demonstration data, not actual university meter readings.
Run: pip install pandas numpy matplotlib openpyxl
     python analyze_energy.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "synthetic_smart_meter_data.csv"
EMISSION_FACTOR = 0.70  # illustrative kg CO2e/kWh; replace with approved factor
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
required = ["timestamp", "building", "day_type", "hour", "hvac_kwh", "total_electricity_kwh"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")
if df[required].isna().any().any():
    raise ValueError("Missing values found in required columns; clean and document them first.")
if df.duplicated(["timestamp", "building"]).any():
    raise ValueError("Duplicate timestamp/building records found.")
if (df[["hvac_kwh", "total_electricity_kwh"]] < 0).any().any():
    raise ValueError("Negative energy values found; check meter data.")

df["date"] = df["timestamp"].dt.date
df["is_after_hours"] = ((df["hour"] < 8) | (df["hour"] >= 18) | (df["day_type"] == "Weekend"))
df["hvac_after_hours_kwh"] = df["hvac_kwh"].where(df["is_after_hours"], 0)
total_kwh = float(df["total_electricity_kwh"].sum())
hvac_kwh = float(df["hvac_kwh"].sum())
after_hours_hvac = float(df["hvac_after_hours_kwh"].sum())
baseline_co2 = total_kwh * EMISSION_FACTOR

# Scenario assumptions are illustrative and may overlap; not verified savings.
scenario_specs = [
    ("Baseline / no changes", 0.00, 0.00, 0.00),
    ("Conservative", 0.25, 0.03, 0.01),
    ("Previous proposed scenario", 0.35, 0.05, 0.025),
    ("Enhanced target scenario (test only)", 0.53, 0.05, 0.025),
]
rows = []
for name, after_rate, setpoint_rate, maintenance_rate in scenario_specs:
    savings = after_hours_hvac * after_rate + hvac_kwh * setpoint_rate + hvac_kwh * maintenance_rate
    reduction_pct = 100 * savings / total_kwh
    rows.append({
        "Scenario": name,
        "After-hours HVAC reduction assumption (%)": after_rate * 100,
        "Setpoint-related HVAC savings assumption (%)": setpoint_rate * 100,
        "Maintenance-related HVAC savings assumption (%)": maintenance_rate * 100,
        "Estimated electricity savings (kWh)": savings,
        "Estimated electricity reduction (%)": reduction_pct,
        "Estimated avoided emissions (kg CO2e)": savings * EMISSION_FACTOR,
        "Estimated remaining emissions (kg CO2e)": baseline_co2 - savings * EMISSION_FACTOR,
        "Meets 15% target?": "Yes, in model only" if reduction_pct >= 15 else "No",
    })
scenarios = pd.DataFrame(rows)
scenarios.to_csv(OUT / "scenario_comparison.csv", index=False)

print(f"Records: {len(df):,}; buildings: {df['building'].nunique()}")
print(f"Total electricity: {total_kwh:,.2f} kWh")
print(f"HVAC electricity: {hvac_kwh:,.2f} kWh ({hvac_kwh/total_kwh:.1%})")
print(f"After-hours HVAC: {after_hours_hvac:,.2f} kWh")
print(f"Baseline emissions: {baseline_co2:,.2f} kg CO2e (illustrative factor)")
print("\nScenario comparison (assumptions, not measured savings):")
print(scenarios[["Scenario", "Estimated electricity savings (kWh)", "Estimated electricity reduction (%)", "Estimated avoided emissions (kg CO2e)", "Meets 15% target?"]].to_string(index=False, formatters={"Estimated electricity savings (kWh)": "{:,.2f}".format, "Estimated electricity reduction (%)": "{:.2f}%".format, "Estimated avoided emissions (kg CO2e)": "{:,.2f}".format}))

# Save charts (no interactive display required)
daily = df.groupby("date", as_index=False).agg(total_electricity_kwh=("total_electricity_kwh", "sum"), hvac_kwh=("hvac_kwh", "sum"))
ax = daily.plot(x="date", y=["total_electricity_kwh", "hvac_kwh"], figsize=(10, 5))
ax.set_title("Daily Electricity Use (Synthetic Demonstration Data)"); ax.set_ylabel("kWh")
plt.tight_layout(); plt.savefig(OUT / "daily_energy_trend.png", dpi=160); plt.close()
hourly = df.groupby("hour", as_index=False)["hvac_kwh"].mean()
ax = hourly.plot(x="hour", y="hvac_kwh", kind="bar", legend=False, figsize=(9, 4))
ax.set_title("Mean HVAC Consumption by Hour (Synthetic Data)"); ax.set_ylabel("Mean HVAC kWh per building-hour")
plt.tight_layout(); plt.savefig(OUT / "hourly_hvac_profile.png", dpi=160); plt.close()
ax = scenarios[scenarios["Scenario"] != "Baseline / no changes"].plot(x="Scenario", y="Estimated electricity reduction (%)", kind="bar", legend=False, figsize=(10, 5))
ax.axhline(15, linestyle="--", linewidth=1, label="15% target"); ax.set_ylabel("Estimated reduction (%)"); ax.set_title("Scenario Sensitivity — Assumptions Only"); ax.tick_params(axis="x", rotation=15)
plt.tight_layout(); plt.savefig(OUT / "scenario_sensitivity.png", dpi=160); plt.close()
print("\nOutputs saved in ./outputs. Replace simulated data with authorised real data before making real-campus claims.")
