# Migration 018: Manual Execution Steps

**Time Required**: 2-3 minutes  
**Difficulty**: Easy (copy-paste)

## Steps

### 1. Open Supabase Dashboard
```
URL: https://app.supabase.com/project/inuuyaxddgbxexljfykg/sql/new
```

- Click the URL above
- You'll be directed to GitHub login (if not logged in)
- Log in with GitHub
- Accept permissions if prompted

### 2. You'll See This Screen
```
┌─ SQL Editor ──────────────────────────────┐
│                                            │
│  [New Query] [▼ Saved Queries]             │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │ SELECT * FROM users LIMIT 10;      │   │ ← Paste SQL here
│  │                                    │   │
│  │                                    │   │
│  └────────────────────────────────────┘   │
│                                            │
│  [▶ Run]  [⚙️ Settings]  [💾 Save]        │
└────────────────────────────────────────────┘
```

### 3. Click in the SQL Editor Box
- Click where it says `SELECT * FROM users LIMIT 10;`
- Select all text (Ctrl+A)
- Delete it

### 4. Paste This SQL

Copy the entire block below:

```sql
-- Migration 018: Document Ingestion Schema Fixes
ALTER TABLE intranet_documents ALTER COLUMN project_id DROP NOT NULL;
ALTER TABLE intranet_documents ALTER COLUMN file_slot DROP NOT NULL;
ALTER TABLE intranet_documents ALTER COLUMN file_type DROP NOT NULL;
ALTER TABLE intranet_documents DROP CONSTRAINT IF EXISTS intranet_documents_doc_type_check;
ALTER TABLE intranet_documents ADD CONSTRAINT intranet_documents_doc_type_check CHECK (doc_type IN ('보고서', '제안서', '실적', '기타', 'proposal', 'report', 'presentation', 'contract', 'reference', 'other'));
ALTER TABLE intranet_documents DROP CONSTRAINT IF EXISTS intranet_documents_project_id_file_slot_key;
CREATE UNIQUE INDEX IF NOT EXISTS idx_intranet_documents_project_file_slot ON intranet_documents(project_id, file_slot) WHERE project_id IS NOT NULL AND file_slot IS NOT NULL;
ALTER TABLE intranet_documents ALTER COLUMN processing_status SET DEFAULT 'extracting';
```

Then paste it into the SQL editor (Ctrl+V or right-click → Paste)

### 5. Click the [▶ Run] Button
- Green play button on the left
- Wait 2-3 seconds

### 6. Verify Success
You should see:

```
✓ SUCCESS (executed 8 statements)
```

Or similar success message.

**If you see an error:**
- "table does not exist" → Run migration 017 first
- "permission denied" → Check your role permissions
- Other → Take a screenshot and share

---

## What This Migration Does

| Step | Action | Purpose |
|------|--------|---------|
| 1 | `ALTER COLUMN project_id DROP NOT NULL` | Allow documents without projects |
| 2 | `ALTER COLUMN file_slot DROP NOT NULL` | Make file_slot optional |
| 3 | `ALTER COLUMN file_type DROP NOT NULL` | Make file_type optional |
| 4 | `DROP CONSTRAINT intranet_documents_doc_type_check` | Remove old constraint |
| 5 | `ADD CONSTRAINT ... CHECK doc_type IN (...)` | Add Korean values support |
| 6 | `DROP CONSTRAINT intranet_documents_project_id_file_slot_key` | Remove old unique constraint |
| 7 | `CREATE UNIQUE INDEX ... WHERE ...` | Partial unique index (allows NULLs) |
| 8 | `ALTER COLUMN processing_status SET DEFAULT` | Change default status |

---

## After Successful Migration

Once you see "SUCCESS", your database is ready for the API!

Next step: Test file upload

```bash
cd /c/project/tenopa\ proposer/-agent-master

python3 << 'EOF'
import requests
import json

with open("test_document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/documents/upload",
        files={"file": ("test.pdf", f, "application/pdf")},
        data={"doc_type": "보고서"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    print(f"HTTP Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ SUCCESS!")
        doc = response.json()
        print(f"Document ID: {doc['id']}")
        print(f"Processing Status: {doc['processing_status']}")
    else:
        print(f"Error: {response.json()}")
EOF
```

---

## Troubleshooting

### Issue: "Could not execute query"
- Refresh the page and try again
- Check your internet connection

### Issue: "Table does not exist"
- Migration 017 may not be applied yet
- Contact DevOps to check

### Issue: Permission denied
- Check your Supabase role
- May need to use a different user account

---

## Done?

Once you see "SUCCESS" in Supabase, **reply here with**:
```
✅ Migration 018 applied successfully
```

Then I'll help you test the upload!
