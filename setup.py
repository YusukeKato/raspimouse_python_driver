from setuptools import find_packages, setup

package_name = 'raspimouse_python_driver'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test', 'test.*']),
    # Used only by colcon / ament. Harmless when installed with pip.
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    python_requires='>=3.10',
    # The only dependency, lgpio, is installed with apt (python3-lgpio).
    # It is deliberately not listed in install_requires so that pip never pulls it from PyPI.
    install_requires=[],
    extras_require={
        'test': ['pytest'],
    },
    zip_safe=True,
    maintainer='YusukeKato',
    maintainer_email='yusukekato.contact@gmail.com',
    description='Pure Python device driver for Raspberry Pi Mouse',
    license='MIT',
    entry_points={
        'console_scripts': [
            'raspimouse-cli = raspimouse_python_driver.tools.cli:main',
        ],
    },
)
