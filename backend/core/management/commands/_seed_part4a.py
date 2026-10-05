"""Part 4A seed additions: a platform admin, the second school's admin, a
student-portal login and a pending KYC submission. Safe to re-run."""
from accounts.models import GuardianVerification, User
from tenants.models import School

from ._seed_part2 import _user


def seed_part4a(stdout):
    _user("platform@schooldimes.test", User.Role.PLATFORM_ADMIN, None, "Pat Platform")
    jinja = School.objects.filter(name__icontains="Jinja").first()
    if jinja:
        _user("admin@jinjadss.schooldimes.test", User.Role.SCHOOL_ADMIN, jinja, "Joel Jinja Admin")
    parent2 = User.objects.filter(email="parent2@schooldimes.test").first()
    if parent2 and not hasattr(parent2, "guardian_verification"):
        GuardianVerification.objects.create(parent=parent2, full_name="Sarah Nansubuga",
                                            id_document_type="national_id", id_number="CF90012345XYZ")
    from students.models import Student
    from students.portal import create_portal_account, portal_account_for

    amina = Student.objects.filter(name="Amina Nakato").first()
    if amina and portal_account_for(amina) is None and not User.objects.filter(
            email="student.amina@kampaladps.schooldimes.test").exists():
        create_portal_account(None, amina, email="student.amina@kampaladps.schooldimes.test", password="pw123456")
    stdout.write("Part 4A demo data ready (platform admin, Jinja admin, KYC submission, Amina's student-portal login)")
