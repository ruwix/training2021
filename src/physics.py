#
# See the documentation for more details on how this works
#
# The idea here is you provide a simulation object that overrides specific
# pieces of WPILib, and modifies motors/sensors accordingly depending on the
# state of the simulation. An example of this would be measuring a motor
# moving for a set period of time, and then changing a limit switch to turn
# on after that period of time. This can help you do more complex simulations
# of your robot code without too much extra effort.
#

import hal.simulation
from pyfrc.physics import motor_cfgs, tankmodel
from pyfrc.physics.core import PhysicsInterface
from pyfrc.physics.units import units

from components import chassis

talon0 = hal.SimDevice("Custom Talon FX[1]")
talon1 = hal.SimDevice("Custom Talon FX[3]")
talon0.createDouble("Position", False, 0)
talon1.createDouble("Position", False, 0)
import wpilib.simulation

class PhysicsEngine:
    """
        Simulates a motor moving something that strikes two limit switches,
        one on each end of the track. Obviously, this is not particularly
        realistic, but it's good enough to illustrate the point
    """

    chassis: chassis.Chassis

    @staticmethod
    def setSimulationPose(pose):
        
        wpilib.simulation.SimDeviceSim(f"Field2D").getDouble("x").set(pose.translation().x)
        wpilib.simulation.SimDeviceSim(f"Field2D").getDouble("y").set(pose.translation().y)
        wpilib.simulation.SimDeviceSim(f"Field2D").getDouble("rot").set(
            pose.rotation().degrees()
        )

    def __init__(self, physics_controller: PhysicsInterface):

        self.physics_controller = physics_controller

        self.drivetrain = tankmodel.TankModel.theory(
            motor_cfgs.MOTOR_CFG_FALCON_500,  # motor configuration
            chassis.Chassis.ROBOT_MASS * units.kilogram,  # robot mass
            chassis.Chassis.GEAR_RATIO,  # drivetrain gear ratio
            2,  # motors per side
            chassis.Chassis.TRACK_WIDTH * units.meter,  # robot wheelbase
            chassis.Chassis.ROBOT_WIDTH * units.meter,  # robot width
            chassis.Chassis.ROBOT_LENGTH * units.meter,  # robot length
            chassis.Chassis.WHEEL_RADIUS * units.meter,  # wheel diameter
        )
        self.wheel_position = chassis.WheelState()
        self.wheel_velocity = chassis.WheelState()

    def getMotorSpeed(self, id):
        return (
            wpilib.simulation.SimDeviceSim(f"Talon FX[{id}]")
            .getDouble("Motor Output")
            .get()
        )

    def setMotorPosition(self, id, position):
        wpilib.simulation.SimDeviceSim(f"Custom Talon FX[{id}]").getDouble("Position").set(
            position
        )

    def update_sim(self, now: float, tm_diff: float) -> None:
        """
            Called when the simulation parameters for the program need to be
            updated.
            
            :param now: The current time as a float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
        """

        self.wheel_velocity.left = self.getMotorSpeed(1) * chassis.Chassis.MAX_VELOCITY
        self.wheel_velocity.right = self.getMotorSpeed(3) * chassis.Chassis.MAX_VELOCITY

        self.wheel_position.left += self.wheel_velocity.left * tm_diff
        self.wheel_position.right += self.wheel_velocity.right * tm_diff

        self.setMotorPosition(1, self.wheel_position.left)
        self.setMotorPosition(3, -self.wheel_position.right)

        transform = self.drivetrain.calculate(
            self.wheel_velocity.left, self.wheel_velocity.right, tm_diff
        )

        pose = self.physics_controller.move_robot(transform)
        PhysicsEngine.setSimulationPose(pose)
