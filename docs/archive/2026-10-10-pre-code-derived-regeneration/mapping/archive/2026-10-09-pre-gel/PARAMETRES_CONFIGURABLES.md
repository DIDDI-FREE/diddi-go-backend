# Registre unique des paramètres configurables

Date de relevé : 9 octobre 2026.

**Pourquoi ce fichier existe.** Les montants, taux, seuils et plafonds ne sont pas arrêtés et vont
bouger, y compris pendant le lancement, selon ce que dira le marché. Les isoler ici évite que les
documents de parcours vieillissent à chaque ajustement commercial. Les parcours décrivent le
**comportement** ; ce fichier porte les **valeurs**.

Règle de lecture, reprise de `PROD-043` : « Les comportements constituent le périmètre produit. Les
montants, taux et plafonds ajustables de tous les modules sont centralisés ; leurs valeurs ne sont pas
figées pour le lancement et peuvent évoluer selon le marché. Les anciens chiffres de discussion ou de
Jira sont des repères historiques, pas des obligations chiffrées définitives. »

**Deux colonnes, deux natures.** Le *repère produit* est un chiffre de cadrage, révisable, dont
l'autorité est `E:\DIDDI AI\diddi-scope-document\PARAMETRES_METIER.md`. La *valeur en vigueur* est un
fait sur le système tel qu'il tourne aujourd'hui. Les deux peuvent légitimement différer ; l'écart n'est
pas en soi un défaut. Une modification de ce fichier ne modifie aucune configuration déployée.

> Ce registre est hébergé dans `diddi-go` parce que c'est là qu'on travaille. S'il doit servir à tous les
> modules, sa place logique est `diddi-scope-document`, à côté de `PARAMETRES_METIER.md`. À arbitrer.

---

## 1. Règle de configuration et mécanismes

**Décision du 9 octobre 2026 — ticket `SCRUM-584`.** Tout paramètre ajustable doit être configurable
**par variable d'environnement**, dans tous les modules. Conséquence voulue : **aucune modification à
chaud**. Un changement qui modifie le fonctionnement de l'application passe par un redéploiement
traçable. C'est intentionnel, pas une limitation subie.

| Mécanisme | Effet | Statut au regard de la règle |
| --- | --- | --- |
| **Variable d'environnement** | redéploiement de la stack, pas de modification de code | ✅ **conforme** — c'est la cible |
| **Constante de code** | modification de code, revue et déploiement | ❌ **dérive** — pas configurable sans toucher au code |
| **Ligne en base éditable à chaud** | changement sans redéploiement ni trace de déploiement | ❌ **dérive** — précisément ce que la règle interdit |

La colonne « Mécanisme » des tableaux suivants se lit donc comme un verdict de conformité. Chaque dérive
relevée a reçu un ticket, listé en section 11.

La règle porte sur le **mécanisme**, pas sur les valeurs. Les valeurs restent révisables selon le marché
(`PROD-043`) — mais elles se révisent par redéploiement, pas par édition en ligne.

---

## 2. DiddiGo — tarification et commission

| Clé documentaire | Repère produit | Unité | Valeur en vigueur | Mécanisme | Emplacement |
| --- | --- | --- | --- | --- | --- |
| `go.commission_rate` | 18 | % | 0,08 (8 %) | **constante de code** | `app_base/modules/ride/application/services.py:51` |
| `go.surge_cap` (V1) | 1,5 | multiplicateur | 1,60 | **constante de code** | `services.py:50` |
| tarif de base | non fixé | XOF | 250 (défaut) | base, sinon constante | règle tarifaire active, sinon `services.py:47` |
| prix au kilomètre | non fixé | XOF | 240 (défaut) | base, sinon constante | règle tarifaire active, sinon `services.py:48` |
| prix à la minute | non fixé | XOF | 0 (défaut) | base, sinon constante | règle tarifaire active, sinon `services.py:49` |
| multiplicateur de majoration | — | multiplicateur | lu en base, borné par le plafond | **base** | règle tarifaire active |
| multiplicateurs de confort | non fixés | multiplicateur | trois niveaux | **constante de code** | `_comfort_multiplier`, `services.py` |

