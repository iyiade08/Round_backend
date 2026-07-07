from django.conf import settings
from firebase_admin import auth, credentials, get_app, initialize_app


def get_firebase_app():
    try:
        return get_app()
    except ValueError:
        options = {}
        if settings.FIREBASE_STORAGE_BUCKET:
            options["storageBucket"] = settings.FIREBASE_STORAGE_BUCKET

        if settings.FIREBASE_CREDENTIALS_PATH:
            credential = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            return initialize_app(credential, options)

        return initialize_app(options=options)


def verify_id_token(id_token):
    return auth.verify_id_token(
        id_token,
        app=get_firebase_app(),
        clock_skew_seconds=60,
    )


def update_user_password(*, email, password, firebase_uid=""):
    app = get_firebase_app()
    if firebase_uid:
        auth.update_user(firebase_uid, password=password, app=app)
        return

    firebase_user = auth.get_user_by_email(email, app=app)
    auth.update_user(firebase_user.uid, password=password, app=app)
