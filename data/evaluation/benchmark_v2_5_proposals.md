# DVJ Proposal Reviewer — Benchmark V2

Benchmark: 5 propositions, 28 obligations par proposition, 140 décisions.

## Résultats globaux

- Accuracy 4 classes : **72.14%** (101/140)
- Violation precision : **55.88%**
- Violation recall : **63.33%**
- Violation F1 : **59.38%**
- Abstention rate : **8.57%** (12/140)
- NOT_APPLICABLE accuracy : **90.00%** (9/10)
- NOT_EVALUATED accuracy : **50.00%** (6/12)

## Détection des violations

| TP | FP | FN | TN | Décisions C/NC |
|---:|---:|---:|---:|---:|
| 19 | 15 | 11 | 67 | 118 |

## Distribution des statuts

| Statut | Ground truth | Prédiction |
|---|---:|---:|
| COMPLIANT | 88 | 79 |
| NON_COMPLIANT | 30 | 38 |
| NOT_EVALUATED | 12 | 12 |
| NOT_APPLICABLE | 10 | 11 |

## Matrice de confusion

| GT \ Pred | COMPLIANT | NON_COMPLIANT | NOT_EVALUATED | NOT_APPLICABLE |
|---|---:|---:|---:|---:|
| COMPLIANT | 67 | 15 | 6 | 0 |
| NON_COMPLIANT | 11 | 19 | 0 | 0 |
| NOT_EVALUATED | 1 | 3 | 6 | 2 |
| NOT_APPLICABLE | 0 | 1 | 0 | 9 |

## Résultats par proposition

| Proposition | Accuracy | Precision | Recall | F1 | Erreurs |
|---|---:|---:|---:|---:|---:|
| P001 | 85.71% | 85.71% | 85.71% | 85.71% | 4 |
| P002 | 71.43% | 40.00% | 40.00% | 40.00% | 8 |
| P003 | 64.29% | 50.00% | 71.43% | 58.82% | 10 |
| P004 | 78.57% | 57.14% | 100.00% | 72.73% | 6 |
| P005 | 60.71% | 40.00% | 28.57% | 33.33% | 11 |

## Erreurs détaillées

### P001 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1044-1068-1102 est présente et cohérente.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P001 — RULE_006

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : La solution proposée est explicitement décrite.
- Explication modèle : L'impact, la valeur ou le bénéfice attendu pour le client n'est pas expliqué.

### P001 — RULE_016

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : La répartition temporelle du planning n'est pas cohérente avec les durées annoncées dans la méthodologie.
- Explication modèle : Les durées des phases sont cohérentes entre la méthodologie et le planning.

### P001 — RULE_027

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les informations disponibles ne permettent pas d'évaluer suffisamment les compétences des contributeurs.
- Explication modèle : Les compétences des intervenants ne sont pas explicitement présentées.

### P002 — RULE_001

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les principales sections obligatoires de la proposition sont présentes.
- Explication modèle : Certaines slides ou sections obligatoires sont absentes.

### P002 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1045-1069-1103 est présente.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P002 — RULE_006

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : La section solution reste générique et indique seulement un accompagnement pour répondre à la problématique sans expliciter la solution proposée.
- Explication modèle : La proposition explique clairement ce que DeVinci Junior propose de réaliser et la valeur attendue pour le client.

### P002 — RULE_007

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : La section solution ne matérialise pas explicitement le lien entre les besoins exposés et une solution structurée.
- Explication modèle : La solution proposée répond de manière cohérente aux besoins et enjeux identifiés.

### P002 — RULE_015

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les quatre phases conservent des titres et un ordre cohérents entre méthodologie, planning et budget.
- Explication modèle : Les phases ne sont pas cohérentes entre la méthodologie, le planning et le budget.

### P002 — RULE_024

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les frais liés à la plateforme d'appels d'offres sont explicitement budgétés à 130 EUR.
- Explication modèle : Les frais applicables à l'appel d'offres ne sont pas intégrés au budget.

### P002 — RULE_025

