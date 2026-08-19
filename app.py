import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Factory Cost Leakage Analyzer", layout="wide")

# -------------------- Helper Functions --------------------
def compute_priority(df_row, full_df):
    impact = df_row['total_leakage']
    impact_score = min(100, (impact / 5000) * 100)
    freq = full_df[(full_df['machine_id'] == df_row['machine_id']) & 
                   (full_df['product_id'] == df_row['product_id'])].shape[0]
    freq_score = min(100, (freq / 50) * 100)
    sub = full_df[(full_df['machine_id'] == df_row['machine_id']) & 
                  (full_df['product_id'] == df_row['product_id']) & 
                  (full_df['date'] >= df_row['date'] - pd.Timedelta(days=90))]
    if len(sub) > 2:
        x = np.arange(len(sub)).reshape(-1, 1)
        y = sub['total_leakage'].values
        try:
            model = LinearRegression().fit(x, y)
            trend_score = min(100, max(0, model.coef_[0] * 10 + 50))
        except:
            trend_score = 50
    else:
        trend_score = 50
    prevent = 80 if df_row['downtime_reason'] in ['Breakdown', 'Maintenance'] else 50
    priority = (impact_score * 0.4 + freq_score * 0.2 + trend_score * 0.2 + prevent * 0.2)
    return priority

