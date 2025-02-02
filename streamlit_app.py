import streamlit as st
import pandas as pd
import base64
import google.generativeai as genai
import os

# Function to create the Indian flag background CSS
def add_bg_with_transparency():
    return """
    <style>
    .stApp {
        background-image: linear-gradient(
            rgba(255, 153, 51, 0.2),
            rgba(255, 255, 255, 0.2),
            rgba(19, 136, 8, 0.2)
        );
        background-size: cover;
    }
    
    .creator-text {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 12px;
        color: rgba(0, 0, 0, 0.5);
    }
    </style>
    """

def calculate_hra(rent_paid, hra_received, basic_salary):
    annual_rent_paid = rent_paid * 12
    annual_hra_received = hra_received * 12
    annual_basic_salary = basic_salary * 12
    hra_exempt = min(annual_hra_received, annual_rent_paid - (0.1 * annual_basic_salary), 0.5 * annual_basic_salary)
    return max(hra_exempt, 0)

def calculate_tax_old_regime(income, std_deduction=True, hra=0, deductions={}):
    total_deductions = (75000 if std_deduction else 0) + hra
    
    # Calculate total deductions excluding 80C (which is already capped)
    total_80c = min(sum(value for key, value in deductions.items() if key.startswith("80C_")), 150000)
    
    # Apply limits to other deductions
    limited_deductions = {
        "80D": min(deductions.get("80D", 0), 25000),
        "80CCD(1B)": min(deductions.get("80CCD(1B)", 0), 50000),
        "80TTA/80TTB": min(deductions.get("80TTA/80TTB", 0), 10000),
        "24(b)": min(deductions.get("24(b)", 0), 200000),
        "80E": deductions.get("80E", 0)  # No limit for education loan interest
    }
    
    total_deductions += sum(limited_deductions.values()) + total_80c
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
    return tax_old, tax_new, better_option, hra_exempt

def get_tax_advice(income, hra_exempt, deductions, tax_old, tax_new):
    # Define section limits
    limits = {
        "80C": 150000,
        "80D": 25000,
        "80CCD(1B)": 50000,
        "80TTA/80TTB": 10000,
        "24(b)": 200000
    }
    
    total_80c = min(sum(value for key, value in deductions.items() if key.startswith("80C_")), limits["80C"])
    
    advice = []
    
    # Check each section for remaining deduction potential
    if total_80c < limits["80C"]:
        remaining_80c = limits["80C"] - total_80c
        advice.append(f"You can save up to ₹{remaining_80c:,.2f} more under Section 80C.")
    
    if deductions.get("80D", 0) < limits["80D"]:
        remaining_80d = limits["80D"] - deductions.get("80D", 0)
        advice.append(f"You can claim up to ₹{remaining_80d:,.2f} more under Section 80D for health insurance.")
    
    if deductions.get("80CCD(1B)", 0) < limits["80CCD(1B)"]:
        remaining_nps = limits["80CCD(1B)"] - deductions.get("80CCD(1B)", 0)
        advice.append(f"You can invest up to ₹{remaining_nps:,.2f} more in NPS under Section 80CCD(1B).")
    
    if deductions.get("24(b)", 0) < limits["24(b)"]:
        remaining_home_loan = limits["24(b)"] - deductions.get("24(b)", 0)
        advice.append(f"You can claim up to ₹{remaining_home_loan:,.2f} more in home loan interest under Section 24(b).")
    
    if not advice:
        advice.append("You are utilizing your deductions well. Consider the regime with lower tax liability.")
    
    advice_text = "\n".join(advice)
    return f"{advice_text}\n\nIf you would like to have me look at your investments and taxes, contact me at https://topmate.io/ishaankhurana"

