from setuptools import setup, find_packages

setup(
    name="hueify",
    version="0.1.0",
    description="Hue control CLI tool",
    author="Mathis Arends",
    url="https://github.com/mathisarends/hueify",
    packages=find_packages(),
    install_requires=[
        "typer[all]",
        "aiohttp>=3.11.0",
        "python-dotenv>=1.0.0",
        "aiohappyeyeballs>=2.6.0",
    ],
    entry_points={
        'console_scripts': [
            'hueify=hueify.cli:app',
        ],
    },
    include_package_data=True,
    python_requires=">=3.7",
    license="MIT",
)