from setuptools import setup
setup(name='rig_bridge', version='0.1.0', packages=['rig_bridge'],
      data_files=[('share/ament_index/resource_index/packages', ['resource/rig_bridge']),
                  ('share/rig_bridge', ['package.xml']),
                  ('share/rig_bridge/launch', ['launch/rig.launch.py'])],
      install_requires=['setuptools', 'pyserial==3.5'],
      entry_points={'console_scripts': ['rig_bridge=rig_bridge.node:main',
                                       'water_fsw=rig_bridge.fsw_runner:main',
                                       'mcu_emulator=rig_bridge.emulator:main']})