Le taux de commission et le barème sont **figés sur chaque course à sa création**
(`services.py:160`) : un changement de valeur n'affecte que les courses postérieures et ne réécrit pas
l'historique. C'est exactement la gouvernance demandée par `PARAMETRES_METIER.md` (« conserver les
montants et règles acceptés pour les opérations déjà engagées ; aucune réécriture d'historique »).

Conséquence à connaître avant tout ajustement : le taux alimente les contrôles comptables bloquants de
`/internal/pilotage/finance-summary` (`platform_commission + driver_earnings == completed_fare_total`).

## 3. DiddiGo — attente et escales

| Clé documentaire | Repère produit | Unité | Valeur en vigueur | Mécanisme | Emplacement |
| --- | --- | --- | --- | --- | --- |
| `go.pickup_wait_rate` | 100 | XOF/min | 100 | **environnement** | `waiting_price_per_minute_xof`, `settings.py:129` |
| franchise d'attente de prise en charge | 180 | s | aucune franchise | — | non implémentée |
| `go.stop_wait_rate` | 100 | XOF/min | même tarif que ci-dessus | **environnement** | idem |
| franchise d'escale | 60 | s | à vérifier | — | `add_stop` / `_stop_waiting` |
| seuil de véhicule arrêté | non fixé | km/h | 3,0 | **environnement** | `waiting_stationary_speed_threshold_kmh`, `settings.py:130` |
| âge maximal de la télémétrie | non fixé | s | 30 | **environnement** | `waiting_telemetry_ttl_seconds`, `settings.py:131` |
| distance de validation d'arrivée | 50 | m | — | — | non implémentée |

## 4. DiddiGo — annulation et fin anticipée

| Clé documentaire | Repère produit | Unité | Valeur en vigueur | Mécanisme | Emplacement |
| --- | --- | --- | --- | --- | --- |
| `go.early_end_free_threshold` | 300 | XOF | — | — | non implémenté |
| délai avant déclaration de client absent | 600 | s | — | — | non implémenté côté serveur |

## 5. DiddiGo — recherche de chauffeur et devis

| Clé documentaire | Repère produit | Unité | Valeur en vigueur | Mécanisme | Emplacement |
| --- | --- | --- | --- | --- | --- |
| rayon de la phase 1 | 1 | km | pas uniforme de 2 km | **environnement** | `matching_search_radius_step_km`, `settings.py:64` |
| rayon de la phase 2 | 3 | km | idem (élargissement par pas) | **environnement** | idem |
| rayon de la phase 3 / plafond | 5 | km | 15 | **environnement** | `matching_search_radius_max_km`, `settings.py:65` |
| durée de la phase 1 | 30 | s | pas de phases nommées | — | modèle différent |
| durée de la phase 2 | 60 | s | idem | — | modèle différent |
| durée de la phase 3 | 180 | s | idem | — | modèle différent |
| budget total de recherche | 270 | s | 120 | **environnement** | `matching_search_budget_seconds`, `settings.py:66` |
| fenêtre de réponse à une offre | non fixée | s | 15 | à vérifier | moteur de matching, couvert par `test_matching.py` |
| validité d'un devis | 900 | s | aucune expiration | — | non implémentée |
| voisinage de déduplication des devis | 1 | km | — | — | non implémenté |
| fenêtre de déduplication des devis | 1 200 | s | — | — | non implémenté |
| taille de la liste courte reclassée par temps de trajet | non fixée | candidats | 10 | **environnement** | `matching_eta_shortlist_size`, `settings.py:59` |

## 6. DiddiGo — priorité chauffeur

Ces valeurs amorcent une configuration **stockée en base**, modifiable par
`PUT /internal/v1/admin/dispatch/config` — c'est le seul bloc de paramètres métier DiddiGo réellement
pilotable à chaud aujourd'hui.

| Clé documentaire | Repère produit | Unité | Valeur d'amorçage | Emplacement |
| --- | --- | --- | --- | --- |
| fenêtre glissante | non fixée | jours | 7 | `settings.py:71` |
| plafond du bonus | non fixé | s | 120 | `settings.py:72` |
| secondes par point | non fixé | s | 10 | `settings.py:73` |
| points par course terminée | non fixé | points | +1 | `settings.py:74` |
| points par annulation chauffeur | non fixé | points | −3 | `settings.py:75` |

## 7. DiddiGo — éligibilité et wallet chauffeur

| Clé documentaire | Repère produit | Unité | Valeur en vigueur | Mécanisme | Emplacement |
| --- | --- | --- | --- | --- | --- |
| `go.online_min_balance` | **non fixé** | XOF | 0 (contrôle neutre) | **environnement** | `driver_min_balance`, `settings.py:124` |
| plafond de commission estimée | non fixé | XOF | 0 (contrôle neutre) | **environnement** | `driver_max_estimated_commission`, `settings.py:125` |
| `professional.withdrawal_minimum` | **aucun minimum commercial** | XOF | — | — | aucune route de retrait exposée |
| `professional.withdrawal_fee` | frais réels, ~3 % cité à titre indicatif | cotation PSP | — | — | idem |

## 8. Clés métier des autres modules

Reprises de `PARAMETRES_METIER.md` pour que le registre soit complet. La colonne d'implémentation n'a
**pas** été relevée : je n'ai pas lu le code de DiddiSend, DiddiFood, DiddiPay ni du Backoffice.

| Clé documentaire | Module | Repère produit | Unité | Comportement associé | Implémentation |
| --- | --- | --- | --- | --- | --- |
| `send.commission_rate` | Send | 18 | % | sur la livraison uniquement, hors valeur du colis | non relevée |
| `food.commission_rate` | Food | 15 | % | sur les plats, indépendamment de la livraison | non relevée |
| `send.cash_outstanding_limit` | Send | 15 000 | XOF | blocage dès plafond atteint **ou** échéance dépassée ; mission active préservée | non relevée |
| `send.cash_warning_amount` | Send | 10 000 | XOF | avertissement avant blocage | non relevée |
| `send.online_min_balance` | Send, livreurs Food inclus | 1 000 | XOF | minimum de mise en ligne, distinct du cash dû et du retrait | non relevée |
| `send.redelivery_price` | Send | **non fixé** | XOF | nouveau devis accepté par le donneur d'ordre | non relevée |
| `send.return_price` | Send | **non fixé** | XOF | payé par le donneur d'ordre si l'échec lui est imputable | non relevée |
| `send.declared_value_limit` | Send | **non fixé** | XOF | limite d'acceptation, distincte d'une garantie d'indemnisation | non relevée |
| `send.compensation_limit` | Send | **non fixé** | XOF | politique de perte ou dommage, à ne pas déduire de la valeur déclarée | non relevée |
| `support.financial_authority_limit` | Support | 5 000 | XOF | portée par rôle et par action, à définir ; ne confère aucun pouvoir par défaut | non relevée |
| `loyalty.reward_amounts_and_caps` | V1 / campagnes | **non fixés** | XOF / points | conditions anti-abus distinctes du montant de l'avantage | non relevée |

Deux échéances connues qui toucheront ce tableau : l'arbitrage **P02 du 13 octobre** (« seuils et
commissions métiers : aligner 0 / 2 000 / 25 000 F historiques sur 1 000 / 15 000 F », Finance +
Backend, état « à aligner ») et le **P03 du 13 octobre** sur les contrats Food/Send et le wallet livreur.

