class Lot:
    def __init__(self, lot_id, material):
        self.lot_id = lot_id
        self.material = material
        self.process_steps = []

    def add_process_step(self, step):
        self.process_steps.append(step)

class DigitalThread:
    def __init__(self):
        self.lots = []

    def add_lot(self, lot):
        self.lots.append(lot)

    def find_lot_by_id(self, lot_id):
        for lot in self.lots:
            if lot.lot_id == lot_id:
                return lot
        return None

    def add_process_step_to_lot(self, lot_id, step):
        lot = self.find_lot_by_id(lot_id)
        if lot:
            lot.add_process_step(step)

    def add_evidence_to_process_step(self, lot_id, step_id, evidence):
        lot = self.find_lot_by_id(lot_id)
        if lot:
            for step in lot.process_steps:
                if step.step_id == step_id:
                    step.evidence = evidence
                    break

class ProcessStep:
    def __init__(self, step_id, process_type):
        self.step_id = step_id
        self.process_type = process_type
        self.evidence = None