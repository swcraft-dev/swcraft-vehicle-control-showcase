.. Written by scripts/generate_requirements_deliveries.py; edit the table there, not this file.

Vehicle control software requirements, delivery 1.0
===================================================

The requirements team's software requirements for the vehicle control architecture.
Synthetic, derived from no real project.

SRS Brake Control
-----------------

.. swreq:: Brake request processing
   :id: SWR-BRK-001
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake controller shall process every brake request within one control cycle.

.. swreq:: Brake request input
   :id: SWR-BRK-002
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake controller shall receive the brake request from the pedal interface.

.. swreq:: Permitted brake action applied
   :id: SWR-BRK-003
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake controller shall apply only the permitted brake action.

.. swreq:: Rear brake temperature use
   :id: SWR-BRK-004
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake controller shall read the rear brake temperature before each brake request is processed.

.. swreq:: Brake request rejection
   :id: SWR-BRK-005
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   A brake request that exceeds the permitted brake action shall be limited, not rejected.

.. swreq:: Brake request timing
   :id: SWR-BRK-006
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   Processing of a brake request shall complete within 10 ms.

.. swreq:: Brake request plausibility
   :id: SWR-BRK-007
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake request shall be checked for plausibility against the operating state.

.. swreq:: Brake pressure ramp
   :id: SWR-BRK-008
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake pressure shall ramp up at no more than 200 bar/s.

.. swreq:: Brake controller start
   :id: SWR-BRK-009
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The brake controller shall be ready to process a brake request 50 ms after start.

.. swreq:: Brake controller degraded mode
   :id: SWR-BRK-010
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   In degraded mode the brake controller shall keep the last permitted brake action.

.. swreq:: Pedal feel
   :id: SWR-BRK-011
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   The pedal feel shall remain constant over the full temperature range.

.. swreq:: Brake request logging
   :id: SWR-BRK-012
   :status: approved
   :document: SRS Brake Control
   :rev: 1

   Each rejected brake request shall be reported to diagnostics.

SRS Thermal Protection
----------------------

.. swreq:: Thermal protection evaluation
   :id: SWR-THP-001
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   Thermal protection shall be evaluated every 50 ms from the brake temperature.

.. swreq:: Thermal protection initialisation
   :id: SWR-THP-002
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   Thermal protection shall be initialised at start with a cold brake assumption.

.. swreq:: Permitted action under fade
   :id: SWR-THP-003
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   When the brake temperature exceeds 600 degC the permitted brake action shall be reduced.

.. swreq:: Thermal protection status
   :id: SWR-THP-004
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   The thermal protection status shall be published to the instrument cluster.

.. swreq:: Thermal protection event
   :id: SWR-THP-005
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   A thermal protection event shall be raised when the permitted brake action is reduced.

.. swreq:: Brake temperature publication
   :id: SWR-THP-006
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   The brake temperature sensor shall publish the brake temperature every 50 ms.

.. swreq:: Brake temperature range
   :id: SWR-THP-007
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   The brake temperature shall be carried from -40 degC to 1000 degC.

.. swreq:: Operating state use
   :id: SWR-THP-008
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   Thermal protection shall take the vehicle operating state into account.

.. swreq:: Temperature sensor fault
   :id: SWR-THP-009
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   A brake temperature sensor fault shall set the thermal protection status to unknown.

.. swreq:: Cooling estimate
   :id: SWR-THP-010
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   The cooling of the brake disc shall be estimated from vehicle speed.

.. swreq:: Fade warning threshold
   :id: SWR-THP-011
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   The fade warning threshold shall be calibratable.

.. swreq:: Thermal protection recovery
   :id: SWR-THP-012
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   Thermal protection shall restore the full permitted brake action below 400 degC.

SRS Diagnostics
---------------

.. swreq:: Diagnostic event processing
   :id: SWR-DIA-001
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   The diagnostic manager shall process every thermal protection event.

.. swreq:: Snapshot storage
   :id: SWR-DIA-002
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   On a thermal protection event the diagnostic manager shall store a snapshot in non-volatile storage.

.. swreq:: Snapshot read service
   :id: SWR-DIA-003
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   The diagnostic manager shall serve a read snapshot request from the tester.

.. swreq:: Brake diagnostics publication
   :id: SWR-DIA-004
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   Brake diagnostics shall be published to the instrument cluster.

.. swreq:: ECU mode dependency
   :id: SWR-DIA-005
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   Diagnostic events shall not be stored while the ECU mode is shutdown.

