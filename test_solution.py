import unittest

class Material:
    def __init__(self, material_id, material_type):
        self.material_id = material_id
        self.material_type = material_type

class Lot:
    def __init__(self, lot_id, material):
        self.lot_id = lot_id
        self.material = material
        self.process_steps = []

    def add_process_step(self, step):
        self.process_steps.append(step)

class ProcessStep:
    def __init__(self, step_id, process_type):
        self.step_id = step_id
        self.process_type = process_type
        self.evidence = None

class Evidence:
    def __init__(self, evidence_id, evidence_type, is_valid):
        self.evidence_id = evidence_id
        self.evidence_type = evidence_type
        self.is_valid = is_valid

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

class TestMaterial(unittest.TestCase):
    def test_material_initialization(self):
        material = Material("123", "Steel")
        self.assertEqual(material.material_id, "123")
        self.assertEqual(material.material_type, "Steel")

class TestLot(unittest.TestCase):
    def test_lot_initialization(self):
        material = Material("123", "Steel")
        lot = Lot("A1", material)
        self.assertEqual(lot.lot_id, "A1")
        self.assertEqual(lot.material, material)
        self.assertEqual(lot.process_steps, [])

    def test_add_process_step(self):
        material = Material("123", "Steel")
        lot = Lot("A1", material)
        step = ProcessStep("S1", "Manufacturing")
        lot.add_process_step(step)
        self.assertEqual(lot.process_steps, [step])

class TestProcessStep(unittest.TestCase):
    def test_process_step_initialization(self):
        step = ProcessStep("S1", "Manufacturing")
        self.assertEqual(step.step_id, "S1")
        self.assertEqual(step.process_type, "Manufacturing")
        self.assertIsNone(step.evidence)

    def test_add_evidence(self):
        step = ProcessStep("S1", "Manufacturing")
        evidence = Evidence("E1", "Certificate", True)
        step.evidence = evidence
        self.assertEqual(step.evidence, evidence)

class TestEvidence(unittest.TestCase):
    def test_evidence_initialization(self):
        evidence = Evidence("E1", "Certificate", True)
        self.assertEqual(evidence.evidence_id, "E1")
        self.assertEqual(evidence.evidence_type, "Certificate")
        self.assertTrue(evidence.is_valid)

class TestDigitalThread(unittest.TestCase):
    def test_digital_thread_initialization(self):
        dt = DigitalThread()
        self.assertEqual(dt.lots, [])

    def test_add_lot(self):
        dt = DigitalThread()
        material = Material("123", "Steel")
        lot = Lot("A1", material)
        dt.add_lot(lot)
        self.assertEqual(dt.lots, [lot])

    def test_find_lot_by_id(self):
        dt = DigitalThread()
        material = Material("123", "Steel")
        lot = Lot("A1", material)
        dt.add_lot(lot)
        found_lot = dt.find_lot_by_id("A1")
        self.assertEqual(found_lot, lot)

    def test_add_process_step_to_lot(self):
        dt = DigitalThread()
        material = Material("123", "Steel")
        lot = Lot("A1", material)
        dt.add_lot(lot)
        step = ProcessStep("S1", "Manufacturing")
        dt.add_process_step_to_lot("A1", step)
        self.assertEqual(lot.process_steps, [step])

    def test_add_evidence_to_process_step(self):
        dt = DigitalThread()
        material = Material("123", "Steel")
        lot = Lot("A1", material)
        dt.add_lot(lot)
        step = ProcessStep("S1", "Manufacturing")
        dt.add_process_step_to_lot("A1", step)  # Ensure process step is added to lot
        evidence = Evidence("E1", "Certificate", True)
        dt.add_evidence_to_process_step("A1", "S1", evidence)
        self.assertEqual(lot.process_steps[0].evidence, evidence)

if __name__ == '__main__':
    unittest.main()