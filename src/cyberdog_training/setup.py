from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'cyberdog_training'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cyberdog',
    maintainer_email='cyberdog@todo.todo',
    description='CyberDog reinforcement learning training package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'train = cyberdog_training.train:main',
            'env_test = cyberdog_training.env_node:main',
        ],
    },
)
