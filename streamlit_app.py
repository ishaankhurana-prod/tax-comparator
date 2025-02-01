import streamlit as st

def calculate_hra(rent_paid, hra_received, basic_salary):
    annual_rent_paid = rent_paid * 12
    annual_hra_received = hra_received * 12
    annual_basic_salary = basic_salary * 12
    hra_exempt = min(annual_hra_received, annual_rent_paid - (0.1 * annual_basic_salary), 0.5 * annual_basic_salary)
    return max(hra_exempt, 0)

def calculate_tax_old_regime(income, std_deduction, hra, deductions):
    total_deductions = (75000 if std_deduction else 0) + hra + sum(deductions.values())
    taxable_income = max(income - total_deductions, 0)
    
    tax = 0
    slabs = [(250000, 0.05), (500000, 0.1), (1000000, 0.2)]
    
    for limit, rate in slabs:
        if taxable_income > limit:
            tax += (min(taxable_income, limit * 2) - limit) * rate
    
    if taxable_income > 1000000:
        tax += (taxable_income - 1000000) * 0.3
    
    return tax

def calculate_tax_new_regime(income, std_deduction):
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

# Streamlit UI
st.title("Income Tax Regime Comparison")

income = st.number_input("Enter your Annual Gross Income:", min_value=0, value=1200000)

std_deduction = st.radio("Apply Standard Deduction (₹75,000)?", ["Yes", "No"]) == "Yes"

st.subheader("HRA Details")
rent_paid = st.number_input("Monthly Rent Paid (₹)", min_value=0, value=20000)
hra_received = st.number_input("Monthly HRA Received (₹)", min_value=0, value=12500)
basic_salary = st.number_input("Monthly Basic Salary (₹)", min_value=0, value=50000)

st.subheader("Deductions under Old Regime")
deductions = {
    "80C": st.number_input("80C Investments (₹)", min_value=0, value=150000),
    "80D": st.number_input("80D (Health Insurance) (₹)", min_value=0, value=25000),
    "80DDB": st.number_input("80DDB (Medical Treatment) (₹)", min_value=0, value=40000),
    "80G": st.number_input("80G (Donations) (₹)", min_value=0, value=10000),
    "Home Loan Interest": st.number_input("Home Loan Interest (₹)", min_value=0, value=200000),
    "TTA": st.number_input("TTA (Savings Interest) (₹)", min_value=0, value=10000),
}

if st.button("Compare Tax Regimes"):
    tax_old, tax_new, better_option = compare_tax_regimes(income, std_deduction, rent_paid, hra_received, basic_salary, deductions)
    st.subheader("Comparison Results")
    st.write(f"Old Regime Tax: ₹{tax_old:,.2f}")
    st.write(f"New Regime Tax: ₹{tax_new:,.2f}")
    st.success(f"Better Option: **{better_option}**")
