from communication import Message, MessagePerformative


def pairing_logic(drone, new_messages, MAX_TIMEOUT_STEP):
    # Helper function to calculate Manhattan distance
    def calculate_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # ========= Pairing logic ==========
    if drone.knowledge.pairing_status == "requesting":
        # Filter accept pairing messages
        accept_pair_messages = [
            msg
            for msg in new_messages
            if msg.get_performative() == MessagePerformative.ACCEPT_PAIRING
        ]

        if accept_pair_messages and drone.knowledge.carried_waste_timeout == 0:
            # Pick closest accept message
            closest_accept: Message = min(
                accept_pair_messages,
                key=lambda msg: calculate_distance(msg.get_content()[1], drone.pos),
            )

            drone.logger.info(
                f"PAIRING: Received pairing acceptance from {closest_accept.get_content()[0]} at {closest_accept.get_content()[1]}"
            )
            drone.knowledge.paired_agent = drone.model.get_agent_by_id(
                closest_accept.get_exp()
            )
            drone.logger.info(
                f"PAIRING: Paired with agent {drone.knowledge.paired_agent.unique_id}"
            )
            drone.knowledge.pairing_status = "paired"
            drone.knowledge.carried_waste_timeout = MAX_TIMEOUT_STEP

            # Reset rejected_by list once paired
            drone.knowledge.rejected_by = []
        elif not accept_pair_messages:
            drone.logger.info(
                "PAIRING: No pairing acceptance received, waiting for a response"
            )
            drone.logger.info(f"New messages: {new_messages}")

        # Handle reject pairing messages
        reject_pair_messages = [
            msg
            for msg in new_messages
            if msg.get_performative() == MessagePerformative.REJECT_PAIRING
        ]

        for msg in reject_pair_messages:
            drone.logger.info(
                f"PAIRING: Received pairing rejection from {msg.get_exp()}"
            )
            drone.knowledge.rejected_by.append(msg.get_exp())

    elif drone.knowledge.pairing_status == "unpaired":
        # Filter request pairing messages
        received_request_pair_messages = [
            msg
            for msg in new_messages
            if msg.get_performative() == MessagePerformative.REQUEST_PAIRING
        ]

        if (
            received_request_pair_messages
            and drone.knowledge.carried_waste_timeout == 0
        ):
            drone.logger.info(
                f"PAIRING: Received {len(received_request_pair_messages)} pairing requests"
            )
            # Accept closest pairing request
            closest_pair: Message = min(
                received_request_pair_messages,
                key=lambda msg: calculate_distance(msg.get_content()[1], drone.pos),
            )

            # Send accept message
            drone.logger.info(
                f"PAIRING: Accepting pairing request from {closest_pair.get_content()[0]} at {closest_pair.get_content()[1]} (ID: {closest_pair.get_exp()})"
            )
            drone.send_message(
                Message(
                    message_performative=MessagePerformative.ACCEPT_PAIRING,
                    from_agent=drone.unique_id,
                    to_agent=closest_pair.get_exp(),
                    content=(drone.unique_id, drone.pos),
                )
            )
            drone.knowledge.pairing_status = "paired"
            drone.knowledge.paired_agent = drone.model.get_agent_by_id(
                closest_pair.get_exp()
            )

        elif received_request_pair_messages:
            # Handle cases where pairing is not possible
            if drone.knowledge.carried_waste_timeout > 0:
                drone.logger.info(
                    "PAIRING: Ignoring pairing requests, carried waste timeout not expired"
                )
            elif drone.knowledge.pairing_status == "paired":
                drone.logger.info(
                    f"PAIRING: Already paired with agent {drone.knowledge.paired_agent.unique_id}"
                )

            for msg in received_request_pair_messages:
                drone.send_message(
                    Message(
                        message_performative=MessagePerformative.REJECT_PAIRING,
                        from_agent=drone.unique_id,
                        to_agent=msg.get_exp(),
                        content=(drone.unique_id, drone.pos),
                    )
                )

        else:
            drone.logger.info("PAIRING: No pairing requests received")

    # ========= Carried Waste Timeout Logic =========
    if (
        drone.knowledge.carried_waste_timeout > 0
        and drone.zone_type < 2
        and len(drone.knowledge.inventory) == 1
    ):
        drone.logger.info("PAIRING: Decreasing carried waste timeout")
        drone.knowledge.carried_waste_timeout -= 1

    elif (
        drone.knowledge.carried_waste_timeout == 0
        and drone.zone_type < 2
        and drone.knowledge.pairing_status != "paired"
    ):
        drone.logger.info("PAIRING: Carried waste timeout expired")
        drone.logger.info("Looking for an agent to take/give waste to")

        # Find compatible agents
        compatible_agents = [
            other_agent
            for other_agent in drone.model.agents
            if other_agent != drone
            and other_agent.__class__.__name__ == "Drone"
            and other_agent.zone_type == drone.zone_type
            and len(other_agent.knowledge.inventory) == 1
            and other_agent.knowledge.inventory[0].waste_color == drone.zone_type
            and other_agent.knowledge.carried_waste_timeout == 0
            and other_agent.unique_id not in drone.knowledge.rejected_by
        ]

        # Pick closest compatible agent
        if compatible_agents:
            drone.knowledge.pairing_status = "requesting"
            drone.knowledge.other_agent_with_extra_waste = min(
                compatible_agents,
                key=lambda agent: calculate_distance(agent.pos, drone.pos),
            )
            drone.logger.info(
                f"PAIRING: Found compatible agent with extra waste: {drone.knowledge.other_agent_with_extra_waste.unique_id}"
            )
            drone.knowledge.carried_waste_timeout = MAX_TIMEOUT_STEP

            # Send a pairing request
            drone.logger.info(
                f"PAIRING: Sending message to agent {drone.knowledge.other_agent_with_extra_waste.unique_id}"
            )
            drone.send_message(
                Message(
                    message_performative=MessagePerformative.REQUEST_PAIRING,
                    from_agent=drone.unique_id,
                    to_agent=drone.knowledge.other_agent_with_extra_waste.unique_id,
                    content=(drone.unique_id, drone.pos),
                )
            )
        else:
            drone.knowledge.other_agent_with_extra_waste = None
            drone.logger.info("PAIRING: No compatible agents found waiting")
