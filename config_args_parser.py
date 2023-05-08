import os
import appdirs
import yaml

import app_defaults
from app_defaults import DEFAULTS

SPECIAL_CONFIG_TAGS = dict(
    user='::USER_CONFIG::',
    app_dir='::APP_DIR_CONFIG::'
)


def add_config_arguments(parser):
    parser.add_argument(
        '-c', '--config',
        default=None,
        help='Config file path.' + (
                (' Available special values: "' + '", "'.join(SPECIAL_CONFIG_TAGS.values()) + '"')
                if len(SPECIAL_CONFIG_TAGS) > 0
                else ''
        )
    )


def translate_special_config_pathname(
        config_pathname,
        config_filename=DEFAULTS['config_file_name']
):
    base_dir = None
    if config_pathname == SPECIAL_CONFIG_TAGS['user']:
        base_dir = appdirs.user_config_dir(app_defaults.NAME, app_defaults.AUTHOR)
    elif config_pathname == SPECIAL_CONFIG_TAGS['app_dir']:
        base_dir = os.path.dirname(__file__)
    if base_dir is not None:
        return os.path.join(base_dir, config_filename)
    return config_pathname


def parse(args, parse_defaults=tuple(DEFAULTS.items())):
    if not isinstance(parse_defaults, dict):
        parse_defaults = dict(parse_defaults)

    args.config = translate_special_config_pathname(args.config)

    config = dict()
    # if (not (args.full_help or args.print_config) or os.path.exists(args.config)) and args.config:
    if args.config:
        if os.path.exists(args.config):
            print(f'Loading configuration file: {args.config}')
            with open(args.config, 'r') as config_f:
                config = yaml.safe_load(config_f)
        else:
            print(f'Config file "{args.config}" does not exist!')
            reply = str(input('Continue without config? [Y/n]:')).lower().strip()
            if len(reply) > 0 and reply[0] == 'n':
                return 0

    for arg_name in vars(args):
        if getattr(args, arg_name, None) is None:
            if arg_name in config:
                v = config[arg_name]
                setattr(args, arg_name, v)
            elif arg_name in parse_defaults:
                setattr(args, arg_name, parse_defaults[arg_name])
                config[arg_name] = parse_defaults[arg_name]
        elif arg_name != 'config':
            config[arg_name] = getattr(args, arg_name)

    for arg_name in parse_defaults:
        if arg_name not in config:
            config[arg_name] = parse_defaults[arg_name]

    return config
