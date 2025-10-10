# GitHub Actions Troubleshooting Guide

## 🚨 "Run workflow" Button Not Visible

### Problem
The "Run workflow" button is missing from the Actions tab in GitHub.

### Root Causes & Solutions

#### 1. **YAML Syntax Errors** ✅ FIXED
- **Issue**: Incorrect indentation in workflow files
- **Solution**: Fixed indentation in both `feature-pipeline.yml` and `training-pipeline.yml`
- **Files affected**: 
  - `.github/workflows/feature-pipeline.yml` (lines 10-12)
  - `.github/workflows/training-pipeline.yml` (lines 10-12)

#### 2. **Missing Permissions** ✅ FIXED
- **Issue**: GitHub Actions requires explicit permissions to show manual triggers
- **Solution**: Added permissions block to both workflows:
```yaml
permissions:
  contents: read
  id-token: write
```

#### 3. **Repository Settings**
Check these settings in your GitHub repository:

**Actions Tab Settings:**
- Go to Repository → Settings → Actions → General
- Ensure "Actions permissions" is set to "Allow all actions and reusable workflows"
- Check "Workflow permissions" is set to "Read repository contents and packages permissions"

**Branch Protection Rules:**
- Go to Repository → Settings → Branches
- If you have branch protection rules, ensure "Allow force pushes" or "Allow deletions" doesn't block Actions

#### 4. **Repository Secrets**
Ensure these secrets are configured in Repository → Settings → Secrets and variables → Actions:
- `GCP_SERVICE_ACCOUNT_KEY`
- `AQICN_TOKEN` 
- `GCP_PROJECT_ID`

### How to Verify the Fix

1. **Check Actions Tab**: 
   - Go to your repository → Actions tab
   - You should see both workflows listed
   - Click on a workflow → "Run workflow" button should appear on the right

2. **Test Manual Run**:
   - Click "Run workflow"
   - Select branch (usually `main`)
   - Click green "Run workflow" button
   - Monitor the execution in real-time

### Workflow Triggers Explained

Our workflows now have these triggers:

#### Feature Pipeline (`feature-pipeline.yml`)
- **Schedule**: Every hour (`0 * * * *`)
- **Manual**: `workflow_dispatch` (Run workflow button)
- **Push**: When `feature_pipeline.py` or `config.py` changes on main branch

#### Training Pipeline (`training-pipeline.yml`)
- **Schedule**: Daily at 2 AM UTC (`0 2 * * *`)
- **Manual**: `workflow_dispatch` (Run workflow button)  
- **Push**: When `training_pipeline.py` or `config.py` changes on main branch

### Team Best Practices

#### For Manual Testing:
1. Always test workflows manually before relying on scheduled runs
2. Use the "Run workflow" button to trigger immediate execution
3. Monitor logs in the Actions tab for debugging

#### For Debugging Failed Runs:
1. **DON'T delete workflow files** - this removes the "Run workflow" button
2. **DO delete individual failed run logs** if needed
3. **DO check the workflow file syntax** if the button disappears

#### For Repository Maintenance:
1. Keep workflow files in `.github/workflows/` directory
2. Maintain proper YAML indentation (2 spaces, not tabs)
3. Test workflow changes in a separate branch first

### Emergency Recovery

If you accidentally delete the `workflow_dispatch` trigger:

1. **Restore the trigger**:
```yaml
on:
  workflow_dispatch:  # Add this line back
  schedule:
    - cron: '0 * * * *'
  push:
    branches: [ main ]
```

2. **Commit and push** the fix
3. **Wait 1-2 minutes** for GitHub to process the changes
4. **Check Actions tab** - button should reappear

### Common Mistakes to Avoid

❌ **Don't do this:**
- Delete the entire workflow file when cleaning up failed runs
- Remove `workflow_dispatch:` from the triggers
- Use tabs instead of spaces for YAML indentation
- Forget to add permissions block

✅ **Do this instead:**
- Delete individual failed run logs only
- Keep `workflow_dispatch:` for manual testing
- Use 2 spaces for YAML indentation consistently
- Include explicit permissions for better reliability

### Need Help?

If the "Run workflow" button still doesn't appear after these fixes:

1. Check GitHub's status page for service issues
2. Verify you have write permissions to the repository
3. Try creating a new workflow file as a test
4. Contact your repository administrator

---

**Last Updated**: December 2024  
**Maintained by**: AQI Team