.. swreq:: NvM write retry
   :id: SWR-DIA-006
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   A failed non-volatile storage write shall be retried once.

.. swreq:: Snapshot content
   :id: SWR-DIA-007
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   A snapshot shall hold the brake temperature and the permitted brake action.

.. swreq:: Event debouncing
   :id: SWR-DIA-008
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   A diagnostic event shall be debounced over three evaluation cycles.

.. swreq:: DTC clearing
   :id: SWR-DIA-009
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   Stored trouble codes shall be cleared only by a tester request.

.. swreq:: Diagnostic session
   :id: SWR-DIA-010
   :status: approved
   :document: SRS Diagnostics
   :rev: 1

   The extended diagnostic session shall time out after 5 s without a request.

SRS Driver Information
----------------------

.. swreq:: Thermal status display
   :id: SWR-DRV-001
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   The instrument cluster shall display the thermal protection status.

.. swreq:: Thermal status update
   :id: SWR-DRV-002
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   The instrument cluster shall update the thermal status within 100 ms.

.. swreq:: Brake diagnostics display
   :id: SWR-DRV-003
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   The instrument cluster shall show brake diagnostics to the driver.

.. swreq:: Odometer display
   :id: SWR-DRV-004
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   The instrument cluster shall display the odometer.

.. swreq:: Warning lamp
   :id: SWR-DRV-005
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   A brake fade warning lamp shall be lit while thermal protection is active.

.. swreq:: Display brightness
   :id: SWR-DRV-006
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   Display brightness shall follow the ambient light sensor.

.. swreq:: Operating state publication
   :id: SWR-DRV-007
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   The vehicle state manager shall publish the operating state every 100 ms.

.. swreq:: Operating state start
   :id: SWR-DRV-008
   :status: approved
   :document: SRS Driver Information
   :rev: 1

   The operating state shall be valid 100 ms after ignition on.

BL-SHOWCASE-001
---------------

.. swreq:: Provide typed context signals
   :id: REQ_SHOWCASE_BASELINE_001
   :status: approved
   :document: BL-SHOWCASE-001
   :rev: 3

   The architecture provides typed context signals for the showcase.

.. swreq:: Provide diagnostic and display endpoints
   :id: REQ_SHOWCASE_BASELINE_002
   :status: approved
   :document: BL-SHOWCASE-001
   :rev: 2

   The architecture provides diagnostic and display endpoints for the showcase.

Requirements without a document
-------------------------------

.. swreq:: Brake temperature resolution
   :id: SWR-GEN-001
   :status: approved
   :rev: 1

   The brake temperature shall have a resolution of 0.1 degC.

.. swreq:: Core load limit
   :id: SWR-GEN-002
   :status: approved
   :rev: 1

   The core load shall stay below 70 percent.

.. swreq:: Service brake availability
   :id: SWR-GEN-003
   :status: approved
   :rev: 1

   The service brake shall remain available after a single fault.

.. swreq:: Software update
   :id: SWR-GEN-004
   :status: approved
   :rev: 1

   The software shall be updatable over the diagnostic interface.

.. swreq:: Brake thermal protection evaluates and publishes
   :id: REQ_SHOWCASE_FEATURE_001
   :status: approved
   :rev: 5

   The brake thermal protection evaluates the brake temperature and publishes the permitted brake action, its status and its events.

.. sgoal:: Prevent brake fade from thermal overload
   :id: REQ_BTP_SAFETY_GOAL
   :status: approved
   :rev: 4
   :safety: D
   :parent: HAZ_BTP_BRAKE_FADE

   Safety goal: the brake system shall not lose braking capability because the brakes overheat. Decomposed into REQ_BTP_DECOMP_MAIN and REQ_BTP_DECOMP_MONITOR, each ASIL B(D). Illustrative.

Test cases
----------

.. test:: Brake request processing test
   :id: TC-BRK-001
   :status: approved
   :rev: 1

   Apply a brake request and check that it is processed within one control cycle.

.. test:: Fade derating test
   :id: TC-THP-001
   :status: approved
   :rev: 1

   Heat the brake above the derating threshold and check that the permitted brake action is reduced.

.. only:: swcraft

   Architecture requirements (SWCraft)
   -----------------------------------

   .. needtable::
      :filter: is_external and type in ["arch_req", "arch_spec"]
      :columns: id, title, derived_from as "Derived from", satisfies_back as "Satisfied by", satisfies_unconfirmed_back as "Satisfied by (unconfirmed)"
      :style: table
