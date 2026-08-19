-- 1. Total Production Cost
SELECT SUM(total_production_cost) AS total_cost FROM fact_production;

-- 2. Monthly Leakage by Category (expected vs actual)
WITH expected AS (
    SELECT 
        DATE_TRUNC('month', date) AS month,
        SUM(planned_quantity * 10) AS expected_material,  -- assume standard rate
        SUM(planned_quantity * 2) AS expected_labor,
        SUM(planned_quantity * 1.5) AS expected_energy,
        SUM(planned_quantity * 0.5) AS expected_maintenance,
        SUM(planned_quantity * 0.1) AS expected_transport
    FROM fact_production
    GROUP BY month
),
actual AS (
    SELECT 
        DATE_TRUNC('month', date) AS month,
        SUM(material_cost) AS actual_material,
        SUM(overtime_cost + actual_quantity * 5) AS actual_labor,
        SUM(energy_cost) AS actual_energy,
        SUM(maintenance_cost) AS actual_maintenance,
        SUM(transportation_cost) AS actual_transport
    FROM fact_production
    GROUP BY month
)
SELECT 
    e.month,
    e.expected_material, a.actual_material, (a.actual_material - e.expected_material) AS material_leakage,
    e.expected_labor, a.actual_labor, (a.actual_labor - e.expected_labor) AS labor_leakage,
    e.expected_energy, a.actual_energy, (a.actual_energy - e.expected_energy) AS energy_leakage
FROM expected e JOIN actual a ON e.month = a.month
ORDER BY month;

-- 3. Top 10 Loss-making Processes (Machines)
SELECT 
    m.machine_id,
    SUM(fp.downtime_hrs * 200) AS downtime_cost,
    SUM(fp.maintenance_cost) AS maintenance_cost,
    SUM(fp.rework_cost) AS rework_cost,
    SUM(fp.material_waste * 15) AS waste_cost,
    SUM(fp.downtime_hrs * 200 + fp.maintenance_cost + fp.rework_cost + fp.material_waste * 15) AS total_leakage
FROM fact_production fp
JOIN dim_machine m ON fp.machine_id = m.machine_id
GROUP BY m.machine_id
ORDER BY total_leakage DESC
LIMIT 10;

-- 4. Supplier Leakage (Material Variance)
SELECT 
    s.supplier_name,
    SUM(fp.standard_material_usage * 10) AS expected_cost,
    SUM(fp.actual_material_usage * 10) AS actual_cost,
    SUM((fp.actual_material_usage - fp.standard_material_usage) * 10) AS leakage,
    AVG(fp.rejection_rate) AS avg_rejection
FROM fact_production fp
JOIN dim_supplier s ON fp.supplier_id = s.supplier_id
GROUP BY s.supplier_name
ORDER BY leakage DESC;

-- 5. Shift Performance
SELECT 
    shift,
    AVG(actual_quantity / planned_quantity) AS efficiency,
    SUM(overtime_cost) AS total_overtime,
    AVG(rejection_rate) AS avg_rejection,
    SUM(downtime_hrs) AS total_downtime
FROM fact_production
GROUP BY shift
ORDER BY efficiency DESC;

-- 6. Product-wise Rejection & Rework Cost
SELECT 
    p.product_name,
    SUM(fp.rejected_units) AS total_rejected,
    SUM(fp.rework_cost) AS rework_cost,
    AVG(fp.rejection_rate) AS avg_rejection
FROM fact_production fp
JOIN dim_product p ON fp.product_id = p.product_id
GROUP BY p.product_name
ORDER BY rework_cost DESC;

-- 7. Energy Variance by Department
SELECT 
    department,
    SUM(energy_consumption_kwh) AS actual_energy,
    SUM(actual_quantity * 0.8) AS expected_energy,
    SUM(energy_consumption_kwh - actual_quantity * 0.8) AS energy_variance,
    SUM(energy_cost) AS energy_cost
FROM fact_production
GROUP BY department
ORDER BY energy_variance DESC;

-- 8. Overtime Cost Trend (Monthly)
SELECT 
    DATE_TRUNC('month', date) AS month,
    SUM(overtime_hours) AS total_ot_hours,
    SUM(overtime_cost) AS total_ot_cost
FROM fact_production
GROUP BY month
ORDER BY month;

-- 9. Department-wise Total Leakage (using CTE)
WITH leakage_by_dept AS (
    SELECT 
        department,
        SUM(material_cost - standard_material_usage * 10) AS mat_leak,
        SUM(overtime_cost) AS ot_leak,
        SUM(downtime_hrs * 200) AS downtime_leak,
        SUM(rework_cost) AS rework_leak,
        SUM(maintenance_cost) AS maint_leak
    FROM fact_production
    GROUP BY department
)
SELECT 
    department,
    mat_leak + ot_leak + downtime_leak + rework_leak + maint_leak AS total_leakage
FROM leakage_by_dept
ORDER BY total_leakage DESC;

-- 10. Window Function: Moving Average of Leakage (3-month)
WITH monthly_leak AS (
    SELECT 
        DATE_TRUNC('month', date) AS month,
        SUM(total_production_cost - (planned_quantity * 8)) AS leakage
    FROM fact_production
    GROUP BY month
)
SELECT 
    month,
    leakage,
    AVG(leakage) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma_3m
FROM monthly_leak;