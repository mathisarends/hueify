from setuptools import setup, find_packages

setup(
    name="hueify",
    version="0.1.0",
    description="Hue control CLI tool",
    author="Dein Name",
    packages=find_packages(),
    install_requires=[
        "typer[all]",
    ],
    entry_points={
        "console_scripts": [
            "hueify = hueify.cli:app",
        ],
    },
    include_package_data=True,
    python_requires=">=3.7",
)