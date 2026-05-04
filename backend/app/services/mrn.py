import uuid

def generate_mrn() -> str:
    """
    Generate a unique Medical Record Number.
    Not guessable, not sequential.
    """
    return f"MRN-{uuid.uuid4().hex[:10].upper()}"