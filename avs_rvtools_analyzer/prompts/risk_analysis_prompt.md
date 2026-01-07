## Azure VMware Solution Migration Risk Analysis

**Risk Type:** {risk_type}
**Severity Level:** {risk_level}
**Description:** {risk_description}

**Detected Issues Count:** {issues_count}

**Issue Details:**
{issues_details}

## Analysis Request

You are analyzing ACTUAL DETECTED ISSUES from a VMware environment scan. These are real problems that exist in the current environment and need to be addressed for Azure VMware Solution migration.

The assumed migration method is VMware HCX-based migration, with a priority to live migration where possible: vMotion or Replication Assisted vMotion (RAV). Bulk migration method can be used for workloads that cannot be live-migrated but should be considered like a warning level risk.

You can refer to both Azure VMware Solution documentation and VMware HCX documentation for migration requirements, best practices, and limitations. Also consider VMware knowledge-base articles related to HCX migration issues.

"Azure Migrate" is not considered in this analysis as it does not support VMware to Azure VMware Solution migration.

Please provide a concise analysis in HTML format with the following sections (MAXIMUM {total_words} words total):

1. **Impact Assessment** (max {impact_words} words): How these specific detected issues affect Azure VMware Solution migration
2. **Recommended Actions** (max {actions_words} words): Specific steps to resolve these detected issues before or during migration
3. **Migration Strategy** (max {strategy_words} words): How to handle these specific items during the migration process
4. **Timeline Considerations** (max {timeline_words} words): When to address these issues in the migration timeline

**Important Instructions:**
- Analyze the SPECIFIC ISSUES provided in the data above
- Do not state that issues "don't apply" - these are confirmed detected problems
- Provide actionable recommendations for the actual detected items
- Generate HTML markup directly (no markdown)
- Use heading levels h5 and below only (h5, h6)
- Include proper HTML tags for paragraphs, lists, and emphasis
- Be specific to the detected issues and Azure VMware Solution requirements
- Do not include HTML document structure tags (html, head, body)
- STRICTLY ADHERE to word limits for each section to ensure complete responses
