import pytest
from fastapi import HTTPException

from app.models.sevak import RoleEnum
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.department import create_department, update_department


def test_department_hod_assignment_allows_only_sevak_profiles(db_session, make_sevak):
    admin = make_sevak(sevak_id=10000, role=RoleEnum.SUPER_ADMIN, email="admin@example.com")
    hr_candidate = make_sevak(sevak_id=10002, role=RoleEnum.HR, email="hr@example.com")

    with pytest.raises(HTTPException) as exc:
        create_department(
            db_session,
            DepartmentCreate(name="Operations", hod_id=hr_candidate.id),
            admin,
        )

    assert exc.value.status_code == 400
    assert "Only Sevak profiles" in exc.value.detail


def test_department_hod_assignment_promotes_sevak_profile(db_session, make_sevak):
    admin = make_sevak(sevak_id=10000, role=RoleEnum.SUPER_ADMIN, email="admin@example.com")
    sevak = make_sevak(sevak_id=10011, role=RoleEnum.SEVAK, email="sevak@example.com")

    department = create_department(
        db_session,
        DepartmentCreate(name="Operations", hod_id=sevak.id),
        admin,
    )

    db_session.refresh(sevak)
    assert department["hod_id"] == sevak.id
    assert sevak.role == RoleEnum.HOD
    assert sevak.department_id == department["id"]


def test_department_hod_change_demotes_previous_hod_but_keeps_department(db_session, make_sevak):
    admin = make_sevak(sevak_id=10000, role=RoleEnum.SUPER_ADMIN, email="admin@example.com")
    old_hod = make_sevak(sevak_id=10011, role=RoleEnum.SEVAK, email="old-hod@example.com")
    new_hod = make_sevak(sevak_id=10012, role=RoleEnum.SEVAK, email="new-hod@example.com")

    department = create_department(
        db_session,
        DepartmentCreate(name="Operations", hod_id=old_hod.id),
        admin,
    )

    updated = update_department(
        db_session,
        department["id"],
        DepartmentUpdate(hod_id=new_hod.id),
        admin,
    )

    db_session.refresh(old_hod)
    db_session.refresh(new_hod)

    assert updated["hod_id"] == new_hod.id
    assert old_hod.role == RoleEnum.SEVAK
    assert old_hod.department_id == department["id"]
    assert new_hod.role == RoleEnum.HOD
    assert new_hod.department_id == department["id"]
