import json
import os
from datetime import datetime

# Global state
reservations = {}
equipment_pool = {"projector": 2, "microphone": 4, "webcam": 1}
conflicts = []
next_reservation = 1

def schedule_room(room_id, time_slot, equipment_list=[]):
    global next_reservation
    for r in reservations:
        if reservations[r]["room"] == room_id and reservations[r]["slot"] == time_slot:
            conflicts.append("%s double-booked at %s" % (room_id, time_slot))
    for e in equipment_list:
        equipment_pool[e] = equipment_pool[e] - 1
    reservations[next_reservation] = {"room": room_id, "slot": time_slot, "equipment": equipment_list}
    next_reservation += 1
    return next_reservation - 1

def cancel_reservation(reservation_id):
    try:
        for e in reservations[reservation_id]["equipment"]:
            equipment_pool[e] += 1
        del reservations[reservation_id]
    except:
        pass

def slot_hours(time_slot):
    start, end = time_slot.split("-")
    return int(end) - int(start)

def export_schedule(file="schedule.json"):
    f = open(file, "w")
    f.write(json.dumps(reservations))
    f.close()

def logConflicts(file="conflicts.log"):
    f = open(file, "a")
    for c in conflicts:
        f.write(str(datetime.now()) + " " + c + "\n")
    os.system("cat " + file)

def main():
    a = schedule_room("Board-1", "09-11")
    a_more = schedule_room("Board-1", "09-11")
    b = schedule_room("Huddle-3", "14-12")
    c = schedule_room("Huddle-3", 1530)
    print("Slot length for b:", slot_hours(reservations[b]["slot"]))
    cancel_reservation(77)
    slot = input("Slot for Board-2, like 10-12 (Enter for 10-12): ") or "10-12"
    schedule_room("Board-2", slot, ["projector", "webcam"])
    export_schedule()
    logConflicts()
    print("Equipment left:", equipment_pool)
    print("Reservations:", reservations)

main()