- Ground truth : `NOT_APPLICABLE`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Aucune licence ou ressource externe payante nécessaire à la mission n'est identifiée.
- Explication modèle : Le budget contient au moins un coût externe sans besoin externe identifiable dans la méthodologie.

### P002 — RULE_027

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Les profils présentés ne démontrent pas suffisamment une adéquation avec les compétences attendues pour une mission de structuration organisationnelle.
- Explication modèle : Les compétences explicitement présentées pour les intervenants sont cohérentes avec les exigences techniques et métier de la mission.

### P003 — RULE_001

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les principales sections obligatoires de la proposition sont présentes.
- Explication modèle : Certaines slides ou sections obligatoires sont absentes.

### P003 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1046-1070-1104 est présente.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P003 — RULE_006

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : La solution décrit concrètement une enquête terrain, la collecte et le contrôle des réponses ainsi que la remise de bases structurées et d'une synthèse.
- Explication modèle : L'impact, la valeur ou le bénéfice attendu pour le client n'est pas expliqué.

### P003 — RULE_008

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Deux références de missions sont présentées.
- Explication modèle : Aucune référence n'est présentée dans la proposition.

### P003 — RULE_009

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : La phase 1 ne comporte que deux actions méthodologiques explicites.
- Explication modèle : Toutes les phases contiennent au moins 3 étapes.

### P003 — RULE_011

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NON_COMPLIANT`
- Raison GT : L'absence de besoin explicite empêche d'évaluer proprement la cohérence entre le besoin et la méthodologie.
- Explication modèle : La méthodologie ne couvre pas les principaux besoins et objectifs annoncés dans la proposition.

### P003 — RULE_015

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les titres et l'ordre des phases sont cohérents entre méthodologie, planning et budget.
- Explication modèle : Les phases ne sont pas cohérentes entre la méthodologie, le planning et le budget.

### P003 — RULE_024

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les frais liés à la plateforme d'appels d'offres sont explicitement budgétés à 130 EUR.
- Explication modèle : Les frais applicables à l'appel d'offres ne sont pas intégrés au budget.

### P003 — RULE_025

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Des outils externes tels que Tally et Apollo sont mentionnés, mais le document ne permet pas de déterminer si leur utilisation implique des coûts ou licences à intégrer.
- Explication modèle : Le budget contient au moins un coût externe sans besoin externe identifiable dans la méthodologie.

### P003 — RULE_026

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : La phase d'enquête terrain prévoit 400 répondants en face-à-face avec contraintes de quotas, lieux et suivi quotidien pour seulement 4 JEH, ce qui rend la charge annoncée incohérente avec le périmètre.
- Explication modèle : La charge en JEH est cohérente avec l'ampleur des travaux et livrables annoncés.

### P004 — RULE_001

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les principales sections obligatoires de la proposition sont présentes.
- Explication modèle : Certaines slides ou sections obligatoires sont absentes.

### P004 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1047-1071-1105 est présente sur la proposition.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P004 — RULE_010

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Durée, nombre de JEH et prix HT sont indiqués pour chacune des quatre phases.
- Explication modèle : Certaines phases ne présentent pas toutes les informations obligatoires.

### P004 — RULE_013

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les formats sont explicités lorsque pertinents : PDF, DOCX/PDF et campagnes activées dans le Business Manager.
- Explication modèle : Le format des livrables n'est pas précisé pour toutes les phases.

### P004 — RULE_016

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : Les durées représentées pour les phases sont cohérentes avec les durées méthodologiques de 2, 3, 8 et 1 semaines.
- Explication modèle : Certaines durées nécessaires à la comparaison sont absentes : phases [1].

### P004 — RULE_025

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NOT_APPLICABLE`
- Raison GT : La mission dépend de plateformes et ressources externes, notamment Meta et Shopify, et un budget publicitaire de 1000 à 1500 EUR est mentionné, mais son traitement comme coût externe dans le budget de la mission n'est pas suffisamment caractérisé.
- Explication modèle : Aucune ressource externe n'est explicitement identifiée dans la méthodologie et aucun coût externe n'est budgété.

