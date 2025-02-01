import streamlit as st
import pandas as pd

def calculate_hra(rent_paid, hra_received, basic_salary):
    annual_rent_paid = rent_paid * 12
    annual_hra_received = hra_received * 12
    annual_basic_salary = basic_salary * 12
    hra_exempt = min(annual_hra_received, annual_rent_paid - (0.1 * annual_basic_salary), 0.5 * annual_basic_salary)
    return max(hra_exempt, 0)

def calculate_tax_old_regime(income, std_deduction=True, hra=0, deductions={}):
    total_deductions = (75000 if std_deduction else 0) + hra
    total_deductions += sum(deductions.values())
    taxable_income = max(income - total_deductions, 0)
    
    tax = 0
    slabs = [(250000, 0.05), (500000, 0.1), (1000000, 0.2)]
    
    for limit, rate in slabs:
        if taxable_income > limit:
            tax += (min(taxable_income, limit * 2) - limit) * rate
    
    if taxable_income > 1000000:
        tax += (taxable_income - 1000000) * 0.3
    
    return tax

def calculate_tax_new_regime(income, std_deduction=True):
    taxable_income = income - (75000 if std_deduction else 0)
    tax = 0
    slabs = [(400000, 0.05), (800000, 0.1), (1200000, 0.15), (1600000, 0.2), (2000000, 0.25)]
    
    for limit, rate in slabs:
        if taxable_income > limit:
            tax += (min(taxable_income, limit * 2) - limit) * rate
    
    if taxable_income > 2400000:
        tax += (taxable_income - 2400000) * 0.3
    
    return tax

def compare_tax_regimes(income, std_deduction, rent_paid, hra_received, basic_salary, deductions):
    hra_exempt = calculate_hra(rent_paid, hra_received, basic_salary)
    tax_old = calculate_tax_old_regime(income, std_deduction, hra_exempt, deductions)
    tax_new = calculate_tax_new_regime(income, std_deduction)
    
    better_option = "Old Regime" if tax_old < tax_new else "New Regime"
    return tax_old, tax_new, better_option

st.set_page_config(page_title="Tax Regime Comparator", layout="wide")
st.title("💰 Tax Regime Comparator: Old vs New")

st.markdown("### Enter Your Details")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Income & HRA Details")
    income = st.number_input("Annual Gross Income (₹)", min_value=0, value=1200000)
    std_deduction = st.radio("Apply Standard Deduction (₹75,000)?", ["Yes", "No"], horizontal=True) == "Yes"
    rent_paid = st.number_input("Monthly Rent Paid (₹)", min_value=0, value=20000)
    hra_received = st.number_input("Monthly HRA Received (₹)", min_value=0, value=12500)
    basic_salary = st.number_input("Monthly Basic Salary (₹)", min_value=0, value=50000)

with col2:
    st.markdown("### Deductions (Old Regime)")
    deductions = {
        "PPF": st.number_input("PPF (₹)", min_value=0, value=50000, step=1000),
        "EPF": st.number_input("EPF (₹)", min_value=0, value=30000, step=1000),
        "NSC": st.number_input("NSC (₹)", min_value=0, value=20000, step=1000),
        "ELSS": st.number_input("ELSS (₹)", min_value=0, value=25000, step=1000),
        "Life Insurance": st.number_input("Life Insurance (₹)", min_value=0, value=15000, step=1000),
        "FD (5-year)": st.number_input("FD (5-year) (₹)", min_value=0, value=20000, step=1000),
        "Tuition Fees": st.number_input("Tuition Fees (₹)", min_value=0, value=50000, step=1000),
        "Home Loan Principal": st.number_input("Home Loan Principal (₹)", min_value=0, value=30000, step=1000),
        "Others": st.number_input("Other 80C Deductions (₹)", min_value=0, value=10000, step=1000),
    }

st.markdown("---")

if st.button("Compare Tax Regimes"):
    tax_old, tax_new, better_option = compare_tax_regimes(income, std_deduction, rent_paid, hra_received, basic_salary, deductions)
    
    st.markdown("### 📊 Comparison Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Old Regime Tax", value=f"₹{tax_old:,.2f}")
    
    with col2:
        st.metric(label="New Regime Tax", value=f"₹{tax_new:,.2f}")
    
    with col3:
        st.success(f"🎯 **Better Option: {better_option}**")
