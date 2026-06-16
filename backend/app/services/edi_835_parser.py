def parse_835_file(raw_text: str):
    """
    Basic 835 parser (simplified).
    Extract key fields for payment posting.
    """

    lines = raw_text.split("~")

    payments = []

    current_payment = {}

    for line in lines:
        parts = line.split("*")

        if parts[0] == "CLP":
            current_payment = {
                "claim_control_number": parts[1],
                "total_charge": float(parts[3]),
                "paid_amount": float(parts[4]),
                "status": parts[2]
            }

        if parts[0] == "NM1":
            if parts[1] == "QC":
                current_payment["patient_name"] = parts[3]

        if parts[0] == "DTM":
            current_payment["payment_date"] = parts[2]

        if parts[0] == "SE":
            payments.append(current_payment)

    return payments