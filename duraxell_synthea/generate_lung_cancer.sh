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
