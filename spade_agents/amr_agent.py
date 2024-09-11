import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
import json

class AMR(spade.agent.Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.state = "Idle"  # Initial state
        self.queue = []  # List to keep track of agents in the queue
        self.position_in_queue = None
        self.coordinates = None  # Coordinates to move to when in the queue

    # Idle behaviour: wait for queue request or updates
    class IdleBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.state == "Idle":
                print("Agent is idle, waiting for instructions...")
                msg = await self.receive(timeout=10)
                if msg and msg.body:
                    try:
                        body = json.loads(msg.body)
                        if body['action'] == 'queue_request':
                            print(f"Received queue request from {msg.sender}")
                            if msg.sender not in self.agent.queue:
                                self.agent.queue.append(msg.sender)
                                print(f"Queue: {self.agent.queue}")
                                if self.agent.position_in_queue is None:
                                    self.agent.position_in_queue = len(self.agent.queue)
                                    print(f"My position in queue: {self.agent.position_in_queue}")
                                self.agent.state = "Queueing"
                        elif body['action'] == 'update_position':
                            # Update position when the agent ahead leaves the queue
                            self.agent.position_in_queue -= 1
                            print(f"Position updated: {self.agent.position_in_queue}")
                            if self.agent.position_in_queue == 1:
                                # Take over the coordinates from the departing agent
                                self.agent.coordinates = body['coordinates']
                                print(f"Received new coordinates: {self.agent.coordinates}")
                    except json.JSONDecodeError:
                        print("Error decoding the message.")
                else:
                    print("No instructions received.")
    
    # Queueing behaviour: manage queue position and perform tasks when it's the agent's turn
    class QueueingBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.state == "Queueing":
                print(f"Agent in queue, position: {self.agent.position_in_queue}")
                if self.agent.position_in_queue == 1:
                    print(f"Moving to coordinates: {self.agent.coordinates}")
                    await self.perform_task()
                    # Notify the next agent in queue to take over
                    await self.notify_next_agent()
                    self.agent.state = "Idle"
                    print("Task completed, going back to Idle state.")
                else:
                    print(f"Waiting for my turn... Position: {self.agent.position_in_queue}")
                    await asyncio.sleep(2)  # Wait before checking queue position again

    # Perform the task and simulate movement
    async def perform_task(self):
        print("Performing queued task...")
        await asyncio.sleep(5)  # Simulate task duration

    # Notify the next agent in the queue to take over
    async def notify_next_agent(self):
        if len(self.agent.queue) > 1:
            # Notify the agent in position 2 to move to position 1
            next_agent_jid = self.agent.queue[1]
            msg = Message(to=next_agent_jid)
            msg.body = json.dumps({
                'action': 'update_position',
                'coordinates': self.agent.coordinates  # Pass the coordinates to the next agent
            })
            await self.send(msg)
        # Remove yourself from the queue
        self.agent.queue.pop(0)

    async def setup(self):
        print("Agent started with Idle and Queueing behaviours.")
        self.add_behaviour(self.IdleBehaviour())
        self.add_behaviour(self.QueueingBehaviour())


# Example usage to start multiple agents
async def main():
    agent1 = AMR("agent1@jabber_server", "password")
    # agent2 = AMR("agent2@jabber_server", "password")
    # agent3 = AMR("agent3@jabber_server", "password")
    
    await agent1.start(auto_register=True)
    # await agent2.start(auto_register=True)
    # await agent3.start(auto_register=True)
    
    # Simulate sending a queue request message to agents
    await asyncio.sleep(2)
    queue_request = Message(to="agent1@jabber_server", body=json.dumps({"action": "queue_request"}))
    # await agent2.send(queue_request)
    # await agent3.send(queue_request)
    
    await spade.wait_until_finished(agent1)
    # await spade.wait_until_finished(agent2)
    # await spade.wait_until_finished(agent3)

if __name__ == "__main__":
    spade.run(main())
