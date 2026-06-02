from setuptools import find_packages, setup

setup(
    name="puck_dynamics",
    version="0.1.0",
    description="A stochastic puck trajectory simulation framework",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "numpy",
        "matplotlib",
        "scipy",
    ],
)
