## Check Build Logs
View the logs of the latest kpack build for a specific application:
```bash
make pipeline-logs APP_NAME=my-app
```

## Best Practices

### Branch Protection
It is highly recommended to enable branch protection rules on your GitOps repository:
- **`main`**: Require Pull Request reviews, status checks, and restrict direct pushes. This ensures Production changes are always reviewed.
- **`develop`**: Allow direct pushes from the CI ServiceAccount (for automated deployments) but require PRs for manual changes.
