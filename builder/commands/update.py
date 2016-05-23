import os
import ConfigParser
import logging
import sys
import argparse
import yaml

from cliff.command import Command
from builder.slave import Slave


class Update(Command):
    """
    Command for updating slaves on jenkins
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = argparse.ArgumentParser(description="Parser")
        parser.add_argument("--conf",
                            type=str,
                            help="Path to the jenkins config file")
        parser.add_argument("yaml",
                            type=str,
                            nargs="+",
                            help="Path to the slave yaml file")
        return parser

    def create_or_update_slave(self, config, yaml_file):
        with open(yaml_file, 'r') as file:
            yaml_str = file.read()
            self.log.debug(yaml_str)

            entries = yaml.load(yaml_str)

            for entry in entries:
                slave = Slave(params=entry['slave'], jenkins=config)
                self.log.debug(slave)

                slave.create_or_update()

    def take_action(self, parsed_args):
        self.log.info("Updating slave node in Jenkins")
        if not parsed_args.conf:
            print parser.print_help()
            sys.exit(1)
        config = self.parse_config(parsed_args.conf)

        for filename in parsed_args.yaml:
            path = os.path.join(filename)

            targets = [path]
            if os.path.isdir(path):
                targets = [os.path.join(path, name) for name in os.listdir(path)]

            for yaml in targets:
                self.log.debug("Slave yaml file: %s" % yaml)
                self.create_or_update_slave(config, yaml)

    def parse_config(self, config_file):
        self.log.debug("Parsing the jenkins config file")
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        user     = config.get('jenkins', 'user')
        password = config.get('jenkins', 'password')
        url      = config.get('jenkins', 'url')

        return dict(url=url, user=user, password=password)
