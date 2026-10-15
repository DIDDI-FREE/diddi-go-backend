# Integration SMS

DiddiGo utilise un port `SmsProvider` pour les SMS d'urgence. Le fournisseur se
selectionne avec `SMS_PROVIDER` sans modifier les routes publiques.

## Fournisseurs

| Valeur | Configuration requise | Usage |
| --- | --- | --- |
| `disabled` | aucune | local, aucun envoi |
| `senndo` | `SENNDO_API_KEY` | sandbox avec `sk_test_*`, production avec `sk_live_*` |
| `yellika` | `YELLIKA_API_TOKEN` | API Yellika v3 |

Variables communes :

```ini
SMS_PROVIDER=senndo
SMS_TIMEOUT_SECONDS=20
EMERGENCY_SUPPORT_SMS=+225...
```

Senndo :

```ini
SENNDO_API_KEY=<secret Portainer>
SENNDO_BASE_URL=https://api.senndo.com
SENNDO_SENDER=DiddiFree
```

Yellika :

```ini
YELLIKA_API_TOKEN=<secret Portainer>
YELLIKA_BASE_URL=https://panel.yellikasms.com
YELLIKA_SENDER_ID=DiddiFree
```

Les secrets restent dans Portainer ou le `.env` local et ne doivent jamais etre
commites. Chaque envoi SOS utilise une cle d'idempotence derivee de la course et
de la cible afin d'eviter une double livraison lors d'un retry.

## Comportement SOS

Le numero du contact d'urgence recoit deux notifications independantes lorsque
les canaux sont configures : WhatsApp via Evolution API et SMS via le fournisseur
selectionne. Le support recoit aussi un SMS lorsque `EMERGENCY_SUPPORT_SMS` est
renseigne. Chaque resultat est journalise avec son canal, son fournisseur, son
statut et son identifiant externe.

Une panne SMS ne masque pas les resultats WhatsApp et ne supprime pas l'evenement
SOS persiste. Elle apparait explicitement comme `failed` dans les notifications
et dans les logs structures.
