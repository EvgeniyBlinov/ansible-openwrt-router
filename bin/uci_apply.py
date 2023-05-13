#!/usr/bin/env python3

import sys
import re
import json
import argparse

from pprint import pprint

def string_unquote(src: str):
    return src.replace('"', '').replace("'", '')


class UciParseError(ValueError):
    """Exception raised when a UCI file can't be parsed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UciFile:
    filepath = ''
    configSections = {}

    # Matches any known type of line
    _LINE_REGEX = re.compile(r"(^\s*$)|((^\s*)(#)(.*$))|((^\s*)(package|config|option|list|[A-Za-z]+)\s+([^\s]+)\s+(.*?)\s*$)")

    _CONFIG_NAME_REGEX = re.compile(r"config\s+([^\s]+)((\s+[^\s]+)|(\s*$))")

    def __init__(self, filepath):
        self.filepath = filepath

    def parse(self):
        lineno = 0

        section_name = ''
        with open(self.filepath, 'r') as fp:
            for line in fp:
                lineno += 1
                match = self._LINE_REGEX.match(line)

                if not match:
                    raise UciParseError("Error on line %d: unrecognized line type" % lineno)
                if match[4] == "#":
                    continue
                elif match[8]:
                    if match[8] == "package":
                        continue
                    elif match[8] == "config":
                        config_match = self._CONFIG_NAME_REGEX.match(line)
                        section_type = config_match[1]
                        section_name = string_unquote(config_match[2].strip())
                        section_fullname = section_type + '___' + section_name
                        if section_type not in self.configSections:
                            self.configSections[section_type] = {}

                        self.configSections[section_type][section_name] = {
                            'options': []
                        }
                    elif match[8] == "option":
                        option_name = match[9]
                        option_value = string_unquote(match[10])
                        self.configSections[section_type][section_name]['options'].append({
                            option_name: option_value
                        })
                        continue
                    elif match[8] == "list":
                        continue

        return self.configSections

    def apply(self, changes: str):
        ch = json.loads(changes)
        for section_type,  st_value in ch.items():
            if section_type in self.configSections:
                for _section_name in st_value:
                    if _section_name == '*':
                        for section_name, old_sn_value in self.configSections[section_type].items():
                            self.configSections[section_type][section_name]['options'] = self.merge_options(
                                self.configSections[section_type][section_name]['options'],
                                st_value[_section_name]['options']
                            )

                    else:
                        self.configSections[section_type][_section_name]['options'] = self.merge_options(
                            self.configSections[section_type][_section_name]['options'],
                            st_value[_section_name]['options']
                        )


    def merge_options(self, src, dst):
        o_name_merged = []
        for option in dst:
            append = True
            for o_name, o_value in option.items():
                for idx, old_opt in enumerate(src):
                    if o_name in old_opt:
                        if not (o_name in o_name_merged and option in src):
                            src[idx][o_name] = o_value
                            append = False
                o_name_merged.append(o_name)
            if append:
                src.append(option)
        return src

    def output(self, type='uci'):
        if type == 'uci':
            for section_type, st_value in self.configSections.items():
                for section_name, sn_value in st_value.items():
                    if section_name:
                        print('config ' + section_type + " '" + section_name + "'")
                    else:
                        print('config ' + section_type)

                    for option in sn_value['options']:
                        for o_name, o_value in option.items():
                            print('\toption '+ o_name + " '" + str(o_value) + "'")
                    print('')
        elif type == 'json':
            print(json.dumps(self.configSections))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output", help="output type (json|uci)",
        choices=['json', 'uci'],
        default='uci'
        )
    parser.add_argument(
        "-f", "--ucifile", help="path to uci file",
        type=str
        )
    parser.add_argument(
        "-a", "--apply", help="apply changes",
        type=str
        )
    args = parser.parse_args()
    ucifile = UciFile(args.ucifile)
    ucifile.parse()
    if args.apply:
        ucifile.apply(args.apply)
        #ucifile.apply("""
        #{
            #"wifi-iface": {
                #"*": {
                    #"options": [
                        #{"network": "lan"},
                        #{"mode": "ap"},
                        #{"ssid": "SOME-SSID"},
                        #{"encryption": "psk2"},
                        #{"key": "secret"}
                    #]
                #}
            #}
        #}
        #""")
    ucifile.output(args.output)
