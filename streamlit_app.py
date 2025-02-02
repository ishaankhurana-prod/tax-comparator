import streamlit as st
import pandas as pd
import base64
import google.generativeai as genai
import os
from PIL import Image
import pytesseract
import pdfplumber

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

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def parse_salary_slip(text):
    deductions = {
        "80C_ELSS": 0,
        "80C_EPF": 0,
        "80C_PPF": 0,
        "80C_HLP": 0,
        "80C_LIC": 0,
        "80C_Other": 0,
        "80D": 0,
        "80CCD(1B)": 0,
        "80TTA/80TTB": 0,
        "24(b)": 0,
        "80E": 0
    }
    
    for line in text.split("\n"):
        for key in deductions.keys():
            if key.split("_")[0] in line:
                value = "".join(filter(str.isdigit, line))
                if value:
                    deductions[key] = int(value)
    
    return deductions

def calculate_hra(rent_paid, hra_received, basic_salary):
    annual_rent_paid = rent_paid * 12
    annual_hra_received = hra_received * 12
    annual_basic_salary = basic_salary * 12
    hra_exempt = min(annual_hra_received, annual_rent_paid - (0.1 * annual_basic_salary), 0.5 * annual_basic_salary)
    return max(hra_exempt, 0)

def compare_tax_regimes(income, std_deduction, rent_paid, hra_received, basic_salary, deductions):
    hra_exempt = calculate_hra(rent_paid, hra_received, basic_salary)
    tax_old = calculate_tax_old_regime(income, std_deduction, hra_exempt, deductions)
    tax_new = calculate_tax_new_regime(income, std_deduction)
    better_option = "Old Regime" if tax_old < tax_new else "New Regime"
    return tax_old, tax_new, better_option, hra_exempt

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

st.set_page_config(page_title="Tax Regime Comparator", layout="wide")
st.markdown(add_bg_with_transparency(), unsafe_allow_html=True)
st.markdown('<div class="creator-text">Made by Shade Slayer</div>', unsafe_allow_html=True)
st.title("💰 Tax Regime Comparator: Old vs New")

uploaded_file = st.file_uploader("Upload Salary Slip (Image/PDF)", type=["png", "jpg", "jpeg", "pdf"])

deductions = {}
if uploaded_file is not None:
    if uploaded_file.type in ["image/png", "image/jpeg"]:
        image = Image.open(uploaded_file)
        extracted_text = extract_text_from_image(image)
    else:
        extracted_text = extract_text_from_pdf(uploaded_file)
    
    deductions = parse_salary_slip(extracted_text)
    st.success("Deductions extracted successfully!")

st.markdown("### Enter Your Details")
income = st.number_input("Annual Gross Income (₹)", min_value=0, value=1200000)
std_deduction = st.radio("Apply Standard Deduction (₹75,000)?", ["Yes", "No"], horizontal=True) == "Yes"
rent_paid = st.number_input("Monthly Rent Paid (₹)", min_value=0, value=20000)
hra_received = st.number_input("Monthly HRA Received (₹)", min_value=0, value=12500)
basic_salary = st.number_input("Monthly Basic Salary (₹)", min_value=0, value=50000)

st.markdown("### Deductions (Editable)")
deductions = {
    key: st.number_input(f"{key.replace('_', ' ')} (₹)", min_value=0, value=value, step=1000)
    for key, value in deductions.items()
}

if st.button("Compare Tax Regimes"):
    tax_old, tax_new, better_option, hra_exempt = compare_tax_regimes(income, std_deduction, rent_paid, hra_received, basic_salary, deductions)
    gemini_advice = get_gemini_advice(income, deductions)
    
    st.metric(label="Old Regime Tax", value=f"₹{tax_old:,.2f}")
    st.metric(label="New Regime Tax", value=f"₹{tax_new:,.2f}")
    st.success(f"🎯 **Better Option: {better_option}**")
    st.markdown(f"### 📌 Additional Insights\n{gemini_advice}")
