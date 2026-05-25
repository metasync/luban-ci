import traceback

import click
from cookiecutter.main import cookiecutter


def render_template(template_path, output_dir, context, overwrite=False):
    click.echo(f"Rendering template from {template_path} to {output_dir}...")
    try:
        cookiecutter(
            template_path,
            no_input=True,
            output_dir=output_dir,
            extra_context=context,
            overwrite_if_exists=overwrite,
        )
        click.echo(f"Successfully generated template in {output_dir}")
    except Exception as e:
        click.echo(f"Error generating template: {e}", err=True)
        traceback.print_exc()
        raise e
