/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady(function () {

    const doctorSelect = document.getElementById("doctor_id");
    const dateInput    = document.getElementById("appointment_date");
    const slotSelect   = document.getElementById("slot_time");
    const slotGrid     = document.getElementById("slot-grid");
    const summaryBox   = document.getElementById("appt-summary");
    const summaryText  = document.getElementById("summary-text");

    if (!doctorSelect || !dateInput || !slotSelect) {
        console.log("Appointment elements not found");
        return;
    }

    // ── Set min date to today  [ORIGINAL — unchanged] ──────────
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
    dateInput.disabled = true;

    let availableDays = [];

    // ── loadAvailableDays  [ORIGINAL — unchanged] ───────────────
    async function loadAvailableDays(doctorId) {
        if (!doctorId) {
            availableDays      = [];
            dateInput.value    = '';
            dateInput.disabled = true;
            slotSelect.innerHTML = '<option value="">-- Select Time Slot --</option>';
            renderSlotGrid();
            return;
        }
        try {
            const response = await fetch('/get-doctor-available-days', {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method:  "call",
                    params:  { doctor_id: parseInt(doctorId) },
                    id:      Date.now(),
                }),
            });
            const data    = await response.json();
            availableDays = data.result || [];
            dateInput.value      = '';
            dateInput.disabled   = false;
            slotSelect.innerHTML = '<option value="">-- Select Time Slot --</option>';
            renderSlotGrid();
        } catch (error) {
            console.error("Available days load error:", error);
            availableDays = [];
        }
    }

    // ── isDateAvailable  [ORIGINAL — unchanged] ─────────────────
    function isDateAvailable(dateStr) {
        if (!availableDays.length) return true;
        const date   = new Date(dateStr);
        const jsDay  = date.getDay();
        const ourDay = jsDay === 0 ? '6' : String(jsDay - 1);
        return availableDays.includes(ourDay);
    }

    // ── loadSlots  [ORIGINAL — unchanged] ───────────────────────
    async function loadSlots() {
        const doctor = doctorSelect.value;
        const date   = dateInput.value;

        slotSelect.innerHTML = '<option value="">Loading...</option>';
        renderSlotGrid();

        if (!doctor || !date) {
            slotSelect.innerHTML = '<option value="">-- Select Time Slot --</option>';
            renderSlotGrid();
            return;
        }

        if (!isDateAvailable(date)) {
            dateInput.value      = '';
            slotSelect.innerHTML = '<option value="">-- Select Time Slot --</option>';
            renderSlotGrid();
            alert("Doctor is not available on this day. Please select another date.");
            return;
        }

        try {
            const response = await fetch('/get-available-slots', {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method:  "call",
                    params: { doctor_id: parseInt(doctor), date: date },
                    id:     Date.now(),
                }),
            });

            const data = await response.json();
            slotSelect.innerHTML = '<option value="">-- Select Time Slot --</option>';

            if (data.result && data.result.length > 0) {
                let hasAvailable = false;
                data.result.forEach(slot => {
                    const option        = document.createElement("option");
                    const [hourStr, minStr] = slot.time.split(":");
                    let hour            = parseInt(hourStr);
                    const ampm          = hour >= 12 ? "PM" : "AM";
                    hour                = hour % 12 || 12;
                    const display12     = `${hour}:${minStr} ${ampm}`;
                    const duration      = slot.duration ? ` (${slot.duration} min)` : '';
                    if (slot.is_booked) {
                        option.value           = "";
                        option.textContent     = `${display12}${duration} — Booked`;
                        option.disabled        = true;
                        option.style.color     = "#dc3545";
                        option.style.fontStyle = "italic";
                    } else {
                        option.value       = slot.time + "|" + slot.shift_id;
                        option.textContent = `${display12}${duration} — Available`;
                        option.style.color = "#198754";
                        hasAvailable       = true;
                    }
                    slotSelect.appendChild(option);
                });
                if (!hasAvailable) {
                    const option       = document.createElement("option");
                    option.value       = "";
                    option.textContent = "All slots are booked for this day";
                    option.disabled    = true;
                    slotSelect.appendChild(option);
                }
            } else {
                const option       = document.createElement("option");
                option.value       = "";
                option.textContent = "No slots available for this day";
                option.disabled    = true;
                slotSelect.appendChild(option);
            }
            renderSlotGrid();

        } catch (error) {
            console.error("Slot Load Error:", error);
            slotSelect.innerHTML = '<option value="">Error Loading Slots</option>';
            renderSlotGrid();
        }
    }

    // ── renderSlotGrid  [NEW — UI only] ─────────────────────────
    function renderSlotGrid() {
        if (!slotGrid) return;

        slotGrid.innerHTML = "";
        if (summaryBox) summaryBox.classList.remove("visible");

        const options = Array.from(slotSelect.options);

        // ── KEY FIX: if more than 1 option exists, always render
        //    buttons regardless of what the first option says.
        //    Only show placeholder when there is exactly 1 option
        //    (the default/loading/error message).
        if (options.length <= 1) {
            const msg            = document.createElement("p");
            msg.className        = "appt-slots-placeholder";
            msg.style.gridColumn = "1 / -1";
            msg.textContent      = options[0]
                ? options[0].textContent
                : "Select a doctor and date to see slots.";
            slotGrid.appendChild(msg);
            return;
        }

        // Render each slot as a clickable button (skip index 0 placeholder)
        options.forEach(function (opt) {
            if (opt.index === 0 && opt.value === "") return;

            const btn       = document.createElement("button");
            btn.type        = "button";
            btn.className   = "appt-slot-btn";

            const parts     = opt.textContent.split(" — ");
            btn.textContent = parts[0] || opt.textContent;

            if (opt.disabled) {
                btn.classList.add("appt-slot-booked");
                btn.disabled = true;
                btn.title    = "Already booked";
            } else {
                btn.addEventListener("click", function () {
                    slotGrid.querySelectorAll(".appt-slot-btn").forEach(function (b) {
                        b.classList.remove("appt-slot-selected");
                    });
                    btn.classList.add("appt-slot-selected");

                    // Set value on slotSelect — form POST reads from here
                    slotSelect.value = opt.value;

                    if (summaryBox && summaryText) {
                        const dateVal   = dateInput.value;
                        const selIdx    = doctorSelect.selectedIndex;
                        const doctorTxt = selIdx >= 0
                            ? doctorSelect.options[selIdx].textContent.trim()
                            : "";
                        if (dateVal && doctorTxt) {
                            const d       = new Date(dateVal);
                            const dateStr = d.toLocaleDateString('en-US', {
                                weekday: 'long',
                                year:    'numeric',
                                month:   'long',
                                day:     'numeric',
                            });
                            summaryText.textContent =
                                "Booking with " + doctorTxt +
                                " on " + dateStr +
                                " at " + parts[0];
                            summaryBox.classList.add("visible");
                        }
                    }
                });
            }
            slotGrid.appendChild(btn);
        });
    }

    // ── Event Listeners  [ORIGINAL — unchanged] ─────────────────
    doctorSelect.addEventListener("change", async function () {
        await loadAvailableDays(this.value);
    });

    dateInput.addEventListener("change", loadSlots);

    // ── Form submit validation — ensure a slot is selected ──────
    const apptForm = document.getElementById("appt-form");
    if (apptForm) {
        apptForm.addEventListener("submit", function (e) {
            if (!slotSelect.value) {
                e.preventDefault();
                if (slotGrid) {
                    slotGrid.style.outline      = "2px solid #ff4d4d";
                    slotGrid.style.borderRadius = "8px";
                    setTimeout(function () {
                        slotGrid.style.outline      = "";
                        slotGrid.style.borderRadius = "";
                    }, 2000);
                }
                alert("Please select a time slot before confirming.");
            }
        });
    }

});


