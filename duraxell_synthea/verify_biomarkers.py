#!/usr/bin/env python3
"""
verify_biomarkers.py
Script de vérification de la présence des biomarqueurs pour le projet DuraXell

Usage:
    python verify_biomarkers.py <output_dir> <cancer_type>
    
Exemples:
    python verify_biomarkers.py ./output/duraxell_breast breast
    python verify_biomarkers.py ./output/duraxell_lung lung
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Codes LOINC pour les biomarqueurs
BIOMARKER_CODES = {
    'breast': {
        'TNM_T': ['21905-5'],  # Primary tumor
        'TNM_N': ['21906-3'],  # Regional lymph nodes
        'TNM_M': ['21907-1'],  # Distant metastases
        'ER': ['16112-5'],     # Estrogen receptor
        'PR': ['16113-3'],     # Progesterone receptor
        'HER2': ['48676-1'],   # HER2
        'Ki67': ['85319-2'],   # Ki-67
        'Clinical_Stage': ['21908-9', '21902-2']  # Clinical and pathological stage
    },
    'lung': {
        'TNM_T': ['21905-5'],
        'TNM_N': ['21906-3'],
        'TNM_M': ['21907-1'],
        'Histology': ['59847-4', '31206-6'],  # Histology type
        'EGFR': ['81691-4'],   # EGFR mutation
        'ALK': ['80546-6'],    # ALK rearrangement
        'PDL1': ['85147-7'],   # PD-L1 expression
        'FEV1': ['20150-9'],   # FEV1
        'DLCO': ['19911-7']    # DLCO
    }
}

# Mots-clés pour identifier les biomarqueurs dans les descriptions
BIOMARKER_KEYWORDS = {
    'breast': {
        'TNM_T': ['primary tumor', 'tumor staging', 't stage', 'tnm t'],
        'TNM_N': ['regional lymph', 'node', 'n stage', 'tnm n', 'lymph node'],
        'TNM_M': ['distant metasta', 'm stage', 'tnm m', 'metastasis'],
        'ER': ['estrogen receptor', 'er receptor', 'er status'],
        'PR': ['progesterone receptor', 'pr receptor', 'pr status'],
        'HER2': ['her2', 'her-2', 'erbb2'],
        'Ki67': ['ki-67', 'ki67', 'mib-1'],
        'Clinical_Stage': ['clinical stage', 'pathological stage', 'cancer stage']
    },
    'lung': {
        'TNM_T': ['primary tumor', 'tumor staging', 't stage', 'tnm t'],
        'TNM_N': ['regional lymph', 'node', 'n stage', 'tnm n', 'lymph node'],
        'TNM_M': ['distant metasta', 'm stage', 'tnm m', 'metastasis'],
        'Histology': ['histolog', 'carcinoma', 'adenocarcinoma', 'squamous'],
        'EGFR': ['egfr', 'epidermal growth factor'],
        'ALK': ['alk', 'anaplastic lymphoma kinase'],
        'PDL1': ['pd-l1', 'pdl1', 'programmed death'],
        'FEV1': ['fev1', 'forced expiratory volume'],
        'DLCO': ['dlco', 'diffusing capacity']
    }
}


def check_biomarker_in_observation(observation: Dict, biomarker_codes: List[str], 
                                   keywords: List[str]) -> bool:
    """
    Vérifie si une observation correspond à un biomarqueur
    """
    # Vérifier le code LOINC
    codes = observation.get('code', {}).get('coding', [])
    for code in codes:
        if code.get('code') in biomarker_codes:
            return True
    
    # Vérifier les mots-clés dans la description
    display = observation.get('code', {}).get('coding', [{}])[0].get('display', '').lower()
    text = observation.get('code', {}).get('text', '').lower()
    
    for keyword in keywords:
        if keyword.lower() in display or keyword.lower() in text:
            return True
    
    return False


def analyze_patient_file(patient_file: Path, cancer_type: str) -> Tuple[str, Set[str]]:
    """
    Analyse un fichier patient FHIR et retourne les biomarqueurs trouvés
    """
    patient_id = patient_file.stem
    found_biomarkers = set()
    
    try:
        with open(patient_file, 'r', encoding='utf-8') as f:
            patient_bundle = json.load(f)
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture de {patient_file.name}: {e}")
        return patient_id, found_biomarkers
    
    biomarker_config = BIOMARKER_CODES.get(cancer_type, {})
    keyword_config = BIOMARKER_KEYWORDS.get(cancer_type, {})
    
    # Parcourir toutes les entrées du bundle
    for entry in patient_bundle.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        if resource_type == 'Observation':
            # Vérifier chaque biomarqueur
            for biomarker_name, codes in biomarker_config.items():
                keywords = keyword_config.get(biomarker_name, [])
                if check_biomarker_in_observation(resource, codes, keywords):
                    found_biomarkers.add(biomarker_name)
    
    return patient_id, found_biomarkers


def verify_biomarkers(output_dir: str, cancer_type: str) -> Dict:
    """
    Vérifie la présence des biomarqueurs dans tous les patients
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
    
    print(f"\n🔍 Analyse de {len(fhir_files)} patients...")
    
    required_biomarkers = set(BIOMARKER_CODES.get(cancer_type, {}).keys())
    stats = {biomarker: 0 for biomarker in required_biomarkers}
    missing_patients = []
    
    # Analyser chaque patient
    for patient_file in fhir_files:
        patient_id, found_biomarkers = analyze_patient_file(patient_file, cancer_type)
        
        # Mettre à jour les statistiques
        for biomarker in found_biomarkers:
            if biomarker in stats:
                stats[biomarker] += 1
        
        # Identifier les biomarqueurs manquants
        missing = required_biomarkers - found_biomarkers
        if missing:
            missing_patients.append({
                'patient_id': patient_id,
                'missing': list(missing),
                'found': list(found_biomarkers)
            })
    
    return {
        'total_patients': len(fhir_files),
        'stats': stats,
        'missing_patients': missing_patients,
        'required_biomarkers': list(required_biomarkers)
    }


