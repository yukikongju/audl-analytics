from setuptools import find_packages, setup

setup(
        name="audl-analytics",
        packages=find_packages(exclude=["tests"]),
        install_requires=[
            "pandas", 
            "numpy",
            "graphene", 
            "neo4j",
            "dagster", 
            "pymongo", 
            "audl", 
            "python-decouple"
        ],
        extras_require={"dev": ["dagster-webserver", "pytest"]}
)