---

## 9. Paramètres techniques à portée de comportement

Ce ne sont pas des montants métier, mais ils changent ce que l'utilisateur observe et sont tous
pilotables par environnement. Ils figurent ici pour qu'une modification ne soit pas faite à l'aveugle.

| Paramètre | Valeur | Effet observable |
| --- | --- | --- |
| `otp_rate_limit_seconds` | 60 | délai minimal avant un nouvel envoi d'OTP |
| `otp_code_lifetime_seconds` | 300 | durée de validité du code |
| `jwt_access_lifetime_minutes` | 15 | fréquence de rafraîchissement de session |
| `jwt_refresh_lifetime_days` | 30 | durée avant reconnexion complète |
| `ride_summary_max_age_days` | 31 | profondeur interrogeable des rapports Pilotage |
| `pilotage_breakdown_current_ttl_seconds` | 300 | fraîcheur d'une ventilation du jour courant |
| `pilotage_breakdown_final_ttl_seconds` | 86 400 | fraîcheur d'une ventilation d'un jour clos |
| `payment_return_context_ttl_seconds` | 900 | durée de validité d'un retour de paiement |
| `kyc_command_idempotency_ttl_seconds` | 86 400 | fenêtre de déduplication des commandes KYC |
| `driver_provisioning_idempotency_ttl_seconds` | 86 400 | idem pour le provisioning chauffeur |
| `capability_projection_delivery_interval_seconds` | 5 | latence de publication des capacités vers DiddiFreeID |
| `capability_projection_reconciliation_interval_seconds` | 30 | délai de rattrapage d'une projection perdue |
| `capability_projection_retry_base_seconds` → `_max_seconds` | 5 → 300 | agressivité du réessai |
| `payment_reconciliation_interval_seconds` | 300 | délai d'auto-réparation d'un webhook perdu |
| `payment_reconciliation_min_age_seconds` | 120 | grâce laissée au payeur sur la page de paiement |
| `payment_reconciliation_max_age_seconds` | 259 200 (72 h) | au-delà, l'intent est considéré expiré |
| `emergency_notification_timeout_seconds` | 10 | délai avant échec d'une alerte d'urgence |
| `push_enabled` | `false` | **les notifications push sont désactivées par défaut** |
| `capability_projection_enabled` | `true` | projection des capacités active |
| `payment_reconciliation_enabled` | `true` | réconciliation paiements active |
| `matching_eta_ranking_enabled` | `true` | reclassement par temps de trajet réel |

