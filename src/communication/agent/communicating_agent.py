#!/usr/bin/env python3
from mesa import Agent

from communication.mailbox.mailbox import Mailbox
from communication.message.message import Message
from communication.message.message_service import MessageService
from objects import Waste, Zone


class CommunicatingAgent(Agent):
    """CommunicatingAgent class.
    Class implementing communicating agent in a generalized manner.

    Not intended to be used on its own, but to inherit its methods to multiple
    other agents.

    attr:
        name: The name of the agent (str)
        mailbox: The mailbox of the agent (Mailbox)
        message_service: The message service used to send and receive message (MessageService)
    """

    def __init__(self, model, name):
        """Create a new communicating agent."""
        super().__init__(model)
        self.__name = name
        self.__mailbox = Mailbox()
        self.__messages_service = MessageService.get_instance()

    def step_agent(self):
        """The step methods of the agent called by the scheduler at each time tick."""
        super().step()

    def get_name(self):
        """Return the name of the communicating agent."""
        return self.__name

    def receive_message(self, message):
        """Receive a message (called by the MessageService object) and store it in the mailbox."""
        self.__mailbox.receive_messages(message)

    def send_message(self, message):
        """Send message through the MessageService object."""
        self.__messages_service.send_message(message)

    def send_broadcast_message(self, performative, content):
        """Broadcast message through the MessageService object."""
        for agent in self.model.agents:
            # Skip the agent itself and the Waste and Zone agents
            # as they are not supposed to receive messages.
            if isinstance(agent, Waste) or isinstance(agent, Zone) or agent == self:
                continue

            message = Message(self.unique_id, agent.unique_id, performative, content)
            self.send_message(message)

    def get_new_messages(self):
        """Return all the unread messages."""
        return self.__mailbox.get_new_messages()

    def get_messages(self):
        """Return all the received messages."""
        return self.__mailbox.get_messages()

    def get_messages_from_performative(self, performative):
        """Return a list of messages which have the same performative."""
        return self.__mailbox.get_messages_from_performative(performative)

    def get_messages_from_exp(self, exp):
        """Return a list of messages which have the same sender."""
        return self.__mailbox.get_messages_from_exp(exp)
