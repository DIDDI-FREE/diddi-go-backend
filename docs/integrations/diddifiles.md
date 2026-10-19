# Integration DiddiFiles

Le client cree une session DiddiFiles, charge directement l'objet, confirme le
fichier, puis transmet uniquement son `file_id` a DiddiGo.

| Champ DiddiGo | Purpose DiddiFiles |
|---|---|
| `license_document_file_id` | `diddigo_driver_kyc_license` |
| `license_back_document_file_id` | `diddigo_driver_kyc_license_back` |
| `national_id_document_file_id` | `diddigo_driver_kyc_national_id` |
| `national_id_back_document_file_id` | `diddigo_driver_kyc_national_id_back` |
| `selfie_document_file_id` | `diddigo_driver_kyc_selfie` |
| `profile_photo_file_id` | `diddigo_driver_profile_photo` |
| `registration_document_file_id` | `diddigo_vehicle_registration` |
| `insurance_document_file_id` | `diddigo_vehicle_insurance` |
| `technical_inspection_document_file_id` | `diddigo_vehicle_technical_inspection` |
| `transport_authorization_document_file_id` | `diddigo_vehicle_transport_authorization` |
| `vehicle_front_photo_file_id` | `diddigo_vehicle_front_photo` |
| `vehicle_back_photo_file_id` | `diddigo_vehicle_back_photo` |
| `vehicle_left_photo_file_id` | `diddigo_vehicle_left_photo` |
| `vehicle_right_photo_file_id` | `diddigo_vehicle_right_photo` |
| `vehicle_interior_photo_file_id` | `diddigo_vehicle_interior_photo` |
| `vehicle_plate_photo_file_id` | `diddigo_vehicle_plate_photo` |

Les fichiers sont prives sauf la photo de profil. Pour les consulter, le
frontend demande une URL signee temporaire a DiddiFiles.
