from setuptools import find_packages, setup

package_name = 'satellite_comm'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jershia',
    maintainer_email='jasmineanisha0813@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
		'ground_station=satellite_comm.ground_station:main',
		'satellite = satellite_comm.satellite:main',
		'attacker = satellite_comm.attacker:main',       
 	],
    },
)
