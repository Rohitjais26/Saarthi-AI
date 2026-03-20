$base = "http://localhost:8000"

$rows = @(
  @{ state_code = "MH"; state_name = "Maharashtra"; district_code = "D001"; district_name = "Pune"; youth_population = 130000; female_participation_rate = 42; unemployment_rate = 10.8; median_household_income = 185000; internet_penetration_rate = 74; skill_gap_index = 62; top_skills = @("retail","sales"); demand_skills = @("digital_marketing","logistics") },
  @{ state_code = "UP"; state_name = "Uttar Pradesh"; district_code = "D002"; district_name = "Lucknow"; youth_population = 165000; female_participation_rate = 36; unemployment_rate = 13.5; median_household_income = 126000; internet_penetration_rate = 58; skill_gap_index = 71; top_skills = @("field_sales","retail"); demand_skills = @("healthcare","operations") },
  @{ state_code = "BR"; state_name = "Bihar"; district_code = "D006"; district_name = "Patna"; youth_population = 172000; female_participation_rate = 29; unemployment_rate = 15.6; median_household_income = 98000; internet_penetration_rate = 49; skill_gap_index = 78; top_skills = @("field_work"); demand_skills = @("construction","healthcare") }
)

Invoke-RestMethod -Method Post -Uri "$base/data/ingest/regional-skill" -ContentType "application/json" -Body (@{
  rows = $rows
} | ConvertTo-Json -Depth 10)

Invoke-RestMethod -Method Post -Uri "$base/leads" -ContentType "application/json" -Body (@{
  id = "L2001"
  first_name = "Ravi"
  age_band = "22-25"
  district_code = "D002"
  preferred_language = "hi"
  digital_literacy_level = "medium"
  employment_status = "unemployed"
  household_income_band = "low"
  consent_sms = $true
  consent_whatsapp = $true
} | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri "$base/leads/L2001/score"

Invoke-RestMethod -Method Post -Uri "$base/campaigns" -ContentType "application/json" -Body (@{
  id = "C2001"
  name = "Demo Outreach"
  goal = "onboarding_start"
  segment_filter = @{
    district_code = @("D002")
    min_propensity = 0.5
  }
} | ConvertTo-Json -Depth 5)

Invoke-RestMethod -Method Post -Uri "$base/campaigns/C2001/approve" -ContentType "application/json" -Body (@{
  approved_by = "admin_demo"
} | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri "$base/campaigns/C2001/deploy" -ContentType "application/json" -Body (@{
  batch_limit = 20
  dry_run = $false
  cta_link = "https://example.org/apply"
} | ConvertTo-Json)

$onboarding = Invoke-RestMethod -Method Post -Uri "$base/onboarding/start" -ContentType "application/json" -Body (@{
  lead_id = "L2001"
  program_id = "P101"
} | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri "$base/onboarding/$($onboarding.case_id)/documents" -ContentType "application/json" -Body (@{
  document_type = "id_proof"
  document_ref = "https://files.example/id-L2001.pdf"
} | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri "$base/onboarding/$($onboarding.case_id)/reminder" -ContentType "application/json" -Body (@{
  note = "Please complete orientation."
} | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri "$base/onboarding/$($onboarding.case_id)/step" -ContentType "application/json" -Body (@{
  state = "confirmed"
  current_step = "confirmation"
} | ConvertTo-Json)

Invoke-RestMethod -Method Get -Uri "$base/analytics/kpis"
Invoke-RestMethod -Method Get -Uri "$base/analytics/optimize"
