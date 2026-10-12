# Integration DiddiFiles

Le client cree une session DiddiFiles, charge directement l'objet, confirme le
fichier, puis transmet uniquement son `file_id` a DiddiGo.

| Champ DiddiGo | Purpose DiddiFiles |
|---|---|
| `license_document_file_id` | `diddigo_driver_kyc_license` |
| `national_id_document_file_id` | `diddigo_driver_kyc_national_id` |
| `selfie_document_file_id` | `diddigo_driver_kyc_selfie` |
| `profile_photo_file_id` | `diddigo_driver_profile_photo` |
| `registration_document_file_id` | `diddigo_vehicle_registration` |
| `vehicle_front_photo_file_id` | `diddigo_vehicle_front_photo` |
| `vehicle_back_photo_file_id` | `diddigo_vehicle_back_photo` |
| `vehicle_left_photo_file_id` | `diddigo_vehicle_left_photo` |
| `vehicle_right_photo_file_id` | `diddigo_vehicle_right_photo` |
| `vehicle_interior_photo_file_id` | `diddigo_vehicle_interior_photo` |
| `vehicle_plate_photo_file_id` | `diddigo_vehicle_plate_photo` |

Les fichiers sont prives sauf la photo de profil. Pour les consulter, le
frontend demande une URL signee temporaire a DiddiFiles.
