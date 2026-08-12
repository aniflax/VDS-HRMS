from app.services.notifications import send_password_reset_email


def send_reset_email(email_to: str, reset_link: str, user_name: str, db=None):
    return send_password_reset_email(
        email_to=email_to,
        reset_link=reset_link,
        user_name=user_name,
        db=db,
    )
