#!/usr/bin/env python3
"""
extract_structured_biomarkers.py
Script d'extraction des biomarqueurs structurés pour le projet DuraXell

Usage:
    python extract_structured_biomarkers.py <output_dir> <cancer_type>
    
Exemples:
    python extract_structured_biomarkers.py ./output/duraxell_breast breast
    python extract_structured_biomarkers.py ./output/duraxell_lung lung
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import csv
from datetime import datetime


def extract_value_from_observation(observation: Dict) -> Optional[Any]:
    """
    Extrait la valeur d'une observation FHIR
    """
    # Valeur quantitative (avec unité)
    if 'valueQuantity' in observation:
        return observation['valueQuantity'].get('value')
    
    # Valeur codée
    if 'valueCodeableConcept' in observation:
        coding = observation['valueCodeableConcept'].get('coding', [{}])[0]
        return coding.get('display')
    
    # Valeur texte
    if 'valueString' in observation:
        return observation['valueString']
    
    return None


def extract_breast_cancer_biomarkers(patient_bundle: Dict) -> Dict:
    """
    Extrait les biomarqueurs spécifiques au cancer du sein
    """
    biomarkers = {
        'patient_id': None,
        'age': None,
        'gender': None,
        'tnm_t': None,
        'tnm_n': None,
        'tnm_m': None,
        'tnm_complete': None,
        'er_status': None,
        'er_percentage': None,
        'pr_status': None,
        'pr_percentage': None,
        'her2_status': None,
        'ki67_percentage': None,
        'clinical_stage': None,
        'pathological_stage': None,
        'histology': None,
        'diagnosis_date': None
    }
    
    for entry in patient_bundle.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        # Informations patient
        if resource_type == 'Patient':
            biomarkers['patient_id'] = resource.get('id')
            biomarkers['gender'] = resource.get('gender')
            
            # Calculer l'âge (approximatif)
            birth_date = resource.get('birthDate')
            if birth_date:
                try:
                    birth_year = int(birth_date.split('-')[0])
                    current_year = datetime.now().year
                    biomarkers['age'] = current_year - birth_year
                except:
                    pass
        
        # Condition (diagnostic)
        elif resource_type == 'Condition':
            codes = resource.get('code', {}).get('coding', [])
            for code in codes:
                display = code.get('display', '').lower()
                if 'breast' in display and 'cancer' in display:
                    biomarkers['diagnosis_date'] = resource.get('onsetDateTime')
                    
                    # Histologie
                    if 'ductal' in display:
                        biomarkers['histology'] = 'Invasive Ductal Carcinoma'
                    elif 'lobular' in display:
                        biomarkers['histology'] = 'Invasive Lobular Carcinoma'
                    elif 'triple negative' in display:
                        biomarkers['histology'] = 'Triple Negative Breast Cancer'
        
        # Observations (biomarqueurs)
        elif resource_type == 'Observation':
            code = resource.get('code', {}).get('coding', [{}])[0]
            loinc_code = code.get('code')
            display = code.get('display', '').lower()
            
            value = extract_value_from_observation(resource)
            
            # TNM
            if loinc_code == '21905-5' or 'primary tumor' in display:
                biomarkers['tnm_t'] = value
            elif loinc_code == '21906-3' or 'lymph node' in display:
                biomarkers['tnm_n'] = value
            elif loinc_code == '21907-1' or 'metasta' in display:
                biomarkers['tnm_m'] = value
            
            # ER
            elif loinc_code == '16112-5' or 'estrogen receptor' in display:
                biomarkers['er_percentage'] = value
                if value:
                    biomarkers['er_status'] = 'Positive' if float(value) > 10 else 'Negative'
            
            # PR
            elif loinc_code == '16113-3' or 'progesterone receptor' in display:
                biomarkers['pr_percentage'] = value
                if value:
                    biomarkers['pr_status'] = 'Positive' if float(value) > 10 else 'Negative'
            
            # HER2
            elif loinc_code == '48676-1' or 'her2' in display or 'her-2' in display:
                biomarkers['her2_status'] = value
            
            # Ki-67
            elif loinc_code == '85319-2' or 'ki-67' in display or 'ki67' in display:
                biomarkers['ki67_percentage'] = value
            
            # Stades
            elif 'clinical stage' in display:
                biomarkers['clinical_stage'] = value
            elif 'pathological stage' in display:
                biomarkers['pathological_stage'] = value
    
    # TNM complet
    if biomarkers['tnm_t'] and biomarkers['tnm_n'] and biomarkers['tnm_m']:
        biomarkers['tnm_complete'] = f"{biomarkers['tnm_t']}, {biomarkers['tnm_n']}, {biomarkers['tnm_m']}"
    
    return biomarkers


def extract_lung_cancer_biomarkers(patient_bundle: Dict) -> Dict:
    """
    Extrait les biomarqueurs spécifiques au cancer du poumon
    """
    biomarkers = {
        'patient_id': None,
        'age': None,
        'gender': None,
        'tnm_t': None,
        'tnm_n': None,
        'tnm_m': None,
        'tnm_complete': None,
        'histology': None,
        'egfr_mutation': None,
        'alk_status': None,
        'pdl1_percentage': None,
        'pdl1_category': None,
        'fev1_percentage': None,
        'fev1_category': None,
        'dlco_percentage': None,
        'dlco_category': None,
        'clinical_stage': None,
        'smoking_status': None,
        'diagnosis_date': None
    }
    
    for entry in patient_bundle.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        # Informations patient
        if resource_type == 'Patient':
            biomarkers['patient_id'] = resource.get('id')
            biomarkers['gender'] = resource.get('gender')
            
            birth_date = resource.get('birthDate')
            if birth_date:
                try:
                    birth_year = int(birth_date.split('-')[0])
                    current_year = datetime.now().year
                    biomarkers['age'] = current_year - birth_year
                except:
                    pass
        
        # Condition (diagnostic)
        elif resource_type == 'Condition':
            codes = resource.get('code', {}).get('coding', [])
            for code in codes:
                display = code.get('display', '').lower()
                if 'lung' in display and 'cancer' in display:
                    biomarkers['diagnosis_date'] = resource.get('onsetDateTime')
        
        # Observations
        elif resource_type == 'Observation':
            code = resource.get('code', {}).get('coding', [{}])[0]
            loinc_code = code.get('code')
            display = code.get('display', '').lower()
            
            value = extract_value_from_observation(resource)
            
            # TNM
            if loinc_code == '21905-5' or 'primary tumor' in display:
                biomarkers['tnm_t'] = value
            elif loinc_code == '21906-3' or 'lymph node' in display:
                biomarkers['tnm_n'] = value
            elif loinc_code == '21907-1' or 'metasta' in display:
                biomarkers['tnm_m'] = value
            
            # Histologie
            elif 'adenocarcinoma' in display:
                biomarkers['histology'] = 'Adenocarcinoma'
            elif 'squamous' in display:
                biomarkers['histology'] = 'Squamous Cell Carcinoma'
            elif 'large cell' in display:
                biomarkers['histology'] = 'Large Cell Carcinoma'
            elif 'small cell' in display:
                biomarkers['histology'] = 'Small Cell Lung Cancer'
            
            # EGFR
            elif loinc_code == '81691-4' or 'egfr' in display:
                biomarkers['egfr_mutation'] = value
            
            # ALK
            elif loinc_code == '80546-6' or 'alk' in display:
                biomarkers['alk_status'] = value
            
            # PD-L1
            elif loinc_code == '85147-7' or 'pd-l1' in display or 'pdl1' in display:
                biomarkers['pdl1_percentage'] = value
                if value:
                    try:
                        pdl1_val = float(value)
                        if pdl1_val >= 50:
                            biomarkers['pdl1_category'] = 'High (≥50%)'
                        elif pdl1_val >= 1:
                            biomarkers['pdl1_category'] = 'Low (1-49%)'
                        else:
                            biomarkers['pdl1_category'] = 'Negative (<1%)'
                    except:
                        pass
            
            # FEV1
            elif loinc_code == '20150-9' or 'fev1' in display:
                biomarkers['fev1_percentage'] = value
                if value:
                    try:
                        fev1_val = float(value)
                        if fev1_val >= 80:
                            biomarkers['fev1_category'] = 'Normal'
                        elif fev1_val >= 60:
                            biomarkers['fev1_category'] = 'Mild obstruction'
                        elif fev1_val >= 40:
                            biomarkers['fev1_category'] = 'Moderate obstruction'
                        else:
                            biomarkers['fev1_category'] = 'Severe obstruction'
                    except:
                        pass
            
            # DLCO
            elif loinc_code == '19911-7' or 'dlco' in display:
                biomarkers['dlco_percentage'] = value
                if value:
                    try:
                        dlco_val = float(value)
                        if dlco_val >= 75:
                            biomarkers['dlco_category'] = 'Normal'
                        elif dlco_val >= 60:
                            biomarkers['dlco_category'] = 'Mild reduction'
                        elif dlco_val >= 40:
                            biomarkers['dlco_category'] = 'Moderate reduction'
                        else:
                            biomarkers['dlco_category'] = 'Severe reduction'
                    except:
                        pass
            
            # Stade clinique
            elif 'clinical stage' in display or 'cancer stage' in display:
                biomarkers['clinical_stage'] = value
            
            # Tabagisme
            elif 'smoking' in display or 'tobacco' in display:
                biomarkers['smoking_status'] = value
    
    # TNM complet
    if biomarkers['tnm_t'] and biomarkers['tnm_n'] and biomarkers['tnm_m']:
        biomarkers['tnm_complete'] = f"{biomarkers['tnm_t']}, {biomarkers['tnm_n']}, {biomarkers['tnm_m']}"
    
    return biomarkers


def extract_biomarkers(output_dir: str, cancer_type: str) -> list:
    """
    Extrait les biomarqueurs de tous les patients
    """
    output_path = Path(output_dir)
    fhir_dir = output_path / 'fhir'
    
    if not fhir_dir.exists():
        print(f"❌ Erreur : Le répertoire {fhir_dir} n'existe pas")
        sys.exit(1)
    
    fhir_files = list(fhir_dir.glob('*.json'))
    
    if not fhir_files:
        print(f"❌ Erreur : Aucun fichier FHIR trouvé dans {fhir_dir}")
        sys.exit(1)
    
    print(f"\n🔍 Extraction des biomarqueurs de {len(fhir_files)} patients...")
    
    all_biomarkers = []
    
    for patient_file in fhir_files:
        try:
            with open(patient_file, 'r', encoding='utf-8') as f:
                patient_bundle = json.load(f)
            
            if cancer_type == 'breast':
                biomarkers = extract_breast_cancer_biomarkers(patient_bundle)
            elif cancer_type == 'lung':
                biomarkers = extract_lung_cancer_biomarkers(patient_bundle)
            else:
                continue
            
            all_biomarkers.append(biomarkers)
            
        except Exception as e:
            print(f"⚠️  Erreur lors du traitement de {patient_file.name}: {e}")
    
    return all_biomarkers


def save_to_csv(biomarkers: list, cancer_type: str, output_filename: str):
    """
    Sauvegarde les biomarqueurs dans un fichier CSV
    """
    if not biomarkers:
        print("❌ Aucun biomarqueur à sauvegarder")
        return
    
    # Obtenir toutes les colonnes
    fieldnames = list(biomarkers[0].keys())
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(biomarkers)
    
    print(f"✅ Données sauvegardées : {output_filename}")


def print_summary(biomarkers: list, cancer_type: str):
    """
    Affiche un résumé des données extraites
    """
    if not biomarkers:
        return
    
    total = len(biomarkers)
    
    print(f"\n{'='*70}")
    print(f"RÉSUMÉ DE L'EXTRACTION - Cancer {cancer_type.upper()}")
    print(f"{'='*70}\n")
    
    print(f"📊 Patients extraits : {total}")
    
    # Calculer la complétude
    complete_fields = {}
    for field in biomarkers[0].keys():
        if field in ['patient_id']:
            continue
        count = sum(1 for b in biomarkers if b.get(field) is not None)
        complete_fields[field] = count
    
    print(f"\n📋 Complétude des champs :")
    print(f"{'Champ':<25} {'Rempli':<15} {'%'}")
    print("-" * 50)
    
    for field, count in sorted(complete_fields.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        status = "✅" if percentage >= 95 else "⚠️" if percentage >= 80 else "❌"
        print(f"{field:<25} {count:>3}/{total:<3} ({percentage:>5.1f}%)  {status}")
    
    # Exemples
    print(f"\n📄 Aperçu des premières lignes :")
    print("-" * 70)
    
    example_fields = ['patient_id', 'age', 'tnm_t', 'tnm_n', 'tnm_m']
    
    if cancer_type == 'breast':
        example_fields.extend(['er_status', 'her2_status', 'ki67_percentage'])
    elif cancer_type == 'lung':
        example_fields.extend(['histology', 'egfr_mutation', 'pdl1_percentage'])
    
    for i, biomarker in enumerate(biomarkers[:3]):
        print(f"\nPatient {i+1}:")
        for field in example_fields:
            value = biomarker.get(field, 'N/A')
            if value is None:
                value = 'N/A'
            print(f"  {field:20}: {value}")
    
    print(f"\n{'='*70}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_structured_biomarkers.py <output_dir> <cancer_type>")
        print("\nExemples:")
        print("  python extract_structured_biomarkers.py ./output/duraxell_breast breast")
        print("  python extract_structured_biomarkers.py ./output/duraxell_lung lung")
        print("\nTypes de cancer supportés: breast, lung")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    cancer_type = sys.argv[2].lower()
    
    if cancer_type not in ['breast', 'lung']:
        print(f"❌ Erreur : Type de cancer '{cancer_type}' non supporté")
        print("Types supportés : breast, lung")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"EXTRACTION DES BIOMARQUEURS - PROJET DURAXELL")
    print(f"{'='*70}")
    print(f"Type de cancer : {cancer_type}")
    print(f"Répertoire     : {output_dir}")
    
    # Extraire les biomarqueurs
    biomarkers = extract_biomarkers(output_dir, cancer_type)
    
    # Sauvegarder en CSV
    output_filename = f"duraxell_dataset_{cancer_type}_structured.csv"
    save_to_csv(biomarkers, cancer_type, output_filename)
    
    # Afficher le résumé
    print_summary(biomarkers, cancer_type)
    
    print(f"\n✅ EXTRACTION TERMINÉE")
    print(f"\n📁 Fichier prêt pour annotation : {output_filename}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