## 10. Gouvernance proposée, non validée

Reprise de `PARAMETRES_METIER.md`, section « Gouvernance technique proposée, non encore validée » :

- version, acteur autorisé, motif, date d'effet, module et environnement pour chaque changement ;
- contrôles de cohérence : avertissement inférieur au plafond, frais et net cohérents, bornes et unités
  explicites ;
- prévisualiser les conséquences et notifier les personnes affectées par un changement d'éligibilité ;
- conserver les montants et règles acceptés pour les opérations déjà engagées, aucune réécriture
  d'historique ;
- réserver un mécanisme de retour à une version antérieure, sans annuler les transactions réalisées.

Le document ajoute : « Un stockage de configuration partagé n'impose pas que tous les modules aient le
même montant ni qu'une panne de configuration bloque toutes les opérations. »

État actuel dans DiddiGo : seule la configuration de dispatch est éditable à chaud et versionnée en base.
Tout le reste est en environnement ou en constante de code, sans journal de changement, sans date
d'effet, sans prévisualisation.

La décision `SCRUM-584` tranche une partie de cette gouvernance : l'édition à chaud n'est pas la cible,
donc le besoin de journal de changement applicatif se reporte sur la traçabilité du **déploiement**.
Le reste — contrôles de cohérence, prévisualisation, conservation des règles pour les opérations déjà
engagées, retour à une version antérieure — reste à valider.

---

## 11. Tickets ouverts par ce registre

Créés le 9 octobre 2026 à partir des dérives et des trous relevés ici.

| Ticket | Sujet | Nature |
| --- | --- | --- |
| `SCRUM-584` | Standard : tout paramètre ajustable passe par variable d'environnement | règle, tous modules |
| `SCRUM-585` | Sortir les paramètres de tarification des constantes de code vers l'environnement | dérive, section 2 |
| `SCRUM-586` | Configuration de dispatch éditable à chaud : aligner sur la règle | dérive, section 6 |
| `SCRUM-587` | Arbitrage : barème tarifaire stocké en base face à la règle | arbitrage, section 2 |
| `SCRUM-588` | Arrivée du chauffeur et attente de prise en charge | parcours manquant, section 3 |
| `SCRUM-589` | Code de prise en charge à six chiffres en secours GPS | parcours manquant, section 3 |
| `SCRUM-590` | Fin anticipée facturée après démarrage de course | parcours manquant, section 4 |
| `SCRUM-591` | Exposer la demande de retrait des gains chauffeur | parcours manquant, section 7 |
| `SCRUM-592` | Devis : validité bornée et déduplication des demandes | parcours manquant, section 5 |
| `SCRUM-593` | Exposer la fraîcheur sur les résumés Pilotage | règle non honorée |

Deux contradictions existantes ont été signalées en commentaire sur les tickets concernés, sans
modification de leur statut : `SCRUM-331` (UC-187, modification du taux de commission à chaud par un
opérateur) et `SCRUM-104` (UC-315, minimum de retrait marqué terminé alors que `PROD-032` le supprime).

**Aucune ligne de code n'a été modifiée.** Les dérives sont documentées et ticketées, pas corrigées.
