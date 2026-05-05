from setuptools import find_packages, setup

package_name = 'diff_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch' , [
            'launch/rsp.launch.py' ,
            'launch/rsp_gazebo.launch.py']) ,
        ('share/' + package_name + '/description' , [
            'description/core_robot.xacro.urdf',
            'description/robot_include.xacro',
            'description/inertial.xacro',
            'description/control.xacro',
            'description/lidar.xacro',
            'description/camera.xacro',
        ])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='youssef',
    maintainer_email='youssef@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "image_process = diff_robot.image_processing:main",
            "control_diff = diff_robot.control_diff:main",
            "teleop = diff_robot.teleop:main"
        ],
    },
)
