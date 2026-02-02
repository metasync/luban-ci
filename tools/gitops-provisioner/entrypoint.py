import os
import sys
import argparse
from cookiecutter.main import cookiecutter

def main():
    parser = argparse.ArgumentParser(description='GitOps Repo Provisioner')
    # All arguments are now required as defaults are handled by the caller (Argo Workflow)
    parser.add_argument('--project-name', required=True, help='Name of the project/repo')
    parser.add_argument('--application-name', required=True, help='Name of the application')
    parser.add_argument('--output-dir', required=True, help='Directory to output the rendered template')
    
    parser.add_argument('--container-port', required=True, help='Port exposed by the container')
    parser.add_argument('--service-port', required=True, help='Port exposed by the service')
    parser.add_argument('--domain-suffix', required=True, help='Domain suffix for ingress/routes')
    parser.add_argument('--default-image-name', required=False, help='Default image name')
    parser.add_argument('--default-image-tag', required=False, help='Default image tag')
    
    args = parser.parse_args()

    template_path = "/templates/luban-gitops-template"
    
    # Build context from arguments
    extra_context = {
        "project_name": args.project_name,
        "app_name": args.application_name,
        "container_port": args.container_port,
        "service_port": args.service_port,
        "domain_suffix": args.domain_suffix
    }
    
    if args.default_image_name:
        extra_context["default_image_name"] = args.default_image_name
    if args.default_image_tag:
        extra_context["default_image_tag"] = args.default_image_tag

    print(f"Provisioning GitOps repo for {args.project_name}...")
    print(f"Context: {extra_context}")
    
    try:
        cookiecutter(
            template_path,
            no_input=True,
            output_dir=args.output_dir,
            extra_context=extra_context
        )
        print(f"Successfully generated template in {args.output_dir}/{args.project_name}")
    except Exception as e:
        print(f"Error generating template: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
