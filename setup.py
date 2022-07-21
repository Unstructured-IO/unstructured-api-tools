"""
setup.py

unstructured_api_tools - Utilities to manage APIs from notebooks

Copyright 2022 Unstructured Technologies, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from setuptools import setup, find_packages

from unstructured_api_tools.__version__ import __version__

setup(
    name="unstructured_api_tools",
    description="A library that prepares raw documents for downstream ML tasks.",
    author="Unstructured Technologies",
    author_email="mrobinson@unstructuredai.io",
    license="Apache-2.0",
    packages=find_packages(),
    include_package_data=True,
    version=__version__,
    entry_points={
        "console_scripts": "unstructured_api_tools=unstructured_api_tools.cli:cli"
    },
    install_requires=[
        "click>=8.1",
        "fastapi",
        "slowapi",
        "Jinja2",
        "nbconvert",
        "python-multipart",
        "uvicorn[standard]",
        "types-requests"
    ],
    extras_require={},
)
