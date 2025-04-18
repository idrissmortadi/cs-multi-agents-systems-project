    def _solve_deadlock(self, new_messages):
        # ================ DEADLOCK CHECK ================
        self.is_deadlocked = (
            self.knowledge.carry_timeout <= 0
            and self.zone_type < 2
            and len(self.knowledge.inventory) == 1
            and self.knowledge.inventory[0].waste_color == self.knowledge.zone_type
        )

        if (
            not self.is_deadlocked
            or self.knowledge.deadlock_status == "waiting_for_giver"
        ):
            return

        self.logger.info(
            f"DEADLOCK: Proposing to other agents (timeout: {self.knowledge.carry_timeout})"
        )

        self._already_proposed = False
        if not self._already_proposed:
            self.send_broadcast_message(
                MessagePerformative.PROPOSE_WASTE,
                (self.knowledge.inventory[0].waste_color, self.pos),
            )
        self._already_proposed = True
        self.knowledge.deadlock_status = "proposing"

        # ==== handle PROPOSE_WASTE when we’re idle =====
        if self.knowledge.deadlock_status == "idle":
            deadlock_messages = [
                m
                for m in new_messages
                if m.get_performative() == MessagePerformative.PROPOSE_WASTE
            ]

            closest_agent = min(
                deadlock_messages,
                key=lambda m: (
                    abs(self.pos[0] - m.get_content()[1][0])
                    + abs(self.pos[1] - m.get_content()[1][1])
                ),
                default=None,
            )

            print(f"received {len(deadlock_messages)} proposals")
            if closest_agent:
                self.logger.info(
                    f"DEADLOCK: Received proposal from agent {closest_agent.get_sender()} at {closest_agent.get_content()[1]}"
                )
                # Send accept
                self.send_message(
                    Message(
                        from_agent=self.unique_id,
                        to_agent=closest_agent.get_exp(),
                        performative=MessagePerformative.ACCEPT_WASTE,
                        content=(self.knowledge.inventory[0].waste_color, self.pos),
                    )
                )

                self.knowledge.deadlock_status = "waiting_for_giver"
                self._wait_timeout = MAX_CARRY_TIMEOUT  # Set a timeout for waiting
                return

        # ==== handle ACCEPT_WASTE when we’re waiting for a giver =====
        if self.knowledge.deadlock_status == "waiting_for_giver":
            self._wait_timeout -= 1
            if self._wait_timeout <= 0:
                self.logger.info("DEADLOCK: No response, moving randomly")
                self.knowledge.deadlock_status = "idle"
                return

        # ===== handle ACCEPT_WASTE when we’ve proposed =====
        if self.knowledge.deadlock_status == "proposing":
            accepts = [
                m
                for m in new_messages
                if m.get_performative() == MessagePerformative.ACCEPT_WASTE
            ]
            if accepts:
                # pick the closest acceptor
                chosen = min(
                    accepts,
                    key=lambda m: abs(self.pos[0] - m.get_content()[1][0])
                    + abs(self.pos[1] - m.get_content()[1][1]),
                )
                target_id, target_pos = chosen.get_sender(), chosen.get_content()[1]
                self.transfer_target = target_id
                self.knowledge.deadlock_status = "moving_to_give"
                self.knowledge.target_pos = target_pos
                self.logger.info(
                    f"DEADLOCK: Moving to give waste to agent {target_id} at {target_pos}"
                )
                return