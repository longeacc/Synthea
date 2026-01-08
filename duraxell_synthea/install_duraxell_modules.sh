#!/bin/bash

###############################################################################
# Script d'installation des modules Synthea enrichis pour DuraXell
# Projet : Le juste usage des LLM en cancérologie
# Laboratoire de Biomécanique Appliquée (LBA)
###############################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_header() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    print_header "Vérification des prérequis"
    
    # Vérifier Java
    if ! command -v java &> /dev/null; then
        print_error "Java n'est pas installé"
        echo "Installation de Java..."
        sudo apt-get update
        sudo apt-get install -y openjdk-11-jdk
    else
        JAVA_VERSION=$(java -version 2>&1 | grep -oP 'version "?\K[0-9.]+')
        print_success "Java $JAVA_VERSION détecté"
    fi
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas installé"
        exit 1
    else
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        print_success "Python $PYTHON_VERSION détecté"
    fi
    
    # Vérifier pip
    if ! command -v pip3 &> /dev/null; then
        print_warning "pip3 n'est pas installé, installation..."
        sudo apt-get install -y python3-pip
    fi
    
    # Installer les dépendances Python
    print_info "Installation des dépendances Python..."
    pip3 install pandas numpy pathlib --quiet
    print_success "Dépendances Python installées"
}

# Vérifier et installer Synthea
check_synthea() {
    print_header "Vérification de Synthea"
    
    if [ ! -d "synthea" ]; then
        print_warning "Synthea n'est pas installé, téléchargement..."
        git clone https://github.com/synthetichealth/synthea.git
        cd synthea
        print_info "Construction de Synthea (cela peut prendre quelques minutes)..."
        ./gradlew build check test
        cd ..
        print_success "Synthea installé avec succès"
    else
        print_success "Synthea déjà installé"
    fi
}

# Installer les modules enrichis
install_enhanced_modules() {
    print_header "Installation des modules enrichis DuraXell"
    
    MODULES_DIR="synthea/src/main/resources/modules"
    
    # Vérifier que les fichiers sources existent
    if [ ! -f "breast_cancer_enhanced.json" ] || [ ! -f "lung_cancer_enhanced.json" ]; then
        print_error "Les fichiers de modules enrichis sont introuvables"
        print_info "Assurez-vous que les fichiers suivants sont présents :"
        print_info "  - breast_cancer_enhanced.json"
        print_info "  - lung_cancer_enhanced.json"
        exit 1
    fi
    
    # Copier les modules
    print_info "Copie des modules enrichis..."
    cp breast_cancer_enhanced.json ${MODULES_DIR}/
    cp lung_cancer_enhanced.json ${MODULES_DIR}/
    
    # Vérifier l'installation
    if [ -f "${MODULES_DIR}/breast_cancer_enhanced.json" ] && [ -f "${MODULES_DIR}/lung_cancer_enhanced.json" ]; then
        print_success "Modules enrichis copiés avec succès"
    else
        print_error "Échec de la copie des modules"
        exit 1
    fi
    
    # Reconstruire Synthea
    print_info "Reconstruction de Synthea avec les nouveaux modules..."
    cd synthea
    ./gradlew build --quiet
    cd ..
    print_success "Synthea reconstruit avec succès"
}

