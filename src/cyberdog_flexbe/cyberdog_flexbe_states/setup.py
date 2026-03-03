from setuptools import setup, find_packages
setup(
    name="cyberdog_flexbe_states",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Vitor Calvi",
    maintainer_email="vitor@calvi.me",
    description="CyberDog FlexBE States",
    license="MIT",
    tests_require=["pytest"],
    entry_points={"console_scripts": []},
)
