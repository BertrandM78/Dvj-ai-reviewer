# DVJ Proposal Reviewer — Benchmark V2

Benchmark: 5 propositions, 28 obligations par proposition, 140 décisions.

## Résultats globaux

- Accuracy 4 classes : **81.43%** (114/140)
- Violation precision : **73.33%**
- Violation recall : **78.57%**
- Violation F1 : **75.86%**
- Abstention rate : **7.86%** (11/140)
- NOT_APPLICABLE accuracy : **90.00%** (9/10)
- NOT_EVALUATED accuracy : **50.00%** (6/12)

## Détection des violations

| TP | FP | FN | TN | Décisions C/NC |
|---:|---:|---:|---:|---:|
| 22 | 8 | 6 | 77 | 118 |

## Distribution des statuts

| Statut | Ground truth | Prédiction |
|---|---:|---:|
| COMPLIANT | 90 | 86 |
| NON_COMPLIANT | 28 | 32 |
| NOT_EVALUATED | 12 | 11 |
| NOT_APPLICABLE | 10 | 11 |

## Matrice de confusion

| GT \ Pred | COMPLIANT | NON_COMPLIANT | NOT_EVALUATED | NOT_APPLICABLE |
|---|---:|---:|---:|---:|
| COMPLIANT | 77 | 8 | 5 | 0 |
| NON_COMPLIANT | 6 | 22 | 0 | 0 |
| NOT_EVALUATED | 3 | 1 | 6 | 2 |
| NOT_APPLICABLE | 0 | 1 | 0 | 9 |

## Résultats par proposition

| Proposition | Accuracy | Precision | Recall | F1 | Erreurs |
|---|---:|---:|---:|---:|---:|
| P001 | 92.86% | 100.00% | 85.71% | 92.31% | 2 |
| P002 | 78.57% | 50.00% | 50.00% | 50.00% | 6 |
| P003 | 75.00% | 83.33% | 71.43% | 76.92% | 7 |
| P004 | 85.71% | 66.67% | 100.00% | 80.00% | 4 |
| P005 | 75.00% | 62.50% | 83.33% | 71.43% | 7 |

## Erreurs détaillées

### P001 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1044-1068-1102 est présente et cohérente.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P001 — RULE_016

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : La répartition temporelle du planning n'est pas cohérente avec les durées annoncées dans la méthodologie.
- Explication modèle : Les durées des phases sont cohérentes entre la méthodologie et le planning.

### P002 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1045-1069-1103 est présente.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P002 — RULE_005

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Le besoin est clairement exposé : clarification des rôles, organisation du travail, circuits de décision et transmission des savoir-faire.
- Explication modèle : La proposition ne démontre pas une compréhension explicite du contexte commercial, du client, de ses enjeux et de son besoin. Les informations sur le mode de mise en relation avec DeVinci Junior, le contexte de l'entreprise cliente et les principaux enjeux liés à la mission sont manquantes.

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

### P002 — RULE_025

- Ground truth : `NOT_APPLICABLE`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Aucune licence ou ressource externe payante nécessaire à la mission n'est identifiée.
- Explication modèle : Le budget contient au moins un coût externe sans besoin externe identifiable dans la méthodologie.

### P002 — RULE_027

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Les profils présentés ne démontrent pas suffisamment une adéquation avec les compétences attendues pour une mission de structuration organisationnelle.
- Explication modèle : Le cursus, la formation ou la spécialisation des contributeurs est cohérent avec la nature des travaux qui leur sont confiés.

### P003 — RULE_002

- Ground truth : `COMPLIANT`
- Prédiction : `NOT_EVALUATED`
- Raison GT : La référence DE-0926-1046-1070-1104 est présente.
- Explication modèle : Le format de la référence est valide, mais la date de proposition n'a pas pu être extraite ; la cohérence MMYY ne peut donc pas être vérifiée.

### P003 — RULE_007

- Ground truth : `NON_COMPLIANT`
- Prédiction : `COMPLIANT`
- Raison GT : Le besoin n'étant pas explicité, la proposition ne permet pas d'établir explicitement la cohérence entre besoin et solution.
- Explication modèle : La solution proposée répond de manière cohérente aux besoins et enjeux identifiés.

### P003 — RULE_008

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Deux références de missions sont présentées.
- Explication modèle : La proposition ne présente pas de références permettant d'illustrer l'expérience de DeVinci Junior.

### P003 — RULE_011

- Ground truth : `NOT_EVALUATED`
- Prédiction : `COMPLIANT`
- Raison GT : L'absence de besoin explicite empêche d'évaluer proprement la cohérence entre le besoin et la méthodologie.
- Explication modèle : La méthodologie couvre les principaux besoins et objectifs annoncés dans la proposition.

### P003 — RULE_016

- Ground truth : `NOT_EVALUATED`
- Prédiction : `COMPLIANT`
- Raison GT : La durée de la phase 3 étant absente de la méthodologie, sa cohérence avec le planning ne peut pas être vérifiée complètement.
- Explication modèle : Les durées des phases sont cohérentes entre la méthodologie et le planning.

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

### P004 — RULE_025

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NOT_APPLICABLE`
- Raison GT : La mission dépend de plateformes et ressources externes, notamment Meta et Shopify, et un budget publicitaire de 1000 à 1500 EUR est mentionné, mais son traitement comme coût externe dans le budget de la mission n'est pas suffisamment caractérisé.
- Explication modèle : Aucune ressource externe n'est explicitement identifiée dans la méthodologie et aucun coût externe n'est budgété.

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

### P005 — RULE_016

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les durées représentées dans les différents plannings correspondent aux durées annoncées pour les phases.
- Explication modèle : Certaines durées annoncées dans la méthodologie ne sont pas cohérentes avec le planning.

### P005 — RULE_017

- Ground truth : `COMPLIANT`
- Prédiction : `NON_COMPLIANT`
- Raison GT : Les durées globales annoncées sont cohérentes avec les plannings et les éventuels chevauchements des phases.
- Explication modèle : La durée totale annoncée ne correspond pas à la durée représentée dans le planning.

### P005 — RULE_025

- Ground truth : `NOT_EVALUATED`
- Prédiction : `NOT_APPLICABLE`
- Raison GT : Certaines prestations nécessitent des ressources ou services externes, notamment un imprimeur, un hébergement et potentiellement des plugins WordPress, sans coût externe suffisamment caractérisé dans les budgets.
- Explication modèle : Aucune ressource externe n'est explicitement identifiée dans la méthodologie et aucun coût externe n'est budgété.

## Méthodologie

Les métriques de détection d'anomalies utilisent uniquement les décisions dont la ground truth est COMPLIANT ou NON_COMPLIANT. NON_COMPLIANT est la classe positive.

Les ground truths NOT_APPLICABLE et NOT_EVALUATED sont exclues du calcul de precision/recall/F1 et évaluées séparément.

Une prédiction NOT_EVALUATED sur une règle réellement NON_COMPLIANT est considérée comme une violation manquée (false negative). Une prédiction NOT_EVALUATED sur une règle COMPLIANT est comptabilisée comme abstention et non comme false positive.

Les métriques globales sont calculées en poolant toutes les décisions. Elles ne correspondent pas à la moyenne des pourcentages par proposition.
