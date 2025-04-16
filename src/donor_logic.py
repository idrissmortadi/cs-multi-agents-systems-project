from communication import Message, MessagePerformative


def donor_logic(drone, new_messages, MAX_TIMEOUT_STEP):
    """
    Main controller function for the drone donor system.
    Handles different states of the drone in the donation process
    and updates timeouts for carrying waste.
    """
    if drone.knowledge.donor_status == "requesting":
        handle_requesting_status(drone, new_messages)
    elif drone.knowledge.donor_status == "idle":
        handle_idle_status(drone, new_messages)

    update_carried_waste_timeout(drone, MAX_TIMEOUT_STEP)


def calculate_distance(pos1, pos2):
    """
    Calculate Manhattan distance between two positions (x1, y1) and (x2, y2).
    Returns the sum of absolute differences in coordinates.
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def handle_requesting_status(drone, new_messages):
    """
    Process incoming messages when drone is in 'requesting' state.
    Handles responses from potential donors and updates drone state accordingly.
    """
    # Filter donation response messages
    donation_responses = [
        msg
        for msg in new_messages
        if msg.get_performative() == MessagePerformative.ACCEPT_DONATION
    ]

    waste_location_messages = [
        msg
        for msg in new_messages
        if msg.get_performative() == MessagePerformative.INFORM_WASTE_POS_ADD_REF
    ]

    rejection_messages = [
        msg
        for msg in new_messages
        if msg.get_performative() == MessagePerformative.REJECT_DONATION
    ]

    if donation_responses:
        process_donor_response(drone, donation_responses)

    if waste_location_messages:
        for msg in waste_location_messages:
            waste_position = msg.get_content()
            drone.logger.info(f"DONOR: Received waste location at {waste_position}")
            drone.knowledge.target_waste_position = waste_position
            drone.knowledge.donor_status = "idle"
            drone.logger.info("DONOR: Moving to collect donated waste")

    if rejection_messages and not donation_responses and not waste_location_messages:
        # Only handle rejections if no acceptances were received
        drone.logger.info(
            "DONOR: Donation request was rejected, looking for other donors"
        )
        # Try to find other potential donors
        potential_donors = find_potential_donors(drone)
        if potential_donors:
            request_donor(drone, potential_donors)
        else:
            drone.logger.info("DONOR: No other potential donors found, waiting...")


def process_donor_response(drone, response_messages):
    """
    Process donation offer responses received from potential donors.
    Selects the most appropriate donation offer based on distance and availability.
    """
    # Find the closest donor
    closest_donor = min(
        response_messages,
        key=lambda msg: calculate_distance(msg.get_content(), drone.pos),
    )

    donor_id = closest_donor.get_exp()
    donor_pos = closest_donor.get_content()

    drone.logger.info(f"DONOR: Donor {donor_id} at {donor_pos} will drop waste")
    # We'll wait for the INFORM_WASTE_POS_ADD_REF message


def handle_idle_status(drone, new_messages):
    """
    Process incoming messages when drone is in 'idle' state.
    Checks for donation requests from other drones and decides whether to respond.
    """
    # Filter donation request messages
    donation_requests = [
        msg
        for msg in new_messages
        if msg.get_performative() == MessagePerformative.REQUEST_DONATION
    ]

    if (
        donation_requests
        and len(drone.knowledge.inventory) == 1
        and drone.knowledge.inventory[0].waste_color == drone.zone_type
    ):
        process_donor_requests(drone, donation_requests)
    elif donation_requests:
        drone.logger.info(
            "DONOR: Received donation request but have no waste to donate"
        )


def process_donor_requests(drone, requests):
    """
    Evaluate incoming donation requests and select the closest requester.
    Prioritizes requests based on proximity to minimize movement.
    Accepts the closest request and rejects all others.
    """
    # Sort requests by distance
    sorted_requests = sorted(
        requests, key=lambda msg: calculate_distance(msg.get_content(), drone.pos)
    )

    # Accept the closest request
    closest_request = sorted_requests[0]
    requester_id = closest_request.get_exp()
    requester_pos = closest_request.get_content()

    drone.logger.info(
        f"DONOR: Selected request from agent {requester_id} at {requester_pos}"
    )

    # Set donate mode and accept the closest request
    set_donate_mode(drone)
    accept_donor_request(drone, closest_request)

    # Reject all other requests
    if len(sorted_requests) > 1:
        for request in sorted_requests[1:]:
            reject_donor_request(drone, request)


def set_donate_mode(drone):
    """
    Update drone status to prepare for donation process.
    """
    drone.knowledge.donor_status = "donating"
    drone.logger.info("DONOR: Entering donation mode")


def accept_donor_request(drone, request):
    """
    Fulfill a donation request by:
    1. Sending acceptance message to requester
    2. Sending the waste position to the requester
    3. Removing waste from inventory
    """
    requester_id = request.get_exp()
    waste_pos = drone.pos  # Position where waste would be dropped

    # Send acceptance message
    drone.send_message(
        Message(
            message_performative=MessagePerformative.ACCEPT_DONATION,
            from_agent=drone.unique_id,
            to_agent=requester_id,
            content=drone.pos,
        )
    )

    # Remove waste from inventory - simulating dropping without placing in environment
    assert (
        len(drone.knowledge.inventory) == 1
        and drone.knowledge.inventory[0].waste_color == drone.zone_type
    ), "Drone should have one waste item of the correct color"

    drone.knowledge.inventory.pop(0)
    drone.logger.info(f"DONOR: Dropped waste at position {waste_pos}")

    # Inform the requester about the waste position
    drone.send_message(
        Message(
            message_performative=MessagePerformative.INFORM_WASTE_POS_ADD_REF,
            from_agent=drone.unique_id,
            to_agent=requester_id,
            content=waste_pos,
        )
    )

    drone.logger.info(
        f"DONOR: Informed agent {requester_id} about waste at {waste_pos}"
    )

    # Reset donor status
    drone.knowledge.donor_status = "idle"


def reject_donor_request(drone, request):
    """
    Reject a donation request by sending a REJECT_DONATION message.
    """
    requester_id = request.get_exp()

    drone.send_message(
        Message(
            message_performative=MessagePerformative.REJECT_DONATION,
            from_agent=drone.unique_id,
            to_agent=requester_id,
            content=drone.pos,
        )
    )

    drone.logger.info(f"DONOR: Rejected donation request from agent {requester_id}")


def update_carried_waste_timeout(drone, MAX_TIMEOUT_STEP):
    """
    Manage the timeout counter for drones carrying waste.
    When timeout expires, initiates the donor request process if conditions are met.
    """
    if (
        drone.knowledge.carried_waste_timeout > 0
        and len(drone.knowledge.inventory) == 1
        and drone.knowledge.inventory[0].waste_color == drone.zone_type
    ):
        drone.knowledge.carried_waste_timeout -= 1
    elif drone.knowledge.carried_waste_timeout == 0 and drone.zone_type < 2:
        handle_timeout_expiration(drone)


def handle_timeout_expiration(drone):
    """
    Handle logic when carried waste timeout expires by searching
    for potential donors that have waste of the required color.
    """
    # Look for potential donors
    potential_donors = find_potential_donors(drone)

    if potential_donors:
        request_donor(drone, potential_donors)
    else:
        drone.logger.info("DONOR: No potential donors found, waiting")


def find_potential_donors(drone):
    """
    Find drones that could potentially donate waste of the required color.
    Returns a list of suitable drone agents.
    """
    return [
        other_agent
        for other_agent in drone.model.agents
        if other_agent != drone
        and other_agent.__class__.__name__ == "Drone"
        and len(other_agent.knowledge.inventory) == 1
        and other_agent.knowledge.inventory[0].waste_color == drone.zone_type
    ]


def request_donor(drone, potential_donors):
    """
    Send donation requests to all potential donors and update status.
    """
    drone.knowledge.donor_status = "requesting"

    closest_donor = min(
        potential_donors,
        key=lambda donor: calculate_distance(donor.pos, drone.pos),
    )

    drone.logger.info(
        f"DONOR: Sending donation request to agent {closest_donor.unique_id}"
    )
    drone.send_message(
        Message(
            message_performative=MessagePerformative.REQUEST_DONATION,
            from_agent=drone.unique_id,
            to_agent=closest_donor.unique_id,
            content=drone.pos,
        )
    )
