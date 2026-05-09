"""Shim para permitir 'pip install -e .' em versoes antigas de pip
(pre-PEP 660). A configuracao real do pacote vive em pyproject.toml."""

from setuptools import setup

setup()
