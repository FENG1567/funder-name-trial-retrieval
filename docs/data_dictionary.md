# Data dictionary

Identifiers are strings. Empty values are missing or inapplicable, never automatic zeros. Boolean strings are parsed explicitly. Registry identifiers and trial families are different units.

## data/aggregate/figure1_source_data.csv

7 records. Fields:

- `source`
- `strategy`
- `coverage_num`
- `coverage_den`
- `reference_posted`
- `reference_eligible`
- `query_posted`
- `query_eligible`
- `posting_status`
- `posting_status_note`

## data/aggregate/figure2_source_data.csv

4 records. Fields:

- `stage`
- `selection_base_n`
- `retained_n`
- `reported_n`
- `reported_denominator`
- `delta_pp_vs_reference`

## data/curated/Supplementary_Data_1_SU2C_historical_evidence.csv

25 records. Fields:

- `NCT`
- `historical_eligible`
- `current_ACTUAL_enrollment_eligible`
- `core_and_expanded_name_query_hit`
- `ctgov_results`
- `external_registry_results`
- `any_registry_results`
- `qualifying_journal_report`
- `registry_or_journal_result`
- `conference_sensitivity_addition`
- `PMID`
- `publication_date`
- `date_precision`
- `clinical_scope`
- `qualifying_report_DOI`
- `qualitative_conference_DOI`
- `qualitative_conference_publisher_date`

## data/curated/Supplementary_Data_2_MRC_paper_evidence.csv

13 records. Fields:

- `source_excel_row`
- `mrc_grant_reference`
- `source_NCTs`
- `matched_registry_identifiers`
- `PMID`
- `DOI`
- `title`
- `primary_outcome_or_role`
- `classification`
- `bibliographic_verification_date`
- `original_assessment_date`

## data/curated/Supplementary_Data_3_NIHR_full125_families.csv

125 records. Fields:

- `family_id`
- `award_title`
- `source_report_DOI_checked_20261113`
- `reference_status`
- `ClinicalTrials_gov_reference_IDs`
- `ISRCTN_reference_IDs`
- `A_known_identifier_hits`
- `any_reference_ID_hit_by_A`
- `other_registry_source_candidates`
- `initial_unresolved_reason`
- `B_fullframe`
- `sample_group`

## data/curated/Supplementary_Data_4_NIHR_full125_links.csv

104 records. Fields:

- `family_id`
- `platform`
- `registry_id`
- `source_registration_statement`
- `identifier_normalization`
- `A_known_identifier_hit`
- `source_report_DOI_checked_20261113`

## data/curated/Supplementary_Data_5_SU2C_project_registration_links.csv

33 records. Fields:

- `project_id`
- `project_title`
- `NCT`
- `official_pdf_page`
- `source_url`

## data/curated/Supplementary_Data_6_MRC_historical_source_rows.csv

58 records. Fields:

- `source_excel_row`
- `mrc_grant_reference_raw`
- `trial_end_date_registry_raw`
- `isctn_reference_raw`
- `clinicaltrials_gov_reference_raw`
- `nct_identifiers_extracted`
- `eudract_euctr_reference_raw`
- `other_who_primary_registry_raw`
- `publication_status_01_12_2024_raw`
- `derived_reporting_class_within_eligible_cohort`

## data/curated/mrc_row_classification.csv

141 records. Fields:

- `source_excel_row`
- `mrc_grant_reference_raw`
- `type_of_study_raw`
- `award_start_date`
- `award_end_date`
- `trial_start_date_registry`
- `trial_end_date_registry_raw`
- `trial_end_date_cell_type`
- `trial_end_actual_estimated_type`
- `isctn_reference_raw`
- `clinicaltrials_gov_reference_raw`
- `nct_identifiers_extracted`
- `nct_identifier_count_in_row`
- `eudract_euctr_reference_raw`
- `other_who_primary_registry_raw`
- `registry_platforms_from_reference_columns`
- `non_nct_platforms_from_reference_columns`
- `publication_status_01_12_2024_raw`
- `date_cutoff_2022_12_31_eligible`
- `date_eligibility_reason`
- `derived_reporting_class_within_eligible_cohort`

## data/curated/nihr_pilot_12_family_reference_links.csv

12 records. Fields:

- `sample`
- `family_id`
- `award_title`
- `source_report_DOI`
- `source_report_PMID`
- `reference_identifiers`
- `reference_status_at_freeze`
- `reference_freeze_date`
- `B_recovered_known_links`

## Interpretation

- SU2C historical evidence: NCT is the row unit; historical eligibility and current ACTUAL-enrollment eligibility must remain separate. Registry/journal evidence is a union. Conference additions enter only sensitivity analysis.
- MRC source evidence: source_excel_row is the unit. Multiple NCTs in a row do not create multiple historical observations. Unconfirmed papers do not mean proven nonpublication.
- NIHR families: family_id is the unit for family coverage; platform plus registry_id identifies a link. sample_group is membership, not a separate search outcome. Full-frame A observations and pilot A queries have different scopes. B_fullframe is not evaluated.
- Figure 1 inputs are aggregate counts. query_posted/query_eligible are blank for the nonestimable KCE full-name comparison. Figure 2 source and name-selection stages have different references.
- Exact outcome definitions, dates, scope, query strings and source references are in search_and_outcome_specifications.md.
