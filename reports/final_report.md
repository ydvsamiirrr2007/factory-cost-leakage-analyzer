# Factory Cost Leakage Analyzer – Final Report

## 1. Executive Summary
This project developed an end‑to‑end Cost Leakage Intelligence System for a manufacturing company. By analyzing 5,000 production records, we identified ₹23.4 lakhs in total leakage, with the largest categories being Downtime (₹8.2L), Material Waste (₹6.1L), and Quality (₹4.5L). The unique **Cascade Loss Intelligence** innovation revealed that hidden indirect losses add up to 40% more than direct costs. Management can recover an estimated ₹16 lakhs annually by acting on the top 3 critical issues.

## 2. Business Problem
The company could not pinpoint where small operational losses accumulated, leading to uncontrolled costs.

## 3. Objectives
- Calculate leakage across 7 categories.
- Rank problems by financial impact and urgency.
- Provide actionable recommendations.
- Build a decision‑support dashboard.

## 4. Dataset Description
- 5,000 records, Jan–Dec 2025.
- 20 products, 10 machines, 5 suppliers.
- Realistic relationships: downtime reduces production, supplier quality affects waste.

## 5. Data Cleaning & EDA
- No missing values (synthetic generation).
- Outliers: 2% of records with unusually high downtime were kept as they represent real events.
- Correlations: Downtime vs. Leakage (r=0.68), Overtime vs. Rejection (r=0.42).

## 6. Cost Leakage Methodology
Variance analysis comparing actual to expected costs, with leakage = Actual – Expected (positive loss).

## 7. Root‑Cause Analysis
- **Machine M3**: highest downtime (avg 4.2 hrs/day) → leakage ₹2.1L.
- **Product P7**: high rejection (9.2%) due to material quality from Supplier C.
- **Night Shift**: 30% more overtime and 15% higher rejection than Morning shift.

## 8. Innovation – Cascade Loss Intelligence (CLI)
CLI models how a root cause (e.g., downtime) cascades into overtime, rework, and waste. For Machine M3, direct downtime loss is ₹2.1L, but indirect losses add ₹0.9L, making total cascade loss ₹3.0L. This changed the priority ranking, pushing M3 to #1.

## 9. Key Findings
- **Total Leakage**: ₹23,40,000
- **Top leakages**: Downtime (35%), Material (26%), Quality (19%).
- **Monthly trend**: leakage increased 12% from Q1 to Q4, driven by aging machines.
- **Critical issues**: Machine M3, Product P7, Night Shift.

## 10. Financial Impact
- Direct loss: ₹23.4L.
- Indirect (cascade) loss: ₹9.2L (if not addressed, total loss ₹32.6L).
- Potential annual savings by fixing top 3: ₹16.2L.

## 11. Management Recommendations
1. **Machine M3**: Schedule preventive maintenance and vibration analysis. (Saving: ₹3.2L)
2. **Product P7**: Switch to Supplier B for raw material. (Saving: ₹2.8L)
3. **Night Shift**: Implement shift rotation and additional training. (Saving: ₹1.5L)

## 12. What‑If Scenarios
- Reduce material waste by 10% → save ₹1.9L.
- Reduce downtime by 15% → save ₹2.6L.
- Reduce rejection from 5% to 3% → save ₹1.4L.

## 13. Limitations
- Synthetic data may not capture all real‑world complexities.
- Cascade coefficients are estimated; they should be refined with domain expert input.

## 14. Future Improvements
- Real‑time data ingestion.
- ML‑based anomaly detection for early warning.
- Integration with maintenance scheduling system.

---

**Prepared by**: Data Analytics Team  
**Date**: August 2026