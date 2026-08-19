import subprocess
import os
import sys

print("🚀 Starting Factory Cost Leakage Analyzer...\n")

# Ensure we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Run data generator
print("Generating synthetic data...")
subprocess.run([sys.executable, "src/data_generator.py"])

# Run analysis
print("\nRunning analysis & cascade engine...")
subprocess.run([sys.executable, "src/analysis.py"])

print("\n✅ All done. Check the following:")
print("  - data/raw_factory_data.csv")
print("  - data/cascade_impact_output.csv")
print("  - reports/eda_analysis.png")
print("\n📊 Open Power BI and import the two CSV files.")