# -------------------- Load Data --------------------
@st.cache_data
def load_data():
    df = pd.read_csv('data/raw_factory_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['expected_material_cost'] = df['standard_material_usage'] * 10
    df['expected_labor_cost'] = df['planned_quantity'] * 2
    df['expected_energy_cost'] = df['planned_quantity'] * 1.5
    df['expected_maintenance_cost'] = df['planned_quantity'] * 0.5
    df['material_leakage'] = (df['material_cost'] - df['expected_material_cost']).clip(lower=0)
    df['labor_leakage'] = (df['overtime_cost'] + (df['actual_quantity'] * 5) - df['expected_labor_cost']).clip(lower=0)
    df['energy_leakage'] = (df['energy_cost'] - df['expected_energy_cost']).clip(lower=0)
    df['maintenance_leakage'] = (df['maintenance_cost'] - df['expected_maintenance_cost']).clip(lower=0)
    df['quality_leakage'] = df['rework_cost'] + (df['rejected_units'] * 5)
    df['downtime_leakage'] = df['downtime_hrs'] * 200
    df['total_leakage'] = (df['material_leakage'] + df['labor_leakage'] +
                           df['energy_leakage'] + df['maintenance_leakage'] +
                           df['quality_leakage'] + df['downtime_leakage'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['priority_score'] = df.apply(lambda row: compute_priority(row, df), axis=1)
    df['priority_level'] = pd.cut(df['priority_score'], bins=[0, 40, 60, 80, 100], labels=['Low', 'Medium', 'High', 'Critical'])
    return df

def load_cascade():
    try:
        cascade = pd.read_csv('data/cascade_impact_output.csv')
        return cascade
    except:
        return None

df = load_data()
cascade = load_cascade()

# -------------------- Sidebar --------------------
st.sidebar.title("🏭 Navigation")
page = st.sidebar.radio("Go to", ["Executive Overview", "Cost Leakage Analysis", "Production & Machine",
                                  "Material & Quality", "Energy & Labor", "Innovation (Cascade)",
                                  "Management Action Center"])

# -------------------- Page 1: Executive Overview --------------------
if page == "Executive Overview":
    st.title("🏭 Factory Cost Leakage – Executive Overview")
    col1, col2, col3, col4 = st.columns(4)
    total_cost = df['total_production_cost'].sum()
    total_leakage = df['total_leakage'].sum()
    leakage_pct = (total_leakage / total_cost) * 100 if total_cost > 0 else 0
    recoverable = df[df['priority_level'].isin(['Critical','High'])]['total_leakage'].sum() * 0.7 + \
                  df[df['priority_level'].isin(['Medium','Low'])]['total_leakage'].sum() * 0.3
    col1.metric("Total Production Cost", f"₹{total_cost:,.0f}")
    col2.metric("Total Leakage", f"₹{total_leakage:,.0f}", f"{leakage_pct:.1f}% of cost")
    col3.metric("Estimated Recoverable Savings", f"₹{recoverable:,.0f}")
    
    st.subheader("🔥 Top 5 Leakage Sources (by ₹)")
    leakage_by_machine = df.groupby('machine_id')['total_leakage'].sum().sort_values(ascending=False).head(5).reset_index()
    fig = px.bar(leakage_by_machine, x='machine_id', y='total_leakage', title="Leakage by Machine")
    st.plotly_chart(fig, width='stretch')
    
    col1, col2 = st.columns(2)
    with col1:
        cat_leak = {
            'Material': df['material_leakage'].sum(),
            'Labor': df['labor_leakage'].sum(),
            'Energy': df['energy_leakage'].sum(),
            'Maintenance': df['maintenance_leakage'].sum(),
            'Quality': df['quality_leakage'].sum(),
            'Downtime': df['downtime_leakage'].sum()
        }
        cat_df = pd.DataFrame(list(cat_leak.items()), columns=['Category', 'Leakage'])
        fig = px.pie(cat_df, values='Leakage', names='Category', title='Leakage by Category')
        st.plotly_chart(fig, width='stretch')
    with col2:
        monthly = df.groupby('month')['total_leakage'].sum().reset_index()
        fig = px.line(monthly, x='month', y='total_leakage', title='Monthly Leakage Trend')
        st.plotly_chart(fig, width='stretch')

# -------------------- Page 2: Cost Leakage Analysis --------------------
elif page == "Cost Leakage Analysis":
    st.title("📊 Cost Leakage Analysis")
    expected_actual = {
        'Material': [df['expected_material_cost'].sum(), df['material_cost'].sum()],
        'Labor': [df['expected_labor_cost'].sum(), df['overtime_cost'].sum() + df['actual_quantity'].sum()*5],
        'Energy': [df['expected_energy_cost'].sum(), df['energy_cost'].sum()],
        'Maintenance': [df['expected_maintenance_cost'].sum(), df['maintenance_cost'].sum()],
    }
    exp_df = pd.DataFrame(expected_actual, index=['Expected', 'Actual']).T.reset_index()
    exp_df.columns = ['Category', 'Expected', 'Actual']
    fig = px.bar(exp_df, x='Category', y=['Expected', 'Actual'], barmode='group', title='Expected vs Actual Cost')
    st.plotly_chart(fig, width='stretch')
    
    col1, col2 = st.columns(2)
    with col1:
        prod_leak = df.groupby('product_id')['total_leakage'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(prod_leak, x='product_id', y='total_leakage', title='Top 10 Products by Leakage')
        st.plotly_chart(fig, width='stretch')
    with col2:
        shift_leak = df.groupby('shift')['total_leakage'].sum().reset_index()
        fig = px.bar(shift_leak, x='shift', y='total_leakage', title='Leakage by Shift')
        st.plotly_chart(fig, width='stretch')
    
    dept_leak = df.groupby('department')['total_leakage'].sum().reset_index()
    fig = px.bar(dept_leak, x='department', y='total_leakage', title='Leakage by Department')
    st.plotly_chart(fig, width='stretch')

# -------------------- Page 3: Production & Machine --------------------
elif page == "Production & Machine":
    st.title("⚙️ Production & Machine Analysis")
    col1, col2 = st.columns(2)
    with col1:
        util = df.groupby('machine_id').agg({'actual_quantity': 'sum', 'planned_quantity': 'sum'})
        util['utilisation'] = util['actual_quantity'] / util['planned_quantity']
        util = util.reset_index()
        fig = px.bar(util, x='machine_id', y='utilisation', title='Machine Utilisation (Actual/Planned)')
        st.plotly_chart(fig, width='stretch')
    with col2:
        downtime_reason = df.groupby('downtime_reason')['downtime_hrs'].sum().reset_index()
        fig = px.pie(downtime_reason, values='downtime_hrs', names='downtime_reason', title='Downtime by Reason')
        st.plotly_chart(fig, width='stretch')
    
    maint = df.groupby('machine_id').agg({'maintenance_cost': 'sum', 'downtime_hrs': 'sum'}).reset_index()
    fig = px.scatter(maint, x='downtime_hrs', y='maintenance_cost', text='machine_id', 
                     title='Maintenance Cost vs Downtime', size='maintenance_cost')
    st.plotly_chart(fig, width='stretch')
    
    df['lost_prod'] = (df['planned_quantity'] - df['actual_quantity']) * 50
    lost_by_machine = df.groupby('machine_id')['lost_prod'].sum().reset_index()
    fig = px.bar(lost_by_machine, x='machine_id', y='lost_prod', title='Lost Production Value (₹)')
    st.plotly_chart(fig, width='stretch')

# -------------------- Page 4: Material & Quality --------------------
elif page == "Material & Quality":
    st.title("🧪 Material & Quality Analysis")
    col1, col2 = st.columns(2)
    with col1:
        mat_var = df.groupby('product_id').agg({'standard_material_usage': 'sum', 'actual_material_usage': 'sum'})
        mat_var['variance'] = mat_var['actual_material_usage'] - mat_var['standard_material_usage']
        mat_var = mat_var.reset_index().sort_values('variance', ascending=False).head(10)
        fig = px.bar(mat_var, x='product_id', y='variance', title='Material Usage Variance (Actual - Standard)')
        st.plotly_chart(fig, width='stretch')
    with col2:
        sup_perf = df.groupby('supplier_id').agg({'material_waste': 'sum', 'rejected_units': 'sum'}).reset_index()
        fig = px.bar(sup_perf, x='supplier_id', y='material_waste', title='Material Waste by Supplier')
        st.plotly_chart(fig, width='stretch')
    
    rej_trend = df.groupby('month')['rejection_rate'].mean().reset_index()
    fig = px.line(rej_trend, x='month', y='rejection_rate', title='Average Rejection Rate Over Time')
    st.plotly_chart(fig, width='stretch')
    
    rework = df.groupby('product_id')['rework_cost'].sum().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(rework, x='product_id', y='rework_cost', title='Rework Cost by Product')
    st.plotly_chart(fig, width='stretch')

# -------------------- Page 5: Energy & Labor --------------------
elif page == "Energy & Labor":
    st.title("⚡ Energy & Labor Analysis")
    col1, col2 = st.columns(2)
    with col1:
        energy = df.groupby('department').agg({'energy_consumption_kwh': 'sum', 'expected_energy_cost': 'sum'})
        energy['expected_kwh'] = energy['expected_energy_cost'] / 10
        energy = energy.reset_index()
        fig = px.bar(energy, x='department', y=['energy_consumption_kwh', 'expected_kwh'], barmode='group',
                     title='Actual vs Expected Energy (kWh)')
        st.plotly_chart(fig, width='stretch')
    with col2:
        ot = df.groupby('shift')['overtime_hours'].sum().reset_index()
        fig = px.bar(ot, x='shift', y='overtime_hours', title='Overtime Hours by Shift')
        st.plotly_chart(fig, width='stretch')
    
    labor_month = df.groupby('month')['overtime_cost'].sum().reset_index()
    fig = px.line(labor_month, x='month', y='overtime_cost', title='Overtime Cost Trend')
    st.plotly_chart(fig, width='stretch')
    
    prod = df.groupby('shift').agg({'actual_quantity': 'sum', 'production_time_hrs': 'sum'})
    prod['units_per_hr'] = prod['actual_quantity'] / prod['production_time_hrs']
    prod = prod.reset_index()
    fig = px.bar(prod, x='shift', y='units_per_hr', title='Productivity (Units per Hour) by Shift')
    st.plotly_chart(fig, width='stretch')

# -------------------- Page 6: Innovation (Cascade) --------------------
elif page == "Innovation (Cascade)":
    st.title("💡 Cascade Loss Intelligence")
    if cascade is not None:
        st.subheader("Top 10 Root Causes by Total Cascade Loss")
        top_cascade = cascade.groupby('machine_id')['total_cascade_loss'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_cascade, x='machine_id', y='total_cascade_loss', 
                     title='Total Cascade Loss (Direct + Indirect)')
        st.plotly_chart(fig, width='stretch')
        
        machine_sel = st.selectbox("Select a machine to see breakdown", cascade['machine_id'].unique())
        machine_data = cascade[cascade['machine_id'] == machine_sel]
        total_dir = machine_data['direct_loss'].sum()
        total_indir = machine_data['indirect_loss'].sum()
        st.metric("Direct Loss", f"₹{total_dir:,.0f}")
        st.metric("Indirect Loss", f"₹{total_indir:,.0f}")
        st.metric("Total Cascade Loss", f"₹{total_dir + total_indir:,.0f}")
        
        st.subheader("Cascade Detail Records")
        st.dataframe(machine_data[['production_id', 'direct_loss', 'indirect_loss', 'total_cascade_loss']])
        
        st.subheader("What-If Intervention Simulator")
        reduce_pct = st.slider("Reduce Downtime by (%)", 0, 50, 10)
        downtime_leak = df['downtime_leakage'].sum()
        saving = downtime_leak * (reduce_pct / 100) * 1.3
        st.success(f"Estimated Total Savings (including cascade effects): ₹{saving:,.0f}")
    else:
        st.warning("Cascade data not found. Run analysis first.")

# -------------------- Page 7: Management Action Center --------------------
elif page == "Management Action Center":
    st.title("🎯 Management Action Center")
    
    problem_df = df.groupby(['machine_id', 'product_id', 'shift', 'downtime_reason']).agg({
        'total_leakage': 'sum',
        'priority_score': 'mean',
        'priority_level': lambda x: x.mode()[0] if not x.mode().empty else 'Low'
    }).reset_index()
    problem_df = problem_df.sort_values('total_leakage', ascending=False)
    
    def recommend_action(row):
        if row['downtime_reason'] == 'Breakdown':
            return "Schedule preventive maintenance"
        elif row['downtime_reason'] == 'Setup':
            return "Optimize setup procedure"
        elif row['downtime_reason'] == 'Maintenance':
            return "Review maintenance schedule"
        else:
            return "Investigate root cause"
    problem_df['Recommended Action'] = problem_df.apply(recommend_action, axis=1)
    problem_df['Potential Saving'] = problem_df['total_leakage'] * 0.7
    
    st.subheader("Top 10 Problems with Recommendations")
    st.dataframe(problem_df[['machine_id', 'product_id', 'shift', 'total_leakage', 
                             'priority_level', 'Recommended Action', 'Potential Saving']].head(10))
    
    st.subheader("🔴 If you can fix only 3 problems, fix these:")
    top3 = problem_df.head(3)
    for idx, row in top3.iterrows():
        with st.container():
            st.markdown(f"**{idx+1}. Machine {row['machine_id']} - Product {row['product_id']}**")
            st.write(f"💸 Loss: ₹{row['total_leakage']:,.0f} | Priority: {row['priority_level']}")
            st.write(f"🔧 Action: {row['Recommended Action']} | 💰 Saving: ₹{row['Potential Saving']:,.0f}")
            st.divider()
    
    st.subheader("Priority Matrix (Frequency vs Financial Impact)")
    freq = df.groupby(['machine_id', 'product_id']).size().reset_index(name='frequency')
    impact = df.groupby(['machine_id', 'product_id'])['total_leakage'].sum().reset_index(name='impact')
    matrix = pd.merge(freq, impact, on=['machine_id', 'product_id'])
    fig = px.scatter(matrix, x='frequency', y='impact', hover_data=['machine_id', 'product_id'],
                     title='Frequency vs Financial Impact')
    st.plotly_chart(fig, width='stretch')