"""Actions for Blue Current integration."""

from datetime import timedelta
import re
from typing import Any

from bluecurrent_api import Client

from bluecurrent_api.types import OverrideCurrentPayload
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from ...exceptions import ServiceValidationError
from .const import DELAYED_CHARGING, PRICE_BASED_CHARGING, SMART_CHARGING, VALUE, DOMAIN


async def set_user_override(
    hass: HomeAssistant,
    client: Client,
    charge_points: dict[str, dict],
    schedules: dict[str, Any],
    service_call: ServiceCall,
) -> None:
    """Set user override action."""
    device_ids = service_call.data["device_ids"]
    devices = [dr.async_get(hass).devices[device_id] for device_id in device_ids]

    current = service_call.data["current"]

    override_start_time = service_call.data["override_start_time"]
    override_start_days = service_call.data["override_start_days"]

    override_end_time = service_call.data["override_end_time"]
    override_end_days = service_call.data["override_end_days"]

    days_to_code = {
        "monday": "MO",
        "tuesday": "TU",
        "wednesday": "WE",
        "thursday": "TH",
        "friday": "FR",
        "saturday": "SA",
        "sunday": "SU",
    }

    start_day_code = [days_to_code[day] for day in override_start_days]
    end_day_code = [days_to_code[day] for day in override_end_days]

    start_time = timedelta_to_str(override_start_time)
    end_time = timedelta_to_str(override_end_time)

    evse_ids = []
    for device in devices:
        evse_ids.append(next(
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
        ))

    existing_schedule_ids = list(
        {schedule_id for schedule_id, schedule in schedules.items() if bool(set(schedule["charge_points"]) & set(evse_ids))}
    )

    # existing_schedule_ids = list({charge_points[evse_id].get("schedule_id") for evse_id in evse_ids})

    override_current_payload = OverrideCurrentPayload(
            chargepoints=evse_ids,
            overridestarttime=start_time,
            overridestartdays=start_day_code,
            overridestoptime=end_time,
            overridestopdays=end_day_code,
            overridevalue=current,
        )

    # When all charge points in the action has a schedule_id of None, no charge point has a schedule yet.
    if len(existing_schedule_ids) == 0:
        # Create schedule with new data.
        await client.set_user_override_current(override_current_payload)
        print("[0] Created new schedule " + str(override_current_payload))
    # When the schedule id length is but not None, all charge points have the same schedule id.
    elif len(existing_schedule_ids) == 1:
        # Update schedule with new data.
        await client.edit_user_override_current(existing_schedule_ids[0], override_current_payload)
        print("[1] edit user override for schedule: " + str(existing_schedule_ids[0]))
        pass
    # The charge points in the action have different or no schedule id.
    else:
        # Remove charge points from schedule when they have a schedule ID
        for schedule_id in existing_schedule_ids:
            schedules[schedule_id]["charge_points"] = [i for i in schedules[schedule_id]["charge_points"] if not i in evse_ids]
            print("[2] Removing existing schedule with ID " + schedule_id + " " + str(schedules[schedule_id]["charge_points"]))

            if len(schedules[schedule_id]["charge_points"]) == 0:
                schedules.pop(schedule_id)
                print("[3] Schedule with no charge points anymore removed " + schedule_id)
                await client.clear_user_override_current(schedule_id)
            else:
                schedule = schedules[schedule_id]
                # Update the schedule so that the user is removed.
                await client.edit_user_override_current(schedule_id, OverrideCurrentPayload(
                    chargepoints=schedule["charge_points"],
                    overridestarttime=schedule["override_start_time"],
                    overridestartdays=[days_to_code[day] for day in schedule["override_start_days"]],
                    overridestoptime=schedule["override_end_time"],
                    overridestopdays=[days_to_code[day] for day in schedule["override_end_days"]],
                    overridevalue=schedule["current"],
                ))

        print("[4] Set new override current " + str(override_current_payload))
        await client.set_user_override_current(override_current_payload)


def timedelta_to_str(time: timedelta) -> str:
    """Convert time delta to an acceptable string format."""
    seconds = int(time.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"
