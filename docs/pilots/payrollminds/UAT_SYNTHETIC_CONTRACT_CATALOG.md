# PayrollMinds synthetic UAT contract catalog

**Status:** Local synthetic test data only. It is not PayrollMinds data, a
customer commitment, or production data approval.

The local-only `seed_payrollminds_demo --reset` command created the
`payrollminds-demo` workspace on 2026-08-02. The resulting fixture contained
six Contract Records and six Documents with these fictional categories:

| ID | Fictional agreement | Type | Test purpose |
|---|---|---|---|
| SYN-01 | Northern Star Mutual NDA | NDA | private access and expiry date |
| SYN-02 | Atlas Workforce Framework Agreement | MSA | renewal and notice dates |
| SYN-03 | Global Payroll Transformation Implementation SOW | SOW | metadata, human review, linked documents and activity |
| SYN-04 | Fictional Subprocessor Data Processing Addendum | DPA | privacy review / restricted data handling |
| SYN-05 | CloudHarbor Advisory Services Agreement | CONSULTING | bulk-import and duplicate fixture |
| SYN-06 | Atlas Workforce Pricing Amendment | AMENDMENT | amendment relationship and date correction |

All party names, domains, values, terms, and document bodies are fictional.
No employee, salary, payroll, government identifier, customer, or confidential
data is permitted in this fixture. The local seed refuses deployed platforms.

```text
PAYROLLMINDS_DEMO_PASSWORD='local-only-value' \
  .venv/bin/python manage.py seed_payrollminds_demo --reset
```

Observed local result: `payrollminds-demo (6 contracts, 6 documents, 3
approvals)`. Local numeric IDs are reset-specific and are not UAT identifiers.
