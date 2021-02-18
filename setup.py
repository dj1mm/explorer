
from setuptools import setup, find_packages

setup(name="explorer",
      version="0.0.1",
      description="A python library to describe a system of multiple pcbs and fpgas",
      url="https://github.com/dj1mm/explorer",
      author="Jimmy Ah Fat",
      author_email="j.ahfat95@gmail.com",
      packages=find_packages(),
      package_data={"explorer": [ "*.jinja2" ]},
      install_requires=["disjoint_set", "Jinja2"],
      python_requires=">=3.7.4",
)