### P005 — RULE_001

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les principales sections obligatoires de la proposition sont présentes.
- Explication modèle : Certaines slides ou sections obligatoires sont absentes.

### P005 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1048-1072-1106 est présente sur la couverture.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P005 — RULE_012

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Toutes les phases ne disposent pas d'un livrable explicitement identifié, notamment la phase de sélection d'un imprimeur et la phase de développement du site.
- Explication modèle : Les livrables associés à chaque phase sont explicitement identifiés.

### P005 — RULE_013

- Ground truth : `NOT_EVALUATED`
- Prédiction : `COMPLIANT`
- Raison GT : Les livrables explicitement identifiés ont généralement un format, mais certaines phases n'identifient pas suffisamment leur livrable pour permettre d'en contrôler le format.
- Explication modèle : Le format des livrables est précisé pour chaque phase lorsque celle-ci produit un livrable.

### P005 — RULE_015

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Pour chacun des blocs de prestation, les intitulés et l'ordre des phases sont cohérents entre méthodologie, planning et budget.
- Explication modèle : Les phases ne sont pas cohérentes entre la méthodologie, le planning et le budget.

### P005 — RULE_017

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les durées globales annoncées sont cohérentes avec les plannings et les éventuels chevauchements des phases.
- Explication modèle : La durée totale annoncée ne correspond pas à la durée représentée dans le planning.

### P005 — RULE_020

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Le bloc Réseaux sociaux indique 3 JEH dans la méthodologie mais 5 JEH dans le budget. Le budget affiche en outre un total de 4 JEH alors que ses lignes indiquent 5 JEH de production et 1 JEH de gestion.
- Explication modèle : Les JEH sont cohérents entre la méthodologie et le budget. Les éventuelles phases absentes du budget sont explicitement gratuites.

### P005 — RULE_021

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Le budget Réseaux sociaux contient une incohérence arithmétique : 5 JEH à 70 EUR devraient représenter 350 EUR HT et non les 420 EUR HT affichés.
- Explication modèle : Les montants des phases sont cohérents entre la méthodologie et le budget. Les éventuelles phases absentes du budget sont explicitement gratuites.

### P005 — RULE_023

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Le budget Réseaux sociaux affiche explicitement un prix unitaire de 70 EUR HT par JEH, inférieur au minimum autorisé de 80 EUR HT.
- Explication modèle : Le prix unitaire par JEH respecte la plage autorisée pour toutes les phases.

### P005 — RULE_025

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NOT_APPLICABLE`
- Raison GT : Certaines prestations nécessitent des ressources ou services externes, notamment un imprimeur, un hébergement et potentiellement des plugins WordPress, sans coût externe suffisamment caractérisé dans les budgets.
- Explication modèle : Aucune ressource externe n'est explicitement identifiée dans la méthodologie et aucun coût externe n'est budgété.

### P005 — RULE_027

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Le profil d'intervenante présenté est pertinent pour le marketing digital et les réseaux sociaux mais ne démontre pas les compétences en design graphique, packaging et développement WordPress nécessaires à l'ensemble des prestations proposées.
- Explication modèle : Les compétences explicitement présentées pour les intervenants sont cohérentes avec les exigences techniques et métier de la mission.

## Méthodologie

Les métriques de détection d'anomalies utilisent uniquement les décisions dont la ground truth est COMPLIANT ou NON_COMPLIANT. NON_COMPLIANT est la classe positive.

Les ground truths NOT_APPLICABLE et NOT_EVALUATED sont exclues du calcul de precision/recall/F1 et évaluées séparément.

Une prédiction NOT_EVALUATED sur une règle réellement NON_COMPLIANT est considérée comme une violation manquée (false negative). Une prédiction NOT_EVALUATED sur une règle COMPLIANT est comptabilisée comme abstention et non comme false positive.

Les métriques globales sont calculées en poolant toutes les décisions. Elles ne correspondent pas à la moyenne des pourcentages par proposition.
