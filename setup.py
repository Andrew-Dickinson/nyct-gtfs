import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="nyct-gtfs",
    version="1.0.0",
    description="Real-time NYC subway data parsing for humans",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Andrew-Dickinson/nyct-gtfs",
    author="Andrew Dickinson",
    author_email="andrew.dickinson.0216@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["nyct_gtfs"],
    include_package_data=True,
    package_data={
        "nyct_gtfs": "gtfs_static/*.txt"
    },
    install_requires=["requests", "protobuf"]
)