# Vérifier que les modules sont bien installés
verify_installation() {
    print_header "Vérification de l'installation"
    
    MODULES_DIR="synthea/src/main/resources/modules"
    
    print_info "Modules disponibles dans Synthea :"
    ls -lh ${MODULES_DIR}/*.json | awk '{print "  - " $9}' | grep enhanced || true
    
    # Test de génération rapide
    print_info "Test de génération (1 patient cancer du sein)..."
    cd synthea
    ./run_synthea -p 1 \
        --exporter.baseDirectory=../test_output \
        -m breast_cancer_enhanced \
        --seed 99 &> /dev/null
    cd ..
    
    if [ -d "test_output/fhir" ] && [ "$(ls -A test_output/fhir)" ]; then
        print_success "Test de génération réussi"
        rm -rf test_output
    else
        print_error "Échec du test de génération"
        exit 1
    fi
}

# Créer les scripts utilitaires
create_utility_scripts() {
    print_header "Création des scripts utilitaires"
    
    # Script de génération rapide
    cat > generate_breast_cancer.sh << 'EOF'
#!/bin/bash
# Génération rapide de patients avec cancer du sein

PATIENT_COUNT=${1:-60}
OUTPUT_DIR=${2:-./output/duraxell_breast}

echo "Génération de ${PATIENT_COUNT} patients avec cancer du sein..."
cd synthea
./run_synthea -p ${PATIENT_COUNT} \
  --exporter.baseDirectory=../${OUTPUT_DIR} \
  --exporter.fhir.export=true \
  --exporter.csv.export=true \
  --exporter.clinical_note.export=true \
  -m breast_cancer_enhanced \
  --seed 42
cd ..
echo "✅ Génération terminée : ${OUTPUT_DIR}"
EOF
    chmod +x generate_breast_cancer.sh
    print_success "Script generate_breast_cancer.sh créé"
    
    # Script de génération cancer du poumon
    cat > generate_lung_cancer.sh << 'EOF'
#!/bin/bash
# Génération rapide de patients avec cancer du poumon

PATIENT_COUNT=${1:-60}
OUTPUT_DIR=${2:-./output/duraxell_lung}

echo "Génération de ${PATIENT_COUNT} patients avec cancer du poumon..."
cd synthea
./run_synthea -p ${PATIENT_COUNT} \
  --exporter.baseDirectory=../${OUTPUT_DIR} \
  --exporter.fhir.export=true \
  --exporter.csv.export=true \
  --exporter.clinical_note.export=true \
  -m lung_cancer_enhanced \
  --seed 43
cd ..
echo "✅ Génération terminée : ${OUTPUT_DIR}"
EOF
    chmod +x generate_lung_cancer.sh
    print_success "Script generate_lung_cancer.sh créé"
    
    print_info "Scripts créés :"
    print_info "  - ./generate_breast_cancer.sh [nombre_patients] [dossier_sortie]"
    print_info "  - ./generate_lung_cancer.sh [nombre_patients] [dossier_sortie]"
}

# Afficher un résumé
display_summary() {
    print_header "Installation terminée avec succès !"
    
    echo -e "${GREEN}Modules enrichis installés :${NC}"
    echo "  ✅ breast_cancer_enhanced.json"
    echo "  ✅ lung_cancer_enhanced.json"
    
    echo -e "\n${GREEN}Biomarqueurs disponibles :${NC}"
    echo "  Cancer du sein : TNM, ER, PR, HER2, Ki-67, Stades"
    echo "  Cancer du poumon : TNM, EGFR, ALK, PD-L1, FEV1, DLCO, Histologie"
    
    echo -e "\n${BLUE}Commandes de génération rapide :${NC}"
    echo "  ${YELLOW}./generate_breast_cancer.sh 60${NC}  # 60 patients cancer du sein"
    echo "  ${YELLOW}./generate_lung_cancer.sh 60${NC}   # 60 patients cancer du poumon"
    
    echo -e "\n${BLUE}Commandes manuelles :${NC}"
    echo "  ${YELLOW}cd synthea${NC}"
    echo "  ${YELLOW}./run_synthea -p 60 -m breast_cancer_enhanced${NC}"
    echo "  ${YELLOW}./run_synthea -p 60 -m lung_cancer_enhanced${NC}"
    
    echo -e "\n${BLUE}Vérification des biomarqueurs :${NC}"
    echo "  ${YELLOW}python verify_biomarkers.py ./output/duraxell_breast breast${NC}"
    echo "  ${YELLOW}python verify_biomarkers.py ./output/duraxell_lung lung${NC}"
    
    echo -e "\n${GREEN}Pour plus d'informations, consultez :${NC}"
    echo "  📄 GUIDE_INSTALLATION_BIOMARQUEURS.md"
    echo "  📄 Documentation DuraXell : DOI 10.3233/SHTI240794"
    echo ""
}

###############################################################################
# MAIN
###############################################################################

main() {
    print_header "Installation des modules Synthea enrichis DuraXell"
    
    check_prerequisites
    check_synthea
    install_enhanced_modules
    verify_installation
    create_utility_scripts
    display_summary
}

# Exécution
main "$@"
