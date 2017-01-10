from codecs import open
from os import path

import seot.agent

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    all_reqs = f.read().split("\n")

install_requires = [x.strip() for x in all_reqs if "git+" not in x]
dependency_links = [x.strip().replace("git+", "") for x in all_reqs
                    if x.startswith("git+")]

setup(
    name="seotagent",
    version=seot.agent.__version__,
    description="SEoT Agent",
    long_description=long_description,
    license="BSD",
    classifiers=[
      "Development Status :: 3 - Alpha",
      "Intended Audience :: Developers",
      "Programming Language :: Python :: 3",
    ],
    keywords="",
    packages=find_packages(exclude=["docs", "tests*"]),
    entry_points={
        "console_scripts": [
            "seot-agent = seot.agent.__init__:main",
            "dptool = seot.agent.dptool:main"
        ],
    },
    include_package_data=True,
    author="Keichi Takahashi",
    install_requires=install_requires,
    dependency_links=dependency_links,
    author_email="keichi.t@me.com"
)
