"""Conference room and equipment scheduler.

This module books meeting rooms for time slots, allocates shared equipment
such as projectors and webcams, logs double-bookings and exports the final
schedule to a JSON file.
"""

import json
from datetime import datetime


class Scheduler:
    """Manages room reservations and the shared pool of equipment."""

    def __init__(self):
        """Initialise the scheduler with empty state and default equipment."""
        self.reservations = {}
        self.equipment_pool = {"projector": 2, "microphone": 4, "webcam": 1}
        self.conflicts = []
        self._next_reservation = 1

    def schedule_room(self, room_id, time_slot, equipment_list=None):
        """Book ``room_id`` for ``time_slot`` and allocate its equipment."""
        if equipment_list is None:
            equipment_list = []
        for reservation in self.reservations.values():
            if (reservation["room"] == room_id
                    and reservation["slot"] == time_slot):
                self.conflicts.append(f"{room_id} double-booked at {time_slot}")
        for equipment in equipment_list:
            self.equipment_pool[equipment] -= 1
        self.reservations[self._next_reservation] = {
            "room": room_id,
            "slot": time_slot,
            "equipment": equipment_list,
        }
        self._next_reservation += 1
        return self._next_reservation - 1

    def cancel_reservation(self, reservation_id):
        """Release a reservation's equipment and remove the reservation."""
        try:
            reservation = self.reservations[reservation_id]
        except KeyError:
            return
        for equipment in reservation["equipment"]:
            self.equipment_pool[equipment] += 1
        del self.reservations[reservation_id]

    @staticmethod
    def slot_hours(time_slot):
        """Return the number of hours spanned by a ``start-end`` slot."""
        start, end = time_slot.split("-")
        return int(end) - int(start)

    def export_schedule(self, file_path="schedule.json"):
        """Write the current reservations to ``file_path`` as JSON."""
        with open(file_path, "w", encoding="utf-8") as output:
            json.dump(self.reservations, output)

    def log_conflicts(self, file_path="conflicts.log"):
        """Append conflicts to ``file_path`` and print them to stdout."""
        with open(file_path, "a", encoding="utf-8") as log_file:
            for conflict in self.conflicts:
                line = f"{datetime.now()} {conflict}\n"
                log_file.write(line)
                print(line, end="")


def main():
    """Demonstrate the scheduler with a short scripted run."""
    scheduler = Scheduler()
    scheduler.schedule_room("Board-1", "09-11")
    scheduler.schedule_room("Board-1", "09-11")
    booking_b = scheduler.schedule_room("Huddle-3", "12-14")
    scheduler.schedule_room("Huddle-3", "15-16")
    print("Slot length for b:", scheduler.slot_hours(scheduler.reservations[booking_b]["slot"]))
    scheduler.cancel_reservation(77)
    slot = input("Slot for Board-2, like 10-12 (Enter for 10-12): ") or "10-12"
    scheduler.schedule_room("Board-2", slot, ["projector", "webcam"])
    scheduler.export_schedule()
    scheduler.log_conflicts()
    print("Equipment left:", scheduler.equipment_pool)
    print("Reservations:", scheduler.reservations)


if __name__ == "__main__":
    main()
