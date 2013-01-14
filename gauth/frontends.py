from gauth.models import User

class ModelFrontend(object):
    create_unknown_user = False
    def authenticate(self, **credentials):
        return None

    def clean_user_token(self, token):
        """
        Performs any cleaning on the "username" prior to using it to get or
        create the user object.  Returns the cleaned username.

        By default, returns the username unchanged.
        """
        return token

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        return user

    def get_user(self, user_token):
        try:
            return User.objects.get(user_token=user_token)
        except User.DoesNotExist:
            return None


class ModelTokenFrontend(ModelFrontend):

    def authenticate(self, user_token=None):
        """
        The username passed as ``remote_user`` is considered trusted.  This
        method simply returns the ``User`` object with the given username,
        creating a new ``User`` object if ``create_unknown_user`` is ``True``.

        Returns None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """
        if not user_token:
            return
        user = None
        user_token = self.clean_user_token(user_token)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = User.objects.get_or_create(user_token=user_token)
            if created:
                user = self.configure_user(user)
        else:
            try:
                user = User.objects.get(user_token=user_token)
            except User.DoesNotExist:
                pass
        return user


class ModelEmailFrontend(ModelTokenFrontend):
    create_unknown_user = False

    def authenticate(self, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None