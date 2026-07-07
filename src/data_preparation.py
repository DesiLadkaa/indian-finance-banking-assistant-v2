"""
data_preparation.py
====================
Indian Finance & Banking FAQ Assistant — Non-Instruction Dataset Builder
Current as of July 2026 — ITA 2025, Budget 2025, Budget 2026

Steps:
  1. Downloads official government PDFs (Income Tax, GST)
  2. Scrapes official government web pages (RBI, SEBI, Income Tax)
  3. Loads manual domain knowledge paragraphs (July 2026 current)
  4. Cleans, chunks, deduplicates
  5. Saves to non_instruction_data.txt

Run in Colab:
    %run data_preparation.py

Output: non_instruction_data.txt
"""

import re
import time
import requests
import pdfplumber
from pathlib import Path
from bs4 import BeautifulSoup

# ── Output file ────────────────────────────────────────────────────────────────
OUTPUT_FILE = Path("non_instruction_data.txt")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PDF_DIR = Path("raw_pdfs")
PDF_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# PDF SOURCES — Official Indian Government Portals
# ─────────────────────────────────────────────────────────────────────────────
PDF_SOURCES = [
    {
        "name": "Income Tax — New vs Old Regime FAQs",
        "url": "https://www.incometax.gov.in/iec/foportal/sites/default/files/2024-07/New%20vs.%20Old%20Regime%20FAQs.pdf",
        "filename": "incometax_new_vs_old_regime_faqs.pdf",
    },
    {
        "name": "Income Tax — Common ITR Filing FAQs AY 2024-25",
        "url": "https://www.incometax.gov.in/iec/foportal/sites/default/files/2024-06/Common%20ITR%20Filing%20FAQs%20AY%202024-25.pdf",
        "filename": "incometax_itr_filing_faqs.pdf",
    },
    {
        "name": "GST — Welcome Kit for New Businesses",
        "url": "https://tutorial.gst.gov.in/downloads/news/welcome_kit_for_new_taxpyers.pdf",
        "filename": "gst_welcome_kit.pdf",
    },
    {
        "name": "GST — GSTR-9 Annual Return FAQs",
        "url": "https://tutorial.gst.gov.in/downloads/news/faq_on_gstr9_for_24_25_dt_15_oct_25_v6_final.pdf",
        "filename": "gst_gstr9_faqs.pdf",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# WEB SOURCES — Official Indian Government Pages
# ─────────────────────────────────────────────────────────────────────────────
WEB_SOURCES = [
    {
        "name": "Income Tax — Salaried Individuals Guide",
        "url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1",
        "tag": "div", "class": "field-items",
    },
    {
        "name": "Income Tax — Senior Citizens Guide",
        "url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-2",
        "tag": "div", "class": "field-items",
    },
    {
        "name": "Income Tax — NRI Guide",
        "url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-0",
        "tag": "div", "class": "field-items",
    },
    {
        "name": "RBI — Digital Rupee FAQ",
        "url": "https://www.rbi.org.in/commonman/english/scripts/FAQs.aspx?Id=3686",
        "tag": "div", "class": "TableStyle",
    },
    {
        "name": "GST — GSTR-2B FAQ",
        "url": "https://tutorial.gst.gov.in/userguide/returns/FAQ_gstr2b.htm",
        "tag": "body", "class": None,
    },
    {
        "name": "SEBI — Mutual Fund Investor Education",
        "url": "https://investor.sebi.gov.in/educational-material/mutual-fund.html",
        "tag": "div", "class": "content",
    },
    {
        "name": "SEBI — Securities Market Basics",
        "url": "https://investor.sebi.gov.in/educational-material/securities-market.html",
        "tag": "div", "class": "content",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# MANUAL DOMAIN KNOWLEDGE — July 2026 Current Data
# Covers ITA 2025, Budget 2025, Budget 2026 changes
# These 30 paragraphs are the backbone — always accurate, always current
# ─────────────────────────────────────────────────────────────────────────────
MANUAL_PARAGRAPHS = """
Income Tax Act 2025 — Overview and Effective Date: The Income Tax Act 2025 replaced the Income Tax Act 1961 effective from April 1, 2026. It is a comprehensive overhaul of India's direct tax law aimed at simplification, clarity, and ease of compliance. The core tax principles, rates, and slabs remain largely unchanged. The key structural change is the introduction of the Tax Year concept replacing the old Previous Year and Assessment Year terminology. Section numbers have been reorganised — for example, TDS on salary (old Section 192) is now Section 391. All proceedings related to income earned before April 1, 2026 continue under the old Income Tax Act 1961.

Tax Year Concept under Income Tax Act 2025: Under the Income Tax Act 2025, the concept of Tax Year replaces both Previous Year and Assessment Year used in the old 1961 Act. Tax Year is simply the 12-month period from April 1 to March 31 in which income is earned. Under the old system, income earned in FY 2024-25 (Previous Year) was assessed in AY 2025-26, causing confusion with two different year labels. Now, income earned from April 2026 to March 2027 is simply called Tax Year 2026-27. This is a terminology change only and does not affect tax liability, rates, or deductions. Old AY/PY terminology still applies for all filings and proceedings related to periods before April 1, 2026.

Income Tax Slabs under New Tax Regime for FY 2025-26 and FY 2026-27: The new tax regime introduced in Budget 2025 has the following slabs — income up to Rs. 4,00,000 is exempt from tax (basic exemption increased from Rs. 3 lakh to Rs. 4 lakh). Income from Rs. 4,00,001 to Rs. 8,00,000 is taxed at 5%. Income from Rs. 8,00,001 to Rs. 12,00,000 is taxed at 10%. Income from Rs. 12,00,001 to Rs. 16,00,000 is taxed at 15%. Income from Rs. 16,00,001 to Rs. 20,00,000 is taxed at 20%. Income from Rs. 20,00,001 to Rs. 24,00,000 is taxed at 25%. Income above Rs. 24,00,000 is taxed at 30%. These slabs continue unchanged for FY 2026-27 as Budget 2026 made no changes to income tax slabs. Health and education cess of 4% applies on the total tax amount.

Section 87A Rebate under New Tax Regime FY 2025-26: Budget 2025 increased the Section 87A rebate to Rs. 60,000 under the new tax regime for resident individuals with taxable income up to Rs. 12,00,000. This means zero income tax is payable for taxable income up to Rs. 12 lakh under the new regime. For salaried individuals, the Rs. 75,000 standard deduction means the effective zero-tax threshold extends to Rs. 12,75,000 gross salary income. The Section 87A rebate of Rs. 60,000 is NOT available on special rate incomes such as Long Term Capital Gains from equity and Short Term Capital Gains — this was specifically clarified by the Income Tax Department. Under the old tax regime, the Section 87A rebate remains Rs. 12,500 for taxable income up to Rs. 5,00,000.

Income Tax Slabs under Old Tax Regime for FY 2025-26: The old tax regime slabs remain unchanged. For individuals below 60 years, income up to Rs. 2,50,000 is exempt. Income from Rs. 2,50,001 to Rs. 5,00,000 is taxed at 5%. Income from Rs. 5,00,001 to Rs. 10,00,000 is taxed at 20%. Income above Rs. 10,00,000 is taxed at 30%. For senior citizens aged 60 to 79 years, the basic exemption limit is Rs. 3,00,000. For super senior citizens aged 80 years and above, the exemption limit is Rs. 5,00,000. Health and education cess of 4% applies on the total tax. The new tax regime is the default from AY 2024-25 onwards and taxpayers must explicitly opt for the old regime when filing their return.

Standard Deduction for Salaried Employees FY 2025-26: The standard deduction for salaried employees and pensioners under the new tax regime is Rs. 75,000 for FY 2025-26. This was increased from Rs. 50,000 in Budget 2024. Under the old tax regime, the standard deduction remains Rs. 50,000. The standard deduction is automatically allowed without any investment proof, bills, or employer certification. Combined with the Rs. 12,00,000 zero-tax threshold under the new regime via Section 87A rebate, salaried individuals with gross salary up to Rs. 12,75,000 pay zero income tax under the new regime. The Rs. 75,000 standard deduction continues unchanged for FY 2026-27 as Budget 2026 made no changes to this benefit.

Budget 2026 Key Income Tax Changes: Budget 2026 did not change income tax slab rates or the Section 87A rebate. Key changes in Budget 2026 related to income tax — the Income Tax Act 2025 was formally operationalised from April 1, 2026 replacing the 64-year-old 1961 Act. The Assessment Year terminology was discontinued and replaced by Tax Year from FY 2026-27. The revised income tax return can now be filed up to March 31 of the following year with a nominal fee, extended from the earlier December 31 deadline. Form 15G and Form 15H can now be submitted to depositories to reduce TDS on dividends. Securities Transaction Tax on Futures and Options was hiked significantly. TAN is no longer mandatory for TDS on property transactions involving NRIs.

Section 80C Deductions under Old Tax Regime: Section 80C of the Income Tax Act allows deductions up to Rs. 1,50,000 per financial year under the old tax regime. Section 80C is not available under the new tax regime. Eligible investments and payments include Employee Provident Fund contributions, Public Provident Fund contributions, Equity Linked Savings Scheme mutual funds with 3-year lock-in, National Savings Certificate, 5-year tax-saving fixed deposits, life insurance premiums, principal repayment of home loan, tuition fees for up to 2 children, Sukanya Samriddhi Yojana contributions, Senior Citizen Savings Scheme deposits, and ULIP premiums. All these instruments combined qualify within the Rs. 1,50,000 annual limit.

Section 80D Health Insurance Deductions: Section 80D allows deductions for health insurance premiums under the old tax regime only. The maximum deductions are Rs. 25,000 for self, spouse, and dependent children's health insurance. An additional Rs. 25,000 is available for parents below 60 years, making the total Rs. 50,000. If parents are senior citizens aged 60 or above, the additional deduction is Rs. 50,000, making the total Rs. 75,000. If both the taxpayer and parents are senior citizens, the maximum deduction is Rs. 1,00,000. Preventive health check-up expenses up to Rs. 5,000 are included within these limits. The entire health insurance premium including 18% GST qualifies for this deduction.

NPS Employer Contribution under New Tax Regime — Section 80CCD(2): Employer contributions to NPS Tier-1 are deductible under Section 80CCD(2) and this deduction is available under both the old and new tax regimes. Under the new tax regime, the limit was raised to 14% of basic salary in Budget 2024. Under the old tax regime the limit is 10% of basic salary. This is one of the very few deductions available under the new tax regime, making employer NPS contributions extremely tax-efficient. For example, if basic salary is Rs. 1,00,000 per month, employer contribution of Rs. 14,000 per month (Rs. 1,68,000 per year) is fully deductible even under the new regime.

Capital Gains Tax on Equity Mutual Funds — FY 2025-26: Budget 2024 revised capital gains tax rates on equity mutual funds and listed equity shares. Long Term Capital Gains on equity held for more than 12 months are taxed at 12.5% on gains exceeding Rs. 1,25,000 per financial year. The earlier rate was 10% on gains exceeding Rs. 1,00,000. Short Term Capital Gains on equity held for 12 months or less are taxed at 20%, increased from the earlier 15%. The Section 87A rebate of Rs. 60,000 is not available to offset LTCG and STCG tax. Debt mutual funds purchased after April 1, 2023 are taxed at the applicable income tax slab rate regardless of holding period — the earlier benefit of 20% LTCG with indexation was removed.

LTCG on House Property — Budget 2024 Change: Budget 2024 changed the taxation of Long Term Capital Gains from the sale of residential house property. The tax rate is now 12.5% without indexation benefit (previously it was 20% with indexation benefit). Short Term Capital Gains from property held for 24 months or less are taxed at applicable income slab rates. To save LTCG tax, the gain can be reinvested under Section 54 in another residential property within 2 years of sale or constructed within 3 years. The Section 54 exemption is capped at Rs. 10 crore. LTCG can also be invested in specified bonds under Section 54EC up to Rs. 50 lakh within 6 months of sale.

GST Registration Threshold Limits: Businesses with annual aggregate turnover exceeding Rs. 40 lakh for goods suppliers in most states must register for GST. For special category states including all northeastern states, Himachal Pradesh, Uttarakhand, and Jammu and Kashmir, the threshold is Rs. 20 lakh for goods. For service providers, the threshold is Rs. 20 lakh in most states and Rs. 10 lakh in special category states. Certain categories must register regardless of turnover — inter-state suppliers, e-commerce operators, casual taxable persons, non-resident taxable persons, and those under the reverse charge mechanism. Voluntary GST registration is also permitted for businesses below the threshold to claim Input Tax Credit.

GST Tax Rates and Slabs: GST is levied at four main rates. The 5% rate applies to essential items including edible oil, sugar, tea, coffee, spices, footwear below Rs. 1,000, essential medicines, and restaurant food without ITC. The 12% rate applies to processed food, butter, cheese, mobile phones, computers, and business class air travel. The 18% rate covers most manufactured goods and services including FMCG products, health insurance premiums, banking and financial services, and IT services. The 28% rate applies to luxury and demerit goods including passenger vehicles, air conditioners, aerated beverages, tobacco products, and cement. A GST Compensation Cess is additionally levied on luxury cars and tobacco products over and above the 28% rate.

GST Composition Scheme for Small Businesses: The Composition Scheme simplifies GST compliance for small taxpayers with annual turnover up to Rs. 1.5 crore (Rs. 75 lakh for special category states). Tax rates under the scheme are 1% of turnover for traders, 2% for manufacturers, 5% for restaurants not serving alcohol, and 6% for service providers with turnover up to Rs. 50 lakh. Benefits include quarterly GSTR-4 return filing instead of monthly returns and simpler bookkeeping. Restrictions include inability to make inter-state supplies, inability to collect GST from customers, no ITC claims, and inability to supply certain exempt goods under the scheme.

Input Tax Credit under GST: Input Tax Credit allows GST-registered businesses to claim credit for the GST paid on business purchases and reduce their GST liability on sales. Conditions for claiming ITC include having a valid tax invoice, actual receipt of goods or services, supplier having paid the tax and filed returns, and the ITC appearing in the buyer's GSTR-2B statement. ITC is not available on motor vehicles for personal use, goods for personal consumption, food and beverages, health insurance for employees, and construction of immovable property. GSTR-2B is generated on the 14th of every month and is the authoritative document for ITC claims.

RBI Repo Rate and Its Impact on Loans: The Repo Rate is the rate at which RBI lends short-term money to commercial banks and is set by the Monetary Policy Committee in bi-monthly meetings. RBI began cutting the repo rate in 2025 to support economic growth. External Benchmark Lending Rate linked home loans and retail loans are reset at least once every three months following any RBI rate change. This means borrowers with EBLR-linked loans benefit from rate cuts relatively quickly. Loans linked to the older MCLR benchmark take longer to reset. Banks are required to pass on rate cuts to existing EBLR-linked borrowers within the specified reset period without requiring the borrower to make any request.

KYC Requirements and Video KYC: KYC (Know Your Customer) is mandatory for all bank accounts and financial services as per RBI guidelines. Officially Valid Documents accepted for KYC include Aadhaar card, Passport, Voter ID card, Driving License, NREGA Job Card, and Letter from the National Population Register. Video-based Customer Identification Process (V-CIP) is permitted by RBI allowing customers to complete KYC via video call without visiting a branch. Periodic KYC updation is required every 2 years for high-risk customers, every 8 years for medium-risk, and every 10 years for low-risk customers. Aadhaar-based e-KYC is the fastest and most widely used method as it provides instant verification.

DICGC Deposit Insurance: The Deposit Insurance and Credit Guarantee Corporation, a subsidiary of RBI, provides insurance for bank deposits up to Rs. 5,00,000 per depositor per bank covering both principal and interest combined. If a depositor has accounts in multiple banks, each bank's deposits are separately insured up to Rs. 5 lakh. This insurance covers savings accounts, fixed deposits, recurring deposits, and current accounts. All commercial banks, small finance banks, payments banks, regional rural banks, and cooperative banks registered with DICGC are covered. The insurance limit was last revised to Rs. 5 lakh in February 2020. If a bank fails, DICGC pays the insured amount within 90 days.

UPI and UPI Lite — Digital Payment Systems: UPI (Unified Payments Interface) is a real-time payment system by NPCI allowing instant money transfers 24 hours a day including weekends and holidays. The per-transaction limit for UPI is Rs. 1,00,000 for most categories, with higher limits of Rs. 2,00,000 to Rs. 5,00,000 for specific categories like healthcare, capital markets, and tax payments. UPI transactions are free for customers. UPI Lite is designed for small-value transactions up to Rs. 1,000 per transaction with a maximum wallet balance of Rs. 4,000. UPI Lite does not require a PIN for each transaction and processes payments offline, making it faster for daily small purchases. India processes over 10 billion UPI transactions per month.

PPF Interest Rate and Rules: Public Provident Fund interest rate for FY 2025-26 is 7.1% per annum compounded annually. The minimum annual deposit is Rs. 500 and the maximum is Rs. 1,50,000 per financial year. The scheme has a tenure of 15 years extendable in blocks of 5 years. PPF enjoys EEE (Exempt-Exempt-Exempt) tax status — investments qualify for Section 80C deduction under the old tax regime, interest is tax-free, and the maturity amount is tax-free. Partial withdrawals are permitted from the 7th financial year onwards. Loans against PPF balance can be availed between the 3rd and 6th financial year. The PPF account cannot be attached by courts for debt recovery except by income tax authorities.

Sukanya Samriddhi Yojana Rules and Interest Rate: Sukanya Samriddhi Yojana is a government savings scheme for the girl child. The interest rate for FY 2025-26 is 8.2% per annum compounded annually. An account can be opened for a girl child up to age 10 years with a maximum of 2 accounts per family. The minimum annual deposit is Rs. 250 and the maximum is Rs. 1,50,000. The account matures 21 years from the date of opening. SSY enjoys EEE tax status — investments qualify under Section 80C, interest is tax-free, and maturity proceeds are tax-free. Partial withdrawal of up to 50% of the balance is permitted when the girl child turns 18 for higher education expenses. Premature closure is allowed on the girl's marriage after she turns 18.

Senior Citizen Savings Scheme: SCSS is a government-backed savings scheme for individuals above 60 years and for those who have taken Voluntary Retirement Scheme and are above 55 years. The maximum deposit is Rs. 30,00,000. The interest rate for FY 2025-26 is approximately 8.2% per annum paid quarterly, making it one of the highest rates among small savings schemes. The tenure is 5 years extendable by 3 years. SCSS deposits qualify for Section 80C deduction under the old tax regime. Interest is fully taxable and TDS is deducted if annual interest exceeds Rs. 50,000. Premature closure before 2 years attracts a penalty of 1.5% and before maturity after 2 years attracts 1% penalty.

National Pension System Tax Benefits: NPS is a voluntary market-linked retirement savings scheme regulated by PFRDA. Under the old tax regime, employee contributions qualify for Section 80CCD(1) deduction up to 10% of salary within the Rs. 1,50,000 Section 80C limit, and an additional exclusive deduction of Rs. 50,000 under Section 80CCD(1B). Under both old and new tax regimes, employer contributions up to 14% of basic salary qualify under Section 80CCD(2). On maturity at age 60, at least 40% of the corpus must be used to purchase an annuity. The remaining 60% can be withdrawn as a lump sum which is completely tax-free. The monthly pension received from the annuity is taxable at applicable slab rates.

STT Changes in Budget 2026 on Futures and Options: Budget 2026 significantly increased Securities Transaction Tax on Futures and Options trading to curb excessive speculation. The new STT rate on Futures is 0.05% of contract value. The new STT rate on Options is 0.15% on the premium value. This hike was motivated by the fact that India's F&O trading volume had grown to exceed 500 times the country's annual GDP, creating systemic risks. Higher STT increases the breakeven point for F&O traders and makes small-margin and high-frequency trades unprofitable. Long-term investors in delivery-based equity are unaffected as STT on delivery transactions remains 0.1% on both buy and sell sides.

ELSS Mutual Funds for Tax Saving: Equity Linked Savings Scheme funds are diversified equity mutual funds that qualify for Section 80C deduction under the old tax regime. They have the shortest lock-in period of 3 years among all Section 80C instruments. Returns are market-linked and historically in the range of 12% to 15% CAGR over long periods. Gains from ELSS are taxed as Long Term Capital Gains at 12.5% on gains exceeding Rs. 1,25,000 per financial year. ELSS can be invested via lump sum or through a Systematic Investment Plan. In a SIP, each instalment has its own 3-year lock-in from the date of that particular investment. ELSS deduction is available only under the old tax regime and not the new tax regime.

Sovereign Gold Bond Tax Treatment: Sovereign Gold Bonds are issued by RBI on behalf of the Government of India. They pay 2.5% interest per annum on the initial issue price, paid semi-annually. This interest is fully taxable at applicable income slab rates. Capital gains at redemption at the end of the 8-year maturity period are completely exempt from tax for original allottees. If sold on the stock exchange before maturity, Long Term Capital Gains tax of 12.5% applies on bonds held over 12 months. Bonds purchased from the secondary market do not receive the maturity tax exemption — only original allottees who hold until maturity get the full capital gains exemption. New SGB issuances have been suspended by RBI since early 2024.

Direct vs Regular Mutual Fund Plans: Direct Plans are purchased directly from the AMC (Asset Management Company) without any intermediary. They have a lower Total Expense Ratio because no distributor commission is included. Regular Plans include a distributor commission in the expense ratio, typically 0.5% to 1% higher than direct plans. Even a 0.7% difference in expense ratio compounded over 20 years on Rs. 10 lakh investment at 12% CAGR results in approximately Rs. 12-15 lakh additional corpus in the direct plan. Direct plans are available on AMC websites, MF Utility, MFCentral, and zero-commission investment platforms. For informed investors who can select and monitor funds themselves, direct plans are always the preferred choice for maximum long-term returns.

Form 26AS and AIS for ITR Filing: Form 26AS is being replaced by Form 168 under the Income Tax Act 2025 for Tax Year 2026-27 onwards. Form 26AS showed TDS deducted, TCS collected, and taxes paid. The Annual Information Statement (AIS) is a more comprehensive document available on the income tax portal showing all financial transactions — salary, FD interest, dividends, stock transactions, mutual fund transactions, foreign remittances, and real estate purchases. The Taxpayer Information Summary (TIS) is a processed version of AIS showing net values after removing duplicates. Taxpayers must review AIS and TIS before filing their ITR to ensure their return data matches the department's records and to avoid mismatch notices.

Advance Tax Payment Rules: Advance tax must be paid when the estimated tax liability for the year exceeds Rs. 10,000 after considering TDS deductions. The advance tax payment schedule is 15% by June 15, 45% by September 15, 75% by December 15, and 100% by March 15 of the financial year. These due dates and percentages remain the same under the Income Tax Act 2025. Senior citizens above 60 years who do not have income from business or profession are exempt from paying advance tax. Failure to pay advance tax or short payment attracts interest at 1% per month under the relevant sections — 1% per month on shortfall at each instalment date and 1% per month from April 1 on total shortfall.

Crypto and Virtual Digital Asset Taxation: Virtual Digital Assets including cryptocurrency, NFTs, and other digital tokens are taxed at a flat rate of 30% regardless of holding period or investor's income slab. Health and education cess of 4% makes the effective rate 31.2%. No deduction is allowed except the cost of acquisition. Trading fees, mining costs, and other expenses cannot be deducted. Loss from one virtual digital asset cannot be set off against gains from another virtual digital asset or any other income. TDS at 1% is deducted on VDA transfers exceeding Rs. 50,000 per transaction. VDA income must be reported in Schedule VDA in the Income Tax Return and non-reporting attracts severe penalties. Gifted VDA is taxable in the receiver's hands at market value on the date of receipt.
"""


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def clean_text(text):
    text = re.sub(r'[^\x20-\x7E\n\u20B9]', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [l.strip() for l in text.split('\n')]
    lines = [l for l in lines if len(l) >= 40]
    text = '\n\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_text(text, min_len=150, max_len=800):
    raw_chunks = re.split(r'\n\n+', text)
    chunks = []
    buffer = ""
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(buffer) + len(chunk) < max_len:
            buffer = (buffer + " " + chunk).strip() if buffer else chunk
        else:
            if len(buffer) >= min_len:
                chunks.append(buffer)
            buffer = chunk
    if len(buffer) >= min_len:
        chunks.append(buffer)
    return chunks


def download_pdf(url, dest_path):
    if dest_path.exists():
        print(f"  [CACHED] {dest_path.name}")
        return True
    try:
        print(f"  [DOWNLOADING] {dest_path.name} ...")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        dest_path.write_bytes(resp.content)
        print(f"  [OK] {dest_path.name} ({len(resp.content)//1024} KB)")
        return True
    except Exception as e:
        print(f"  [FAILED] {dest_path.name}: {e}")
        return False


def extract_pdf_text(pdf_path):
    try:
        all_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text.append(page_text)
        return "\n\n".join(all_text)
    except Exception as e:
        print(f"  [PDF ERROR] {pdf_path.name}: {e}")
        return ""


def scrape_webpage(url, tag, css_class):
    try:
        print(f"  [SCRAPING] {url}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for noise in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            noise.decompose()
        target = soup.find(tag, class_=css_class) if css_class else soup.find(tag)
        if not target:
            target = soup.find("body") or soup
        text = target.get_text(separator="\n")
        print(f"  [OK] {len(text)} chars")
        return text
    except Exception as e:
        print(f"  [SCRAPE ERROR] {url}: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    all_chunks = []
    source_log = []

    # Step 1 — Manual paragraphs (July 2026 current data)
    print("\n" + "="*55)
    print("STEP 1: Manual domain knowledge (July 2026 current)")
    print("="*55)
    manual_chunks = chunk_text(MANUAL_PARAGRAPHS, min_len=100)
    all_chunks.extend(manual_chunks)
    print(f"  [OK] {len(manual_chunks)} paragraphs")
    source_log.append({"source": "Manual Domain Knowledge (July 2026)", "chunks": len(manual_chunks)})

    # Step 2 — Download PDFs
    print("\n" + "="*55)
    print("STEP 2: Downloading government PDFs")
    print("="*55)
    for pdf_info in PDF_SOURCES:
        print(f"\n[PDF] {pdf_info['name']}")
        dest = PDF_DIR / pdf_info["filename"]
        if download_pdf(pdf_info["url"], dest):
            raw = extract_pdf_text(dest)
            if raw:
                chunks = chunk_text(clean_text(raw))
                all_chunks.extend(chunks)
                print(f"  [EXTRACTED] {len(chunks)} chunks")
                source_log.append({"source": pdf_info["name"], "chunks": len(chunks)})
        time.sleep(1)

    # Step 3 — Scrape web pages
    print("\n" + "="*55)
    print("STEP 3: Scraping government web pages")
    print("="*55)
    for web_info in WEB_SOURCES:
        print(f"\n[WEB] {web_info['name']}")
        raw = scrape_webpage(web_info["url"], web_info["tag"], web_info.get("class"))
        if raw:
            chunks = chunk_text(clean_text(raw))
            all_chunks.extend(chunks)
            print(f"  [EXTRACTED] {len(chunks)} chunks")
            source_log.append({"source": web_info["name"], "chunks": len(chunks)})
        time.sleep(2)

    # Step 4 — Deduplicate
    print("\n" + "="*55)
    print("STEP 4: Deduplicating")
    print("="*55)
    seen = set()
    unique_chunks = []
    for chunk in all_chunks:
        key = chunk[:80].lower().strip()
        if key not in seen:
            seen.add(key)
            unique_chunks.append(chunk)
    print(f"  Before: {len(all_chunks)}  →  After: {len(unique_chunks)} unique chunks")

    # Step 5 — Save
    print("\n" + "="*55)
    print("STEP 5: Saving non_instruction_data.txt")
    print("="*55)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Indian Finance & Banking FAQ Assistant\n")
        f.write("# Non-Instruction Fine-Tuning Dataset\n")
        f.write("# Current as of July 2026 — ITA 2025, Budget 2025, Budget 2026\n")
        f.write("# Sources: incometax.gov.in, gst.gov.in, rbi.org.in, sebi.gov.in\n")
        f.write(f"# Total paragraphs: {len(unique_chunks)}\n")
        f.write("=" * 55 + "\n\n")
        for chunk in unique_chunks:
            f.write(chunk.strip() + "\n\n")
    print(f"  [SAVED] {OUTPUT_FILE}")

    # Summary
    print("\n" + "="*55)
    print("COMPLETE — SUMMARY")
    print("="*55)
    for log in source_log:
        print(f"  {log['chunks']:>4} chunks  |  {log['source']}")
    print(f"\n  TOTAL: {len(unique_chunks)} unique chunks")
    if len(unique_chunks) >= 50:
        print("  [OK] Minimum requirement met (50+ paragraphs)")
    else:
        print(f"  [WARN] Only {len(unique_chunks)} chunks — need 50+")


if __name__ == "__main__":
    main()
