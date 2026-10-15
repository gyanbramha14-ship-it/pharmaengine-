import re
from urllib.parse import quote
import pandas as pd
import requests
import streamlit as st

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

st.set_page_config(page_title="PharmaLens", page_icon="💊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.stApp{background:#f4f7fb}.block-container{max-width:1450px;padding-top:1.5rem}
.hero{padding:30px;border-radius:24px;color:white;background:linear-gradient(135deg,#075985,#0f766e);box-shadow:0 10px 30px rgba(15,23,42,.18);margin-bottom:18px}
.hero h1{color:white;font-size:2.5rem;margin-bottom:6px}.hero p{color:#e0f2fe;font-size:1.08rem;margin:0}
.notice{background:#fff7ed;color:#7c2d12;border-left:6px solid #f97316;border-radius:12px;padding:14px;margin:12px 0}
.success-box{background:#ecfdf5;color:#064e3b;border-left:6px solid #059669;border-radius:12px;padding:14px;margin:12px 0}
div[data-testid="stMetric"]{background:white;border-radius:15px;padding:12px;box-shadow:0 2px 12px rgba(15,23,42,.08)}
div[data-testid="stExpander"]{border-radius:14px}
</style>""", unsafe_allow_html=True)

# ----------------------------
# API database
# ----------------------------
DRUGS = [{'name': 'Paracetamol',
  'class': 'Analgesic / Antipyretic',
  'forms': ['Tablet', 'Capsule', 'Syrup', 'Suspension', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Pain and fever',
  'solubility': 'Moderately soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture and excessive heat'},
 {'name': 'Ibuprofen',
  'class': 'NSAID',
  'forms': ['Tablet', 'Capsule', 'Suspension', 'Gel'],
  'routes': ['Oral', 'Topical'],
  'uses': 'Pain, inflammation and fever',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Aspirin',
  'class': 'NSAID / Antiplatelet',
  'forms': ['Tablet', 'Chewable Tablet'],
  'routes': ['Oral'],
  'uses': 'Pain, fever and antiplatelet therapy',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Moisture sensitive; hydrolysis may occur'},
 {'name': 'Naproxen',
  'class': 'NSAID',
  'forms': ['Tablet', 'Capsule', 'Suspension'],
  'routes': ['Oral'],
  'uses': 'Pain and inflammation',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Diclofenac',
  'class': 'NSAID',
  'forms': ['Tablet', 'Capsule', 'Gel', 'Injection', 'Suppository'],
  'routes': ['Oral', 'Topical', 'Intramuscular', 'Rectal'],
  'uses': 'Pain and inflammation',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Ketoprofen',
  'class': 'NSAID',
  'forms': ['Capsule', 'Tablet', 'Gel'],
  'routes': ['Oral', 'Topical'],
  'uses': 'Pain and inflammation',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Amoxicillin',
  'class': 'Penicillin Antibiotic',
  'forms': ['Tablet', 'Capsule', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture and excessive heat'},
 {'name': 'Azithromycin',
  'class': 'Macrolide Antibiotic',
  'forms': ['Tablet', 'Capsule', 'Oral Suspension', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Clarithromycin',
  'class': 'Macrolide Antibiotic',
  'forms': ['Tablet', 'Extended-Release Tablet', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Ciprofloxacin',
  'class': 'Fluoroquinolone Antibiotic',
  'forms': ['Tablet', 'Oral Suspension', 'Eye Drops', 'Injection'],
  'routes': ['Oral', 'Ophthalmic', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Levofloxacin',
  'class': 'Fluoroquinolone Antibiotic',
  'forms': ['Tablet', 'Eye Drops', 'Injection'],
  'routes': ['Oral', 'Ophthalmic', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Soluble in acidic conditions',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Moxifloxacin',
  'class': 'Fluoroquinolone Antibiotic',
  'forms': ['Tablet', 'Eye Drops', 'Injection'],
  'routes': ['Oral', 'Ophthalmic', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Doxycycline',
  'class': 'Tetracycline Antibiotic',
  'forms': ['Tablet', 'Capsule'],
  'routes': ['Oral'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Metronidazole',
  'class': 'Antibacterial / Antiprotozoal',
  'forms': ['Tablet', 'Suspension', 'Gel', 'Injection'],
  'routes': ['Oral', 'Topical', 'Intravenous'],
  'uses': 'Anaerobic and protozoal infections',
  'solubility': 'Sparingly soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from light'},
 {'name': 'Tinidazole',
  'class': 'Antiprotozoal',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Protozoal and anaerobic infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture'},
 {'name': 'Metoclopramide',
  'class': 'Antiemetic / Gastroprokinetic',
  'forms': ['Tablet', 'Injection', 'Oral Solution'],
  'routes': ['Oral', 'Intravenous', 'Intramuscular'],
  'uses': 'Nausea and vomiting',
  'solubility': 'Soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light'},
 {'name': 'Loperamide',
  'class': 'Antidiarrheal',
  'forms': ['Capsule', 'Tablet', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Diarrhea',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Lactulose',
  'class': 'Osmotic Laxative',
  'forms': ['Oral Solution', 'Syrup'],
  'routes': ['Oral'],
  'uses': 'Constipation and hepatic encephalopathy',
  'solubility': 'Freely soluble in water',
  'dose_type': 'High volume liquid dose',
  'stability': 'Protect from excessive heat'},
 {'name': 'Metformin',
  'class': 'Biguanide Antidiabetic',
  'forms': ['Tablet', 'Extended-Release Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Freely soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture'},
 {'name': 'Glimepiride',
  'class': 'Sulfonylurea Antidiabetic',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Gliclazide',
  'class': 'Sulfonylurea Antidiabetic',
  'forms': ['Tablet', 'Modified-Release Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Sitagliptin',
  'class': 'DPP-4 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Vildagliptin',
  'class': 'DPP-4 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Dapagliflozin',
  'class': 'SGLT2 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Diabetes and selected cardiovascular or renal conditions',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Empagliflozin',
  'class': 'SGLT2 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Diabetes and selected cardiovascular or renal conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Pioglitazone',
  'class': 'Thiazolidinedione',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Levothyroxine',
  'class': 'Thyroid Hormone',
  'forms': ['Tablet', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Hypothyroidism',
  'solubility': 'Very slightly soluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Sensitive to light and moisture'},
 {'name': 'Amlodipine',
  'class': 'Calcium Channel Blocker',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Hypertension and angina',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Ketoconazole',
  'class': 'Imidazole Antifungal',
  'forms': ['Cream', 'Shampoo', 'Tablet'],
  'routes': ['Topical', 'Oral'],
  'uses': 'Fungal infections',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light'},
 {'name': 'Fluconazole',
  'class': 'Triazole Antifungal',
  'forms': ['Tablet', 'Capsule', 'Oral Suspension', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Fungal infections',
  'solubility': 'Soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Acyclovir',
  'class': 'Antiviral',
  'forms': ['Tablet', 'Cream', 'Ointment', 'Injection'],
  'routes': ['Oral', 'Topical', 'Intravenous'],
  'uses': 'Herpes virus infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from moisture'},
 {'name': 'Oseltamivir',
  'class': 'Antiviral',
  'forms': ['Capsule', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Influenza',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Hydrocortisone',
  'class': 'Corticosteroid',
  'forms': ['Cream', 'Ointment', 'Tablet', 'Injection'],
  'routes': ['Topical', 'Oral', 'Intravenous'],
  'uses': 'Inflammatory and allergic conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light'},
 {'name': 'Betamethasone',
  'class': 'Corticosteroid',
  'forms': ['Cream', 'Ointment', 'Tablet', 'Injection'],
  'routes': ['Topical', 'Oral', 'Intramuscular'],
  'uses': 'Inflammatory and allergic conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Adapalene',
  'class': 'Topical Retinoid',
  'forms': ['Gel', 'Cream'],
  'routes': ['Topical'],
  'uses': 'Acne',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Tretinoin',
  'class': 'Topical Retinoid',
  'forms': ['Cream', 'Gel', 'Lotion'],
  'routes': ['Topical'],
  'uses': 'Acne and selected dermatological conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Povidone Iodine',
  'class': 'Antiseptic',
  'forms': ['Solution', 'Ointment', 'Gargle'],
  'routes': ['Topical', 'Oral cavity'],
  'uses': 'Antisepsis',
  'solubility': 'Soluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Chlorhexidine',
  'class': 'Antiseptic',
  'forms': ['Solution', 'Gel', 'Mouthwash'],
  'routes': ['Topical', 'Oral cavity'],
  'uses': 'Antisepsis and oral hygiene',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Silver Sulfadiazine',
  'class': 'Topical Antimicrobial',
  'forms': ['Cream'],
  'routes': ['Topical'],
  'uses': 'Burn wound infection prevention',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Calamine',
  'class': 'Topical Protective',
  'forms': ['Lotion', 'Cream'],
  'routes': ['Topical'],
  'uses': 'Skin irritation and itching',
  'solubility': 'Insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from contamination'},
 {'name': 'Lidocaine',
  'class': 'Local Anesthetic',
  'forms': ['Gel', 'Cream', 'Injection', 'Spray'],
  'routes': ['Topical', 'Local', 'Intravenous'],
  'uses': 'Local anesthesia',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from light'},
 {'name': 'Bupivacaine',
  'class': 'Local Anesthetic',
  'forms': ['Injection'],
  'routes': ['Local', 'Epidural'],
  'uses': 'Local and regional anesthesia',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Low dose',
  'stability': 'Sterile product; protect from light'},
 {'name': 'Tramadol',
  'class': 'Opioid Analgesic',
  'forms': ['Tablet', 'Capsule', 'Oral Drops', 'Injection'],
  'routes': ['Oral', 'Intravenous', 'Intramuscular'],
  'uses': 'Moderate pain',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Gabapentin',
  'class': 'Anticonvulsant / Neuropathic Pain Agent',
  'forms': ['Capsule', 'Tablet', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Neuropathic pain and seizure disorders',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from moisture'},
 {'name': 'Pregabalin',
  'class': 'Anticonvulsant / Neuropathic Pain Agent',
  'forms': ['Capsule', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Neuropathic pain and seizure disorders',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Ferrous Sulfate',
  'class': 'Hematinic',
  'forms': ['Tablet', 'Capsule', 'Syrup'],
  'routes': ['Oral'],
  'uses': 'Iron deficiency',
  'solubility': 'Soluble depending on hydrate and medium',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture and oxidation'},
 {'name': 'Folic Acid',
  'class': 'Vitamin',
  'forms': ['Tablet', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Folate deficiency',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Calcium Carbonate',
  'class': 'Mineral Supplement / Antacid',
  'forms': ['Tablet', 'Chewable Tablet', 'Suspension'],
  'routes': ['Oral'],
  'uses': 'Calcium supplementation and antacid use',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture'},
 {'name': 'Vitamin D3',
  'class': 'Vitamin',
  'forms': ['Tablet', 'Capsule', 'Oral Drops'],
  'routes': ['Oral'],
  'uses': 'Vitamin D supplementation',
  'solubility': 'Fat soluble',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light and oxidation'},
 {'name': 'Vitamin B12',
  'class': 'Vitamin',
  'forms': ['Tablet', 'Injection', 'Oral Solution'],
  'routes': ['Oral', 'Intramuscular'],
  'uses': 'Vitamin B12 supplementation',
  'solubility': 'Soluble depending on form',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Zinc Sulfate',
  'class': 'Mineral Supplement',
  'forms': ['Tablet', 'Capsule', 'Syrup'],
  'routes': ['Oral'],
  'uses': 'Zinc supplementation',
  'solubility': 'Soluble in water',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Potassium Chloride',
  'class': 'Electrolyte',
  'forms': ['Extended-Release Tablet', 'Oral Solution', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Potassium replacement',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from moisture'},
 {'name': 'Sodium Chloride',
  'class': 'Electrolyte',
  'forms': ['Injection', 'Nasal Solution', 'Tablet'],
  'routes': ['Intravenous', 'Nasal', 'Oral'],
  'uses': 'Electrolyte replacement and irrigation',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from contamination'},
 {'name': 'Insulin Human',
  'class': 'Antidiabetic Hormone',
  'forms': ['Injection', 'Cartridge'],
  'routes': ['Subcutaneous', 'Intravenous'],
  'uses': 'Diabetes',
  'solubility': 'Protein formulation',
  'dose_type': 'Biologic dose',
  'stability': 'Temperature controlled; avoid freezing'},
 {'name': 'Sildenafil',
  'class': 'PDE-5 Inhibitor',
  'forms': ['Tablet', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Selected cardiovascular and sexual health indications',
  'solubility': 'Slightly soluble depending on salt form',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Tamsulosin',
  'class': 'Alpha-1 Adrenergic Blocker',
  'forms': ['Modified-Release Capsule'],
  'routes': ['Oral'],
  'uses': 'Lower urinary tract symptoms',
  'solubility': 'Slightly soluble depending on salt form',
  'dose_type': 'Very low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Finasteride',
  'class': '5-Alpha Reductase Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Selected prostate and hair-loss indications',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light and moisture'}]

EXCIPIENTS = {'Diluent': ['Microcrystalline cellulose',
             'Lactose monohydrate',
             'Dicalcium phosphate',
             'Mannitol',
             'Calcium carbonate'],
 'Binder': ['Povidone', 'Pregelatinized starch', 'Hydroxypropyl cellulose', 'Hypromellose'],
 'Disintegrant': ['Croscarmellose sodium', 'Crospovidone', 'Sodium starch glycolate'],
 'Lubricant': ['Magnesium stearate', 'Stearic acid', 'Sodium stearyl fumarate'],
 'Glidant': ['Colloidal silicon dioxide', 'Talc'],
 'Suspending agent': ['Sodium carboxymethylcellulose', 'Xanthan gum', 'Methylcellulose'],
 'Preservative': ['Methylparaben', 'Propylparaben', 'Potassium sorbate', 'Sodium benzoate'],
 'Vehicle': ['Purified water', 'Glycerin', 'Propylene glycol', 'Polyethylene glycol'],
 'Sweetener': ['Sucrose', 'Sorbitol', 'Sucralose', 'Saccharin sodium'],
 'Film former': ['Hypromellose', 'Polyvinyl alcohol', 'Cellulose derivatives'],
 'Topical base': ['White soft paraffin', 'Liquid paraffin', 'Carbomer', 'Cetostearyl alcohol'],
 'Sterile vehicle': ['Water for Injection', 'Sodium chloride solution', 'Phosphate buffer']}

PROCESS_DATA = {'Tablet': {'process': ['Dispensing and material verification',
                        'Sifting or milling where justified',
                        'Blending or granulation',
                        'Drying and moisture control where applicable',
                        'Final blending and lubrication',
                        'Compression',
                        'Optional film coating',
                        'Packing and reconciliation'],
            'defects': ['Weight variation from poor powder flow',
                        'Capping or lamination from air entrapment or compression conditions',
                        'Sticking or picking from excess moisture or tooling issues',
                        'Chipping from weak granules or insufficient binding',
                        'Slow dissolution from over-lubrication or excessive hardness',
                        'Content-uniformity failure from segregation'],
            'tests': ['Appearance',
                      'Weight variation',
                      'Hardness',
                      'Friability',
                      'Disintegration',
                      'Dissolution',
                      'Assay',
                      'Content uniformity']},
 'Capsule': {'process': ['Dispensing and sieving',
                         'Powder blending or granulation',
                         'Flow and bulk-density evaluation',
                         'Capsule filling',
                         'Fill-weight checks',
                         'Visual inspection',
                         'Packing and reconciliation'],
             'defects': ['Fill-weight variation',
                         'Poor flow and machine blockage',
                         'Capsule body-cap separation',
                         'Powder leakage',
                         'Content-uniformity failure',
                         'Moisture-related brittleness or softening'],
             'tests': ['Appearance',
                       'Fill-weight variation',
                       'Disintegration',
                       'Dissolution',
                       'Assay',
                       'Content uniformity',
                       'Moisture']},
 'Liquid': {'process': ['Vehicle preparation',
                        'Dissolution or dispersion of ingredients',
                        'pH adjustment where required',
                        'Addition of sweetener, flavor and preservative',
                        'Volume make-up',
                        'Filtration or homogenization where justified',
                        'Filling and packing'],
            'defects': ['Precipitation or crystallization',
                        'Incorrect pH',
                        'Microbial contamination',
                        'Viscosity variation',
                        'Sedimentation',
                        'Fill-volume variation',
                        'Color or flavor instability'],
            'tests': ['Appearance',
                      'pH',
                      'Viscosity',
                      'Specific gravity',
                      'Assay',
                      'Microbial limits',
                      'Fill volume',
                      'Stability']},
 'Suspension': {'process': ['Vehicle preparation',
                            'Wetting and dispersion of API',
                            'Particle-size control',
                            'Addition of suspending agents',
                            'Homogenization',
                            'pH and viscosity adjustment',
                            'Filling and packing'],
                'defects': ['Rapid sedimentation',
                            'Caking and poor redispersibility',
                            'Particle-size growth',
                            'Viscosity drift',
                            'Foaming',
                            'Microbial contamination',
                            'Dose non-uniformity'],
                'tests': ['Appearance',
                          'pH',
                          'Viscosity',
                          'Particle-size distribution',
                          'Sedimentation volume',
                          'Redispersibility',
                          'Assay',
                          'Microbial limits']},
 'Sterile': {'process': ['Raw-material and container verification',
                         'Solution or suspension preparation',
                         'pH and osmolality adjustment',
                         'Sterile filtration where applicable',
                         'Aseptic filling or validated terminal sterilization',
                         'Container closure',
                         'Visual inspection',
                         'Packaging and quarantine release'],
             'defects': ['Sterility failure',
                         'Bacterial endotoxin failure',
                         'Particulate contamination',
                         'pH or osmolality variation',
                         'Fill-volume variation',
                         'Container-closure leakage',
                         'Precipitation or loss of potency'],
             'tests': ['Appearance',
                       'pH',
                       'Assay',
                       'Sterility',
                       'Bacterial endotoxins',
                       'Particulate matter',
                       'Fill volume',
                       'Container-closure integrity']},
 'Topical': {'process': ['Oil-phase or base preparation',
                         'Aqueous-phase preparation where applicable',
                         'API levigation, dissolution or dispersion',
                         'Emulsification or polymer hydration',
                         'Homogenization',
                         'Cooling and de-aeration',
                         'Filling and packing'],
             'defects': ['Phase separation',
                         'Creaming or cracking',
                         'Lumping or grittiness',
                         'Viscosity variation',
                         'Air entrapment',
                         'Microbial contamination',
                         'Non-uniform API distribution'],
             'tests': ['Appearance',
                       'Homogeneity',
                       'pH',
                       'Viscosity',
                       'Spreadability',
                       'Assay',
                       'Microbial limits',
                       'Stability']}}

# ----------------------------
# Generic-product metadata
# ----------------------------
GENERIC_STATUS = {'Paracetamol': ('Generic products widely available',
                 'Small-molecule generic',
                 'Reference/brand status is country-specific.'),
 'Ibuprofen': ('Generic products widely available',
               'Small-molecule generic',
               'Reference/brand status is country-specific.'),
 'Aspirin': ('Generic products widely available',
             'Small-molecule generic',
             'Reference/brand status is country-specific.'),
 'Naproxen': ('Generic products widely available',
              'Small-molecule generic',
              'Reference/brand status is country-specific.'),
 'Diclofenac': ('Generic products widely available',
                'Small-molecule generic',
                'Reference/brand status is country-specific.'),
 'Amoxicillin': ('Generic products widely available',
                 'Small-molecule generic',
                 'Check salt/strength/dosage form.'),
 'Azithromycin': ('Generic products widely available',
                  'Small-molecule generic',
                  'Check salt/strength/dosage form.'),
 'Metformin': ('Generic products widely available',
               'Small-molecule generic',
               'Immediate-release and extended-release are different products.'),
 'Amlodipine': ('Generic products widely available',
                'Small-molecule generic',
                'Salt form/strength should be verified.'),
 'Fluconazole': ('Generic products widely available',
                 'Small-molecule generic',
                 'Check dosage form and strength.'),
 'Insulin Human': ('Biosimilar/biological-product pathway; not conventional small-molecule generic',
                   'Biologic',
                   'Interchangeability/biosimilarity is jurisdiction-specific.')}

STUDY_DATA = {'Paracetamol': {'in_vitro': [['Dissolution',
                               'Dissolution medium, pH, apparatus, rpm, sampling times, % drug released'],
                              ['Assay / content',
                               'Assay %, content uniformity, analytical method, calibration range'],
                              ['Drug-excipient compatibility',
                               'FTIR/DSC/TGA, physical appearance, degradation markers'],
                              ['Stability',
                               'Assay, degradation products, dissolution, moisture, appearance']],
                 'in_vivo': [['Pharmacokinetics',
                              'Cmax, Tmax, AUC, t1/2, kel, relative/absolute bioavailability'],
                             ['Bioequivalence', 'Test/reference AUC and Cmax, geometric mean ratio, 90% CI'],
                             ['Efficacy / pharmacodynamics',
                              'Pain/fever endpoint as applicable to study design'],
                             ['Safety', 'Adverse events, clinical observations, laboratory parameters']]},
 'Ibuprofen': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, time points, % released'],
                            ['Solubility', 'Equilibrium solubility versus pH, temperature, salt/form'],
                            ['Permeability', 'Apparent permeability / transport direction where applicable'],
                            ['Compatibility', 'DSC/FTIR and degradation/interaction assessment']],
               'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2, clearance, volume of distribution'],
                           ['Bioequivalence', 'AUC and Cmax test/reference comparison with 90% CI'],
                           ['Pharmacodynamics', 'Pain/inflammation endpoints where studied'],
                           ['Safety', 'GI and other adverse events, clinical/lab observations']]},
 'Metformin': {'in_vitro': [['Dissolution', 'Multiple pH media, apparatus, rpm, sampling times, % release'],
                            ['Release kinetics',
                             'Zero-order/first-order/Higuchi/Korsmeyer-Peppas fitting where justified'],
                            ['Assay / content uniformity',
                             'Assay %, individual content, acceptance criteria'],
                            ['Compatibility', 'FTIR/DSC and moisture/stability assessment']],
               'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2, renal elimination-related parameters'],
                           ['Bioequivalence', 'AUC and Cmax comparison of test/reference products'],
                           ['Food effect',
                            'AUC/Cmax and Tmax under fed versus fasted conditions where studied'],
                           ['Safety', 'Adverse events and clinical/laboratory observations']]},
 'Amlodipine': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, sampling times, % release'],
                             ['Assay', 'Potency, content uniformity, related substances'],
                             ['Compatibility', 'DSC/FTIR and degradation assessment'],
                             ['Stability',
                              'Assay, impurities, dissolution, appearance under storage conditions']],
                'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2'],
                            ['Bioequivalence', 'AUC/Cmax test-reference ratio and 90% CI'],
                            ['Food effect', 'PK parameters under fed/fasted conditions where studied'],
                            ['Safety', 'Adverse events and clinical/laboratory parameters']]},
 'Amoxicillin': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, time points, % release'],
                              ['Assay', 'Potency, content uniformity, related substances'],
                              ['Stability', 'Assay, degradation products, moisture and dissolution'],
                              ['Antibacterial activity',
                               'MIC/MBC or zone of inhibition when formulation/product study includes '
                               'microbiology']],
                 'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2'],
                             ['Bioequivalence', 'AUC/Cmax test-reference comparison'],
                             ['Antibacterial efficacy',
                              'Microbiological/clinical endpoint according to study design'],
                             ['Safety', 'Adverse events and laboratory parameters']]},
 'Diclofenac': {'in_vitro': [['Dissolution / release',
                              'Medium, pH, apparatus, rpm, sampling times, % release'],
                             ['Topical permeation',
                              'Flux, permeability coefficient, cumulative amount permeated, skin retention'],
                             ['Assay / impurities', 'Assay, related substances, content uniformity'],
                             ['Stability', 'Assay, impurities, dissolution/release, appearance']],
                'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2'],
                            ['Bioequivalence', 'AUC/Cmax comparison where applicable'],
                            ['Pharmacodynamic efficacy',
                             'Pain/inflammation outcome measures according to design'],
                            ['Safety', 'Adverse events and clinical/lab parameters']]},
 'Aspirin': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, sampling times, % release'],
                          ['Hydrolysis / stability',
                           'Aspirin degradation, salicylic acid formation, moisture'],
                          ['Assay', 'Potency, related substances, content uniformity'],
                          ['Compatibility', 'DSC/FTIR and excipient interaction assessment']],
             'in_vivo': [['PK', 'Salicylate/acetylsalicylic acid-related Cmax, Tmax, AUC where measured'],
                         ['Pharmacodynamic platelet effect',
                          'Platelet aggregation or thromboxane-related endpoint where studied'],
                         ['Bioequivalence', 'PK/PD comparison according to product and regulatory design'],
                         ['Safety', 'Bleeding/GI and other adverse events as appropriate']]}}


def find_drug(name):
    return next((item for item in DRUGS if item["name"] == name), None)

def clean_text(value):
    if isinstance(value,list): return " ".join(str(x) for x in value)
    return str(value) if value else "Not available"

def get_process_type(form):
    tablet=["Tablet","Delayed-Release Tablet","Chewable Tablet","Extended-Release Tablet","Modified-Release Tablet","Orally Disintegrating Tablet","Sublingual Tablet","Vaginal Tablet","Granules","Lozenge"]
    capsule=["Capsule","Delayed-Release Capsule","Modified-Release Capsule"]
    liquid=["Syrup","Oral Solution","Oral Drops","Nasal Solution","Solution","Mouthwash","Gargle"]
    suspension=["Suspension","Oral Suspension","Nebulizer Suspension"]
    sterile=["Injection","Eye Drops"]
    topical=["Cream","Gel","Ointment","Lotion","Shampoo"]
    if form in tablet:return "Tablet"
    if form in capsule:return "Capsule"
    if form in liquid:return "Liquid"
    if form in suspension:return "Suspension"
    if form in sterile:return "Sterile"
    if form in topical:return "Topical"
    return "Tablet"

def get_daily_med_search_url(name):
    return "https://dailymed.nlm.nih.gov/dailymed/search.cfm?query="+quote(name)

def get_pubmed_search_url(name, study_type=None):
    query=f'"{name}"'
    if study_type=="In vitro": query+=' AND (in vitro OR dissolution OR permeability OR "drug release")'
    if study_type=="In vivo": query+=' AND (in vivo OR pharmacokinetic OR bioavailability OR bioequivalence)'
    return "https://pubmed.ncbi.nlm.nih.gov/?term="+quote(query)

def get_suggestions(drug,form):
    result={}
    tablet=["Tablet","Delayed-Release Tablet","Chewable Tablet","Extended-Release Tablet","Modified-Release Tablet","Orally Disintegrating Tablet","Sublingual Tablet","Vaginal Tablet"]
    capsule=["Capsule","Delayed-Release Capsule","Modified-Release Capsule"]
    liquid=["Syrup","Oral Solution","Suspension","Oral Suspension","Oral Drops","Nasal Solution","Solution","Mouthwash","Gargle"]
    topical=["Cream","Gel","Ointment","Lotion","Shampoo"]; sterile=["Injection","Eye Drops"]
    if form in tablet:
        result["Diluent"]=EXCIPIENTS["Diluent"]; result["Binder"]=EXCIPIENTS["Binder"]; result["Disintegrant"]=EXCIPIENTS["Disintegrant"]; result["Lubricant"]=EXCIPIENTS["Lubricant"]; result["Glidant"]=EXCIPIENTS["Glidant"]
    if form in capsule:
        result["Capsule-fill diluent"]=EXCIPIENTS["Diluent"]; result["Binder or granulation aid"]=EXCIPIENTS["Binder"]; result["Glidant"]=EXCIPIENTS["Glidant"]; result["Lubricant"]=EXCIPIENTS["Lubricant"]
    if form in liquid:
        result["Vehicle"]=EXCIPIENTS["Vehicle"]; result["Preservative"]=EXCIPIENTS["Preservative"]; result["Sweetener"]=EXCIPIENTS["Sweetener"]
    if form in ["Suspension","Oral Suspension"]: result["Suspending agent"]=EXCIPIENTS["Suspending agent"]
    if form in topical: result["Topical base"]=EXCIPIENTS["Topical base"]; result["Preservative"]=EXCIPIENTS["Preservative"]
    if form in sterile: result["Sterile vehicle"]=EXCIPIENTS["Sterile vehicle"]
    if "Practically insoluble" in drug["solubility"]:
        result["Solubility-development topics"]=["Particle-size reduction","Surfactant screening","Cosolvent screening","Salt or pH screening","Solid-dispersion investigation"]
    if "Very low dose" in drug["dose_type"]:
        result["Low-dose control topics"]=["Content uniformity","Geometric dilution","Blend segregation study","Validated assay method"]
    if "High dose" in drug["dose_type"]:
        result["High-dose control topics"]=["Drug-loading capability","Blend uniformity","Powder flow","Dosage-form size"]
    return result

@st.cache_data(ttl=86400,show_spinner=False)
def get_pubchem_data(name):
    props="IUPACName,MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,XLogP,TPSA"
    url="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"+quote(name)+"/property/"+props+"/JSON"
    try:
        r=requests.get(url,timeout=25)
        if r.status_code!=200:return {"Status":"No PubChem record found"}
        x=r.json()["PropertyTable"]["Properties"][0]
        return {"PubChem CID":x.get("CID","Not available"),"IUPAC Name":x.get("IUPACName","Not available"),"Molecular Formula":x.get("MolecularFormula","Not available"),"Molecular Weight":x.get("MolecularWeight","Not available"),"Hydrogen Bond Donors":x.get("HBondDonorCount","Not available"),"Hydrogen Bond Acceptors":x.get("HBondAcceptorCount","Not available"),"Rotatable Bonds":x.get("RotatableBondCount","Not available"),"XLogP":x.get("XLogP","Not available"),"TPSA":x.get("TPSA","Not available"),"Canonical SMILES":x.get("ConnectivitySMILES","Not available"),"Isomeric SMILES":x.get("SMILES","Not available")}
    except Exception as e:return {"Error":str(e)}

@st.cache_data(ttl=86400,show_spinner=False)
def get_openfda_data(name):
    url="https://api.fda.gov/drug/label.json?search=openfda.generic_name:"+quote(name.lower())+"&limit=1"
    try:
        r=requests.get(url,timeout=25)
        if r.status_code!=200:return {"Status":"No matching openFDA label found"}
        x=r.json()["results"][0]; o=x.get("openfda",{})
        return {"Indications":clean_text(x.get("indications_and_usage")),"Warnings":clean_text(x.get("warnings")),"Dosage and Administration":clean_text(x.get("dosage_and_administration")),"Routes":clean_text(x.get("route")),"Manufacturers":clean_text(x.get("manufacturer_name")),"OpenFDA Brand Names":clean_text(o.get("brand_name")),"OpenFDA Generic Names":clean_text(o.get("generic_name")),"Product Type":clean_text(o.get("product_type"))}
    except Exception as e:return {"Error":str(e)}

@st.cache_data(ttl=86400,show_spinner=False)
def get_dailymed_records(name):
    url="https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name="+quote(name)
    try:
        r=requests.get(url,timeout=30)
        if r.status_code!=200:return []
        d=r.json()
        if isinstance(d,list):return d
        if isinstance(d,dict):
            for k in ["data","results","spls"]:
                if isinstance(d.get(k),list):return d[k]
        return []
    except Exception:return []

def normalize_dailymed_records(records):
    rows=[]
    for x in records[:30]:
        sid=x.get("setid") or x.get("setId") or x.get("set_id") or x.get("SETID") or ""
        title=x.get("title") or x.get("drug_name") or x.get("drugName") or x.get("name") or "DailyMed label"
        manufacturer=x.get("labeler") or x.get("manufacturer") or x.get("companyName") or "Not listed"
        url="https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid="+quote(str(sid)) if sid else ""
        rows.append({"Product / label":title,"Manufacturer":manufacturer,"Set ID":sid or "Not available","Label URL":url})
    return rows

@st.cache_data(ttl=86400,show_spinner=False)
def get_dailymed_xml(set_id):
    try:
        r=requests.get("https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/"+quote(str(set_id))+".xml",timeout=35)
        return r.text if r.status_code==200 else ""
    except Exception:return ""

def extract_inactive_ingredients(xml_text):
    if not xml_text or BeautifulSoup is None:return []
    soup=BeautifulSoup(xml_text,"xml"); out=[]
    for e in soup.find_all(string=re.compile("inactive ingredients",re.I)):
        for node in e.parent.find_all_next(["ingredient","ingredientSubstance"],limit=100):
            t=node.get_text(" ",strip=True)
            if t and t not in out:out.append(t)
        if out:break
    return out[:100]


# ----------------------------
# Research-intelligence engine
# ----------------------------

def _first_text(value):
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _pubmed_url(pmid):
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _doi_url(doi):
    return f"https://doi.org/{doi}" if doi else ""


def _strip_xml(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _abstract_from_article(article):
    parts = []
    for node in article.findall(".//Abstract/AbstractText"):
        label = node.attrib.get("Label", "")
        txt = _strip_xml("".join(node.itertext()))
        if txt:
            parts.append(f"{label}: {txt}" if label else txt)
    return " ".join(parts)


def _publication_year(article):
    for path in [
        ".//PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubDate/MedlineDate",
    ]:
        node = article.find(path)
        if node is not None and node.text:
            m = re.search(r"(19|20)\d{2}", node.text)
            if m:
                return m.group(0)
    return "Not stated"


def _authors(article):
    names = []
    for a in article.findall(".//AuthorList/Author"):
        collective = a.findtext("CollectiveName")
        if collective:
            names.append(collective)
            continue
        last = a.findtext("LastName") or ""
        initials = a.findtext("Initials") or ""
        name = (last + " " + initials).strip()
        if name:
            names.append(name)
    return ", ".join(names[:8])


def _article_ids(article):
    pmid = ""
    pmcid = ""
    doi = ""
    for node in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        kind = (node.attrib.get("IdType") or "").lower()
        value = (node.text or "").strip()
        if kind == "pubmed":
            pmid = value
        elif kind == "pmc":
            pmcid = value
        elif kind == "doi":
            doi = value
    if not pmid:
        node = article.find(".//MedlineCitation/PMID")
        if node is not None:
            pmid = (node.text or "").strip()
    return pmid, pmcid, doi


def _classify_study(title, abstract, publication_types):
    text = (title + " " + abstract + " " + " ".join(publication_types)).lower()
    labels = []
    if re.search(r"\bin vitro\b|dissolution|release study|permeation|permeability|cell line|caco-2", text):
        labels.append("In-vitro")
    if re.search(r"\bin vivo\b|rat|rats|mouse|mice|rabbit|dog|animal|human subjects|volunteers|patients", text):
        labels.append("In-vivo")
    if re.search(r"pharmacokinetic|\bpk\b|cmax|tmax|auc|bioavailability", text):
        labels.append("PK / bioavailability")
    if re.search(r"bioequivalence|\bbe study\b|test/reference|90% confidence interval", text):
        labels.append("Bioequivalence")
    if re.search(r"formulation|tablet|capsule|microparticle|nanoparticle|liposome|gel|suspension", text):
        labels.append("Formulation")
    return ", ".join(dict.fromkeys(labels)) or "Other / not classifiable from abstract"


def _sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text or "") if len(x.strip()) > 25]


def _extract_sentences(text, keywords, limit=5):
    out = []
    for sent in _sentences(text):
        low = sent.lower()
        if any(k in low for k in keywords):
            out.append(sent)
    return out[:limit]


def _extract_numeric_mentions(text, limit=25):
    if not text:
        return []
    # Preserve the exact reported value/unit phrase from the abstract. These are
    # observations, not model-derived ranges.
    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:%|mg/mL|mg\/kg|mg|g|µg|ug|ng/mL|ng|\u00b5M|uM|nM|mM|h|hr|hours?|min|minutes?|sec|s|\u00b0C|C|mm|nm|\bday[s]?|week[s]?)\b",
        r"\b(?:Cmax|Tmax|AUC(?:0-[^ ,;]+)?|t1/2|half-life|MIC|MBC|EC50|IC50|Papp|flux)\s*(?:=|of|was|were|:)?\s*\d+(?:\.\d+)?\s*[A-Za-zµ%/0-9.\-]+",
        r"\b\d+(?:\.\d+)?\s*(?:to|[-–])\s*\d+(?:\.\d+)?\s*[A-Za-zµ%/0-9.\-]+",
    ]
    found = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.I):
            val = m.group(0).strip()
            if val not in found:
                found.append(val)
            if len(found) >= limit:
                return found
    return found


def _extract_study_fields(title, abstract):
    text = abstract or ""
    lower = text.lower()
    model = _extract_sentences(text, [
        "healthy volunteer", "healthy volunteers", "patient", "patients", "rat", "rats", "mouse", "mice",
        "rabbit", "rabbits", "dog", "dogs", "caco-2", "cell line", "cells", "animal model", "human"
    ], 4)
    design = _extract_sentences(text, [
        "randomized", "randomised", "crossover", "cross-over", "parallel", "open-label", "double-blind",
        "single-dose", "multiple-dose", "in vitro", "ex vivo", "in vivo", "comparative", "stability study"
    ], 4)
    formulation = _extract_sentences(text, [
        "formulation", "tablet", "capsule", "suspension", "solution", "gel", "cream", "microparticle",
        "nanoparticle", "liposome", "solid dispersion", "granule", "matrix", "release"
    ], 5)
    endpoints = _extract_sentences(text, [
        "dissolution", "release", "permeability", "permeation", "assay", "content uniformity", "cmax", "tmax",
        "auc", "half-life", "bioavailability", "bioequivalence", "mic", "mbc", "stability", "degradation",
        "adverse", "safety", "efficacy", "pain score", "platelet"
    ], 7)
    results = _extract_sentences(text, [
        "significantly", "significant", "increased", "decreased", "higher", "lower", "greater", "reduced",
        "resulted", "showed", "demonstrated", "found", "improved", "similar", "equivalent", "difference"
    ], 8)
    excipient_terms = [
        "lactose", "microcrystalline cellulose", "mannitol", "starch", "povidone", "crospovidone", "croscarmellose",
        "magnesium stearate", "colloidal silicon dioxide", "silicon dioxide", "hypromellose", "HPMC", "PEG",
        "poloxamer", "carbopol", "carbomer", "sodium lauryl sulfate", "sodium starch glycolate", "talc",
        "ethylcellulose", "cellulose acetate", "pva", "pvp", "hydroxypropyl methylcellulose"
    ]
    excipients = [x for x in excipient_terms if x.lower() in lower]
    dose_sentences = _extract_sentences(text, ["dose", "mg", "mg/kg", "administered", "oral", "intravenous", "topical"], 5)
    return {
        "Model / population evidence": " ".join(model) if model else "Not stated in abstract",
        "Study design evidence": " ".join(design) if design else "Not stated in abstract",
        "Formulation / intervention evidence": " ".join(formulation) if formulation else "Not stated in abstract",
        "Endpoints / parameters reported": " ".join(endpoints) if endpoints else "Not stated in abstract",
        "Reported result evidence": " ".join(results) if results else "Not stated in abstract",
        "Dose / route evidence": " ".join(dose_sentences) if dose_sentences else "Not stated in abstract",
        "Excipient/material names detected": ", ".join(excipients) if excipients else "No common excipient term detected in abstract",
        "Numeric findings reported": "; ".join(_extract_numeric_mentions(text)) or "No numeric value detected in abstract",
    }


@st.cache_data(ttl=21600, show_spinner=False)
def pubmed_search_ids(query, retmax=20):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": int(retmax), "sort": "relevance"}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return []
        return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


@st.cache_data(ttl=21600, show_spinner=False)
def pubmed_fetch_records(pmids):
    if not pmids:
        return []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    try:
        r = requests.get(url, params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}, timeout=40)
        if r.status_code != 200:
            return []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        records = []
        for article in root.findall(".//PubmedArticle"):
            title_node = article.find(".//ArticleTitle")
            title = _strip_xml("".join(title_node.itertext())) if title_node is not None else "Untitled"
            abstract = _abstract_from_article(article)
            journal = article.findtext(".//Journal/Title") or "Not stated"
            pmid, pmcid, doi = _article_ids(article)
            pub_types = [x.text.strip() for x in article.findall(".//PublicationTypeList/PublicationType") if x.text]
            year = _publication_year(article)
            authors = _authors(article)
            fields = _extract_study_fields(title, abstract)
            records.append({
                "PMID": pmid,
                "PMCID": pmcid,
                "DOI": doi,
                "Title": title,
                "Journal": journal,
                "Year": year,
                "Authors": authors,
                "Publication types": ", ".join(pub_types),
                "Study type": _classify_study(title, abstract, pub_types),
                "Abstract": abstract or "Abstract not available",
                **fields,
            })
        return records
    except Exception:
        return []


def get_actual_literature(name, max_each=15):
    # Two complementary searches reduce the chance that an in-vitro-only or
    # in-vivo-only paper is missed by one broad query.
    q_invitro = f'"{name}" AND ("in vitro" OR dissolution OR permeability OR permeation OR "drug release" OR formulation)'
    q_invivo = f'"{name}" AND ("in vivo" OR pharmacokinetic OR bioavailability OR bioequivalence OR pharmacodynamic)'
    ids = []
    for q in [q_invitro, q_invivo]:
        for pmid in pubmed_search_ids(q, max_each):
            if pmid not in ids:
                ids.append(pmid)
    return pubmed_fetch_records(ids[: max_each * 2])


@st.cache_data(ttl=86400, show_spinner=False)
def get_pmc_fulltext_sections(pmcid):
    """Fetch open-access PMC full text through NCBI BioC, when available."""
    if not pmcid:
        return {"status": "No PMCID is attached to this record.", "methods": [], "results": [], "other": []}
    pmc = str(pmcid).strip()
    if not pmc.startswith("PMC"):
        pmc = "PMC" + pmc
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmc}/unicode"
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "PharmaLens educational research dashboard"})
        if response.status_code != 200:
            return {"status": f"Open-access full text not available through PMC BioC (HTTP {response.status_code}).", "methods": [], "results": [], "other": []}
        payload = response.json()
        documents = payload if isinstance(payload, list) else payload.get("documents", [])
        passages = []
        for doc in documents:
            for passage in doc.get("passages", []):
                text_value = (passage.get("text") or "").strip()
                infons = passage.get("infons") or {}
                section = str(infons.get("section_type") or infons.get("section") or infons.get("type") or "").lower()
                if text_value:
                    passages.append((section, text_value))
        methods = [t for sec, t in passages if any(k in sec for k in ["methods", "materials", "experimental", "study design", "methodology"]) ]
        results = [t for sec, t in passages if any(k in sec for k in ["results", "discussion", "conclusion"]) ]
        other = [t for sec, t in passages if not any(k in sec for k in ["methods", "materials", "experimental", "study design", "methodology", "results", "discussion", "conclusion"]) ]
        if not methods and not results and not passages:
            return {"status": "PMC returned no parseable full-text passages.", "methods": [], "results": [], "other": []}
        return {"status": "Open-access full text retrieved. Section labels depend on the article's XML structure.", "methods": methods[:100], "results": results[:100], "other": other[:30]}
    except Exception as exc:
        return {"status": f"Could not retrieve full text: {type(exc).__name__}", "methods": [], "results": [], "other": []}


def extract_paper_specific_animal_dose_evidence(fulltext, abstract=""):
    """Extract paper-specific evidence passages without inventing missing values."""
    methods = fulltext.get("methods", []) if isinstance(fulltext, dict) else []
    results = fulltext.get("results", []) if isinstance(fulltext, dict) else []
    other = fulltext.get("other", []) if isinstance(fulltext, dict) else []

    patterns = {
        "Actual animal / species / strain / sex / age / weight": re.compile(
            r"\b(rat|rats|mouse|mice|rabbit|rabbits|guinea pigs?|hamsters?|dogs?|monkeys?|"
            r"animals?|wistar|sprague[- ]?dawley|balb/c|c57bl/6|swiss albino|male|female|"
            r"weigh(?:ing|ed|t)?|body weight|weeks old|months old|strain|species)\b", re.I),
        "Actual dose / concentration / units": re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:mg|g|µg|μg|mcg|ng|mmol|µmol|μmol|mg/ml|mg/mL|µg/ml|µg/mL)"
            r"(?:\s*/\s*(?:kg|g|mL|ml|L|day|d|h|hour|dose|animal))?\b|"
            r"\b(dose|doses|concentration|dose-dependent|dose response)\b", re.I),
        "Route / frequency / duration / timing": re.compile(
            r"\b(oral|orally|intraperitoneal|intravenous|subcutaneous|intragastric|intramuscular|"
            r"topical|inhalation|p\.o\.|i\.p\.|i\.v\.|s\.c\.|once daily|twice daily|daily|"
            r"every \d+|for \d+\s*(?:h|hours?|days?|weeks?)|before|after|pretreat|post.?treat|"
            r"administered|injected|route|duration)\b", re.I),
        "Actual groups / controls / sample size": re.compile(
            r"\b(group|groups|control|vehicle|placebo|positive control|standard drug|"
            r"n\s*=\s*\d+|\d+\s*(?:animals|rats|mice|subjects)\s+per group|randomi[sz]ed|"
            r"allocated|each group|per group)\b", re.I),
        "Materials / reagents / formulation / vehicle": re.compile(
            r"\b(reagent|kit|supplier|purchased|vehicle|saline|buffer|solvent|ethanol|"
            r"distilled water|suspension|solution|formulation|excipient|batch|purity|grade)\b", re.I),
        "Equipment / apparatus / assay / endpoint": re.compile(
            r"\b(assay|apparatus|instrument|plate reader|spectrophotometer|chromatograph|"
            r"ELISA|COX.?1|COX.?2|formalin|hot.?plate|tail.?flick|writhing|paw|flinch|"
            r"latency|inhibition|absorbance|measurement|endpoint|temperature|calibrat)\b", re.I),
        "Ethics / housing / acclimatization": re.compile(
            r"\b(ethic|IACUC|CPCSEA|institutional animal|approval|approved protocol|housing|"
            r"acclimat|light.?dark|food and water|ad libitum)\b", re.I),
        "Statistical methods / significance": re.compile(
            r"\b(mean\s*[±+/-]|SEM|SD\b|standard error|ANOVA|t.?test|p\s*[<=>]\s*0?\.\d+|"
            r"statistical|significant|confidence interval|replicate)\b", re.I),
        "Actual results / numerical outcomes": re.compile(
            r"\b(dose|mg/kg|µg|μg|analges|inhibit|significant|reduced|increased|decreased|"
            r"compared with|versus|%|percent|p\s*[<=>]\s*0?\.\d+|mean|SEM|SD)\b", re.I),
    }

    def clean_unique(paragraphs):
        out = []
        for para in paragraphs:
            value = re.sub(r"\s+", " ", str(para)).strip()
            if value and value not in out:
                out.append(value)
        return out

    clean_methods = clean_unique(methods)
    clean_results = clean_unique(results)
    clean_other = clean_unique(other)
    all_paragraphs = clean_methods + clean_results + clean_other
    extracted = {}
    for label, pattern in patterns.items():
        pool = clean_results if label == "Actual results / numerical outcomes" else clean_methods
        hits = [para for para in pool if pattern.search(para)]
        if not hits:
            hits = [para for para in clean_other if pattern.search(para)]
        extracted[label] = hits[:35]

    # Preserve the earlier keys so the rest of the app remains compatible.
    extracted["animal_details"] = extracted["Actual animal / species / strain / sex / age / weight"]
    extracted["dose_details"] = list(dict.fromkeys(
        extracted["Actual dose / concentration / units"] +
        extracted["Route / frequency / duration / timing"]
    ))
    extracted["result_details"] = extracted["Actual results / numerical outcomes"]

    # Specific, user-facing mentions requested for animal / dose / administration / materials.
    # These are literal mentions from retrieved paper passages, not inferred experimental values.
    source_text = " ".join(all_paragraphs)
    if not source_text.strip():
        source_text = str(abstract or "")
    mention_patterns = {
        "Animal mentions (mouse / rat / pig etc.)": re.compile(
            r"\b(?:mice|mouse|rats?|pigs?|swine|porcine|rabbits?|guinea pigs?|hamsters?|dogs?|monkeys?)\b", re.I),
        "Dose values with units": re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:mg|g|µg|μg|mcg|ng|mmol|µmol|μmol)(?:\s*/\s*(?:kg|g|mL|ml|L|day|d|h|hour|dose|animal))?\b", re.I),
        "Possible dose levels (25 / 50 / 100 etc.)": re.compile(
            r"\b(?:dose|doses|dosage|treated at|received|administered|concentration|group)\b[^.;]{0,100}\b\d+(?:\.\d+)?(?:\s*[,/]\s*\d+(?:\.\d+)?){0,5}", re.I),
        "Administration / route wording": re.compile(
            r"\b(?:orally|oral|intravenous|intraperitoneal|subcutaneous|intramuscular|intragastric|topical|intranasal|inhalation|gavage|injected|administered|instilled|infused|\w+\s+route)\b[^.;]{0,100}", re.I),
        "Anatomical site wording (e.g. neck / pelvic region)": re.compile(
            r"\b[^.;]{0,70}\b(?:pelvi[sc]|pelvic region|neck|cervical region)\b[^.;]{0,70}", re.I),
        "Solution / vehicle mentions (saline / Ringer's etc.)": re.compile(
            r"\b(?:normal saline|saline solution|saline|ringer(?:'s)? solution|ringer solution|lactated ringer(?:'s)?|vehicle|buffer|solvent)\b[^.;]{0,80}", re.I),
    }
    for label, pattern in mention_patterns.items():
        matches = []
        for match in pattern.finditer(source_text):
            value = re.sub(r"\s+", " ", match.group(0)).strip(" ,;:")
            if value and value not in matches:
                matches.append(value)
        extracted[label] = matches[:50]

    extracted["animal_details"] = extracted["Actual animal / species / strain / sex / age / weight"]
    extracted["dose_details"] = list(dict.fromkeys(
        extracted["Actual dose / concentration / units"] +
        extracted["Route / frequency / duration / timing"]
    ))
    extracted["result_details"] = extracted["Actual results / numerical outcomes"]
    extracted["abstract_evidence"] = str(abstract or "")
    return extracted


@st.cache_data(ttl=21600, show_spinner=False)
def get_objective_literature(name, objective, stream, max_results=20):
    """Search PubMed for an API + therapeutic objective + study stream."""
    objective_terms = {
        "Analgesic / pain relief": '(analgesic OR analgesia OR antinociceptive OR pain OR nociception)',
        "Antipyretic / fever reduction": '(antipyretic OR fever OR pyrexia OR hyperthermia OR body temperature)',
        "Anti-inflammatory": '(anti-inflammatory OR inflammation OR prostaglandin OR cyclooxygenase)',
        "Pharmacokinetics / bioavailability": '(pharmacokinetic OR Cmax OR Tmax OR AUC OR bioavailability)',
        "Bioequivalence": '(bioequivalence OR bioequivalent OR "test reference" OR ANDA)',
        "Formulation / dissolution": '(formulation OR dissolution OR "drug release" OR excipient OR stability)',
        "Antimicrobial activity": '(antimicrobial OR antibacterial OR MIC OR MBC OR susceptibility)',
        "General pharmacology / safety": '(pharmacology OR safety OR toxicology OR adverse events)',
    }
    stream_terms = {
        "In-vitro": '("in vitro" OR cell OR cellular OR enzyme OR assay OR dissolution OR permeability OR permeation)',
        "In-vivo / animal": '("in vivo" OR animal OR mice OR mouse OR rats OR rat OR rabbit OR fever OR pain model)',
        "Human / clinical": '(human OR clinical OR patients OR volunteers OR randomized OR crossover)',
        "All study types": '(study OR evaluation OR analysis OR trial OR formulation)',
    }
    q = f'"{name}" AND {objective_terms.get(objective, "(pharmacology OR formulation)")} AND {stream_terms.get(stream, "(study)")}'
    ids = pubmed_search_ids(q, max_results)
    return pubmed_fetch_records(ids)


@st.cache_data(ttl=21600, show_spinner=False)
def get_orange_book_products(name):
    """Return current public FDA Orange Book product records for an API.

    The endpoint is public and does not require an API key for ordinary queries.
    The app treats the result as regulatory evidence, not as a blanket claim
    that every product is generic or therapeutically equivalent.
    """
    url = "https://api.fda.gov/drug/orangebook.json"
    params = {"search": f'products.active_ingredients.name:"{name.upper()}"', "limit": 99}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])
        rows = []
        for rec in results:
            app_no = rec.get("application_number", "")
            app_type = rec.get("application_type", "")
            sponsor = rec.get("sponsor_name", "")
            for product in rec.get("products", []) or []:
                active = product.get("active_ingredients", []) or []
                names = ", ".join(str(x.get("name", "")) for x in active if x.get("name"))
                strengths = ", ".join(str(x.get("strength", "")) for x in active if x.get("strength"))
                rows.append({
                    "Application": app_no,
                    "Application type": app_type,
                    "Sponsor": sponsor,
                    "Ingredient": names or name,
                    "Strength": strengths,
                    "Dosage form": product.get("dosage_form", ""),
                    "Route": ", ".join(product.get("route", []) or []),
                    "Marketing status": product.get("marketing_status", ""),
                    "Product number": product.get("product_number", ""),
                    "Reference drug": product.get("reference_drug", ""),
                    "Reference standard": product.get("reference_standard", ""),
                    "TE code": product.get("te_code", ""),
                })
        return rows
    except Exception:
        return []


def evidence_summary(records):
    if not records:
        return {}
    buckets = {
        "Study types": {},
        "Parameters / endpoints": {},
        "Materials / excipients detected": {},
    }
    for rec in records:
        for label in [x.strip() for x in rec["Study type"].split(",") if x.strip()]:
            buckets["Study types"][label] = buckets["Study types"].get(label, 0) + 1
        for x in rec["Endpoints / parameters reported"].split(" "):
            pass
        # Keep the exact evidence snippets rather than inventing a numerical range.
    return buckets

st.markdown("""<div class="hero"><h1>💊 PharmaLens 100</h1><p>API properties, dosage forms, product-label ingredients, formulation development, manufacturing risk and research-study intelligence.</p></div>""",unsafe_allow_html=True)
st.markdown("""<div class="notice"><b>Research-intelligence notice:</b> PharmaLens retrieves live public literature and regulatory records and extracts evidence from them. It reduces source-hunting, but it does not replace the original publication, official label or regulatory record for final academic/regulatory decisions.</div>""",unsafe_allow_html=True)

st.sidebar.header("🔎 API search")
search_text=st.sidebar.text_input("Search API",placeholder="Example: Paracetamol")
filtered=[d for d in DRUGS if search_text.lower() in d["name"].lower()] if search_text else DRUGS
if not filtered:st.error("API not found. Try another spelling.");st.stop()
selected_name=st.sidebar.selectbox("Select API",[d["name"] for d in filtered])
selected_drug=find_drug(selected_name)
selected_form=st.sidebar.selectbox("Select dosage form",selected_drug["forms"])
st.sidebar.divider();st.sidebar.metric("APIs loaded",len(DRUGS))

m1,m2,m3,m4=st.columns(4)
with m1:st.metric("API",selected_drug["name"])
with m2:st.metric("Class",selected_drug["class"])
with m3:st.metric("Market forms",len(selected_drug["forms"]))
with m4:st.metric("Selected form",selected_form)

tabs=st.tabs(["🧬 API profile","🌐 Live properties","🧪 Exact ingredients","🏛️ Regulatory Intelligence","🧪 In Vivo / In Vitro Studies","🏭 Process defects","📋 Development notes","💊 Generic & Brand/Originator Dosage Forms"])

with tabs[0]:
    st.subheader("API profile")
    profile=pd.DataFrame([["API name",selected_drug["name"]],["Therapeutic class",selected_drug["class"]],["Common use",selected_drug["uses"]],["Solubility note",selected_drug["solubility"]],["Dose category",selected_drug["dose_type"]],["Stability note",selected_drug["stability"]],["Marketed dosage forms",", ".join(selected_drug["forms"])],["Routes",", ".join(selected_drug["routes"])]],columns=["Property","Information"])
    st.dataframe(profile,use_container_width=True,hide_index=True)
    st.subheader("💊 Generic / product-status intelligence")
    status,ptype,note=GENERIC_STATUS.get(selected_name,("Not curated in local database","Needs verification","Generic status is product-, strength-, dosage-form- and jurisdiction-specific."))
    st.dataframe(pd.DataFrame([["Generic product availability",status],["Product type",ptype],["Interpretation",note],["Important distinction","API = active ingredient; generic = medicinal product using the API and meeting applicable regulatory requirements."]],columns=["Field","Information"]),use_container_width=True,hide_index=True)
    st.info("A generic/brand decision is jurisdiction-specific. For regulatory work, verify the exact product, reference product, strength, dosage form and applicable bioequivalence requirements.")

with tabs[1]:
    st.subheader("Live public properties")
    if st.button("Fetch PubChem + openFDA data",type="primary",use_container_width=True):
        with st.spinner("Fetching public data..."):
            pc=get_pubchem_data(selected_name);fd=get_openfda_data(selected_name)
        st.write("### PubChem chemical properties");st.json(pc)
        st.write("### openFDA label information")
        if "Error" in fd or "Status" in fd:st.warning(fd)
        else:
            for title,value in fd.items():
                with st.expander(title):st.write(value)

with tabs[2]:
    st.subheader(f"Product-specific ingredients: {selected_name}")
    st.markdown("""<div class="success-box">Exact inactive ingredients depend on product, strength, manufacturer, country and dosage form. Select a specific DailyMed label before treating an ingredient list as product-specific.</div>""",unsafe_allow_html=True)
    st.link_button("🔗 Open DailyMed manual search",get_daily_med_search_url(selected_name),use_container_width=True)
    if st.button("Search current DailyMed records",use_container_width=True):
        rec=normalize_dailymed_records(get_dailymed_records(selected_name))
        if rec:
            st.dataframe(pd.DataFrame(rec),use_container_width=True,hide_index=True)
            ids=[x["Set ID"] for x in rec if x["Set ID"]!="Not available"]
            if ids:
                sid=st.selectbox("Select a product Set ID",ids)
                if st.button("Read inactive ingredients from selected label"):
                    ing=extract_inactive_ingredients(get_dailymed_xml(sid))
                    if ing:st.dataframe(pd.DataFrame({"Product-specific ingredient record":ing}),use_container_width=True,hide_index=True)
                    else:st.warning("Automatic extraction failed. Open the original DailyMed label manually.")
        else:st.warning("No DailyMed API records were returned.")
    st.subheader("Role-based excipient development suggestions")
    rows=[{"Role / development topic":r,"Examples":", ".join(v),"Development note":"Confirm grade, compatibility, concentration, safety, regulatory status and stability."} for r,v in get_suggestions(selected_drug,selected_form).items()]
    if rows:st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.link_button("🔗 FDA Inactive Ingredient Database","https://www.accessdata.fda.gov/scripts/cder/iig/index.cfm",use_container_width=True)

with tabs[3]:
    st.subheader(f"🏛️ Regulatory intelligence: {selected_name}")
    st.markdown(
        """<div class="success-box"><b>Goal:</b> bring public regulatory evidence into the same API dashboard. FDA Orange Book data can show approved products, application type, dosage form, route, reference status and TE code; DailyMed provides current submitted labeling; openFDA provides structured label data.</div>""",
        unsafe_allow_html=True,
    )

    if st.button("🏛️ Fetch current FDA regulatory evidence", type="primary", use_container_width=True):
        with st.spinner("Fetching Orange Book + openFDA + DailyMed evidence..."):
            ob = get_orange_book_products(selected_name)
            fd = get_openfda_data(selected_name)
            dm = normalize_dailymed_records(get_dailymed_records(selected_name))
        st.session_state[f"reg_{selected_name}"] = {"orange": ob, "fda": fd, "dailymed": dm}

    reg = st.session_state.get(f"reg_{selected_name}", {})
    orange = reg.get("orange", [])
    fda = reg.get("fda", {})
    dm = reg.get("dailymed", [])

    if orange:
        st.write("### 💊 FDA Orange Book product evidence")
        st.dataframe(pd.DataFrame(orange), use_container_width=True, hide_index=True)
        st.caption("Orange Book records are product-level regulatory evidence. TE codes, reference status and application type must be interpreted in the exact dosage-form/route/strength context.")
    else:
        st.warning("No Orange Book records were returned for this API, or the endpoint was temporarily unavailable.")

    st.write("### 🏷️ openFDA structured label evidence")
    if fda:
        for title, value in fda.items():
            with st.expander(title):
                st.write(value)
    else:
        st.info("Fetch regulatory evidence above to load current openFDA label data.")

    st.write("### 📄 DailyMed label evidence")
    if dm:
        st.dataframe(pd.DataFrame(dm), use_container_width=True, hide_index=True)
    else:
        st.info("No DailyMed records loaded yet. The Exact Ingredients tab can search and inspect individual SPL labels.")

    st.write("### 🌍 Regulatory-source map")
    st.dataframe(pd.DataFrame([
        ["US generic / therapeutic equivalence", "FDA Orange Book", "Product, dosage form, route, application, reference status, TE code"],
        ["US approval history", "Drugs@FDA / openFDA", "Applications, products, submissions and approval-related data"],
        ["US current labeling", "DailyMed / NLM", "Structured product labeling submitted by companies and currently in use"],
        ["EU product information", "EMA ePI", "Electronic product information including SmPC, package leaflet and labelling where available"],
    ], columns=["Purpose", "Source", "What PharmaLens can use"]), use_container_width=True, hide_index=True)

    st.caption("Source map: FDA Orange Book, openFDA, DailyMed/NLM and EMA ePI. Product-level regulatory status remains jurisdiction-, strength-, dosage-form- and route-specific.")

with tabs[4]:
    st.subheader(f"🧪 In Vivo / In Vitro Studies: {selected_name}")
    st.caption("Choose a study objective to see its relevant assays, test system, materials, measurements and reporting fields. Values vary by method, formulation and approved protocol; illustrative fields are not universal experimental instructions.")

    # Study options are selected from the API's therapeutic class/use, rather than
    # displaying a generic past-literature table or a generic checklist.
    drug_class = selected_drug["class"].lower()
    drug_uses = selected_drug["uses"].lower()
    study_options = ["API / formulation quality assays", "Dissolution / drug release", "Drug-excipient compatibility", "Stability-indicating study"]
    # Keep this available for exploratory research questions for any API; inclusion
    # does not imply that the API is an established antimicrobial.
    study_options += ["Antimicrobial activity"]
    if any(term in drug_class + " " + drug_uses for term in ["analgesic", "pain", "nsaid"]):
        study_options += ["Analgesic activity", "Anti-inflammatory activity"]
    if any(term in drug_class + " " + drug_uses for term in ["antipyretic", "fever"]):
        study_options += ["Antipyretic activity"]
    if any(term in drug_class + " " + drug_uses for term in ["antidiabetic", "diabetes"]):
        study_options += ["Antidiabetic activity"]
    study_options += ["Pharmacokinetic / bioavailability study"]

    study_type = st.selectbox("Select particular study", list(dict.fromkeys(study_options)), key=f"study_select_{selected_name}")

    assay_library = {
        "API / formulation quality assays": [
            ("Assay / drug content", "API or dosage-form sample", "Validated analytical method; reference standard; suitable solvent/mobile phase", "Drug content / potency (% label claim)", "Method, calibration, sample preparation, replicate results, units and acceptance criteria"),
            ("Content uniformity (where applicable)", "Individual dosage units", "Validated assay method and individual unit preparations", "Individual content and variability", "Unit-wise values, mean, SD and applicable pharmacopoeial acceptance criteria"),
            ("Impurity / degradation profile", "API or finished product", "Stability-indicating chromatographic method and reference/impurity standards where available", "Specified and unspecified impurities", "Chromatograms, method conditions, impurity identity/level and reporting threshold")],
        "Dissolution / drug release": [
            ("Dissolution profile", "Finished dosage units", "Dissolution apparatus, specified medium, sampling equipment and validated assay", "% drug released at each sampling time", "Product-specific medium, apparatus, speed, temperature, sampling schedule, sink-condition justification and individual/mean profile"),
            ("Release kinetics (if justified)", "Dissolution/release data", "Validated spreadsheet or statistical software", "Model fit and release pattern", "Model used, assumptions, fitted parameters and goodness-of-fit; do not select a model solely by highest R²")],
        "Drug-excipient compatibility": [
            ("FTIR", "API, excipient and physical mixture", "FTIR spectrometer and appropriate sampling accessories", "Characteristic peaks / peak shifts", "Spectra, wavenumber range, resolution, sample preparation and interpretation"),
            ("DSC / thermal analysis", "API, excipient and mixture", "DSC instrument and calibrated temperature reference", "Thermal transitions / event changes", "Heating program, atmosphere, sample mass, thermograms and interpretation"),
            ("Visual / chemical compatibility", "API-excipient mixtures", "Suitable containers and stability-indicating assay if needed", "Colour, odour, physical changes and assay/impurities", "Composition, storage conditions, time points and analytical evidence")],
        "Stability-indicating study": [
            ("Accelerated / long-term stability", "API or finished product in proposed pack", "Qualified stability chambers and stability-indicating analytical methods", "Assay, impurities, appearance and relevant performance tests", "Applicable guideline/monograph, storage conditions, time points, packaging, results and trend analysis"),
            ("Photostability (if applicable)", "API/product and suitable controls", "Qualified light-exposure chamber and monitoring instruments", "Change in assay, impurities or appearance", "Exposure conditions, controls, cumulative exposure and comparative results")],
        "Antimicrobial activity": [
            ("Minimum inhibitory concentration (MIC)", "Specified microorganism/strain; appropriate reference strains", "Suitable broth/agar medium, inoculum standardisation, controls and validated readout", "MIC in the method-defined concentration units", "Organism and strain ID, medium, inoculum, dilution series, incubation conditions, positive/negative controls and replicate results"),
            ("Agar diffusion / zone of inhibition (if suitable)", "Specified microorganism and agar medium", "Agar plates, sterile applicators/wells/discs and zone-measurement device", "Zone diameter (mm)", "Organism, medium, inoculum, sample amount/concentration, controls, incubation conditions and measured zones"),
            ("Minimum bactericidal concentration (MBC; where appropriate)", "Organism from MIC assay", "Appropriate subculture media and microbiology equipment", "MBC under the selected method definition", "Link to MIC method, subculture procedure, controls and recorded outcome")],
        "Analgesic activity": [
            ("Analgesic endpoint selection", "Validated in-vitro model or approved animal/human model appropriate to the question", "Method-specific equipment and validated measurement procedure", "Predefined pain-related endpoint", "Model rationale, controls, blinding/randomisation where applicable, observation times, raw data and statistical plan"),
            ("Exposure / dose documentation", "Study-specific test system", "Calibrated preparation and measurement equipment", "Protocol-defined exposure or dose and response", "Use a published, model-appropriate and ethically approved protocol. Dose levels, species, sex, route and duration must be justified and must not be assumed from a generic template")],
        "Anti-inflammatory activity": [
            ("Inflammation-related endpoint", "Validated in-vitro model or approved model suited to the scientific question", "Model-specific reagents, controls and measurement instrument", "Predefined inflammatory marker or response", "Model validation, controls, time points, units, replicate plan and statistical analysis"),
            ("Exposure / dose documentation", "Study-specific test system", "Suitable preparation and measurement equipment", "Protocol-defined exposure or dose and response", "Select species/model and dose only from relevant evidence and an approved protocol; no universal dose range applies")],
        "Antipyretic activity": [
            ("Temperature / antipyretic endpoint", "Appropriate validated model under an approved protocol", "Calibrated temperature-measurement device and model-specific materials", "Temperature change over defined time points", "Baseline, model induction where applicable, controls, measurement schedule, humane endpoints and analysis plan"),
            ("Exposure / dose documentation", "Study-specific test system", "Calibrated preparation and measurement equipment", "Protocol-defined exposure or dose and response", "Dose, species, sex, route and duration must come from relevant published evidence and approved ethical review, not a generic fixed list")],
        "Antidiabetic activity": [
            ("Glucose-related assay / endpoint", "Validated biochemical or cellular model; animal model only where justified and approved", "Suitable assay kit/reagents, controls and calibrated reader", "Glucose or predefined metabolic endpoint", "Model, sample type, units, calibration, controls, time points and analysis plan"),
            ("Exposure / dose documentation", "Study-specific test system", "Method-appropriate preparation and measurement equipment", "Protocol-defined exposure or dose and response", "Use evidence-based, approved protocol parameters; do not treat example doses as universal recommendations")],
        "Pharmacokinetic / bioavailability study": [
            ("Drug concentration-time analysis", "Appropriately justified and authorised study population/model", "Validated bioanalytical method, reference standards and qualified instrument", "Concentration-time profile", "Sampling schedule, validated method, matrix, LLOQ/ULOQ, actual measured concentrations and quality controls"),
            ("PK parameter calculation", "Concentration-time data", "Validated noncompartmental/compartmental analysis software as appropriate", "Cmax, Tmax, AUC and other justified parameters", "Method and units, individual data, calculation rules, variability and confidence intervals where applicable")]
    }

    assay_rows = assay_library.get(study_type, assay_library["API / formulation quality assays"])
    assay_names = [row[0] for row in assay_rows]
    selected_assay = st.selectbox("Select assay within this study", assay_names, key=f"assay_select_{selected_name}_{study_type}")
    assay = next(row for row in assay_rows if row[0] == selected_assay)

    st.markdown("### Selected assay: " + selected_assay)
    st.dataframe(pd.DataFrame([
        {"Field": "Selected API", "Study-specific information": selected_name},
        {"Field": "Study category", "Study-specific information": study_type},
        {"Field": "Assay", "Study-specific information": assay[0]},
        {"Field": "Test system / sample", "Study-specific information": assay[1]},
        {"Field": "Materials / reagents / equipment", "Study-specific information": assay[2]},
        {"Field": "Main endpoint / output", "Study-specific information": assay[3]},
        {"Field": "Data to record / reporting requirements", "Study-specific information": assay[4]},
    ]), use_container_width=True, hide_index=True)

    st.markdown("### Study-specific parameter fields")
    if study_type == "Antimicrobial activity":
        st.write("**Core parameters:** organism and strain ID; inoculum standardisation; medium; test concentration series; positive and negative controls; incubation conditions; replicate count; MIC/MBC or zone diameter; raw results and interpretation.")
        st.info("This assay can be selected as an exploratory research question for any API, but selecting it does not mean the API has established antimicrobial efficacy. Confirm scientific rationale and use an appropriate validated microbiology method.")
    elif study_type in ["Analgesic activity", "Anti-inflammatory activity", "Antipyretic activity", "Antidiabetic activity"]:
        st.write("**Core parameters:** model and justification; species/strain and sex only if an animal model is justified; age/body-weight eligibility; test article and vehicle; control groups; route; protocol-approved dose levels and units; timing/duration; endpoint and measurement schedule; adverse observations; sample size rationale; statistical plan.")
        st.warning("Animal species and doses are not universal API properties. Do not assume 'mouse/rat' or doses such as 20/50 mg/kg are suitable for every drug. Use values reported for the same model and route, check toxicity/exposure evidence, and obtain required institutional animal ethics approval before any animal work.")

        st.markdown("#### Animal-study parameters with examples")
        st.caption("Examples below demonstrate how study information is recorded; they are not a recommended protocol or dose schedule. Actual values must come from relevant published evidence and an approved study protocol.")
        animal_parameter_examples = [
            {"Parameter": "Animal species", "What to record": "Common name and scientific name", "Example format": "Rat (Rattus norvegicus) or mouse (Mus musculus), only if justified for the study"},
            {"Parameter": "Strain", "What to record": "Specific strain / stock", "Example format": "Wistar rat or Sprague-Dawley rat; report the strain actually used"},
            {"Parameter": "Sex", "What to record": "Male, female, or both; justify selection", "Example format": "Male and female animals, with results reported by sex where relevant"},
            {"Parameter": "Age", "What to record": "Age at study start", "Example format": "8–10 weeks, only if this is what the approved protocol specifies"},
            {"Parameter": "Body weight", "What to record": "Eligibility range and individual weights", "Example format": "180–220 g; record actual weight for each animal"},
            {"Parameter": "Dose / concentration", "What to record": "Each group dose, unit, basis and justification", "Example format": "Low / medium / high dose in mg/kg body weight, or test concentration in µg/mL; enter actual literature/protocol values, not generic defaults"},
            {"Parameter": "Administration route", "What to record": "Route and any relevant administration details", "Example format": "Oral gavage, intraperitoneal, intravenous, topical; choose only the route specified by the study protocol"},
            {"Parameter": "Study groups and controls", "What to record": "Group name, number of animals and treatment", "Example format": "Vehicle control, reference/positive control, and test-treatment groups; group sizes need a scientific justification"},
            {"Parameter": "Vehicle / solution", "What to record": "Vehicle, solvent, concentration and preparation", "Example format": "Saline, purified water, or a validated formulation vehicle only when compatible with the test article and protocol"},
            {"Parameter": "Study duration / observation time", "What to record": "Treatment period and pre-defined measurement time points", "Example format": "Baseline, then protocol-defined observations such as 1 h, 2 h, and 4 h; these times are examples of recording format only"},
            {"Parameter": "Endpoints", "What to record": "Primary endpoint, secondary endpoints and measurement units", "Example format": "Change in paw volume (mL), temperature (°C), pain-response latency (s), blood glucose (mg/dL), or a validated biomarker, depending on the study objective"},
            {"Parameter": "Statistical analysis", "What to record": "Planned test, assumptions, significance level and software", "Example format": "Mean ± SD; one-way ANOVA with a justified post-hoc test for suitable multi-group data, or a suitable non-parametric/repeated-measures method when assumptions/design require it; report n, exact p-values and effect sizes where possible"},
            {"Parameter": "Randomisation / blinding", "What to record": "Allocation method and whether outcome assessors were blinded", "Example format": "Random group allocation and blinded endpoint assessment, when feasible"},
            {"Parameter": "Humane endpoints / adverse observations", "What to record": "Monitoring criteria, adverse signs and action taken", "Example format": "Predefined clinical observations and humane stopping criteria approved by the ethics committee"},
        ]
        st.dataframe(pd.DataFrame(animal_parameter_examples), use_container_width=True, hide_index=True)
        st.info("For dose and animal selection, PharmaLens should display source-reported values when available. Do not infer a suitable dose from the API name alone; species, strain, sex, route, formulation and study objective can change the interpretation.")
    elif study_type == "Pharmacokinetic / bioavailability study":
        st.write("**Core parameters:** population/model, formulation, route, dose as approved in the protocol, sampling time points, biological matrix, bioanalytical validation, concentration-time data, Cmax, Tmax, AUC, half-life where estimable, and safety observations.")
    else:
        st.write("**Core parameters:** sample/batch identity, method and version, materials/reagents, instrument settings, controls/reference standards, replicate plan, raw readings, calculations, acceptance criteria, deviations and final interpretation.")

    st.markdown("### Retrieve actual reported values from published studies")
    st.caption("Published study values are shown only when retrieved from the literature. The app must not invent an animal species, dose, concentration, sex, reagent or result when the source does not report it.")
    if st.button("Fetch published study evidence for this API and assay", key=f"fetch_assay_evidence_{selected_name}_{study_type}_{selected_assay}", use_container_width=True):
        query_terms = {
            "Antimicrobial activity": ' (antimicrobial OR antibacterial OR antifungal OR MIC OR "zone of inhibition")',
            "Analgesic activity": ' (analgesic OR pain OR nociception)',
            "Anti-inflammatory activity": ' (anti-inflammatory OR inflammation)',
            "Antipyretic activity": ' (antipyretic OR fever)',
            "Antidiabetic activity": ' (antidiabetic OR glucose)',
            "Pharmacokinetic / bioavailability study": ' (pharmacokinetic OR bioavailability OR Cmax OR AUC)',
            "Dissolution / drug release": ' (dissolution OR "drug release")',
            "Drug-excipient compatibility": ' (FTIR OR DSC OR compatibility)',
            "Stability-indicating study": ' (stability OR degradation OR impurities)',
            "API / formulation quality assays": ' (assay OR "content uniformity" OR impurities)'
        }
        objective_map = {
            "Analgesic activity": "Analgesic / pain relief",
            "Antipyretic activity": "Antipyretic / fever reduction",
            "Anti-inflammatory activity": "Anti-inflammatory",
            "Antimicrobial activity": "Antimicrobial activity",
            "Pharmacokinetic / bioavailability study": "Pharmacokinetics / bioavailability",
            "Dissolution / drug release": "Formulation / dissolution",
            "Drug-excipient compatibility": "Formulation / dissolution",
            "Stability-indicating study": "Formulation / dissolution",
            "API / formulation quality assays": "Formulation / dissolution",
            "Antidiabetic activity": "General pharmacology / safety",
        }
        with st.spinner("Searching PubMed for the selected API and study objective..."):
            evidence_records = get_objective_literature(selected_name, objective_map.get(study_type, "General pharmacology / safety"), "In-vitro" if study_type in ["Antimicrobial activity", "Dissolution / drug release", "Drug-excipient compatibility", "Stability-indicating study", "API / formulation quality assays"] else "In-vivo / animal", max_results=12)
        st.session_state[f"assay_evidence_{selected_name}_{study_type}_{selected_assay}"] = evidence_records

    evidence_records = st.session_state.get(f"assay_evidence_{selected_name}_{study_type}_{selected_assay}", [])
    if evidence_records:
        for rec in evidence_records:
            with st.expander(f"{rec.get('Year', 'Year n/a')} | {rec.get('Title', 'Untitled study')}"):
                st.write("**Study type:**", rec.get("Study type", "Not stated"))
                st.write("**Model / population evidence:**", rec.get("Model / population evidence", "Not stated in abstract"))
                st.write("**Dose / route evidence:**", rec.get("Dose / route evidence", "Not stated in abstract"))
                st.write("**Endpoints / parameters:**", rec.get("Endpoints / parameters reported", "Not stated in abstract"))
                st.write("**Reported result evidence:**", rec.get("Reported result evidence", "Not stated in abstract"))
                st.write("**Numeric findings reported:**", rec.get("Numeric findings reported", "No numeric value detected in abstract"))
                if rec.get("PMID"):
                    st.link_button("Open original PubMed record", _pubmed_url(rec["PMID"]))
    else:
        st.info("No study records are loaded for this selection yet. Use the button above to retrieve matching public literature. A missing value means it was not found in the retrieved record, not that the value is zero.")

    st.caption("Educational research dashboard only. Verify the original paper, validated method, current pharmacopoeia/guideline and required ethics/regulatory permissions before using any study parameter in a protocol.")

with tabs[5]:
    process=PROCESS_DATA[get_process_type(selected_form)]
    st.subheader(f"High-level manufacturing risk map: {selected_form}")
    st.write("### Process stages")
    for n,step in enumerate(process["process"],1):st.write(f"{n}. {step}")
    st.write("### Possible defects")
    st.dataframe(pd.DataFrame([{"Possible defect":d,"Investigation focus":"Review material attributes, equipment status, process parameters, IPC data, deviation history, cleaning and batch documentation."} for d in process["defects"]]),use_container_width=True,hide_index=True)
    st.write("### Typical quality checks")
    st.dataframe(pd.DataFrame({"Quality check":process["tests"],"Purpose":["Confirm dosage-form performance and consistency"]*len(process["tests"])}),use_container_width=True,hide_index=True)
    st.warning("Actual production must follow approved specifications, validated processes, GMP requirements, authorized SOPs and approved batch records.")

with tabs[6]:
    st.subheader("Formulation-development checklist")
    for item in ["Confirm API identity, assay, polymorph or salt form where relevant","Evaluate particle size, flow, density, moisture and compatibility","Select dosage form based on therapeutic need and product performance","Screen excipient compatibility and concentration ranges","Define critical quality attributes","Identify critical material attributes and process parameters","Perform stability and packaging studies","Define in-process controls and acceptance criteria","Investigate defects through documented root-cause analysis","Use CAPA and continued process verification after validation"]:
        st.checkbox(item,value=False)

st.divider()
st.caption("PharmaLens 100 | Educational research dashboard | Always verify current product labels, publications and regulatory requirements.")

with tabs[7]:
    st.subheader(f"Generic vs Brand/Originator Dosage Forms: {selected_name}")
    st.markdown(
        "This section uses **pre-entered, source-linked product information** instead of live openFDA fetching. "
        "Brand names and marketed forms can vary by country and date. A brand name alone does not prove current patent or reference-product status."
    )

    st.write("### 1. Generic drug dosage-form information")
    generic_forms = selected_drug.get("forms", [])
    generic_routes = selected_drug.get("routes", [])
    st.dataframe(
        pd.DataFrame([
            {"Field": "Active ingredient (API)", "Information": selected_name},
            {"Field": "Dosage forms in PharmaLens API database", "Information": ", ".join(generic_forms) or "Not curated"},
            {"Field": "Routes in PharmaLens API database", "Information": ", ".join(generic_routes) or "Not curated"},
            {"Field": "Therapeutic class", "Information": selected_drug.get("class", "Not available")},
            {"Field": "Common use", "Information": selected_drug.get("uses", "Not available")},
        ]), use_container_width=True, hide_index=True
    )
    st.caption("API-level dosage-form options are not confirmation that every form is currently marketed or approved in every country.")

    st.write("### 2. Manually curated brand / product-label information")
    st.caption("The records below are embedded in the app and do not depend on an API fetch. Source links are provided for verification.")

    manual_products = {
        "paracetamol": [
            {"Country/market": "India", "Brand/product": "Crocin 650 Tablets with OPTIZORB", "Active ingredient(s)": "Paracetamol 650 mg", "Dosage form": "Tablet", "Route": "Oral", "Labelled use / product information": "Pain relief; manufacturer product page describes paracetamol as the active ingredient.", "Source": "Official Crocin product page", "Source URL": "https://www.crocin.com/crocin-products-for-adult/"},
            {"Country/market": "India", "Brand/product": "Crocin Advance", "Active ingredient(s)": "Paracetamol 500 mg", "Dosage form": "Tablet", "Route": "Oral", "Labelled use / product information": "Pain relief; product page describes OPTIZORB formulation.", "Source": "Official Crocin product page", "Source URL": "https://www.crocin.com/everyday-pain-relief-with-crocin/"},
            {"Country/market": "India", "Brand/product": "Crocin 240", "Active ingredient(s)": "Paracetamol 240 mg per 5 mL", "Dosage form": "Paediatric oral suspension", "Route": "Oral", "Labelled use / product information": "Analgesic and antipyretic; product information leaflet gives the concentration and dosage form.", "Source": "Crocin product information leaflet (PDF)", "Source URL": "https://www.crocin.com/content/dam/cf-consumer-healthcare/panadol/en_in/documents/Crocin%20Suspension%20240%20PI.pdf"},
            {"Country/market": "United States", "Brand/product": "Acetaminophen oral suspension (DailyMed example; generic-labelled product)", "Active ingredient(s)": "Acetaminophen 160 mg per 5 mL", "Dosage form": "Oral suspension", "Route": "Oral", "Labelled use / product information": "Pain reliever / fever reducer; label lists temporary reduction of fever and relief of minor aches and pains.", "Source": "DailyMed official label", "Source URL": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a3031139-4709-43f2-95a8-89840c595f7f"},
        ],
        "ibuprofen": [
            {"Country/market": "United States", "Brand/product": "Advil (brand example; verify specific pack/label)", "Active ingredient(s)": "Ibuprofen", "Dosage form": "Product-specific; commonly oral tablets/capsules and liquid products", "Route": "Oral", "Labelled use / product information": "NSAID pain reliever/fever reducer; exact strength and formulation depend on product.", "Source": "Official Advil website", "Source URL": "https://www.advil.com/"},
        ],
        "metformin": [
            {"Country/market": "United States", "Brand/product": "Glucophage (brand example; verify specific pack/label)", "Active ingredient(s)": "Metformin hydrochloride", "Dosage form": "Immediate-release and extended-release tablets exist; confirm exact product label", "Route": "Oral", "Labelled use / product information": "Antidiabetic medicine; product indications and strengths are product-specific.", "Source": "Official GLUCOPHAGE website", "Source URL": "https://www.glucophage.com/"},
        ],
        "amlodipine": [
            {"Country/market": "United States", "Brand/product": "Norvasc (brand example; verify specific pack/label)", "Active ingredient(s)": "Amlodipine besylate", "Dosage form": "Tablet", "Route": "Oral", "Labelled use / product information": "Calcium-channel blocker; confirm exact approved indications and strength on the product label.", "Source": "Official NORVASC website", "Source URL": "https://www.pfizermedicalinformation.com/norvasc"},
        ],
    }
    # Curated brand-name examples for the complete API list in this app.
    # These are example brands, not an exhaustive/currently-available market inventory.
    # Verify country, strength, salt, release type and label before treating a brand as a match.
    brand_examples = {
        "aspirin": ["Ecosprin", "Disprin", "Aspirin (generic)"],
        "naproxen": ["Naprosyn", "Naxdom (naproxen + domperidone; combination product)", "Naproxen (generic)"],
        "diclofenac": ["Voveran", "Voltaren", "Dynapar"],
        "ketoprofen": ["Ketoflam", "Ketoprofen (generic)"],
        "amoxicillin": ["Mox", "Novamox", "Amoxil"],
        "azithromycin": ["Azee", "Azithral", "Zithromax"],
        "clarithromycin": ["Claribid", "Klacid", "Biaxin"],
        "ciprofloxacin": ["Ciplox", "Cifran", "Cipro"],
        "levofloxacin": ["Glevo", "Levoflox", "Levaquin"],
        "moxifloxacin": ["Moxicip", "Avelox", "Vigamox (ophthalmic product)"],
        "doxycycline": ["Doxy-1", "Doxicip", "Vibramycin"],
        "metronidazole": ["Metrogyl", "Flagyl", "Metronidazole (generic)"],
        "tinidazole": ["Fasigyn", "Tiniba", "Tinidazole (generic)"],
        "metoclopramide": ["Perinorm", "Reglan", "Maxolon"],
        "loperamide": ["Eldoper", "Imodium", "Loperamide (generic)"],
        "lactulose": ["Duphalac", "Looz", "Lactulose (generic)"],
        "metformin": ["Glycomet", "Glucophage", "Obimet"],
        "glimepiride": ["Amaryl", "Glimestar", "Glimepiride (generic)"],
        "gliclazide": ["Diamicron", "Reclide", "Gliclazide (generic)"],
        "sitagliptin": ["Januvia", "Istavel", "Sitagliptin (generic)"],
        "vildagliptin": ["Galvus", "Jalra", "Vildagliptin (generic)"],
        "dapagliflozin": ["Forxiga", "Oxra", "Dapagliflozin (generic)"],
        "empagliflozin": ["Jardiance", "Empaone", "Empagliflozin (generic)"],
        "pioglitazone": ["Pioz", "Actos", "Pioglitazone (generic)"],
        "levothyroxine": ["Thyronorm", "Eltroxin", "Synthroid"],
        "ketoconazole": ["Nizoral", "Ketomac", "Ketoconazole (generic)"],
        "fluconazole": ["Forcan", "Zocon", "Diflucan"],
        "acyclovir": ["Acivir", "Zovirax", "Acyclovir (generic)"],
        "oseltamivir": ["Antiflu", "Fluvir", "Tamiflu"],
        "hydrocortisone": ["Cort S (product-specific formulation; verify label)", "Hydrocort", "Hydrocortisone (generic)"],
        "betamethasone": ["Betnovate", "Betnesol", "Celestone"],
        "adapalene": ["Adaferin", "Deriva", "Differin"],
        "tretinoin": ["A-Ret", "Retino-A", "Retin-A"],
        "povidone iodine": ["Betadine", "Wokadine", "Povidone-iodine (generic)"],
        "chlorhexidine": ["Hexidine", "Clohex", "Corsodyl"],
        "silver sulfadiazine": ["Silverex", "Flamazine", "Silvadene"],
        "calamine": ["Lacto Calamine (combination; check exact ingredients)", "Caladryl (market-specific formulation)", "Calamine lotion (generic)"],
        "lidocaine": ["Xylocaine", "Lignocaine (generic name used in India)", "Lidoderm (patch; market-specific)"],
        "bupivacaine": ["Marcaine", "Sensorcaine", "Bupivacaine (generic)"],
        "tramadol": ["Contramal", "Ultram", "Tramazac"],
        "gabapentin": ["Gabapin", "Gabantin", "Neurontin"],
        "pregabalin": ["Pregalin", "Maxgalin", "Lyrica"],
        "ferrous sulfate": ["Fefol (combination; verify ingredients)", "Feosol", "Ferrous sulfate (generic)"],
        "folic acid": ["Folvite", "Fol 5", "Folic acid (generic)"],
        "calcium carbonate": ["Shelcal (combination; verify ingredients)", "Calcimax (formulation-specific)", "Calcium carbonate (generic)"],
        "vitamin d3": ["Uprise-D3", "D-Rise", "Calcirol"],
        "vitamin b12": ["Nurokind", "Methycobal", "Neurobion (combination; verify ingredients)"],
        "zinc sulfate": ["Zinconia", "Zincovit (combination; verify ingredients)", "Zinc sulfate (generic)"],
        "potassium chloride": ["K-Dur", "Slow-K", "Potklor"],
        "sodium chloride": ["Natrium Chloratum (market-specific)", "Normal saline 0.9% (product-specific)", "Sodium chloride (generic)"],
        "insulin human": ["Humulin R", "Humulin N", "Insuman Rapid (market-specific availability)"],
        "sildenafil": ["Caverta", "Suhagra", "Viagra"],
        "tamsulosin": ["Urimax", "Contiflo", "Flomax"],
        "finasteride": ["Finpecia", "Fincar", "Propecia"],
    }
    for api_name, brand_list in brand_examples.items():
        if api_name not in manual_products:
            manual_products[api_name] = []
            for brand in brand_list:
                manual_products[api_name].append({
                    "Country/market": "India / international example; market varies",
                    "Brand/product": brand,
                    "Active ingredient(s)": selected_drug.get("name", api_name),
                    "Dosage form": ", ".join(selected_drug.get("forms", [])) or "Verify exact product label",
                    "Route": ", ".join(selected_drug.get("routes", [])) or "Verify exact product label",
                    "Labelled use / product information": "Brand-name example only. Exact strength, formulation, combination ingredients and current marketing status must be checked against the product label.",
                    "Source": "Google search for official product label / manufacturer source",
                    "Source URL": "https://www.google.com/search?q=" + quote(brand + " " + api_name + " official product label manufacturer"),
                })

    api_key = selected_name.strip().lower()
    products = manual_products.get(api_key, [])
    if products:
        display_products = [{k: v for k, v in item.items() if k != "Source URL"} for item in products]
        st.dataframe(pd.DataFrame(display_products), use_container_width=True, hide_index=True)
        st.write("#### Official source links")
        for item in products:
            st.markdown(f"- **{item['Brand/product']}**: [ {item['Source']} ]({item['Source URL']})")
    else:
        st.info(f"No brand/product record has been manually curated yet for {selected_name}. The generic dosage-form information above is available, but brand details are not invented.")
        st.link_button("Search official product information on the web", f"https://www.google.com/search?q={quote(selected_name + ' official product label dosage form brand')}", use_container_width=True)

    st.warning(
        "Brand examples are not a complete market list. Match the exact active ingredient/salt, strength, dosage form, "
        "route, release type and country before comparing products. This table is educational and is not proof of current "
        "patent status, generic approval, interchangeability or bioequivalence. Check the linked current label before use."
    )
