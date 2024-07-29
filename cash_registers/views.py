from cash_registers.models import CashRegister, Shift


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def open_shift(cash_register_id: int, doctor_profile_id: int):
    check_shift = Shift.check_shift(cash_register_id, doctor_profile_id)
    if not check_shift["ok"]:
        return check_shift
    new_shift = Shift.open_shift(cash_register_id, doctor_profile_id)
    data = {"cashRegisterId": new_shift["cash_register_id"], "shiftId": new_shift["shift_id"]}
    return {"ok": True, "message": "", "data": data}


def close_shift(doctor_profile_id: int):
    result = Shift.close_shift(doctor_profile_id)
    return {"ok": result, "message": ""}
