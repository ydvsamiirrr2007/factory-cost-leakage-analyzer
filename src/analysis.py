import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import warnings
import os

# Correct way to ignore warnings
warnings.filterwarnings('ignore')

# Try to import CascadeEngine – if it fails, define a dummy class (fallback)
try:
    from cascade_engine import CascadeEngine
except ImportError:
    # If not found, try from src.cascade_engine (if running from root)
    try:
        from src.cascade_engine import CascadeEngine
    except ImportError:
        # Define a simple fallback class
        class CascadeEngine:
            def __init__(self, df):
                self.df = df
                self.cascade_impacts = None
            def compute_cascade(self):
                self.cascade_impacts = pd.DataFrame({
                    'production_id': self.df.index,
                    'machine_id': self.df['machine_id'],
                    'product_id': self.df['product_id'],
                    'shift': self.df['shift'],
                    'direct_loss': self.df['total_leakage'],
                    'indirect_loss': 0,
                    'total_cascade_loss': self.df['total_leakage'],
                    'downtime_reason': self.df['downtime_reason']
                })
                return self.cascade_impacts
            def aggregate_cascade(self):
                agg = self.cascade_impacts.groupby('machine_id').agg({
                    'direct_loss': 'sum',
                    'indirect_loss': 'sum',
                    'total_cascade_loss': 'sum'
                }).reset_index()
                agg['cascade_rank'] = agg['total_cascade_loss'].rank(ascending=False)
                return agg.sort_values('total_cascade_loss', ascending=False)

# Ensure folders exist
os.makedirs('data', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# ---- Load data ----
df = pd.read_csv('data/raw_factory_data.csv')
df['date'] = pd.to_datetime(df['date'])

# ---- Feature Engineering ----
df['month'] = df['date'].dt.to_period('M')
df['week'] = df['date'].dt.isocalendar().week
df['day_of_week'] = df['date'].dt.day_name()

# Expected costs (simplified)
df['expected_material_cost'] = df['standard_material_usage'] * 10
df['expected_labor_cost'] = df['planned_quantity'] * 2
df['expected_energy_cost'] = df['planned_quantity'] * 1.5
df['expected_maintenance_cost'] = df['planned_quantity'] * 0.5

# Leakage per category (positive only)
df['material_leakage'] = (df['material_cost'] - df['expected_material_cost']).clip(lower=0)
df['labor_leakage'] = (df['overtime_cost'] + (df['actual_quantity'] * 5) - df['expected_labor_cost']).clip(lower=0)
df['energy_leakage'] = (df['energy_cost'] - df['expected_energy_cost']).clip(lower=0)
df['maintenance_leakage'] = (df['maintenance_cost'] - df['expected_maintenance_cost']).clip(lower=0)
df['quality_leakage'] = df['rework_cost'] + (df['rejected_units'] * 5)
df['downtime_leakage'] = df['downtime_hrs'] * 200

df['total_leakage'] = (df['material_leakage'] + 
                       df['labor_leakage'] +
                       df['energy_leakage'] +
                       df['maintenance_leakage'] +
                       df['quality_leakage'] +
                       df['downtime_leakage'])

# ---- Priority Scoring ----
def compute_priority(row):
    impact = row['total_leakage']
    impact_score = min(100, (impact / 5000) * 100)
    
    freq = df[(df['machine_id'] == row['machine_id']) & 
              (df['product_id'] == row['product_id'])].shape[0]
    freq_score = min(100, (freq / 50) * 100)
    
    sub = df[(df['machine_id'] == row['machine_id']) & 
             (df['product_id'] == row['product_id']) & 
             (df['date'] >= row['date'] - pd.Timedelta(days=90))]
    if len(sub) > 2:
        x = np.arange(len(sub)).reshape(-1,1)
        y = sub['total_leakage'].values
        try:
            model = LinearRegression().fit(x, y)
            trend_score = min(100, max(0, model.coef_[0] * 10 + 50))
        except:
            trend_score = 50
    else:
        trend_score = 50
    
    prevent = 80 if row['downtime_reason'] in ['Breakdown', 'Maintenance'] else 50
    
    priority = (impact_score * 0.4 + freq_score * 0.2 + trend_score * 0.2 + prevent * 0.2)
    return priority

df['priority_score'] = df.apply(compute_priority, axis=1)
df['priority_level'] = pd.cut(df['priority_score'], 
                              bins=[0, 40, 60, 80, 100], 
                              labels=['Low', 'Medium', 'High', 'Critical'])

# ---- Cascade Engine ----
engine = CascadeEngine(df)
cascade_df = engine.compute_cascade()
cascade_agg = engine.aggregate_cascade()

# Save cascade output
cascade_df.to_csv('data/cascade_impact_output.csv', index=False)

# ---- What-If Scenarios ----
scenarios = {
    'Reduce Material Waste by 10%': df['material_waste'].sum() * 0.1 * 10,
    'Reduce Downtime by 15%': df['downtime_hrs'].sum() * 0.15 * 200,
    'Reduce Rejection Rate from 5% to 3%': (df['rejected_units'].sum() * 0.4) * 50,
    'Reduce Overtime by 20%': df['overtime_cost'].sum() * 0.2
}

# ---- Visualisations ----
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

leakage_by_cat = {
    'Material': df['material_leakage'].sum(),
    'Labor': df['labor_leakage'].sum(),
    'Energy': df['energy_leakage'].sum(),
    'Maintenance': df['maintenance_leakage'].sum(),
    'Quality': df['quality_leakage'].sum(),
    'Downtime': df['downtime_leakage'].sum()
}
sns.barplot(x=list(leakage_by_cat.keys()), y=list(leakage_by_cat.values()), ax=axes[0,0])
axes[0,0].set_title('Leakage by Category (₹)')
axes[0,0].tick_params(axis='x', rotation=45)

monthly = df.groupby('month')['total_leakage'].sum().reset_index()
monthly['month'] = monthly['month'].astype(str)
sns.lineplot(data=monthly, x='month', y='total_leakage', ax=axes[0,1])
axes[0,1].set_title('Monthly Leakage Trend')
axes[0,1].tick_params(axis='x', rotation=45)

sns.scatterplot(data=df, x='downtime_hrs', y='total_leakage', hue='shift', ax=axes[1,0])
axes[1,0].set_title('Downtime vs Leakage')

top_products = df.groupby('product_id')['total_leakage'].sum().nlargest(5).reset_index()
sns.barplot(data=top_products, x='product_id', y='total_leakage', ax=axes[1,1])
axes[1,1].set_title('Top 5 Products by Leakage')

plt.tight_layout()
plt.savefig('reports/eda_analysis.png')
print("✅ Analysis plots saved to reports/eda_analysis.png")

# ---- Print summary ----
print("\n=== Leakage by Category (₹) ===")
for k, v in leakage_by_cat.items():
    print(f"{k}: {v:,.2f}")

print("\n=== Priority Summary ===")
print(df['priority_level'].value_counts())

print("\n=== Top 3 Critical Issues ===")
critical = df[df['priority_level'] == 'Critical'].sort_values('priority_score', ascending=False)
print(critical[['machine_id', 'product_id', 'shift', 'total_leakage', 'priority_score']].head(3))

print("\n=== Cascade Aggregate (Top 5 Machines) ===")
print(cascade_agg.head(5))

print("\n=== What-If Scenario Savings (₹) ===")
for name, saving in scenarios.items():
    print(f"{name}: ₹{saving:,.2f}")

print("\n✅ Analysis complete. Outputs saved.")