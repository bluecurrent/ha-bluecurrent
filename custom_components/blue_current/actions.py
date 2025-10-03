"""Actions for Blue Current integration."""

from datetime import timedelta
import re
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.types import (
    OverrideCurrentPayload,
)

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import (
    CHARGE_POINTS,
    CURRENT,
    DEVICE_IDS,
    DOMAIN,
    FRIDAY,
    MONDAY,
    OVERRIDE_END_DAYS,
    OVERRIDE_END_TIME,
    OVERRIDE_START_DAYS,
    OVERRIDE_START_TIME,
    SATURDAY,
    START_TIME,
    SUNDAY,
    THURSDAY,
    TUESDAY,
    WEDNESDAY,
    STOP_TIME,
)


async def set_user_override(
    hass: HomeAssistant,
    client: Client,
    schedules: dict[str, Any],
    service_call: ServiceCall,
) -> None:
    """Set user override action."""
    device_ids = service_call.data[DEVICE_IDS]
    devices = [dr.async_get(hass).devices[device_id] for device_id in device_ids]

    current = service_call.data[CURRENT]

    override_start_time = service_call.data[OVERRIDE_START_TIME]
    override_start_days = service_call.data[OVERRIDE_START_DAYS]

    override_end_time = service_call.data[OVERRIDE_END_TIME]
    override_end_days = service_call.data[OVERRIDE_END_DAYS]

    days_to_code = {
        MONDAY: "MO",
        TUESDAY: "TU",
        WEDNESDAY: "WE",
        THURSDAY: "TH",
        FRIDAY: "FR",
        SATURDAY: "SA",
        SUNDAY: "SU",
    }

    start_day_code = [days_to_code[day] for day in override_start_days]
    end_day_code = [days_to_code[day] for day in override_end_days]

    start_time = timedelta_to_str(override_start_time)
    end_time = timedelta_to_str(override_end_time)

    evse_ids = [
        next(
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
        )
        for device in devices
    ]

    existing_schedule_ids = list(
        {
            schedule_id
            for schedule_id, schedule in schedules.items()
            if bool(set(schedule["charge_points"]) & set(evse_ids))
        }
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
    # When the schedule id length is but not None, all charge points have the same schedule id.
    elif len(existing_schedule_ids) == 1:
        # Update schedule with new data.

        # TODO: Add Check if the given charge points are the same (or added) looking at the original schedule
        # TODO: When one charge point is missing, create a NEW schedule with the new values and update the OLD schedule
        # that removes the currently selected charge points in the action.

        await client.edit_user_override_current(
            existing_schedule_ids[0], override_current_payload
        )

    # The charge points in the action have different or no schedule id.
    else:
        # Remove charge points from schedule when they have a schedule ID
        for schedule_id in existing_schedule_ids:
            schedules[schedule_id][CHARGE_POINTS] = [
                i for i in schedules[schedule_id][CHARGE_POINTS] if i not in evse_ids
            ]

            if len(schedules[schedule_id][CHARGE_POINTS]) == 0:
                schedules.pop(schedule_id)
                await client.clear_user_override_current(schedule_id)
                await client.wait_for_clear_override_current()
            else:
                schedule = schedules[schedule_id]
                # Update the schedule so that the user is removed.
                await client.edit_user_override_current(
                    schedule_id,
                    OverrideCurrentPayload(
                        chargepoints=schedule[CHARGE_POINTS],
                        overridestarttime=schedule[START_TIME],
                        overridestartdays=schedule[OVERRIDE_START_DAYS],
                        overridestoptime=schedule[STOP_TIME],
                        overridestopdays=schedule[OVERRIDE_END_DAYS],
                        overridevalue=schedule["override_current"],
                    ),
                )

                await client.wait_for_update_override_current()

        await client.set_user_override_current(override_current_payload)


def timedelta_to_str(time: timedelta) -> str:
    """Convert time delta to an acceptable string format."""
    seconds = int(time.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"