def get_gemini_advice(income, deductions):
    prompt = f"""
    Generate a tax advice summary with the following sections:
    
    **Important Considerations:** Key points about tax planning for someone earning {income} INR.
    
    **Recommendations:** Based on the provided deductions: {deductions}.
    
    **Disclaimer:** A general disclaimer about tax advice.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = model.generate_content(prompt)
    return response.text if response else "Unable to generate advice."

# Apply the background and creator text
st.set_page_config(page_title="Tax Regime Comparator", layout="wide")
st.markdown(add_bg_with_transparency(), unsafe_allow_html=True)
st.markdown('<div class="creator-text">Made by Shade Slayer</div>', unsafe_allow_html=True)

st.title("💰 Tax Regime Comparator: Old vs New")

st.markdown("### Enter Your Details")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("### Income & HRA Details")
    income = st.number_input("Annual Gross Income (₹)", min_value=0, value=1200000)
    std_deduction = st.radio("Apply Standard Deduction (₹75,000)?", ["Yes", "No"], horizontal=True) == "Yes"
    rent_paid = st.number_input("Monthly Rent Paid (₹)", min_value=0, value=20000)
    hra_received = st.number_input("Monthly HRA Received (₹)", min_value=0, value=12500)
    basic_salary = st.number_input("Monthly Basic Salary (₹)", min_value=0, value=50000)

with col2:
    st.markdown("### Deductions (80C)")
    deductions = {
        "80C_ELSS": st.number_input("ELSS Mutual Funds (₹)", min_value=0, value=0, step=1000),
        "80C_EPF": st.number_input("Employee Provident Fund (₹)", min_value=0, value=0, step=1000),
        "80C_PPF": st.number_input("Public Provident Fund (₹)", min_value=0, value=0, step=1000),
        "80C_HLP": st.number_input("Home Loan Principal (₹)", min_value=0, value=0, step=1000),
        "80C_LIC": st.number_input("LIC Premium (₹)", min_value=0, value=0, step=1000),
        "80C_Other": st.number_input("Other 80C Investments (₹)", min_value=0, value=0, step=1000)
    }
    
    # Calculate total 80C deductions (limited to ₹1.5 lakhs)
    total_80c = sum(deductions[k] for k in deductions if k.startswith("80C_"))
    total_80c = min(total_80c, 150000)  # Apply 80C limit of 1.5 lakhs
    
    # Display total 80C deductions
    st.markdown(f"**Total 80C Deductions: ₹{total_80c:,.2f}**")
    if total_80c > 150000:
        st.warning("Note: 80C deductions are capped at ₹1.5 lakhs")

with col3:
    st.markdown("### Other Deductions")
    
    # 80D with limit
    deductions["80D"] = st.number_input("Section 80D (Health Insurance) (₹)", min_value=0, value=0, step=1000, max_value=25000)
    if deductions["80D"] == 25000:
        st.warning("Maximum limit for Section 80D reached")
    
    # 80CCD(1B) with limit
    deductions["80CCD(1B)"] = st.number_input("Section 80CCD(1B) - NPS (₹)", min_value=0, value=0, step=1000, max_value=50000)
    if deductions["80CCD(1B)"] == 50000:
        st.warning("Maximum limit for Section 80CCD(1B) reached")
    
    # 80TTA/80TTB with limit
    deductions["80TTA/80TTB"] = st.number_input("Section 80TTA/80TTB - Interest Income (₹)", min_value=0, value=0, step=1000, max_value=10000)
    if deductions["80TTA/80TTB"] == 10000:
        st.warning("Maximum limit for Section 80TTA/80TTB reached")
    
    # 24(b) with limit
    deductions["24(b)"] = st.number_input("Section 24(b) - Home Loan Interest (₹)", min_value=0, value=0, step=1000, max_value=200000)
    if deductions["24(b)"] == 200000:
        st.warning("Maximum limit for Section 24(b) reached")
    
    # 80E (no limit)
    deductions["80E"] = st.number_input("Section 80E - Education Loan Interest (₹)", min_value=0, value=0, step=1000)

if st.button("Compare Tax Regimes"):
    with st.spinner("Generating tax advice..."):
        tax_old, tax_new, better_option, hra_exempt = compare_tax_regimes(income, std_deduction, rent_paid, hra_received, basic_salary, deductions)
        advice = get_tax_advice(income, hra_exempt, deductions, tax_old, tax_new)
        gemini_advice = get_gemini_advice(income, deductions)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Old Regime Tax", value=f"₹{tax_old:,.2f}")
    with col2:
        st.metric(label="New Regime Tax", value=f"₹{tax_new:,.2f}")
    with col3:
        tax_diff = abs(tax_old - tax_new)
        st.metric(label="Tax Difference", value=f"₹{tax_diff:,.2f}")
    
    st.success(f"🎯 **Better Option: {better_option}**")
    st.info(advice)
    st.markdown(f"### 📌 Additional Insights\n{gemini_advice}")
