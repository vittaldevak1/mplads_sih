"""
MPLADS CSV Ingestion Pipeline
Reads 12 canonical CSV files and loads them into PostgreSQL.
"""

import pandas as pd
import numpy as np
import re
import os
import sys
from datetime import datetime
from typing import Tuple, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import (
    Work, WorkRecommendation, WorkSanction, WorkCompletion,
    Expenditure, Vendor, MPAllocation, CalamityConsent, IngestionLog
)

# =============================================
# UTILITY FUNCTIONS
# =============================================

def normalize_work_id(raw_field: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract and normalize Work ID from raw CSV field.
    Returns (normalized_id, work_description)
    
    Examples:
        Input:  "WS/\t MP620/2024-2025/133166-Construction of buildings..."
        Output: ("WS/MP620/2024-2025/133166", "Construction of buildings...")
    """
    if pd.isna(raw_field) or not raw_field:
        return None, None
    
    # Remove tabs and normalize whitespace
    cleaned = re.sub(r'\s+', ' ', str(raw_field)).strip()
    
    # Extract Work ID pattern: WS/MPXXXX/YYYY-YYYY/NNNNNN
    match = re.match(r'(WS/MP\d+/\d{4}-\d{4}/\d+)', cleaned)
    
    if match:
        work_id = match.group(1)
        # Remove trailing dash and description
        description = cleaned[len(work_id):].lstrip('-').strip()
        return work_id, description
    else:
        # Fallback: use cleaned field as-is
        return cleaned, None

def clean_currency(value) -> Optional[float]:
    """Clean currency values (remove ₹, commas, spaces)."""
    if pd.isna(value) or value == '' or value == 'N/A':
        return None
    
    cleaned = str(value).replace('₹', '').replace(',', '').replace(' ', '').strip()
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def clean_date(value) -> Optional[datetime]:
    """Parse dates in DD-Mon-YYYY or DD-Mon-YY format."""
    if pd.isna(value) or value == '' or value == 'N/A':
        return None
    
    date_str = str(value).strip()
    
    # Try different formats
    for fmt in ['%d-%b-%Y', '%d-%b-%y']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def clean_string(value) -> Optional[str]:
    """Clean string values."""
    if pd.isna(value) or value == '':
        return None
    
    cleaned = str(value).strip()
    
    # Convert N/A to None
    if cleaned.upper() in ['N/A', 'NA', 'NaN', '']:
        return None
    
    return cleaned

def clean_mp_name(name: str) -> Optional[str]:
    """Clean MP name (remove tenure suffixes like (2022-28) (NaN-NaN))."""
    if pd.isna(name):
        return None
    
    cleaned = str(name).strip()
    
    # Remove (NaN-NaN) pattern
    cleaned = re.sub(r'\s*\(NaN-NaN\)', '', cleaned)
    
    # Remove tenure patterns like (2022-28) (2022-2028)
    cleaned = re.sub(r'\s*\(\d{4}-\d{2,4}\)\s*(\(\d{4}-\d{4}\))?', '', cleaned)
    
    return cleaned.strip() if cleaned.strip() else None

def is_sc_constituency(constituency: str) -> bool:
    """Check if constituency is SC reserved."""
    if not constituency:
        return False
    return '(SC)' in str(constituency).upper()

def is_st_constituency(constituency: str) -> bool:
    """Check if constituency is ST reserved."""
    if not constituency:
        return False
    return '(ST)' in str(constituency).upper()

# =============================================
# INGESTION LOGGING
# =============================================

def log_ingestion(db, file_name, dataset_type, parliament_house, 
                  rows_read, rows_inserted, rows_skipped, errors, warnings):
    """Log ingestion results."""
    log = IngestionLog(
        file_name=file_name,
        dataset_type=dataset_type,
        parliament_house=parliament_house,
        rows_read=rows_read,
        rows_inserted=rows_inserted,
        rows_skipped=rows_skipped,
        errors=errors,
        warnings=warnings
    )
    db.add(log)
    db.commit()

# =============================================
# CSV PROCESSORS
# =============================================

def process_works_recommended(file_path: str, parliament_house: str, db) -> dict:
    """Process Works Recommended CSV."""
    errors = []
    warnings = []
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows_read = len(df)
        
        # Filter out Grand Total rows
        df = df[df['Sr. No.'] != 'Grand Total']
        df = df[~df['Sr. No.'].str.contains('Grand Total', na=False)]
        
        for _, row in df.iterrows():
            try:
                # Normalize work ID
                raw_work = row.get('WORK') or row.get('Work')
                work_id, work_desc = normalize_work_id(raw_work)
                
                if not work_id:
                    rows_skipped += 1
                    continue
                
                # Check if work already exists
                existing_work = db.query(Work).filter_by(work_id=work_id).first()
                
                if not existing_work:
                    # Create new work
                    work = Work(
                        work_id=work_id,
                        work_id_raw=str(raw_work),
                        work_category=clean_string(row.get('Work category')),
                        work_description=work_desc or clean_string(row.get('Work description')),
                        state=clean_string(row.get('State')),
                        ida=clean_string(row.get('IDA')),
                        constituency=clean_string(row.get('Constituency')),
                        parliament_house=parliament_house,
                        source_file=os.path.basename(file_path),
                        is_sc_quota=is_sc_constituency(row.get('Constituency', '')),
                        is_st_quota=is_st_constituency(row.get('Constituency', '')),
                    )
                    db.add(work)
                    db.flush()
                
                # Create recommendation record
                recommendation = WorkRecommendation(
                    work_id=work_id,
                    mp_name=clean_mp_name(row.get("Hon'ble Members of Parliament")),
                    recommended_date=clean_date(row.get('Recommended date')),
                    recommended_amount=clean_currency(row.get('RECOMMENDED AMOUNT   ( ₹ )') or row.get('RECOMMENDED AMOUNT ( ₹ )')),
                )
                db.add(recommendation)
                rows_inserted += 1
                
            except Exception as e:
                errors.append(str(e))
                rows_skipped += 1
        
        db.commit()
        
        log_ingestion(db, os.path.basename(file_path), 'works_recommended', 
                      parliament_house, rows_read, rows_inserted, rows_skipped, 
                      errors, warnings)
        
        return {
            'file': os.path.basename(file_path),
            'dataset_type': 'works_recommended',
            'parliament_house': parliament_house,
            'rows_read': rows_read,
            'rows_inserted': rows_inserted,
            'rows_skipped': rows_skipped,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        return {'error': str(e)}

def process_works_sanctioned(file_path: str, parliament_house: str, db) -> dict:
    """Process Works Sanctioned CSV."""
    errors = []
    warnings = []
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows_read = len(df)
        
        # Filter out Grand Total rows
        df = df[~df['Sr. No.'].astype(str).str.contains('Grand Total', na=False)]
        
        for _, row in df.iterrows():
            try:
                # Normalize work ID
                raw_work = row.get('Work')
                work_id, work_desc = normalize_work_id(raw_work)
                
                if not work_id:
                    rows_skipped += 1
                    continue
                
                # Check if work already exists
                existing_work = db.query(Work).filter_by(work_id=work_id).first()
                
                if not existing_work:
                    # Create new work
                    work = Work(
                        work_id=work_id,
                        work_id_raw=str(raw_work),
                        work_category=clean_string(row.get('Work category')),
                        work_description=work_desc or clean_string(row.get('Work description')),
                        state=clean_string(row.get('State')),
                        ida=clean_string(row.get('IDA')),
                        constituency=clean_string(row.get('Constituency')),
                        parliament_house=parliament_house,
                        source_file=os.path.basename(file_path),
                        is_sc_quota=is_sc_constituency(row.get('Constituency', '')),
                        is_st_quota=is_st_constituency(row.get('Constituency', '')),
                    )
                    db.add(work)
                    db.flush()
                
                # Create sanction record
                sanction = WorkSanction(
                    work_id=work_id,
                    sanction_date=clean_date(row.get('Sanction Date')),
                    sanction_amount=clean_currency(row.get('Sanction Amount ( ₹ )')),
                    work_status=clean_string(row.get('Work Status')),
                )
                db.add(sanction)
                rows_inserted += 1
                
            except Exception as e:
                errors.append(str(e))
                rows_skipped += 1
        
        db.commit()
        
        log_ingestion(db, os.path.basename(file_path), 'works_sanctioned', 
                      parliament_house, rows_read, rows_inserted, rows_skipped, 
                      errors, warnings)
        
        return {
            'file': os.path.basename(file_path),
            'dataset_type': 'works_sanctioned',
            'parliament_house': parliament_house,
            'rows_read': rows_read,
            'rows_inserted': rows_inserted,
            'rows_skipped': rows_skipped,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        return {'error': str(e)}

def process_works_completed(file_path: str, parliament_house: str, db) -> dict:
    """Process Works Completed CSV."""
    errors = []
    warnings = []
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows_read = len(df)
        
        # Filter out Grand Total rows
        df = df[~df['Sr. No.'].astype(str).str.contains('Grand Total', na=False)]
        
        for _, row in df.iterrows():
            try:
                # Normalize work ID
                raw_work = row.get('Work')
                work_id, work_desc = normalize_work_id(raw_work)
                
                if not work_id:
                    rows_skipped += 1
                    continue
                
                # Check if work already exists
                existing_work = db.query(Work).filter_by(work_id=work_id).first()
                
                if not existing_work:
                    # Create new work
                    work = Work(
                        work_id=work_id,
                        work_id_raw=str(raw_work),
                        work_category=clean_string(row.get('Work Category')),
                        work_description=work_desc or clean_string(row.get('Work Description')),
                        state=clean_string(row.get('State')),
                        ida=clean_string(row.get('IDA')),
                        constituency=clean_string(row.get('Constituency')),
                        parliament_house=parliament_house,
                        source_file=os.path.basename(file_path),
                        has_image_proof=str(row.get('Image', '')).strip() == 'Images',
                        is_sc_quota=is_sc_constituency(row.get('Constituency', '')),
                        is_st_quota=is_st_constituency(row.get('Constituency', '')),
                    )
                    db.add(work)
                    db.flush()
                
                # Create completion record
                completion = WorkCompletion(
                    work_id=work_id,
                    completion_date=clean_date(row.get('Completion Date')),
                    amount_disbursed=clean_currency(row.get('Amount Disbursed ( ₹ )')),
                    image_status=clean_string(row.get('Image')),
                    elected_nominated=clean_string(row.get('Elected/Nominated')),
                )
                db.add(completion)
                rows_inserted += 1
                
            except Exception as e:
                errors.append(str(e))
                rows_skipped += 1
        
        db.commit()
        
        log_ingestion(db, os.path.basename(file_path), 'works_completed', 
                      parliament_house, rows_read, rows_inserted, rows_skipped, 
                      errors, warnings)
        
        return {
            'file': os.path.basename(file_path),
            'dataset_type': 'works_completed',
            'parliament_house': parliament_house,
            'rows_read': rows_read,
            'rows_inserted': rows_inserted,
            'rows_skipped': rows_skipped,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        return {'error': str(e)}

def process_expenditure(file_path: str, parliament_house: str, db) -> dict:
    """Process Expenditure CSV."""
    errors = []
    warnings = []
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows_read = len(df)
        
        # Filter out Grand Total rows
        df = df[~df['Sr. No.'].astype(str).str.contains('Grand Total', na=False)]
        
        for _, row in df.iterrows():
            try:
                # Extract work ID from Work ID column
                work_id_raw = row.get('Work ID')
                if pd.isna(work_id_raw):
                    rows_skipped += 1
                    continue
                
                work_id, _ = normalize_work_id(work_id_raw)
                
                if not work_id:
                    rows_skipped += 1
                    continue
                
                # Create expenditure record
                expenditure = Expenditure(
                    work_id=work_id,
                    expenditure_date=clean_date(row.get('Expenditure Date')),
                    vendor_name=clean_string(row.get('Vendor Name')),
                    payment_status=clean_string(row.get('Payment Status')),
                    fund_disbursed_amount=clean_currency(row.get('Fund Disbursed Amount ( ₹ )')),
                    mp_name=clean_mp_name(row.get("Hon'ble Members of Parliament")),
                    state=clean_string(row.get('State')),
                    ida=clean_string(row.get('IDA')),
                )
                db.add(expenditure)
                rows_inserted += 1
                
            except Exception as e:
                errors.append(str(e))
                rows_skipped += 1
        
        db.commit()
        
        log_ingestion(db, os.path.basename(file_path), 'expenditure', 
                      parliament_house, rows_read, rows_inserted, rows_skipped, 
                      errors, warnings)
        
        return {
            'file': os.path.basename(file_path),
            'dataset_type': 'expenditure',
            'parliament_house': parliament_house,
            'rows_read': rows_read,
            'rows_inserted': rows_inserted,
            'rows_skipped': rows_skipped,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        return {'error': str(e)}

def process_allocated_limit(file_path: str, parliament_house: str, db) -> dict:
    """Process Allocated Limit CSV."""
    errors = []
    warnings = []
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows_read = len(df)
        
        # Filter out Grand Total rows
        df = df[~df['Sr. No.'].astype(str).str.contains('Grand Total', na=False)]
        
        for _, row in df.iterrows():
            try:
                # Get MP name - handle different column names
                mp_name = row.get("Hon'ble Members of Parliament") or row.get("Hon'ble Members of Parliaments")
                
                allocation = MPAllocation(
                    mp_name=clean_mp_name(mp_name),
                    state=clean_string(row.get('State')),
                    constituency=clean_string(row.get('Constituency')),
                    parliament_house=parliament_house,
                    allocated_amount=clean_currency(row.get('Allocated AMOUNT ( ₹ )')),
                    elected_nominated=clean_string(row.get('Elected/Nominated')),
                )
                db.add(allocation)
                rows_inserted += 1
                
            except Exception as e:
                errors.append(str(e))
                rows_skipped += 1
        
        db.commit()
        
        log_ingestion(db, os.path.basename(file_path), 'mp_allocations', 
                      parliament_house, rows_read, rows_inserted, rows_skipped, 
                      errors, warnings)
        
        return {
            'file': os.path.basename(file_path),
            'dataset_type': 'mp_allocations',
            'parliament_house': parliament_house,
            'rows_read': rows_read,
            'rows_inserted': rows_inserted,
            'rows_skipped': rows_skipped,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        return {'error': str(e)}

def process_calamity(file_path: str, parliament_house: str, db) -> dict:
    """Process Calamity Consent CSV."""
    errors = []
    warnings = []
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        rows_read = len(df)
        
        # Filter out Grand Total rows
        df = df[~df['Sr. No.'].astype(str).str.contains('Grand Total', na=False)]
        
        for _, row in df.iterrows():
            try:
                consent = CalamityConsent(
                    calamity_type=clean_string(row.get('Calamity Type')),
                    calamity_name=clean_string(row.get('Calamity Name')),
                    mp_name=clean_mp_name(row.get("Hon'ble Members of Parliament")),
                    consent_date=clean_date(row.get('Date of Consent')),
                    consent_amount=clean_currency(row.get('Consent Amount ( ₹ )')),
                    parliament_house=parliament_house,
                )
                db.add(consent)
                rows_inserted += 1
                
            except Exception as e:
                errors.append(str(e))
                rows_skipped += 1
        
        db.commit()
        
        log_ingestion(db, os.path.basename(file_path), 'calamity_consents', 
                      parliament_house, rows_read, rows_inserted, rows_skipped, 
                      errors, warnings)
        
        return {
            'file': os.path.basename(file_path),
            'dataset_type': 'calamity_consents',
            'parliament_house': parliament_house,
            'rows_read': rows_read,
            'rows_inserted': rows_inserted,
            'rows_skipped': rows_skipped,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        return {'error': str(e)}

# =============================================
# MAIN INGESTION
# =============================================

def run_ingestion():
    """Run full ingestion pipeline."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    results = []
    
    # Define file mappings
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
    
    lok_files = {
        'works_recommended': os.path.join(data_dir, 'lok_sabha', 'Works Recommended lok.csv'),
        'works_sanctioned': os.path.join(data_dir, 'lok_sabha', 'Works Sanctioned lok.csv'),
        'works_completed': os.path.join(data_dir, 'lok_sabha', 'Works Completed lok.csv'),
        'expenditure': os.path.join(data_dir, 'lok_sabha', 'Expenditure on Completed and On-going Works as on Date lok.csv'),
        'allocated_limit': os.path.join(data_dir, 'lok_sabha', 'Allocated Limit for Honble MPs (1).csv'),
        'calamity': os.path.join(data_dir, 'lok_sabha', 'Amount consented for Calamity lok.csv'),
    }
    
    rajya_files = {
        'works_recommended': os.path.join(data_dir, 'rajya_sabha', 'Works Recommended (2).csv'),
        'works_sanctioned': os.path.join(data_dir, 'rajya_sabha', 'Works Sanctioned (2).csv'),
        'works_completed': os.path.join(data_dir, 'rajya_sabha', 'Works Completed (1).csv'),
        'expenditure': os.path.join(data_dir, 'rajya_sabha', 'Expenditure on Completed and On-going Works as on Date.csv'),
        'allocated_limit': os.path.join(data_dir, 'rajya_sabha', 'Allocated Limit for Honble raj.csv'),
        'calamity': os.path.join(data_dir, 'rajya_sabha', 'Amount consented for Calamity raj.csv'),
    }
    
    # Process Lok Sabha files
    print("\n=== Processing Lok Sabha Files ===")
    for file_type, file_path in lok_files.items():
        if os.path.exists(file_path):
            print(f"\nProcessing {file_type}...")
            if file_type == 'works_recommended':
                result = process_works_recommended(file_path, 'lok_sabha', db)
            elif file_type == 'works_sanctioned':
                result = process_works_sanctioned(file_path, 'lok_sabha', db)
            elif file_type == 'works_completed':
                result = process_works_completed(file_path, 'lok_sabha', db)
            elif file_type == 'expenditure':
                result = process_expenditure(file_path, 'lok_sabha', db)
            elif file_type == 'allocated_limit':
                result = process_allocated_limit(file_path, 'lok_sabha', db)
            elif file_type == 'calamity':
                result = process_calamity(file_path, 'lok_sabha', db)
            
            results.append(result)
            print(f"  Result: {result}")
        else:
            print(f"  File not found: {file_path}")
    
    # Process Rajya Sabha files
    print("\n=== Processing Rajya Sabha Files ===")
    for file_type, file_path in rajya_files.items():
        if os.path.exists(file_path):
            print(f"\nProcessing {file_type}...")
            if file_type == 'works_recommended':
                result = process_works_recommended(file_path, 'rajya_sabha', db)
            elif file_type == 'works_sanctioned':
                result = process_works_sanctioned(file_path, 'rajya_sabha', db)
            elif file_type == 'works_completed':
                result = process_works_completed(file_path, 'rajya_sabha', db)
            elif file_type == 'expenditure':
                result = process_expenditure(file_path, 'rajya_sabha', db)
            elif file_type == 'allocated_limit':
                result = process_allocated_limit(file_path, 'rajya_sabha', db)
            elif file_type == 'calamity':
                result = process_calamity(file_path, 'rajya_sabha', db)
            
            results.append(result)
            print(f"  Result: {result}")
        else:
            print(f"  File not found: {file_path}")
    
    # Process vendors
    print("\n=== Processing Vendors ===")
    process_vendors(db)
    
    db.close()
    
    return results

def process_vendors(db):
    """Extract and aggregate vendor data from expenditures."""
    from sqlalchemy import func
    
    # Get distinct vendors with their totals
    vendor_stats = db.query(
        Expenditure.vendor_name,
        func.count(Expenditure.id).label('total_works'),
        func.sum(Expenditure.fund_disbursed_amount).label('total_expenditure')
    ).filter(
        Expenditure.vendor_name.isnot(None)
    ).group_by(
        Expenditure.vendor_name
    ).all()
    
    for vendor_name, total_works, total_expenditure in vendor_stats:
        if vendor_name:
            vendor = Vendor(
                vendor_name=vendor_name,
                total_works=total_works,
                total_expenditure=total_expenditure or 0
            )
            db.merge(vendor)
    
    db.commit()
    print(f"  Processed {len(vendor_stats)} vendors")

# =============================================
# VERIFICATION
# =============================================

def verify_ingestion():
    """Verify ingestion results."""
    db = SessionLocal()
    
    from sqlalchemy import func
    
    print("\n=== Ingestion Verification ===")
    
    # Works
    total_works = db.query(func.count(Work.id)).scalar()
    lok_works = db.query(func.count(Work.id)).filter(Work.parliament_house == 'lok_sabha').scalar()
    rajya_works = db.query(func.count(Work.id)).filter(Work.parliament_house == 'rajya_sabha').scalar()
    print(f"Works: {total_works} total ({lok_works} Lok, {rajya_works} Rajya)")
    
    # Recommendations
    total_recs = db.query(func.count(WorkRecommendation.id)).scalar()
    print(f"Recommendations: {total_recs}")
    
    # Sanctions
    total_sanctions = db.query(func.count(WorkSanction.id)).scalar()
    print(f"Sanctions: {total_sanctions}")
    
    # Completions
    total_completions = db.query(func.count(WorkCompletion.id)).scalar()
    print(f"Completions: {total_completions}")
    
    # Expenditures
    total_expenditures = db.query(func.count(Expenditure.id)).scalar()
    print(f"Expenditures: {total_expenditures}")
    
    # Vendors
    total_vendors = db.query(func.count(Vendor.id)).scalar()
    print(f"Vendors: {total_vendors}")
    
    # Allocations
    total_allocations = db.query(func.count(MPAllocation.id)).scalar()
    print(f"MP Allocations: {total_allocations}")
    
    # Calamity Consents
    total_calamity = db.query(func.count(CalamityConsent.id)).scalar()
    print(f"Calamity Consents: {total_calamity}")
    
    # Ingestion Logs
    total_logs = db.query(func.count(IngestionLog.id)).scalar()
    print(f"Ingestion Logs: {total_logs}")
    
    db.close()

if __name__ == '__main__':
    print("Starting MPLADS CSV Ingestion...")
    results = run_ingestion()
    verify_ingestion()
    print("\nIngestion complete!")