def print_report(results: Dict, cancer_type: str):
    """
    Affiche le rapport de vérification
    """
    total = results['total_patients']
    stats = results['stats']
    missing = results['missing_patients']
    required = results['required_biomarkers']
    
    print(f"\n{'='*70}")
    print(f"RAPPORT DE VÉRIFICATION - Cancer {cancer_type.upper()}")
    print(f"{'='*70}\n")
    
    print(f"📊 Patients analysés : {total}")
    print(f"📋 Biomarqueurs requis : {len(required)}")
    print(f"\n{'Biomarqueur':<20} {'Présent':<12} {'Couverture':<15} {'Statut'}")
    print("-" * 70)
    
    all_complete = True
    for biomarker in sorted(required):
        count = stats.get(biomarker, 0)
        percentage = (count / total * 100) if total > 0 else 0
        status = "✅" if percentage >= 95 else "⚠️" if percentage >= 80 else "❌"
        
        if percentage < 95:
            all_complete = False
        
        print(f"{biomarker:<20} {count:>3}/{total:<3}     {percentage:>5.1f}%          {status}")
    
    print("-" * 70)
    
    if missing:
        print(f"\n⚠️  ATTENTION : {len(missing)} patients avec biomarqueurs manquants")
        print(f"\nExemples (premiers 5 patients) :")
        
        for patient in missing[:5]:
            print(f"\n  Patient : {patient['patient_id']}")
            print(f"    Trouvés   : {', '.join(patient['found']) if patient['found'] else 'Aucun'}")
            print(f"    Manquants : {', '.join(patient['missing'])}")
    else:
        print(f"\n✅ SUCCÈS : Tous les patients ont tous les biomarqueurs requis !")
    
    # Résumé final
    print(f"\n{'='*70}")
    if all_complete and not missing:
        print("🎉 VALIDATION RÉUSSIE - Dataset prêt pour annotation")
    else:
        print("⚠️  VALIDATION INCOMPLÈTE - Vérifier les biomarqueurs manquants")
    print(f"{'='*70}\n")
    
    return all_complete and not missing


def main():
    if len(sys.argv) < 3:
        print("Usage: python verify_biomarkers.py <output_dir> <cancer_type>")
        print("\nExemples:")
        print("  python verify_biomarkers.py ./output/duraxell_breast breast")
        print("  python verify_biomarkers.py ./output/duraxell_lung lung")
        print("\nTypes de cancer supportés: breast, lung")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    cancer_type = sys.argv[2].lower()
    
    if cancer_type not in ['breast', 'lung']:
        print(f"❌ Erreur : Type de cancer '{cancer_type}' non supporté")
        print("Types supportés : breast, lung")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"VÉRIFICATION DES BIOMARQUEURS - PROJET DURAXELL")
    print(f"{'='*70}")
    print(f"Type de cancer : {cancer_type}")
    print(f"Répertoire     : {output_dir}")
    
    results = verify_biomarkers(output_dir, cancer_type)
    success = print_report(results, cancer_type)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
