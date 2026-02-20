import click
import os
import yaml
from utils import load_config_from_dir

@click.command(name='config')
@click.option('--output-file', default='/workdir/config.yaml', help='Output path for config file')
@click.option('--luban-config-dir', default='/etc/config/luban', help='Path to Luban system config')
@click.option('--app-config-dir', default='/etc/config/app', help='Path to App specific config')
@click.option('--set', 'overrides', multiple=True, help='Override config values (key=value)')
def config(output_file, luban_config_dir, app_config_dir, overrides):
    """Generate consolidated configuration file"""
    final_config = {}
    
    # 1. Load System Config
    if os.path.exists(luban_config_dir):
        click.echo(f"Loading system config from {luban_config_dir}")
        final_config.update(load_config_from_dir(luban_config_dir))
        
    # 2. Load App Config
    if os.path.exists(app_config_dir):
        click.echo(f"Loading app config from {app_config_dir}")
        final_config.update(load_config_from_dir(app_config_dir))
        
    # 3. Apply Overrides
    for override in overrides:
        if '=' in override:
            k, v = override.split('=', 1)
            # Handle template variables that might be passed as strings
            if v and v != "None" and not v.startswith("{{"):
                final_config[k] = v
        
    # 4. Write
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, 'w') as f:
        yaml.dump(final_config, f)
    
    click.echo(f"Generated config at {output_file}")
    click.echo(yaml.dump(final_config))
