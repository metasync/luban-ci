import json
import os

import click
from ruamel.yaml import YAML


def load_config(config_file):
    if not config_file or not os.path.exists(config_file):
        return {}

    try:
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                return json.load(f)
            return YAML(typ="safe").load(f)
    except Exception as e:
        click.echo(f"Error loading config file {config_file}: {e}", err=True)
        return {}


def load_config_from_dir(config_dir):
    config = {}
    if not os.path.exists(config_dir):
        return config

    for filename in os.listdir(config_dir):
        if filename.startswith("..") or filename.startswith("."):
            continue

        file_path = os.path.join(config_dir, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        config[filename] = content
            except Exception as e:
                click.echo(f"Warning: Failed to read config file {file_path}: {e}", err=True)
    return config
