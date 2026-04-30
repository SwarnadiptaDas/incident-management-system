from abc import ABC, abstractmethod
from models import SeverityEnum, StateEnum, WorkItem
import logging

# Set up structured logging
logger = logging.getLogger("ims_engine")
logger.setLevel(logging.INFO)

# =========================================================================
# STRATEGY PATTERN: Alerting Logic
# This uses the Strategy Pattern to dynamically switch alerting logic based
# on incident severity. This allows adding new notification channels (e.g., SMS)
# without modifying the core worker engine.
# =========================================================================

class AlertStrategy(ABC):
    @abstractmethod
    def alert(self, signal_data: dict, work_item_id: int):
        pass

class P0AlertStrategy(AlertStrategy):
    """Critical priority: Immediate PagerDuty/Incident command escalation."""
    def alert(self, signal_data: dict, work_item_id: int):
        logger.error(f"🚨 [STRATEGY: P0] Immediate Escalation for {signal_data['component_id']}! "
                     f"Work Item: #{work_item_id}")

class P1AlertStrategy(AlertStrategy):
    """High priority: Slack/Email notification to on-call engineers."""
    def alert(self, signal_data: dict, work_item_id: int):
        logger.warning(f"⚠️ [STRATEGY: P1] High Priority Alert for {signal_data['component_id']}. "
                       f"Work Item: #{work_item_id}")

class P2AlertStrategy(AlertStrategy):
    """Normal priority: Logged and added to daily summary reports."""
    def alert(self, signal_data: dict, work_item_id: int):
        logger.info(f"ℹ️ [STRATEGY: P2/P3] Logged for {signal_data['component_id']}. "
                    f"Work Item: #{work_item_id}")

def get_alert_strategy(severity: SeverityEnum) -> AlertStrategy:
    strategies = {
        SeverityEnum.P0: P0AlertStrategy(),
        SeverityEnum.P1: P1AlertStrategy(),
        SeverityEnum.P2: P2AlertStrategy(),
        SeverityEnum.P3: P2AlertStrategy(),
    }
    return strategies.get(severity, P2AlertStrategy())


# =========================================================================
# STATE PATTERN: Incident Lifecycle
# This implements the State Pattern to manage lifecycle transitions safely.
# It prevents invalid transitions (e.g., closing an incident without RCA)
# and ensures the workflow integrity.
# =========================================================================

class IncidentState(ABC):
    @abstractmethod
    def handle_transition(self, work_item: WorkItem, new_state: StateEnum):
        pass

class OpenState(IncidentState):
    def handle_transition(self, work_item: WorkItem, new_state: StateEnum):
        if new_state in [StateEnum.INVESTIGATING, StateEnum.RESOLVED]:
            work_item.state = new_state
        elif new_state == StateEnum.CLOSED:
            raise ValueError("STATE ERROR: Cannot close directly from OPEN. Must resolve first.")
        else:
            raise ValueError(f"STATE ERROR: Invalid transition from OPEN to {new_state}")

class InvestigatingState(IncidentState):
    def handle_transition(self, work_item: WorkItem, new_state: StateEnum):
        if new_state == StateEnum.RESOLVED:
            work_item.state = new_state
        elif new_state == StateEnum.OPEN:
             work_item.state = new_state
        else:
            raise ValueError(f"STATE ERROR: Invalid transition from INVESTIGATING to {new_state}")

class ResolvedState(IncidentState):
    def handle_transition(self, work_item: WorkItem, new_state: StateEnum):
        if new_state == StateEnum.CLOSED:
            # STRICT RCA VALIDATION: Enforced at the state transition level
            if not all([work_item.rca_category, work_item.fix_applied, work_item.prevention_steps]):
                raise ValueError("VALIDATION ERROR: RCA Category, Fix, and Prevention are mandatory to CLOSE.")
            work_item.state = new_state
        elif new_state == StateEnum.INVESTIGATING:
            work_item.state = new_state
        else:
            raise ValueError(f"STATE ERROR: Invalid transition from RESOLVED to {new_state}")

class ClosedState(IncidentState):
    def handle_transition(self, work_item: WorkItem, new_state: StateEnum):
        raise ValueError("STATE ERROR: Incident is CLOSED and final.")

class WorkflowEngine:
    """Entry point for state transitions."""
    @staticmethod
    def transition(work_item: WorkItem, new_state: StateEnum):
        state_map = {
            StateEnum.OPEN: OpenState(),
            StateEnum.INVESTIGATING: InvestigatingState(),
            StateEnum.RESOLVED: ResolvedState(),
            StateEnum.CLOSED: ClosedState(),
        }
        handler = state_map.get(work_item.state)
        handler.handle_transition(work_item, new_state)
