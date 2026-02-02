import os
import shutil
import subprocess
import yaml
from cookiecutter.main import cookiecutter

def test_template_generation():
    # Define test parameters
    template_dir = "luban-gitops-template"
    output_dir = "/tmp/test_output"
    project_name = "test-project-gitops"
    app_name = "test-app"
    
    # Clean up previous test run
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    print(f"Generating template in {output_dir}...")
    
    # Run cookiecutter programmatically
    cookiecutter(
        template_dir,
        no_input=True,
        output_dir=output_dir,
        extra_context={
            "project_name": project_name,
            "app_name": app_name
        }
    )

    project_path = os.path.join(output_dir, project_name)
    
    # 1. Verify Directory Structure
    expected_files = [
        "app/base/kustomization.yaml",
        "app/base/deployment.yaml",
        "app/base/service.yaml",
        "app/base/httproute.yaml",
        "app/base/configmap.yaml",  # Added ConfigMap
        "app/overlays/snd/kustomization.yaml",
        "app/overlays/snd/configmap.yaml", # Added Overlay ConfigMap
        "app/overlays/prd/kustomization.yaml"
    ]
    
    for rel_path in expected_files:
        full_path = os.path.join(project_path, rel_path)
        if not os.path.exists(full_path):
            print(f"❌ Missing file: {rel_path}")
            return
        else:
            print(f"✅ Found file: {rel_path}")

    # 2. Verify Content: Base Kustomization (Labels)
    base_kust_path = os.path.join(project_path, "app/base/kustomization.yaml")
    with open(base_kust_path, 'r') as f:
        content = yaml.safe_load(f)
        labels = content.get('labels', [])
        if labels and labels[0]['pairs']['app.kubernetes.io/name'] == app_name:
            print(f"✅ Base Kustomization labels correct: {app_name}")
        else:
            print(f"❌ Base Kustomization labels incorrect: {labels}")

    # 3. Verify Content: Overlay Namespace (SND)
    snd_kust_path = os.path.join(project_path, "app/overlays/snd/kustomization.yaml")
    with open(snd_kust_path, 'r') as f:
        content = yaml.safe_load(f)
        namespace = content.get('namespace')
        expected_ns = f"snd-{project_name}"
        if namespace == expected_ns:
            print(f"✅ SND Overlay namespace correct: {namespace}")
        else:
            print(f"❌ SND Overlay namespace incorrect: {namespace} (expected {expected_ns})")

    # 4. Verify Content: Deployment has envFrom
    deploy_path = os.path.join(project_path, "app/base/deployment.yaml")
    with open(deploy_path, 'r') as f:
        content = yaml.safe_load(f)
        try:
            env_from = content['spec']['template']['spec']['containers'][0]['envFrom']
            if env_from[0]['configMapRef']['name'] == f"{app_name}-config":
                print(f"✅ Deployment envFrom ConfigMap correct: {app_name}-config")
            else:
                print(f"❌ Deployment envFrom incorrect: {env_from}")
        except (KeyError, IndexError):
            print("❌ Deployment envFrom missing or malformed")

    # 5. Dry Run Kustomize Build (Optional but recommended)
    # This checks if the generated YAML is actually valid Kustomize
    print("\nRunning 'kustomize build' verification...")
    try:
        subprocess.run(
            ["kustomize", "build", os.path.join(project_path, "app/overlays/snd")],
            check=True,
            capture_output=True
        )
        print("✅ Kustomize build (SND) successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Kustomize build (SND) failed:\n{e.stderr.decode()}")

    print("\nTest completed.")

if __name__ == "__main__":
    test_template_generation()
