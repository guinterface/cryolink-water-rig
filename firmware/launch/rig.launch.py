"""Water bench launch. Source fsw/env.sh and install this package first."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    fsw = ['transfer_sequencer', 'coupling_manager', 'chilldown_controller',
           'pressure_controller', 'fill_estimator', 'thermal_controller',
           'fdir_monitor', 'host_bridge', 'tm_gateway']
    actions = [DeclareLaunchArgument('port', default_value='/dev/ttyUSB0'),
               DeclareLaunchArgument('wall_threshold_c', default_value='15.0'),
               DeclareLaunchArgument('wall_hold_s', default_value='5.0'),
               DeclareLaunchArgument('fill_target_ml', default_value='50.0'),
               Node(package='rig_bridge', executable='rig_bridge',
                    parameters=[{'port': LaunchConfiguration('port'), 'use_sim_time': False,
                                 **{key: ParameterValue(LaunchConfiguration(key), value_type=float)
                                    for key in ('wall_threshold_c', 'wall_hold_s', 'fill_target_ml')}}], output='screen')]
    for name in fsw:
        remaps = []
        if name == 'coupling_manager':
            remaps = [('/leakcheck/result', '/diagnostics/lox/leakcheck')]
        elif name == 'chilldown_controller':
            remaps = [('/state/chill', '/diagnostics/lox/chill')]
        elif name == 'fill_estimator':
            remaps = [('/state/fill', '/diagnostics/lox/fill')]
        actions.append(Node(package='rig_bridge', executable='water_fsw', arguments=[name],
                            parameters=[{'use_sim_time': False}], remappings=remaps, output='screen'))
    return LaunchDescription(actions)
