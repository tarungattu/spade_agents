import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
import json
import time

class CoordinatorAgent(spade.agent.Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.state = "IDLE"  # Initial state
        self.current_jid = None
        self.end_agent = None

    # IDLE behaviour: wait for the JID of the first agent in the queue and send coordinates
    class IdleBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.state == "IDLE":
                print("Coordinator is idle, waiting for JID...")
                msg = await self.receive(timeout=10)
                if msg and msg.body:
                    if msg.body == 'provide_coordinates':
                        # Ensure current_jid is a string
                        self.agent.current_jid = str(msg.sender)
                        coordinates = [-6.69, 4.028]  # Example coordinates to send
                        print(f"Sending coordinates {coordinates} to {self.agent.current_jid}")

                        # Create and send a response message with the coordinates
                        response_msg = Message(to=self.agent.current_jid)
                        response_msg.body = str(coordinates)  # Send coordinates as a string
                        await self.send(response_msg)

                        # Update agent state to PROCESSING
                        self.agent.state = "PROCESSING"
                    else:
                        print("Received unexpected message body:", msg.body)
                else:
                    print("No message received.")
    
    # PROCESSING behaviour: wait for a while and then send new coordinates
    class ProcessingBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.state == "PROCESSING":
                print("Coordinator is processing...")

                # Start tracking the process
                process_completed = False
                start_time = time.time()

                # Keep track of the original sender (the agent that received the first coordinates)
                original_sender_jid = self.agent.current_jid

                while not process_completed:
                    # Check if the process is completed
                    current_time = time.time()
                    if current_time - start_time >= 15:  # Example condition (e.g., 15 seconds)
                        process_completed = True
                        print("Process completed.")
                    
                    # Receive a message while waiting for the process to complete
                    msg = await self.receive(timeout=1)  # Short timeout to keep checking for process completion
                    if msg and msg.body:
                        print(f"Received message from {msg.sender}: {msg.body}")
                        
                        # Only respond with new coordinates if the sender is different from the original
                        if str(msg.sender) != str(original_sender_jid):
                            if not self.agent.end_agent:
                                # If no end_agent, send new coordinates
                                new_coordinates = [3.0, 4.0]  # Example coordinates
                                print(f"Sending new coordinates {new_coordinates} to {msg.sender}")
                                
                                response_msg = Message(to=str(msg.sender))
                                response_msg.body = json.dumps(new_coordinates)
                                await self.send(response_msg)
                            else:
                                # Send the JID of the current end_agent
                                queue_end_agent = self.agent.end_agent
                                print(f"Sending the current end agent's JID {queue_end_agent} to {msg.sender}")
                                
                                response_msg = Message(to=str(msg.sender))
                                response_msg.body = json.dumps({"end_agent": str(queue_end_agent)})
                                await self.send(response_msg)
                                
                            # Set the sender as the new end agent
                            self.agent.end_agent = str(msg.sender)
                            print(f"End agent is now: {self.agent.end_agent}")

                        else:
                            print(f"Received message from original sender {msg.sender}, not sending new coordinates.")
                    
                    # Short sleep to prevent excessive CPU usage while waiting
                    await asyncio.sleep(0.1)

                # After processing is done, reset end_agent to None if it matches the current agent
                if self.agent.end_agent == self.agent.current_jid:
                    print(f"End agent {self.agent.end_agent} has finished processing. Resetting end agent.")
                    self.agent.end_agent = None  # Reset the end agent
                
                print("current end agent", self.agent.end_agent)

                # Once the process is complete, transition back to IDLE
                self.agent.state = "IDLE"
                print("Returning to IDLE state.")


    async def setup(self):
        print("Coordinator agent started with IDLE and PROCESSING behaviours.")
        self.add_behaviour(self.IdleBehaviour())
        self.add_behaviour(self.ProcessingBehaviour())


# Example usage to start the coordinator agent
async def main():
    coordinator = CoordinatorAgent("loading_dock@jabber.fr", "imagent1")

    print('loading dock is up and running')
    await coordinator.start(auto_register=True)
    
    await spade.wait_until_finished(coordinator)
    await coordinator.stop()

if __name__ == "__main__":
    spade.run(main())
