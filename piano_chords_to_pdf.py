#!/usr/bin/env python3.7

# Dependencies:
# - wkhtmltopdf

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from itertools import repeat
from pathlib import Path
from typing import List


KEYS_JSON_DIR = 'chord_links'
OUTPUT_PDF_DIR = 'Chords PDF'


def safe_unix_name(name):
    """
    Piano chord names might contain slash - /
    This might break file saving because / is a directory separator in Unix
    """
    return name.replace('/', '-slash-')


@dataclass
class Chord:
    link: str
    name: str = field(default=property)

    @name.default
    def name(self) -> str:
        return safe_unix_name(self._name)

    @name.setter
    def name(self, value) -> None:
        self._name = value


@dataclass
class KeySignature:
    full_path: Path

    def name(self) -> str:
        """
        The chord key name is derived from the file name
        Example: /long/path/C#.json would return C#
        """
        key_signature_name = self.full_path.stem
        return safe_unix_name(key_signature_name)

    def output_dir(self) -> Path:
        return Path(OUTPUT_PDF_DIR).joinpath(self.name())

    def chords(self) -> List[Chord]:
        """Get all chords for the current key signature""" 
        file_content = self.full_path.read_text()
        chords_dict = json.loads(file_content)
        return [Chord(**chord_dict_item) for chord_dict_item in chords_dict]


def read_key_signature_json_files(files_path: str) -> List[KeySignature]:
    """
    Get all key signature JSON files which contain chord information from 8notes
    """
    key_signatures = Path(files_path).glob('*.json')
    return [KeySignature(key_sig_path) for key_sig_path in key_signatures]


def download_chord(chord: Chord, output_dir: Path) -> None:
    chord_pdf_file = output_dir.joinpath(f'{chord.name}.pdf')
    subprocess.run(['wkhtmltopdf', '--quiet', chord.link, chord_pdf_file])


def main() -> None:
    key_signatures = read_key_signature_json_files(KEYS_JSON_DIR)

    for key_sig in key_signatures:
        output_dir = key_sig.output_dir()
        if output_dir.is_dir():
            print(f'The directory "{output_dir}" already exists. Skipping download.')
            continue

        output_dir.mkdir(parents=True)
        print(f'Beginning download for "{key_sig.name()}" chords in "{output_dir}"')

        # https://yuanjiang.space/threadpoolexecutor-map-method-with-multiple-parameters
        with ThreadPoolExecutor(max_workers=7) as executor:
            executor.map(download_chord, key_sig.chords(), repeat(output_dir))


if __name__ == '__main__':
    main()
