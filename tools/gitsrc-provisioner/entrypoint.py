import os
import sys
import argparse
from cookiecutter.main import cookiecutter

def main():
    parser = argparse.ArgumentParser(description='Source Repo Provisioner')
    parser.add_argument('--project-name', required=True, help='Name of the project (e.g., team name)')
    parser.add_argument('--application-name', required=True, help='Name of the application')
    parser.add_argument('--output-dir', required=True, help='Directory to output the rendered template')
    
    args = parser.parse_args()

    # Currently only supports one template: luban-python-template
    template_path = "/templates/luban-python-template"
    
    package_name = args.application_name.replace('-', '_')
    extra_context = {
        "project_name": args.project_name, # Passed to template for context (e.g. repo tagging)
        "app_name": args.application_name,
        "package_name": package_name,
        "description": "A sample Python app for Luban CI. Replace this with your own description.",
        "version": "0.1.0"
    }

    # For logging purposes
    print(f"Provisioning source repo for app {args.application_name} in project {args.project_name}...")
    print(f"Context: {extra_context}")
    
    try:
        cookiecutter(
            template_path,
            no_input=True,
            output_dir=args.output_dir,
            extra_context=extra_context
        )
        print(f"Successfully generated template in {args.output_dir}/{args.application_name}")
    except Exception as e:
        print(f"Error generating template: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
