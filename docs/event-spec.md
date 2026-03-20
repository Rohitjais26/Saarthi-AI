# Event Tracking Spec

Naming convention: domain.object.action

Core events:
- lead.created
- lead.scored
- data.ingested
- campaign.created
- campaign.approved
- campaign.message.queued
- campaign.message.sent
- campaign.message.failed
- campaign.message.replied
- onboarding.started
- onboarding.step.completed
- onboarding.document.uploaded
- onboarding.reminder.sent
- onboarding.reminder.failed
- onboarding.abandoned
- onboarding.enrolled
- user.opted_out
- consent.updated

Required event fields:
- id
- event_name
- ts
- lead_id (optional if not user-specific)
- campaign_id (optional)
- channel (optional)
- props_json
