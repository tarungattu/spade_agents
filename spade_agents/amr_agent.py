import spade
from spade.message import Message
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
import asyncio
import json

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, PoseStamped
from geometry_msgs.msg import Pose

class AMRAgent(spade.agent.Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.navigator = BasicNavigator()
        self.current_goal = None
        self.rclpy_init_flag = 0

    class RequestCoordinatesBehaviour(OneShotBehaviour):
        async def run(self):
            print("AMR Agent: Sending request for coordinates...")

            # Create a message to send to the coordinator
            msg = Message(to="loading_dock@jabber.fr")  # Coordinator's JID
            msg.body = "provide_coordinates"  # The request message body
            
            await self.send(msg)
            print("AMR Agent: Request sent.")
    
    class ReceiveCoordinatesBehaviour(CyclicBehaviour):
        async def run(self):
            print("AMR Agent: Waiting to receive coordinates...")
            
            # Receive a message from the coordinator agent
            msg = await self.receive(timeout=10)  # Wait for 10 seconds to receive the message
            if msg:
                print(f"AMR Agent: Received message: {msg.body}")
                
                # Parse the received coordinates
                try:
                    coordinates = json.loads(msg.body)
                    x, y = coordinates[0], coordinates[1]
                    print(f"AMR Agent: Coordinates received: x={x}, y={y}")
                    
                    # Set the current goal for navigation
                    self.agent.current_goal = (x, y)
                except json.JSONDecodeError:
                    print(f"AMR Agent: Unable to decode received message: {msg.body}")
            else:
                print("AMR Agent: No message received.")
    
    class GoToPoseBehaviour(CyclicBehaviour):
        rclpy.init()
        async def run(self):
            if self.agent.current_goal:
                x, y = self.agent.current_goal
                print(f"AMR Agent: Navigating to coordinates: x={x}, y={y}")
                
                # Create a PoseStamped goal using the coordinates
                goal_pose = PoseStamped()
                goal_pose.header.frame_id = "map"
                goal_pose.pose.position.x = x
                goal_pose.pose.position.y = y
                goal_pose.pose.orientation.w = 1.0  # Set orientation (assuming facing forward)

                # Start navigation
                self.agent.navigator.goToPose(goal_pose)

                # Wait until the robot reaches the goal or fails
                while not self.agent.navigator.isTaskComplete():
                    await asyncio.sleep(0.5)  # Wait before checking the status again
                
                # Check if the robot successfully reached the goal
                result = self.agent.navigator.getResult()
                if result == BasicNavigator.SUCCEEDED:
                    print("AMR Agent: Successfully reached the goal.")
                else:
                    print("AMR Agent: Failed to reach the goal.")
                
                # Clear the current goal after reaching it
                self.agent.current_goal = None
                print("AMR Agent: Waiting for next set of coordinates.")
    
    async def setup(self):
        print("AMR Agent: Starting...")

        # Add the behaviour to send a request for coordinates
        request_behaviour = self.RequestCoordinatesBehaviour()
        self.add_behaviour(request_behaviour)

        # Add the behaviour to receive coordinates
        receive_behaviour = self.ReceiveCoordinatesBehaviour()
        self.add_behaviour(receive_behaviour)

        # Add the behaviour to go to the received pose
        goto_pose_behaviour = self.GoToPoseBehaviour()
        self.add_behaviour(goto_pose_behaviour)


# Example usage to start the AMR agent
async def main():
    amr_agent = AMRAgent("amr1@jabber.fr", "imagent1")

    print("AMR Agent is starting up...")
    await amr_agent.start(auto_register=True)
    
    await spade.wait_until_finished(amr_agent)
    await amr_agent.stop()

if __name__ == "__main__":
    spade.run(main())
