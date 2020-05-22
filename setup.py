import sys

from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = [
    "click",
    "rasterio[s3]>=1.0.9",
    "numpy~=1.15",
    "supermercado",
    "mercantile",
    "geojson",
    "mxnet-cu90"
]

if sys.version_info < (3, 3):
    inst_reqs.append("contextlib2")

extra_reqs = {
    "test": ["pytest", "pytest-cov", "rio-tiler"],
    "dev": ["pytest", "pytest-cov", "rio-tiler", "pre-commit"],
}

if sys.version_info >= (3, 6):
    extra_reqs["test"].append("cogdumper")
    extra_reqs["dev"].append("cogdumper")

setup(
    name="car_detection",
    version="1.0.0",
    description=u"Use AI Model to Detect Cars.",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    zip_safe=False,
    entry_points="""
      [rasterio.rio_plugins]
      detection=car_detection.cli:detection
      """,
)
