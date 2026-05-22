from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_project_user_serviceaccount_token_secrets_template():
    content = _read(
        "tools/luban-provisioner/templates/infra-ci-base/{{cookiecutter.repo_name}}/base/secrets/project-user-service-account-tokens.yaml"
    )
    assert "type: kubernetes.io/service-account-token" in content
    assert "name: project-admin.service-account-token" in content
    assert "kubernetes.io/service-account.name: project-admin" in content
    assert "name: project-developer.service-account-token" in content
    assert "kubernetes.io/service-account.name: project-developer" in content


def test_infra_ci_base_kustomization_includes_token_secrets():
    content = _read(
        "tools/luban-provisioner/templates/infra-ci-base/{{cookiecutter.repo_name}}/base/kustomization.yaml"
    )
    assert "secrets/project-user-service-account-tokens.yaml" in content


def test_infra_provision_workflow_ignores_controller_managed_token_secret_fields():
    content = _read("manifests/workflows/ci-infra-provision-workflow-template.yaml")
    assert "name: project-admin.service-account-token" in content
    assert "name: project-developer.service-account-token" in content
    assert "- /data" in content
    assert "- /metadata/annotations/kubernetes.io~1service-account.uid" in content
    assert "- /metadata/ownerReferences" in content

