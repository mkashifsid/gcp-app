# app-code

Sample Flask backend + frontend deployed to the GKE cluster provisioned by
`infra-terraform`. Kubernetes manifests here (Kustomize) are this repo's
responsibility — infra changes and app releases are fully decoupled.

## Repo layout

```
backend/                 Flask app + Dockerfile (queries Cloud SQL)
frontend/                Flask app + Dockerfile (calls the backend)
k8s/base/                Deployment + Service definitions, image name is a placeholder
k8s/overlays/staging/    namespace demo-app-staging, no public ingress
k8s/overlays/production/ namespace demo-app, public Ingress using infra repo's static IP
.github/workflows/ci-cd.yml
```

## Pipeline behavior

| Branch pushed   | Environment | What happens                                      |
|------------------|-------------|-----------------------------------------------------|
| `main`           | production  | build, push, deploy to `demo-app`, smoke test via public LB IP |
| `release/**`     | staging     | build, push, deploy to `demo-app-staging`, smoke test via port-forward |
| `bug/**`         | staging     | same as release, tagged `hotfix-<sha>` for traceability |
| PR to `main`     | none        | lint + docker build sanity check only, no deploy |

The branch → environment routing is regex-matched in the
`determine-environment` job (`[[ "$REF" =~ ^release/ ]]`, etc.) rather than
hardcoded per-branch jobs, so adding a new `release/*` branch needs no
workflow changes.

`deploy` runs under a GitHub Environment named after the target
(`production` / `staging`) — add required reviewers on `production` in
Settings if you want a manual gate before it goes live.

## Setup

```bash
gh repo create YOUR_GH_ORG/app-code --private --source=. --push
```

### GitHub repo secrets (Settings -> Secrets and variables -> Actions)

| Secret                    | Value                                                        |
|-----------------------------|----------------------------------------------------------------|
| `WIF_PROVIDER`              | same value as in `infra-terraform` (`workload_identity_provider` output) |
| `APP_CI_SA_EMAIL`           | `terraform output -raw app_ci_service_account_email` (from infra repo) |
| `GCP_PROJECT_ID`            | your project ID |
| `ARTIFACT_REGISTRY_REPO`    | `terraform output -raw artifact_registry_repo` (from infra repo) |

### Try it locally first (optional)

```bash
docker build -t backend:local backend
docker build -t frontend:local frontend
```

### Trigger a deploy

```bash
git checkout -b release/1.0
git push origin release/1.0   # -> deploys to staging, smoke-tested via port-forward

git checkout main && git merge release/1.0
git push origin main          # -> deploys to production, smoke-tested via the public LB
```

## Note on the Ingress static IP

`k8s/overlays/production/ingress.yaml` references the static IP by name
(`demo-gke-app-ip`). That name comes from `google_compute_global_address`
in the infra repo — if you rename it there, update it here too. This is
the one place the two repos are implicitly coupled; a cleaner setup would
publish it as a repo variable fetched at deploy time instead of hardcoding it.
