import click
from commands.gitops import gitops
from commands.source import source
from commands.project import project

@click.group()
def cli():
    """Luban Provisioner Tooling"""
    pass

cli.add_command(gitops)
cli.add_command(source)
cli.add_command(project)

if __name__ == '__main__':
    cli()
